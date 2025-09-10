"""Controller responsible for creating pull requests.

The controller keeps the existing behaviour as the default path.  When
``enable_caas_workflow`` is set in the feature flags the controller runs
the new Temporal workflow that orchestrates the PR creation logic inside
a CaaS container.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Sequence

from chatgpt_code_worker.pr_creator.workflow import (
    ContainerConfig,
    CreatePullRequestWorkflowInput,
    CreatePullRequestWorkflowResult,
    GitCloneOptions,
    GitCommitOptions,
    PushOptions,
    SedimentArtifact,
    WorkflowStep,
    run_create_pull_request_workflow,
)

__all__ = [
    "CreatePullRequestRequest",
    "CreatePullRequestResponse",
    "PullRequestController",
    "PullRequestFeatureFlags",
]


class PullRequestWorkflowRunner(Protocol):
    """Protocol for objects that can run the workflow."""

    async def run(self, workflow_input: CreatePullRequestWorkflowInput) -> CreatePullRequestWorkflowResult:
        """Execute the workflow and return the result."""


@dataclass(slots=True)
class PullRequestFeatureFlags:
    """Feature flag container for the controller."""

    enable_caas_workflow: bool = False


@dataclass(slots=True)
class CreatePullRequestRequest:
    """Input payload for :meth:`PullRequestController.create_pull_request`."""

    repository_url: str
    base_branch: str
    new_branch: str
    sediment_storage_key: str
    commit_message: str
    author_name: str
    author_email: str
    push_options: Optional[PushOptions] = None


@dataclass(slots=True)
class CreatePullRequestResponse:
    """Response returned after creating the PR."""

    branch: str
    commit_sha: str
    used_temporal_workflow: bool
    steps: Sequence[WorkflowStep]


class LocalWorkflowRunner:
    """Fallback runner that executes the workflow inline for tests."""

    async def run(self, workflow_input: CreatePullRequestWorkflowInput) -> CreatePullRequestWorkflowResult:
        return await run_create_pull_request_workflow(workflow_input)


class PullRequestController:
    """High level controller used by the HTTP endpoint."""

    def __init__(
        self,
        *,
        feature_flags: PullRequestFeatureFlags | None = None,
        workflow_runner: PullRequestWorkflowRunner | None = None,
        container_config: ContainerConfig | None = None,
    ) -> None:
        self._feature_flags = feature_flags or PullRequestFeatureFlags()
        self._workflow_runner = workflow_runner or LocalWorkflowRunner()
        self._container_config = container_config or ContainerConfig(
            image="ghcr.io/openai/chatgpt-code-worker:latest",
            command=("/bin/bash",),
        )

    async def create_pull_request(self, request: CreatePullRequestRequest) -> CreatePullRequestResponse:
        """Create the PR either via the workflow or the legacy path."""

        if not self._feature_flags.enable_caas_workflow:
            return self._legacy_create_pull_request(request)

        workflow_input = CreatePullRequestWorkflowInput(
            container=self._container_config,
            clone=GitCloneOptions(repository_url=request.repository_url, branch=request.base_branch),
            sediment=SedimentArtifact(storage_key=request.sediment_storage_key),
            new_branch=request.new_branch,
            commit=GitCommitOptions(
                message=request.commit_message,
                author_name=request.author_name,
                author_email=request.author_email,
            ),
            push=request.push_options or PushOptions(),
        )
        result = await self._workflow_runner.run(workflow_input)
        return CreatePullRequestResponse(
            branch=result.new_branch,
            commit_sha=result.commit_sha,
            used_temporal_workflow=True,
            steps=result.steps,
        )

    def _legacy_create_pull_request(self, request: CreatePullRequestRequest) -> CreatePullRequestResponse:
        """Placeholder for the existing PR creation path."""

        return CreatePullRequestResponse(
            branch=request.new_branch,
            commit_sha="",
            used_temporal_workflow=False,
            steps=[],
        )
