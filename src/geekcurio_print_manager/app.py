import sys

from geekcurio_print_manager.services.inspection_service import InspectionService
from geekcurio_print_manager.services.quote_service import QuoteService
from geekcurio_print_manager.ui.console import run
from geekcurio_print_manager.ui.quote_console import run_quote


def main() -> None:
    service = InspectionService()
    sys.exit(run(service, sys.argv[1:]))


def quote_main() -> None:
    inspection_service = InspectionService()
    quote_service = QuoteService()
    sys.exit(run_quote(inspection_service, quote_service, sys.argv[1:]))
