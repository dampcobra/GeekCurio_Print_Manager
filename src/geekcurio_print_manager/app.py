import sys

from geekcurio_print_manager.services.inspection_service import InspectionService
from geekcurio_print_manager.ui.console import run
from geekcurio_print_manager.ui.quote_console import run_quote


def main() -> None:
    service = InspectionService()
    sys.exit(run(service, sys.argv[1:]))


def quote_main() -> None:
    sys.exit(run_quote(InspectionService(), sys.argv[1:]))
