"""Variation engine for deterministic input fuzzing."""

import random
from typing import Any

from turbulence.variation.config import VariationConfig, VariationType


class VariationEngine:
    """Generates deterministic variations based on seed and configuration.

    Each instance gets a unique but reproducible seed derived from the base seed
    and instance index. This ensures diverse inputs while maintaining full
    reproducibility for debugging and regression testing.
    """

    def __init__(self, config: VariationConfig, base_seed: int) -> None:
        """Initialize the variation engine.

        Args:
            config: Variation configuration defining parameters, toggles, and timing
            base_seed: Base seed for the run (variations are derived per instance)
        """
        self.config = config
        self.base_seed = base_seed

    def apply(self, instance_index: int) -> dict[str, Any]:
        """Generate variation values for a specific instance.

        Args:
            instance_index: Zero-based instance index

        Returns:
            Dictionary of variation values to inject into context
        """
        # Create deterministic RNG for this instance
        seed = self.base_seed + instance_index
        rng = random.Random(seed)

        result: dict[str, Any] = {}

        # Apply parameter variations
        for param_name, param_config in self.config.parameters.items():
            if param_config.type == VariationType.CHOICE:
                if param_config.values:
                    result[param_name] = rng.choice(param_config.values)
            elif param_config.type == VariationType.RANGE:
                if param_config.min is not None and param_config.max is not None:
                    result[param_name] = rng.uniform(param_config.min, param_config.max)

        # Apply toggle variations (boolean flags with probability)
        for toggle in self.config.toggles:
            result[toggle.name] = rng.random() < toggle.probability

        # Apply timing variations (stored with _ prefix for internal use)
        if self.config.timing:
            if self.config.timing.jitter_ms:
                result["_timing_jitter_ms"] = rng.randint(
                    self.config.timing.jitter_ms["min"],
                    self.config.timing.jitter_ms["max"],
                )
            if self.config.timing.step_delay_ms:
                result["_step_delay_ms"] = rng.randint(
                    self.config.timing.step_delay_ms["min"],
                    self.config.timing.step_delay_ms["max"],
                )

        return result
