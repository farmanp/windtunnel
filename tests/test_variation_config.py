import pytest
from pydantic import ValidationError
from turbulence.variation.config import (
    VariationConfig, 
    ParameterVariation, 
    VariationType, 
    ToggleVariation,
    TimingConfig
)

def test_parameter_variation_choice():
    config = ParameterVariation(type=VariationType.CHOICE, values=[1, 2, 3])
    assert config.type == VariationType.CHOICE
    assert config.values == [1, 2, 3]

def test_parameter_variation_choice_invalid():
    with pytest.raises(ValueError, match="Choice variation requires 'values' list"):
        ParameterVariation(type=VariationType.CHOICE)

def test_parameter_variation_range():
    config = ParameterVariation(type=VariationType.RANGE, min=1, max=10)
    assert config.type == VariationType.RANGE
    assert config.min == 1
    assert config.max == 10

def test_parameter_variation_range_invalid():
    with pytest.raises(ValueError, match="Range 'min' must be less than 'max'"):
        ParameterVariation(type=VariationType.RANGE, min=10, max=1)

def test_toggle_variation():
    config = ToggleVariation(name="test", probability=0.5)
    assert config.name == "test"
    assert config.probability == 0.5

def test_toggle_variation_invalid_probability():
    with pytest.raises(ValidationError):
        ToggleVariation(name="test", probability=1.5)

def test_timing_config_valid():
    config = TimingConfig(
        jitter_ms={"min": 0, "max": 100},
        step_delay_ms={"min": 100, "max": 200}
    )
    assert config.jitter_ms["min"] == 0
    assert config.step_delay_ms["max"] == 200

def test_timing_config_invalid():
    with pytest.raises(ValueError, match="jitter_ms 'min' must be less than 'max'"):
        TimingConfig(jitter_ms={"min": 100, "max": 0})

def test_variation_config_full():
    config = VariationConfig(
        parameters={"q": ParameterVariation(type=VariationType.CHOICE, values=[1, 2])},
        toggles=[ToggleVariation(name="t", probability=0.1)],
        timing=TimingConfig(jitter_ms={"min": 0, "max": 10})
    )
    assert "q" in config.parameters
    assert len(config.toggles) == 1
    assert config.timing.jitter_ms["max"] == 10
