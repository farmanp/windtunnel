"""Workflow context management for instance execution."""

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class WorkflowContext(BaseModel):
    """Context for a single workflow instance execution.

    Manages the data flow between workflow steps, including:
    - Entry data from the scenario definition
    - Extracted values from HTTP responses
    - Generated identifiers (run_id, correlation_id, instance_id)
    """

    model_config = ConfigDict(extra="allow")

    run_id: str = Field(
        default_factory=lambda: f"run_{uuid4().hex[:12]}",
        description="Unique identifier for the run",
    )
    instance_id: str = Field(
        default_factory=lambda: f"inst_{uuid4().hex[:12]}",
        description="Unique identifier for this workflow instance",
    )
    correlation_id: str = Field(
        default_factory=lambda: f"corr_{uuid4().hex[:12]}",
        description="Correlation ID for request tracing",
    )
    entry: dict[str, Any] = Field(
        default_factory=dict,
        description="Entry context from scenario definition",
    )
    _extracted: dict[str, Any] = {}

    def __init__(self, **data: Any) -> None:
        """Initialize workflow context."""
        super().__init__(**data)
        self._extracted = {}

    def set_entry(self, entry_data: dict[str, Any]) -> None:
        """Set the entry context from scenario definition.

        Args:
            entry_data: Entry block data from scenario
        """
        self.entry = entry_data

    def extract(self, key: str, value: Any) -> None:
        """Store an extracted value from a response.

        Args:
            key: The variable name to store
            value: The extracted value
        """
        self._extracted[key] = value

    def extract_many(self, extractions: dict[str, Any]) -> None:
        """Store multiple extracted values.

        Args:
            extractions: Dictionary of variable names to values
        """
        self._extracted.update(extractions)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from context.

        Searches in order: extracted values, entry data, model fields.

        Args:
            key: The key to look up
            default: Default value if not found

        Returns:
            The value or default
        """
        if key in self._extracted:
            return self._extracted[key]
        if key in self.entry:
            return self.entry[key]
        if hasattr(self, key):
            return getattr(self, key)
        return default

    def to_dict(self) -> dict[str, Any]:
        """Convert context to a flat dictionary for template rendering.

        Returns:
            Dictionary with all context values accessible for templating
        """
        result: dict[str, Any] = {
            "run_id": self.run_id,
            "instance_id": self.instance_id,
            "correlation_id": self.correlation_id,
            "entry": self.entry,
        }
        # Add extracted values at top level for easy access
        result.update(self._extracted)
        return result

    def copy_with_extractions(self) -> "WorkflowContext":
        """Create a copy of this context preserving extractions.

        Returns:
            New WorkflowContext with same data
        """
        new_ctx = WorkflowContext(
            run_id=self.run_id,
            instance_id=self.instance_id,
            correlation_id=self.correlation_id,
            entry=self.entry.copy(),
        )
        new_ctx._extracted = self._extracted.copy()
        return new_ctx

    @classmethod
    def from_scenario_entry(
        cls,
        entry_data: dict[str, Any],
        run_id: str | None = None,
    ) -> "WorkflowContext":
        """Create a new context from a scenario's entry block.

        Args:
            entry_data: The entry block from a scenario
            run_id: Optional run ID (generated if not provided)

        Returns:
            New WorkflowContext initialized with entry data
        """
        ctx = cls(run_id=run_id) if run_id else cls()
        ctx.set_entry(entry_data)
        return ctx
