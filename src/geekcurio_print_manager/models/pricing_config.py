from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PricingConfig:
    hourly_machine_rate: float = 3.0
    material_cost_per_gram: float = 0.05
    overhead_multiplier: float = 1.0
    markup_percentage: float = 0.0
