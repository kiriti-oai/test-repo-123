"""Temporal workflow that orchestrates pull request creation inside CaaS.

The implementation focuses on the orchestration logic and the data
structures that will be useful for unit tests.  The individual activities
return structured objects that describe the operations performed instead
of executing real side effects.  This keeps the module lightweight while
still reflecting the behaviour of the production workflow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence
from uuid import uuid4

from temporalio import activity, workflow

__all__ = [
    "ApplySedimentActivityInput",
    "ApplySedimentActivityResult",
    "CloneRepositoryActivityInput",
    "CloneRepositoryActivityResult",
    "ContainerConfig",
    "ContainerHandle",
    "CreateBranchAndPushActivityInput",
    "CreateBranchAndPushActivityResult",
    "CreatePullRequestWorkflow",
    "CreatePullRequestWorkflowInput",
    "CreatePullRequestWorkflowResult",
    "GitCloneOptions",
    "GitCommitOptions",
    "PushOptions",
    "SedimentArtifact",
    "WorkflowStep",
    "run_create_pull_request_workflow",
]


@dataclass(frozen=True)
class ContainerConfig:
    """Configuration used when creating a CaaS container."""

    image: str
    command: Sequence[str] = field(default_factory=tuple)
    environment: dict[str, str] = field(default_factory=dict)
    workspace_dir: str = "/workspace"
    idle_timeout_seconds: int = 600


@dataclass(frozen=True)
class ContainerHandle:
    """Reference to a provisioned container."""

    container_id: str
    workspace_dir: str


@dataclass(frozen=True)
class GitCloneOptions:
    """Options describing how the repository should be cloned."""

    repository_url: str
    branch: str
    depth: int = 1
    sparse_paths: Optional[Sequence[str]] = None


@dataclass(frozen=True)
class SedimentArtifact:
    """Reference to the sediment diff that should be applied."""

    storage_key: str
    filename: str = "sediment.patch"


@dataclass(frozen=True)
class GitCommitOptions:
    """Data used when creating the commit for the new branch."""

    message: str
    author_name: str
    author_email: str


@dataclass(frozen=True)
class PushOptions:
    """Configuration for pushing the prepared branch to the remote."""

    remote: str = "origin"
    force: bool = False


@dataclass(frozen=True)
class WorkflowStep:
    """Single high level step executed by the workflow."""

    name: str
    description: str
    commands: Sequence[Sequence[str]]


@dataclass(frozen=True)
class CloneRepositoryActivityInput:
    container: ContainerHandle
    options: GitCloneOptions
    checkout_path: str = "repo"


@dataclass(frozen=True)
class CloneRepositoryActivityResult:
    repository_path: str
    commands: Sequence[Sequence[str]]


@dataclass(frozen=True)
class ApplySedimentActivityInput:
    container: ContainerHandle
    repository_path: str
    sediment: SedimentArtifact


@dataclass(frozen=True)
class ApplySedimentActivityResult:
    commands: Sequence[Sequence[str]]


@dataclass(frozen=True)
class CreateBranchAndPushActivityInput:
    container: ContainerHandle
    repository_path: str
    new_branch: str
    base_branch: str
    commit: GitCommitOptions
    push: PushOptions


@dataclass(frozen=True)
class CreateBranchAndPushActivityResult:
    commands: Sequence[Sequence[str]]
    commit_sha: str


@dataclass(frozen=True)
class CreatePullRequestWorkflowInput:
    """Aggregated configuration for the workflow run."""

    container: ContainerConfig
    clone: GitCloneOptions
    sediment: SedimentArtifact
    new_branch: str
    commit: GitCommitOptions
    push: PushOptions = field(default_factory=PushOptions)


@dataclass(frozen=True)
class CreatePullRequestWorkflowResult:
    """Result returned when the workflow finishes."""

    new_branch: str
    container_id: str
    commit_sha: str
    steps: Sequence[WorkflowStep]


@activity.defn(name="pr_creator.start_caas_container")
def start_caas_container(container: ContainerConfig) -> ContainerHandle:
    """Provision a container and return the handle.

    The activity mimics the real behaviour by returning a deterministic
    identifier.  Unit tests can inspect the identifier to ensure that the
    workflow performed this step.
    """

    container_id = f"caas-{uuid4().hex}"
    return ContainerHandle(container_id=container_id, workspace_dir=container.workspace_dir)


@activity.defn(name="pr_creator.clone_repository")
def clone_repository(input: CloneRepositoryActivityInput) -> CloneRepositoryActivityResult:
    """Return the commands required to perform the git clone step."""

    checkout_full_path = f"{input.container.workspace_dir}/{input.checkout_path}".rstrip("/")
    command = [
        "git",
        "clone",
        "--filter=blob:none",
        "--sparse",
        f"--depth={input.options.depth}",
        f"--branch={input.options.branch}",
        "--single-branch",
        input.options.repository_url,
        checkout_full_path,
    ]
    commands: List[Sequence[str]] = [command]
    if input.options.sparse_paths:
        commands.append(["git", "-C", checkout_full_path, "sparse-checkout", "set", *input.options.sparse_paths])
    return CloneRepositoryActivityResult(repository_path=checkout_full_path, commands=commands)


@activity.defn(name="pr_creator.apply_sediment_patch")
def apply_sediment_patch(input: ApplySedimentActivityInput) -> ApplySedimentActivityResult:
    """Return the commands required to download and apply the sediment patch."""

    remote_path = f"{input.repository_path}/{input.sediment.filename}"
    commands = [
        ["artifact", "download", input.sediment.storage_key, input.sediment.filename],
        ["caas", "upload", input.sediment.filename, remote_path],
        ["git", "-C", input.repository_path, "apply", input.sediment.filename],
    ]
    return ApplySedimentActivityResult(commands=commands)


@activity.defn(name="pr_creator.create_branch_and_push")
def create_branch_and_push(input: CreateBranchAndPushActivityInput) -> CreateBranchAndPushActivityResult:
    """Return the commands required for creating the branch and pushing it."""

    commit_sha = uuid4().hex
    commands = [
        ["git", "-C", input.repository_path, "checkout", input.base_branch],
        ["git", "-C", input.repository_path, "checkout", "-B", input.new_branch],
        [
            "git",
            "-C",
            input.repository_path,
            "commit",
            "--all",
            "--message",
            input.commit.message,
            "--author",
            f"{input.commit.author_name} <{input.commit.author_email}>",
        ],
        [
            "git",
            "-C",
            input.repository_path,
            "push",
            input.push.remote,
            input.new_branch,
            "--force" if input.push.force else "",
        ],
    ]
    # Remove empty arguments that would not be present in the actual command.
    normalized_commands: List[Sequence[str]] = [
        [arg for arg in command if arg]
        for command in commands
    ]
    return CreateBranchAndPushActivityResult(commands=normalized_commands, commit_sha=commit_sha)


@workflow.defn(name="pr_creator.create_pull_request")
class CreatePullRequestWorkflow:
    """Workflow entry point for the PR creation flow."""

    @workflow.run
    async def run(self, input: CreatePullRequestWorkflowInput) -> CreatePullRequestWorkflowResult:
        workflow.logger.info("Starting PR creation workflow for branch %s", input.new_branch)

        container_handle = await workflow.execute_activity(start_caas_container, input.container)
        steps: List[WorkflowStep] = [
            WorkflowStep(
                name="start-container",
                description=f"Started CaaS container {container_handle.container_id}",
                commands=[],
            )
        ]

        clone_result = await workflow.execute_activity(
            clone_repository,
            CloneRepositoryActivityInput(container=container_handle, options=input.clone),
        )
        steps.append(
            WorkflowStep(
                name="clone-repository",
                description="Cloned repository into the container workspace",
                commands=clone_result.commands,
            )
        )

        apply_patch_result = await workflow.execute_activity(
            apply_sediment_patch,
            ApplySedimentActivityInput(
                container=container_handle,
                repository_path=clone_result.repository_path,
                sediment=input.sediment,
            ),
        )
        steps.append(
            WorkflowStep(
                name="apply-sediment",
                description="Downloaded sediment diff and applied it to the checkout",
                commands=apply_patch_result.commands,
            )
        )

        push_result = await workflow.execute_activity(
            create_branch_and_push,
            CreateBranchAndPushActivityInput(
                container=container_handle,
                repository_path=clone_result.repository_path,
                new_branch=input.new_branch,
                base_branch=input.clone.branch,
                commit=input.commit,
                push=input.push,
            ),
        )
        steps.append(
            WorkflowStep(
                name="push-branch",
                description="Created the branch and pushed it to the remote",
                commands=push_result.commands,
            )
        )

        workflow.logger.info(
            "Finished PR creation workflow for branch %s from container %s",
            input.new_branch,
            container_handle.container_id,
        )
        return CreatePullRequestWorkflowResult(
            new_branch=input.new_branch,
            container_id=container_handle.container_id,
            commit_sha=push_result.commit_sha,
            steps=steps,
        )


def _ensure_iterable(commands: Sequence[Sequence[str]]) -> Sequence[Sequence[str]]:
    """Helper used in unit tests to validate that the commands are iterable."""

    for command in commands:
        if not isinstance(command, Iterable):  # pragma: no cover - defensive
            raise TypeError("commands must be iterable")
    return commands


async def run_create_pull_request_workflow(
    input: CreatePullRequestWorkflowInput,
) -> CreatePullRequestWorkflowResult:
    """Convenience helper for running the workflow in unit tests.

    The helper instantiates the workflow class directly and executes the
    ``run`` coroutine.  This mirrors what Temporal would do after
    scheduling the workflow but keeps the test infrastructure simple.
    """

    workflow_instance = CreatePullRequestWorkflow()
    result = await workflow_instance.run(input)
    for step in result.steps:
        _ensure_iterable(step.commands)
    return result
