from decimal import Decimal, ROUND_HALF_UP

from geekcurio_print_manager.models.pricing_config import PricingConfig
from geekcurio_print_manager.models.print_job import PrintJob
from geekcurio_print_manager.models.quote import QuoteBreakdown

_PENNY = Decimal("0.01")


class QuoteService:
    def __init__(self, config: PricingConfig | None = None) -> None:
        self._config = config if config is not None else PricingConfig()

    def calculate(self, job: PrintJob) -> QuoteBreakdown:
        # Convert measurements to Decimal at the calculation boundary.
        # print_time_s is int, so Decimal(int) is exact with no representation issue.
        # weight_g is float from the parser; str() gives the shortest exact representation.
        hours = Decimal(job.total_print_time_s) / Decimal("3600")
        weight = Decimal(str(job.total_weight_g))

        time_cost = hours * self._config.hourly_machine_rate
        material_cost = weight * self._config.material_cost_per_gram
        subtotal = (time_cost + material_cost) * self._config.overhead_multiplier
        markup_amount = subtotal * (self._config.markup_percentage / Decimal("100"))
        total = subtotal + markup_amount

        return QuoteBreakdown(
            print_time_hours=float(hours),
            print_time_cost=time_cost.quantize(_PENNY, ROUND_HALF_UP),
            material_weight_g=job.total_weight_g,
            material_cost=material_cost.quantize(_PENNY, ROUND_HALF_UP),
            overhead_multiplier=self._config.overhead_multiplier,
            markup_percentage=self._config.markup_percentage,
            subtotal=subtotal.quantize(_PENNY, ROUND_HALF_UP),
            markup_amount=markup_amount.quantize(_PENNY, ROUND_HALF_UP),
            total=total.quantize(_PENNY, ROUND_HALF_UP),
        )
