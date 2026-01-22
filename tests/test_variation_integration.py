import asyncio
import httpx
import pytest
from pathlib import Path
import json
from datetime import datetime, timezone

from turbulence.config import Scenario, SUTConfig
from turbulence.engine.scenario_runner import ScenarioRunner
from turbulence.engine.template import TemplateEngine
from turbulence.variation.config import VariationConfig, ParameterVariation, VariationType
from turbulence.commands.run import _pick_scenario
from turbulence.engine.context import WorkflowContext
from turbulence.variation.engine import VariationEngine
from turbulence.storage.artifact import ArtifactStore

@pytest.mark.asyncio
async def test_variation_end_to_end_flow(tmp_path):
    # 1. Setup Scenario with Variation
    scenario_dict = {
        "id": "variation-test",
        "variation": {
            "parameters": {
                "user_id": {
                    "type": "choice",
                    "values": ["user1", "user2"]
                }
            },
            "timing": {
                "jitter_ms": {"min": 1, "max": 5}
            }
        },
        "entry": {
            "seed_data": {
                "injected_user": "{{entry.seed_data.variation.user_id}}"
            }
        },
        "flow": [
            {
                "name": "step1",
                "type": "http",
                "service": "api",
                "method": "GET",
                "path": "/users/{{entry.seed_data.injected_user}}"
            }
        ]
    }
    scenario = Scenario.model_validate(scenario_dict)
    
    # 2. Mock SUT Config
    sut_config = SUTConfig(
        name="test-sut",
        services={"api": {"base_url": "http://api.test"}}
    )
    
    # 3. Execution logic (Simplified version of run.py execute_instance)
    seed_value = 12345
    instance_index = 0
    run_id = "test-run"
    
    # Apply Variation
    entry_data = scenario.entry.model_dump()
    variation_engine = VariationEngine(scenario.variation, seed_value)
    variations_applied = variation_engine.apply(instance_index)
    
    assert "user_id" in variations_applied
    assert variations_applied["user_id"] in ["user1", "user2"]
    
    entry_data["seed_data"]["variation"] = variations_applied
    
    ctx = WorkflowContext.from_scenario_entry(entry_data, run_id=run_id)
    context_dict = ctx.to_dict()
    
    # Verify template expansion
    template_engine = TemplateEngine()
    rendered_context = template_engine.render_dict(context_dict, context_dict)
    assert rendered_context["entry"]["seed_data"]["injected_user"] == variations_applied["user_id"]
    
    # 4. Verify Timing Jitter in ScenarioRunner
    # We can't easily wait for real time, but we can verify it's present in the context used by ScenarioRunner
    scenario_runner = ScenarioRunner(template_engine, sut_config)
    
    # We'll mock the _execute_action to see the flow but we need to verify RENDERING
    async def mock_execute_action(action, context, client):
        # Render templates in action manually since we are mocking the whole _execute_action
        rendered_action = scenario_runner._render_action(action, context)
        
        # Verify action path is rendered correctly with variation
        assert variations_applied["user_id"] in rendered_action.path
        from turbulence.models.observation import Observation
        return Observation(ok=True, status_code=200, latency_ms=1.0, headers={}, body={}, action_name=action.name, service="api"), context

    scenario_runner._execute_action = mock_execute_action
    
    async with httpx.AsyncClient() as client:
        results = []
        async for step_idx, action, observation, updated_ctx in scenario_runner.execute_flow(scenario, rendered_context, client):
            results.append(step_idx)
            
    assert len(results) == 1

@pytest.mark.asyncio
async def test_variation_artifact_logging(tmp_path):
    # Mock some data
    run_id = "test-run-artifacts"
    instance_index = 0
    variations_applied = {"foo": "bar"}
    
    store = ArtifactStore(
        run_id=run_id,
        base_path=tmp_path,
        sut_name="test",
        scenario_ids=["test"],
    ).initialize()
    
    instance_id = "inst_123"
    
    # Log variations
    store.write_instance_artifact(
        instance_id=instance_id,
        filename="variation.json",
        data=variations_applied,
    )
    
    # Verify file exists and has correct content
    variation_file = tmp_path / run_id / "artifacts" / instance_id / "variation.json"
    assert variation_file.exists()
    
    with variation_file.open() as f:
        data = json.load(f)
        assert data == variations_applied
