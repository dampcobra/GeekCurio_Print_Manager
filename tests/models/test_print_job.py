from pathlib import Path

import pytest

from geekcurio_print_manager.models.print_job import FilamentUsage, PlateSummary, PrintJob


def _job() -> PrintJob:
    return PrintJob(
        source_path=Path("job.3mf"),
        slicer="bambu_studio_orcaslicer",
        plates=(
            PlateSummary(
                index=1,
                print_time_s=100,
                weight_g=10.0,
                filaments=(FilamentUsage(filament_id=1, type="PLA", used_g=10.0, color="#FFFFFF"),),
            ),
            PlateSummary(
                index=2,
                print_time_s=200,
                weight_g=5.0,
                filaments=(
                    FilamentUsage(filament_id=1, type="PLA", used_g=3.0, color="#FFFFFF"),
                    FilamentUsage(filament_id=2, type="PETG", used_g=2.0, color="#000000"),
                ),
            ),
        ),
    )


def test_total_print_time_sums_across_plates():
    assert _job().total_print_time_s == 300


def test_total_weight_sums_across_plates():
    assert _job().total_weight_g == pytest.approx(15.0)


def test_filament_totals_grouped_by_type_and_color():
    totals = _job().filament_totals_by_material()
    assert totals[("PLA", "#FFFFFF")] == pytest.approx(13.0)
    assert totals[("PETG", "#000000")] == pytest.approx(2.0)


def test_empty_print_job_has_zero_totals():
    job = PrintJob(source_path=Path("empty.3mf"), slicer="bambu_studio_orcaslicer")
    assert job.total_print_time_s == 0
    assert job.total_weight_g == 0
    assert job.filament_totals_by_material() == {}
