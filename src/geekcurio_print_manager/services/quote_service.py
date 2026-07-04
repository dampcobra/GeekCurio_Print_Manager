from geekcurio_print_manager.models.pricing_config import PricingConfig
from geekcurio_print_manager.models.print_job import PrintJob
from geekcurio_print_manager.models.quote import QuoteBreakdown


class QuoteService:
    def __init__(self, config: PricingConfig | None = None) -> None:
        self._config = config if config is not None else PricingConfig()

    def calculate(self, job: PrintJob) -> QuoteBreakdown:
        hours = job.total_print_time_s / 3600
        time_cost = hours * self._config.hourly_machine_rate
        material_cost = job.total_weight_g * self._config.material_cost_per_gram
        subtotal = (time_cost + material_cost) * self._config.overhead_multiplier
        markup_amount = subtotal * (self._config.markup_percentage / 100)
        total = subtotal + markup_amount
        return QuoteBreakdown(
            print_time_hours=hours,
            print_time_cost=time_cost,
            material_weight_g=job.total_weight_g,
            material_cost=material_cost,
            overhead_multiplier=self._config.overhead_multiplier,
            markup_percentage=self._config.markup_percentage,
            subtotal=subtotal,
            markup_amount=markup_amount,
            total=total,
        )
