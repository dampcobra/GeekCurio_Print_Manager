from pathlib import Path

from geekcurio_print_manager.exporters.text_export import (
    build_csv_rows,
    build_text_report,
    write_csv_report,
    write_text_report,
)
from geekcurio_print_manager.models.print_job import FilamentUsage, PlateSummary, PrintJob


def _job() -> PrintJob:
    return PrintJob(
        source_path=Path("job.3mf"),
        slicer="bambu_studio_orcaslicer",
        plates=(
            PlateSummary(
                index=1,
                print_time_s=3661,
                weight_g=18.46,
                filaments=(FilamentUsage(filament_id=1, type="PLA", used_g=18.46),),
            ),
            PlateSummary(index=2, print_time_s=100, weight_g=1234.0),
        ),
    )


def test_build_text_report_contains_totals():
    report = build_text_report(_job())
    assert "job.3mf" in report
    assert "Plate 1" in report
    assert "Plate 2" in report
    assert "01:01:01" in report
    assert "Total print time" in report
    assert "Total material used" in report
    assert "1.25 kg" in report


def test_build_csv_rows_has_header_and_one_row_per_plate():
    rows = build_csv_rows(_job())
    assert rows[0] == ("plate", "print_time_s", "print_time", "weight_g")
    assert len(rows) == 3
    assert rows[1] == ("1", "3661", "01:01:01", "18.46")


def test_write_text_report(tmp_path):
    destination = tmp_path / "report.txt"
    write_text_report(_job(), destination)
    assert "Total print time" in destination.read_text(encoding="utf-8")


def test_write_csv_report(tmp_path):
    destination = tmp_path / "report.csv"
    write_csv_report(_job(), destination)
    content = destination.read_text(encoding="utf-8")
    assert "plate,print_time_s,print_time,weight_g" in content
