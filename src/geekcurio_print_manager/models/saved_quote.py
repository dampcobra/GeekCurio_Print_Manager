from dataclasses import dataclass

from geekcurio_print_manager.models.print_job import PlateSummary
from geekcurio_print_manager.models.quote import QuoteBreakdown


@dataclass(frozen=True, slots=True)
class SavedQuote:
    quote_ref: str
    created_at: str
    source_file: str
    slicer: str
    profile_name: str
    profile_label: str
    breakdown: QuoteBreakdown
    plates: tuple[PlateSummary, ...]
    notes: str | None = None
    customer_name: str | None = None
    project_name: str | None = None
