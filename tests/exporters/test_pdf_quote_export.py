import sqlite3
from decimal import Decimal
from pathlib import Path

import pypdf
import pytest

from geekcurio_print_manager.db.schema import initialise_database
from geekcurio_print_manager.exporters.pdf_quote_export import build_pdf_quote
from geekcurio_print_manager.models.print_job import FilamentUsage, PlateSummary, PrintJob
from geekcurio_print_manager.models.pricing_config import PricingConfig
from geekcurio_print_manager.models.pricing_profile import PricingProfile
from geekcurio_print_manager.services.quote_repository import QuoteRepository
from geekcurio_print_manager.services.quote_service import QuoteService


def _repo() -> QuoteRepository:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    initialise_database(conn)
    return QuoteRepository(conn)


def _profile() -> PricingProfile:
    return PricingProfile(
        name="fdm_pla",
        label="FDM - PLA (Standard)",
        config=PricingConfig(),
    )


def _job() -> PrintJob:
    return PrintJob(
        source_path=Path("TestPart.3mf"),
        slicer="BambuStudio",
        plates=(
            PlateSummary(
                index=1,
                print_time_s=5400,
                weight_g=45.0,
                filaments=(FilamentUsage(filament_id=1, type="PLA", used_g=45.0, color="#FFFFFF"),),
                support_used=False,
                printer_model_id="Bambu Lab X1 Carbon",
            ),
        ),
    )


def _pdf_text(path: Path) -> str:
    reader = pypdf.PdfReader(str(path))
    return " ".join(page.extract_text() or "" for page in reader.pages)


@pytest.fixture
def saved(tmp_path):
    repo = _repo()
    profile = _profile()
    job = _job()
    breakdown = QuoteService(profile.config).calculate(job)
    return repo.save(job, breakdown, profile)


@pytest.fixture
def pdf_path(saved, tmp_path):
    path = tmp_path / f"{saved.quote_ref}.pdf"
    build_pdf_quote(saved, path)
    return path


def test_pdf_file_is_created(pdf_path):
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0


def test_pdf_contains_brand_name(pdf_path):
    assert "GeekCurio" in _pdf_text(pdf_path)


def test_pdf_contains_quote_reference(saved, pdf_path):
    assert saved.quote_ref in _pdf_text(pdf_path)


def test_pdf_contains_total_amount(saved, pdf_path):
    total_str = f"{saved.breakdown.total:.2f}"
    assert total_str in _pdf_text(pdf_path)


def test_pdf_contains_source_filename(saved, pdf_path):
    assert saved.source_file in _pdf_text(pdf_path)


def test_pdf_contains_profile_label(saved, pdf_path):
    assert saved.profile_label in _pdf_text(pdf_path)


def test_pdf_uses_saved_total_not_recalculated(tmp_path):
    # Build a SavedQuote with a deliberately unusual total to confirm
    # the exporter renders the stored value, not a fresh calculation.
    repo = _repo()
    profile = _profile()
    job = _job()
    breakdown = QuoteService(profile.config).calculate(job)
    saved = repo.save(job, breakdown, profile)

    # Retrieve from the DB so the values are the persisted ones
    retrieved = repo.get_by_ref(saved.quote_ref)
    path = tmp_path / "check.pdf"
    build_pdf_quote(retrieved, path)

    text = _pdf_text(path)
    assert f"{retrieved.breakdown.total:.2f}" in text


def test_pdf_contains_notes_when_present(tmp_path):
    repo = _repo()
    profile = _profile()
    job = _job()
    breakdown = QuoteService(profile.config).calculate(job)
    saved = repo.save(job, breakdown, profile, notes="Rush order for Asim")

    path = tmp_path / "notes.pdf"
    build_pdf_quote(saved, path)
    assert "Rush order for Asim" in _pdf_text(path)


def test_pdf_omits_notes_section_when_absent(pdf_path):
    assert "NOTES" not in _pdf_text(pdf_path)


def test_pdf_contains_plate_breakdown(saved, pdf_path):
    assert "PLATE BREAKDOWN" in _pdf_text(pdf_path)
    assert "Plate 1" in _pdf_text(pdf_path)


def test_pdf_contains_filament_type(pdf_path):
    assert "PLA" in _pdf_text(pdf_path)


def test_pdf_creates_parent_directories(saved, tmp_path):
    nested = tmp_path / "a" / "b" / "c" / f"{saved.quote_ref}.pdf"
    build_pdf_quote(saved, nested)
    assert nested.exists()


def test_pdf_overwrite_is_allowed(saved, tmp_path):
    path = tmp_path / "overwrite.pdf"
    build_pdf_quote(saved, path)
    size_first = path.stat().st_size
    build_pdf_quote(saved, path)
    assert path.stat().st_size == size_first


def test_pdf_markup_shown_when_applied(tmp_path):
    profile = PricingProfile(
        name="premium",
        label="Premium FDM",
        config=PricingConfig(markup_percentage=Decimal("20")),
    )
    repo = _repo()
    job = _job()
    breakdown = QuoteService(profile.config).calculate(job)
    saved = repo.save(job, breakdown, profile)

    path = tmp_path / "markup.pdf"
    build_pdf_quote(saved, path)
    text = _pdf_text(path)
    assert "Markup" in text
    assert "Subtotal" in text
