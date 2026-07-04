from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PricingConfig:
    hourly_machine_rate: Decimal = Decimal("3.00")
    material_cost_per_gram: Decimal = Decimal("0.05")
    overhead_multiplier: Decimal = Decimal("1.0")
    markup_percentage: Decimal = Decimal("0")
