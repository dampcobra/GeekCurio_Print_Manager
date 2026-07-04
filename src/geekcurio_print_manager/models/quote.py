from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuoteBreakdown:
    print_time_hours: float
    print_time_cost: float
    material_weight_g: float
    material_cost: float
    overhead_multiplier: float
    markup_percentage: float
    subtotal: float
    markup_amount: float
    total: float
