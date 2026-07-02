import sys

from geekcurio_print_manager.services.inspection_service import InspectionService
from geekcurio_print_manager.ui.console import run


def main() -> None:
    service = InspectionService()
    sys.exit(run(service, sys.argv[1:]))
