import csv
import io
from pathlib import Path

from geekcurio_print_manager.models.print_job import PrintJob
from geekcurio_print_manager.utils.formatting import format_duration, format_weight

CSV_HEADER = ("plate", "print_time_s", "print_time", "weight_g")


def build_text_report(job: PrintJob) -> str:
    lines = [f"3MF Project Inspection: {job.source_path.name}", ""]
    for plate in job.plates:
        lines.append(
            f"Plate {plate.index}: "
            f"{format_duration(plate.print_time_s)} print time, "
            f"{format_weight(plate.weight_g)} material"
        )
    lines.append("")
    lines.append(f"Total print time: {format_duration(job.total_print_time_s)}")
    lines.append(f"Total material used: {format_weight(job.total_weight_g)}")
    return "\n".join(lines)


def build_csv_rows(job: PrintJob) -> list[tuple[str, ...]]:
    rows = [CSV_HEADER]
    for plate in job.plates:
        rows.append(
            (
                str(plate.index),
                str(plate.print_time_s),
                format_duration(plate.print_time_s),
                f"{plate.weight_g:.2f}",
            )
        )
    return rows


def write_text_report(job: PrintJob, destination: Path) -> None:
    destination.write_text(build_text_report(job), encoding="utf-8")


def write_csv_report(job: PrintJob, destination: Path) -> None:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(build_csv_rows(job))
    destination.write_text(buffer.getvalue(), encoding="utf-8", newline="")
