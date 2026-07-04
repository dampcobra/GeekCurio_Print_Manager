from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class QuoteBreakdown:
    print_time_hours: float       # measurement — stays float
    print_time_cost: Decimal
    material_weight_g: float      # measurement — stays float
    material_cost: Decimal
    overhead_multiplier: Decimal  # carried from PricingConfig
    markup_percentage: Decimal    # carried from PricingConfig
    subtotal: Decimal
    markup_amount: Decimal
    total: Decimal
