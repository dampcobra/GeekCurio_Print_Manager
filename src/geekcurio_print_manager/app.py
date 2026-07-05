import sys

from geekcurio_print_manager.db.database import open_connection
from geekcurio_print_manager.db.schema import initialise_database
from geekcurio_print_manager.services.inspection_service import InspectionService
from geekcurio_print_manager.services.quote_repository import QuoteRepository
from geekcurio_print_manager.ui.console import run
from geekcurio_print_manager.ui.quote_console import run_quote


def main() -> None:
    service = InspectionService()
    sys.exit(run(service, sys.argv[1:]))


def quote_main() -> None:
    conn = open_connection()
    initialise_database(conn)
    repo = QuoteRepository(conn)
    result = run_quote(InspectionService(), repo, sys.argv[1:])
    conn.close()
    sys.exit(result)
