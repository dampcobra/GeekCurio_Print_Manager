from decimal import Decimal

from geekcurio_print_manager.models.print_job import PrintJob
from geekcurio_print_manager.models.quote import QuoteBreakdown
from geekcurio_print_manager.utils.formatting import format_weight

_LW = 26  # label column width; rows are 2 + _LW + 1 + 9 = _LW + 12 chars wide


def _row(label: str, amount: Decimal) -> str:
    return f"  {label:<{_LW}} £{amount:>8.2f}"


def _sep(char: str = "-") -> str:
    return f"  {char * (_LW + 10)}"


def build_quote_report(
    job: PrintJob,
    breakdown: QuoteBreakdown,
    profile_label: str | None = None,
) -> str:
    header = f"GeekCurio Quote: {job.source_path.name}"
    if profile_label:
        header += f"  [{profile_label}]"
    lines = [header, ""]
    lines.append(_row(f"Print time ({breakdown.print_time_hours:.2f} hrs)", breakdown.print_time_cost))
    lines.append(_row(f"Material ({format_weight(breakdown.material_weight_g)})", breakdown.material_cost))

    has_overhead = breakdown.overhead_multiplier != Decimal("1")
    has_markup = breakdown.markup_amount > Decimal("0")

    if has_overhead:
        overhead_amount = breakdown.subtotal - breakdown.print_time_cost - breakdown.material_cost
        lines.append(_row(f"Overhead (x{breakdown.overhead_multiplier:.2f})", overhead_amount))

    lines.append(_sep())

    if has_markup:
        lines.append(_row("Subtotal", breakdown.subtotal))
        lines.append(_row(f"Markup ({breakdown.markup_percentage:.1f}%)", breakdown.markup_amount))
        lines.append(_sep("="))

    lines.append(_row("Total", breakdown.total))
    return "\n".join(lines)
