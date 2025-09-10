"""Minimal stub of the :mod:`temporalio` package for unit tests.

The real project depends on the Temporal Python SDK.  The test
environment used in these kata-style problems does not provide the
third party dependency, therefore this module implements a very small
subset of the public API.  Only the parts that are exercised by the
workflow in this repository are implemented.  The goal is to allow unit
and type checks to import the module without raising an
:class:`ImportError` while still keeping the surface area explicit.

The stub intentionally keeps the behaviour extremely small: workflow
and activity decorators simply return the original callable, and
``workflow.execute_activity`` invokes the provided function directly.
This allows simple unit tests to execute the workflow synchronously
without needing a Temporal service.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

__all__ = ["activity", "workflow"]


class _DecoratorModule:
    """Utility that mimics the decorator behaviour of the SDK."""

    def __init__(self, logger_name: str | None = None) -> None:
        self.logger = logging.getLogger(logger_name or __name__)

    def defn(self, target: Callable | None = None, **_: Any) -> Callable:
        """Return a decorator compatible with :func:`temporalio.workflow.defn`.

        The decorator is intentionally a no-op because the real
        registration of workflows or activities happens in the worker
        process which is not part of these exercises.
        """

        def decorator(obj: Callable) -> Callable:
            return obj

        if target is not None:
            return decorator(target)
        return decorator

    # The real SDK exposes aliases such as ``@workflow.run`` and
    # ``@workflow.signal``.  The stub only needs ``run`` for the
    # workflow implementation below, but ``signal`` and ``query`` are
    # provided for completeness and to avoid surprises when the module
    # is imported elsewhere.
    run = defn
    signal = defn
    query = defn


class _ActivityModule(_DecoratorModule):
    """Simplified activity namespace."""

    def __getattr__(self, item: str) -> Any:  # pragma: no cover - defensive
        raise AttributeError(item)


class _WorkflowModule(_DecoratorModule):
    """Simplified workflow namespace with a synchronous activity runner."""

    async def execute_activity(
        self,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Synchronously execute the provided activity.

        Real Temporal workflows hand the activity off to the service and
        therefore ``execute_activity`` returns an awaitable.  For tests we
        call the provided callable directly which keeps the code easy to
        reason about and avoids a dependency on the Temporal runtime.
        """

        call_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key
            not in {
                "schedule_to_close_timeout",
                "start_to_close_timeout",
                "retry_policy",
                "heartbeat_timeout",
            }
        }
        result = fn(*args, **call_kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result


activity = _ActivityModule("temporal.activity")
workflow = _WorkflowModule("temporal.workflow")
