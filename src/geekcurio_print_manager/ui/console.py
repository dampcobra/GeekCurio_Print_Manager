from collections.abc import Sequence
from pathlib import Path

from geekcurio_print_manager.exceptions import PrintManagerError
from geekcurio_print_manager.exporters.text_export import build_text_report, write_csv_report, write_text_report
from geekcurio_print_manager.services.inspection_service import InspectionService


def run(service: InspectionService, argv: Sequence[str] | None = None) -> int:
    path_input = argv[0] if argv else input("Enter the path to a sliced .3mf file: ").strip()

    try:
        job = service.inspect(path_input)
    except PrintManagerError as exc:
        print(f"Error: {exc}")
        return 1

    print(build_text_report(job))

    destination = input(
        "\nExport results? Enter a destination path (no extension), or press Enter to skip: "
    ).strip()
    if destination:
        base = Path(destination)
        write_text_report(job, base.with_suffix(".txt"))
        write_csv_report(job, base.with_suffix(".csv"))
        print(f"Wrote {base.with_suffix('.txt')} and {base.with_suffix('.csv')}")

    return 0
