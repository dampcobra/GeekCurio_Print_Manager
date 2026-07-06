"""Tests for pdf_quote_export.

Note on £ extraction: pypdf does not reliably decode the pound sign from
Helvetica's WinAnsiEncoding, so tests assert on the numeric amount only
(e.g. "6.75") rather than the full "£6.75" string.
"""
import sqlite3
from decimal import Decimal
from pathlib import Path

import pypdf
import pytest

from geekcurio_print_manager.db.schema import initialise_database
from geekcurio_print_manager.exporters.pdf_quote_export import (
    _allocate_plate_costs,
    build_pdf_quote,
)
from geekcurio_print_manager.models.print_job import FilamentUsage, PlateSummary, PrintJob
from geekcurio_print_manager.models.pricing_config import PricingConfig
from geekcurio_print_manager.models.pricing_profile import PricingProfile
from geekcurio_print_manager.services.quote_repository import QuoteRepository
from geekcurio_print_manager.services.quote_service import QuoteService


# ── Test helpers ──────────────────────────────────────────────────────────────

def _repo() -> QuoteRepository:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    initialise_database(conn)
    return QuoteRepository(conn)


def _profile(**overrides) -> PricingProfile:
    defaults = dict(name="fdm_pla", label="FDM - PLA (Standard)", config=PricingConfig())
    defaults.update(overrides)
    return PricingProfile(**defaults)


def _job(plates=None) -> PrintJob:
    if plates is None:
        plates = (
            PlateSummary(
                index=1,
                print_time_s=5400,
                weight_g=45.0,
                filaments=(FilamentUsage(filament_id=1, type="PLA", used_g=45.0, color="#FFFFFF"),),
                support_used=False,
                printer_model_id="Bambu Lab X1 Carbon",
            ),
        )
    return PrintJob(source_path=Path("TestPart.3mf"), slicer="BambuStudio", plates=plates)


def _multi_plate_job() -> PrintJob:
    return PrintJob(
        source_path=Path("MultiPart.3mf"),
        slicer="BambuStudio",
        plates=(
            PlateSummary(
                index=1,
                print_time_s=5400,
                weight_g=45.0,
                filaments=(FilamentUsage(filament_id=1, type="PLA", used_g=45.0),),
            ),
            PlateSummary(
                index=2,
                print_time_s=3600,
                weight_g=30.0,
                filaments=(FilamentUsage(filament_id=1, type="PETG", used_g=30.0),),
            ),
        ),
    )


def _pdf_text(path: Path) -> str:
    reader = pypdf.PdfReader(str(path))
    return " ".join(page.extract_text() or "" for page in reader.pages)


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def saved(tmp_path):
    repo = _repo()
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    return repo.save(_job(), breakdown, profile)


@pytest.fixture
def pdf_path(saved, tmp_path):
    path = tmp_path / f"{saved.quote_ref}.pdf"
    build_pdf_quote(saved, path)
    return path


@pytest.fixture
def multi_saved(tmp_path):
    repo = _repo()
    profile = _profile()
    job = _multi_plate_job()
    breakdown = QuoteService(profile.config).calculate(job)
    return repo.save(job, breakdown, profile)


@pytest.fixture
def multi_pdf_path(multi_saved, tmp_path):
    path = tmp_path / f"{multi_saved.quote_ref}.pdf"
    build_pdf_quote(multi_saved, path)
    return path


# ── File creation ─────────────────────────────────────────────────────────────

def test_pdf_file_is_created(pdf_path):
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0


def test_pdf_creates_parent_directories(saved, tmp_path):
    nested = tmp_path / "a" / "b" / f"{saved.quote_ref}.pdf"
    build_pdf_quote(saved, nested)
    assert nested.exists()


def test_pdf_overwrite_is_allowed(saved, tmp_path):
    path = tmp_path / "overwrite.pdf"
    build_pdf_quote(saved, path)
    size_first = path.stat().st_size
    build_pdf_quote(saved, path)
    assert path.stat().st_size == size_first


# ── Header / title block ──────────────────────────────────────────────────────

def test_pdf_contains_brand_name(pdf_path):
    assert "GeekCurio" in _pdf_text(pdf_path)


def test_pdf_contains_commission_quotation_title(pdf_path):
    assert "Commission Quotation" in _pdf_text(pdf_path)


def test_pdf_contains_quote_reference(saved, pdf_path):
    assert saved.quote_ref in _pdf_text(pdf_path)


def test_pdf_contains_project_stem(saved, pdf_path):
    # PDF shows the filename stem (without .3mf extension)
    assert Path(saved.source_file).stem in _pdf_text(pdf_path)


def test_pdf_does_not_contain_raw_file_extension(pdf_path):
    assert ".3mf" not in _pdf_text(pdf_path)


def test_pdf_contains_issued_date(pdf_path):
    # "Issued" label must appear in the metadata block
    assert "Issued" in _pdf_text(pdf_path)


# ── Tagline and intro ─────────────────────────────────────────────────────────

def test_pdf_contains_tagline(pdf_path):
    assert "Premium Tabletop Gaming Accessories" in _pdf_text(pdf_path)


def test_pdf_contains_uk_tagline(pdf_path):
    assert "Designed and Printed in the UK" in _pdf_text(pdf_path)


# ── Summary section ───────────────────────────────────────────────────────────

def test_pdf_contains_summary_section(pdf_path):
    assert "Summary" in _pdf_text(pdf_path)


def test_pdf_summary_shows_build_plate_count(pdf_path):
    text = _pdf_text(pdf_path)
    assert "Build Plates" in text
    assert "1" in text


def test_pdf_summary_shows_production_cost(saved, pdf_path):
    # Amount appears without £ symbol (pypdf encoding limitation)
    assert f"{saved.breakdown.total:.2f}" in _pdf_text(pdf_path)


def test_pdf_summary_shows_postage_placeholder(pdf_path):
    assert "Postage" in _pdf_text(pdf_path)


# ── Plate breakdown table ─────────────────────────────────────────────────────

def test_pdf_contains_plate_table_headers(pdf_path):
    text = _pdf_text(pdf_path)
    assert "Plate" in text
    assert "Description" in text
    assert "Time" in text
    assert "Filament" in text
    assert "Cost" in text


def test_pdf_plate_table_has_row_for_each_plate(saved, pdf_path):
    text = _pdf_text(pdf_path)
    for plate in saved.plates:
        assert str(plate.index) in text


def test_pdf_plate_table_shows_filament_weight(pdf_path):
    # Filament column shows weight (e.g. "45.0 g"), not material type
    assert "45.0" in _pdf_text(pdf_path)


def test_pdf_plate_table_shows_placeholder_description(pdf_path):
    assert "Printed components" in _pdf_text(pdf_path)


def test_pdf_plate_table_shows_print_time(pdf_path):
    assert "1h 30m" in _pdf_text(pdf_path)


# ── Plate cost allocation ─────────────────────────────────────────────────────

def test_pdf_uses_saved_total_not_recalculated(saved, pdf_path):
    assert f"{saved.breakdown.total:.2f}" in _pdf_text(pdf_path)


def test_allocate_plate_costs_single_plate_equals_total():
    from geekcurio_print_manager.models.quote import QuoteBreakdown
    bd = QuoteBreakdown(
        print_time_hours=1.5, print_time_cost=Decimal("4.50"),
        material_weight_g=45.0, material_cost=Decimal("2.25"),
        overhead_multiplier=Decimal("1"), markup_percentage=Decimal("0"),
        subtotal=Decimal("6.75"), markup_amount=Decimal("0.00"), total=Decimal("6.75"),
    )
    plates = (PlateSummary(index=1, print_time_s=5400, weight_g=45.0),)
    costs = _allocate_plate_costs(plates, bd)
    assert costs == [Decimal("6.75")]


def test_allocate_plate_costs_sum_equals_saved_total():
    from geekcurio_print_manager.models.quote import QuoteBreakdown
    bd = QuoteBreakdown(
        print_time_hours=2.5, print_time_cost=Decimal("7.50"),
        material_weight_g=75.0, material_cost=Decimal("3.75"),
        overhead_multiplier=Decimal("1"), markup_percentage=Decimal("0"),
        subtotal=Decimal("11.25"), markup_amount=Decimal("0.00"), total=Decimal("11.25"),
    )
    plates = (
        PlateSummary(index=1, print_time_s=5400, weight_g=45.0),
        PlateSummary(index=2, print_time_s=3600, weight_g=30.0),
    )
    costs = _allocate_plate_costs(plates, bd)
    assert sum(costs) == bd.total


def test_allocate_plate_costs_with_markup_sums_to_total():
    from geekcurio_print_manager.models.quote import QuoteBreakdown
    bd = QuoteBreakdown(
        print_time_hours=2.5, print_time_cost=Decimal("7.50"),
        material_weight_g=75.0, material_cost=Decimal("3.75"),
        overhead_multiplier=Decimal("1"), markup_percentage=Decimal("20"),
        subtotal=Decimal("11.25"), markup_amount=Decimal("2.25"), total=Decimal("13.50"),
    )
    plates = (
        PlateSummary(index=1, print_time_s=5400, weight_g=45.0),
        PlateSummary(index=2, print_time_s=3600, weight_g=30.0),
        PlateSummary(index=3, print_time_s=1800, weight_g=10.0),
    )
    costs = _allocate_plate_costs(plates, bd)
    assert sum(costs) == bd.total
    assert all(c >= Decimal("0") for c in costs)


def test_pdf_plate_allocated_cost_appears_in_table(saved, pdf_path):
    from geekcurio_print_manager.exporters.pdf_quote_export import _allocate_plate_costs
    costs = _allocate_plate_costs(saved.plates, saved.breakdown)
    text = _pdf_text(pdf_path)
    for cost in costs:
        assert f"{cost:.2f}" in text


# ── Internal pricing mechanics not exposed ────────────────────────────────────

def test_pdf_does_not_expose_markup():
    repo = _repo()
    profile = PricingProfile(
        name="premium", label="Premium FDM",
        config=PricingConfig(markup_percentage=Decimal("20")),
    )
    job = _job()
    breakdown = QuoteService(profile.config).calculate(job)
    saved = repo.save(job, breakdown, profile)

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "test.pdf"
        build_pdf_quote(saved, path)
        text = _pdf_text(path)

    assert "Markup" not in text
    assert "markup" not in text


def test_pdf_does_not_expose_subtotal_line():
    repo = _repo()
    profile = PricingProfile(
        name="premium", label="Premium FDM",
        config=PricingConfig(markup_percentage=Decimal("20")),
    )
    job = _job()
    breakdown = QuoteService(profile.config).calculate(job)
    saved = repo.save(job, breakdown, profile)

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "test.pdf"
        build_pdf_quote(saved, path)
        text = _pdf_text(path)

    assert "Subtotal" not in text


def test_pdf_does_not_expose_profile_label(saved, pdf_path):
    assert saved.profile_label not in _pdf_text(pdf_path)


def test_pdf_does_not_expose_hourly_rate(pdf_path):
    text = _pdf_text(pdf_path)
    assert "per hour" not in text.lower()
    assert "/hr" not in text
    assert "per gram" not in text.lower()


# ── Notes section ─────────────────────────────────────────────────────────────

def test_pdf_shows_default_notes_when_absent(pdf_path):
    text = _pdf_text(pdf_path)
    assert "Notes" in text
    assert "high quality filament" in text


def test_pdf_contains_saved_notes_when_present(tmp_path):
    repo = _repo()
    profile = _profile()
    job = _job()
    breakdown = QuoteService(profile.config).calculate(job)
    saved = repo.save(job, breakdown, profile, notes="Rush order for testing")

    path = tmp_path / "notes.pdf"
    build_pdf_quote(saved, path)
    assert "Rush order for testing" in _pdf_text(path)


def test_pdf_saved_notes_replace_default_notes(tmp_path):
    repo = _repo()
    profile = _profile()
    job = _job()
    breakdown = QuoteService(profile.config).calculate(job)
    saved = repo.save(job, breakdown, profile, notes="Custom note only")

    path = tmp_path / "custom.pdf"
    build_pdf_quote(saved, path)
    text = _pdf_text(path)
    assert "Custom note only" in text
    # Default notes should not appear when saved notes are present
    assert "high quality filament" not in text


# ── Recommendation section ────────────────────────────────────────────────────

def test_pdf_recommendation_shown_for_multi_plate(multi_pdf_path):
    assert "Recommendation" in _pdf_text(multi_pdf_path)


def test_pdf_recommendation_omitted_for_single_plate(pdf_path):
    assert "Recommendation" not in _pdf_text(pdf_path)


# ── Closing line ──────────────────────────────────────────────────────────────

def test_pdf_contains_closing_line(pdf_path):
    assert "Thank you for considering GeekCurio" in _pdf_text(pdf_path)
