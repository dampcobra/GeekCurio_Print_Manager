from collections.abc import Sequence

from geekcurio_print_manager.exceptions import PrintManagerError
from geekcurio_print_manager.exporters.quote_export import build_quote_report
from geekcurio_print_manager.services.inspection_service import InspectionService
from geekcurio_print_manager.services.quote_service import QuoteService


def run_quote(
    inspection_service: InspectionService,
    quote_service: QuoteService,
    argv: Sequence[str] | None = None,
) -> int:
    path_input = argv[0] if argv else input("Enter the path to a sliced .3mf file: ").strip()

    try:
        job = inspection_service.inspect(path_input)
    except PrintManagerError as exc:
        print(f"Error: {exc}")
        return 1

    breakdown = quote_service.calculate(job)
    print(build_quote_report(job, breakdown))
    return 0
