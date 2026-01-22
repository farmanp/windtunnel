"""Base classes and protocols for action runners."""

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from windtunnel.models.observation import Observation


@runtime_checkable
class ActionRunner(Protocol):
    """Protocol defining the interface for action runners.

    Action runners execute specific types of actions (HTTP, wait, etc.)
    and return observations capturing the execution results.
    """

    @abstractmethod
    async def execute(
        self,
        context: dict[str, Any],
    ) -> tuple[Observation, dict[str, Any]]:
        """Execute the action and return observation with updated context.

        Args:
            context: Current execution context with variables.

        Returns:
            A tuple of (Observation, updated_context) where updated_context
            contains any extracted values merged with the input context.
        """
        ...


class BaseActionRunner(ABC):
    """Abstract base class for action runners.

    Provides common functionality for action runners while requiring
    subclasses to implement the execute method.
    """

    @abstractmethod
    async def execute(
        self,
        context: dict[str, Any],
    ) -> tuple[Observation, dict[str, Any]]:
        """Execute the action and return observation with updated context.

        Args:
            context: Current execution context with variables.

        Returns:
            A tuple of (Observation, updated_context) where updated_context
            contains any extracted values merged with the input context.
        """
        ...
