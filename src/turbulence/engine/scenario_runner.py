"""Scenario execution engine.

Consolidates step-by-step scenario execution logic used by both
the run command and replay engine.
"""

import asyncio
import logging
from typing import Any, AsyncIterator

import httpx

from turbulence.actions.assert_ import AssertActionRunner
from turbulence.actions.http import HttpActionRunner
from turbulence.actions.wait import WaitActionRunner
from turbulence.config.scenario import (
    Action,
    AssertAction,
    HttpAction,
    Scenario,
    WaitAction,
)
from turbulence.config.sut import SUTConfig
from turbulence.engine.template import TemplateEngine
from turbulence.models.observation import Observation
from turbulence.pressure.engine import TurbulenceEngine

logger = logging.getLogger(__name__)


class ScenarioRunner:
    """Executes scenario flows with context management and action execution.

    Handles template rendering, action execution, and context updates for
    scenario steps. Used by both run command and replay engine to ensure
    consistent execution behavior.
    """

    def __init__(
        self,
        template_engine: TemplateEngine,
        sut_config: SUTConfig,
        turbulence_engine: TurbulenceEngine | None = None,
    ) -> None:
        """Initialize the scenario runner.

        Args:
            template_engine: Engine for rendering template variables
            sut_config: System under test configuration
            turbulence_engine: Optional engine for fault injection
        """
        self.template_engine = template_engine
        self.sut_config = sut_config
        self.turbulence_engine = turbulence_engine

    async def execute_flow(
        self,
        scenario: Scenario,
        context: dict[str, Any],
        client: httpx.AsyncClient,
    ) -> AsyncIterator[tuple[int, Action, Observation, dict[str, Any]]]:
        """Execute scenario flow steps, yielding results for each step.

        Args:
            scenario: Scenario definition with flow steps
            context: Execution context dictionary
            client: HTTP client for requests

        Yields:
            Tuple of (step_index, action, observation, updated_context)
            for each executed step
        """
        # Extract timing config from context if present (injected by VariationEngine)
        variation_data = context.get("entry", {}).get("seed_data", {}).get("variation", {})
        step_delay_ms = variation_data.get("_step_delay_ms", 0)
        jitter_ms = variation_data.get("_timing_jitter_ms", 0)

        for step_index, action in enumerate(scenario.flow):
            # Apply delays/jitter
            total_delay_ms = 0
            if step_index > 0:
                total_delay_ms += step_delay_ms
            total_delay_ms += jitter_ms

            if total_delay_ms > 0:
                await asyncio.sleep(total_delay_ms / 1000.0)

            observation, context = await self._execute_action(
                action=action,
                context=context,
                client=client,
            )

            # Update last_response context for HTTP and Wait actions
            if isinstance(action, (HttpAction, WaitAction)):
                self._update_last_response(context, observation)

            yield step_index, action, observation, context

            # Stop if action failed and scenario is configured to halt
            if not observation.ok and scenario.stop_when.any_action_fails:
                break

    async def _execute_action(
        self,
        action: Action,
        context: dict[str, Any],
        client: httpx.AsyncClient,
    ) -> tuple[Observation, dict[str, Any]]:
        """Execute a single action with template rendering.

        Args:
            action: Action to execute
            context: Current execution context
            client: HTTP client for requests

        Returns:
            Tuple of (observation, updated_context)
        """
        # Render templates in action
        rendered_action = self._render_action(action, context)

        # Execute based on action type
        if isinstance(rendered_action, HttpAction):
            runner = HttpActionRunner(
                action=rendered_action,
                sut_config=self.sut_config,
                client=client,
            )

            # Apply turbulence if configured
            if self.turbulence_engine is not None:
                policy = self.turbulence_engine.resolve_policy(
                    service=rendered_action.service,
                    action=rendered_action.name,
                )
                if policy is not None:
                    return await self.turbulence_engine.apply(
                        policy=policy,
                        action_name=rendered_action.name,
                        service_name=rendered_action.service,
                        instance_id=str(context.get("instance_id", "")),
                        context=context,
                        execute=lambda: runner.execute(context),
                    )

            return await runner.execute(context)

        if isinstance(rendered_action, WaitAction):
            runner = WaitActionRunner(
                action=rendered_action,
                sut_config=self.sut_config,
                client=client,
            )
            return await runner.execute(context)

        if isinstance(rendered_action, AssertAction):
            runner = AssertActionRunner(action=rendered_action)
            return await runner.execute(context)

        raise ValueError(f"Unknown action type: {type(action)}")

    def _render_action(
        self,
        action: Action,
        context: dict[str, Any],
    ) -> Action:
        """Render template variables in an action.

        Args:
            action: Action with potential template variables
            context: Context for template rendering

        Returns:
            Action with templates rendered
        """
        action_dict = action.model_dump()
        rendered_dict = self.template_engine.render_dict(action_dict, context)

        if isinstance(action, HttpAction):
            return HttpAction(**rendered_dict)
        if isinstance(action, WaitAction):
            return WaitAction(**rendered_dict)
        # AssertAction is the only remaining possibility
        return AssertAction(**rendered_dict)

    def _update_last_response(
        self,
        context: dict[str, Any],
        observation: Observation,
    ) -> None:
        """Update context with last response data.

        Args:
            context: Context to update
            observation: Observation from action execution
        """
        context["last_response"] = {
            "status_code": getattr(observation, "status_code", None),
            "headers": getattr(observation, "headers", {}),
            "body": getattr(observation, "body", None),
        }
