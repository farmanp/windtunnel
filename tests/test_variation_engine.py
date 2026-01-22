import pytest
from turbulence.variation.config import (
    VariationConfig, 
    ParameterVariation, 
    VariationType, 
    ToggleVariation,
    TimingConfig
)
from turbulence.variation.engine import VariationEngine

def test_variation_engine_determinism():
    config = VariationConfig(
        parameters={
            "choice": ParameterVariation(type=VariationType.CHOICE, values=["a", "b", "c"]),
            "range": ParameterVariation(type=VariationType.RANGE, min=0, max=100)
        },
        toggles=[ToggleVariation(name="toggle", probability=0.5)],
        timing=TimingConfig(jitter_ms={"min": 10, "max": 20})
    )
    
    engine1 = VariationEngine(config, base_seed=12345)
    engine2 = VariationEngine(config, base_seed=12345)
    
    # Same seed, same instance index -> same results
    res1 = engine1.apply(0)
    res2 = engine2.apply(0)
    assert res1 == res2
    
    # Same seed, different instance index -> different results (usually)
    res3 = engine1.apply(1)
    assert res1 != res3

def test_variation_engine_parameter_distribution():
    values = ["a", "b", "c"]
    config = VariationConfig(
        parameters={"p": ParameterVariation(type=VariationType.CHOICE, values=values)}
    )
    engine = VariationEngine(config, base_seed=1)
    
    results = [engine.apply(i)["p"] for i in range(100)]
    # Check that all values were picked at least once
    for v in values:
        assert v in results

def test_variation_engine_toggles():
    config = VariationConfig(
        toggles=[ToggleVariation(name="t", probability=0.5)]
    )
    engine = VariationEngine(config, base_seed=42)
    
    results = [engine.apply(i)["t"] for i in range(100)]
    # Check that we got a mix of True/False
    assert True in results
    assert False in results
    
    # Verification of approximate probability (not strictly 0.5 due to small sample, but should be close)
    true_count = sum(1 for r in results if r)
    assert 30 <= true_count <= 70

def test_variation_engine_timing():
    config = VariationConfig(
        timing=TimingConfig(
            jitter_ms={"min": 10, "max": 50},
            step_delay_ms={"min": 100, "max": 200}
        )
    )
    engine = VariationEngine(config, base_seed=7)
    
    res = engine.apply(0)
    assert 10 <= res["_timing_jitter_ms"] <= 50
    assert 100 <= res["_step_delay_ms"] <= 200
