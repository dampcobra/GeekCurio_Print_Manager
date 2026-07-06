import sqlite3
from pathlib import Path

import pytest

from geekcurio_print_manager.db.schema import initialise_database
from geekcurio_print_manager.models.print_job import FilamentUsage, PlateSummary, PrintJob
from geekcurio_print_manager.models.pricing_config import PricingConfig
from geekcurio_print_manager.models.pricing_profile import PricingProfile
from geekcurio_print_manager.services.quote_repository import QuoteRepository
from geekcurio_print_manager.services.quote_service import QuoteService
from geekcurio_print_manager.ui.pdf_quote_console import run_pdf_quote


def _repo() -> QuoteRepository:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    initialise_database(conn)
    return QuoteRepository(conn)


def _save_one(repo: QuoteRepository) -> str:
    profile = PricingProfile(name="fdm_pla", label="FDM - PLA", config=PricingConfig())
    job = PrintJob(
        source_path=Path("cli-test.3mf"),
        slicer="BambuStudio",
        plates=(
            PlateSummary(
                index=1,
                print_time_s=3600,
                weight_g=30.0,
                filaments=(FilamentUsage(filament_id=1, type="PLA", used_g=30.0),),
            ),
        ),
    )
    breakdown = QuoteService(profile.config).calculate(job)
    saved = repo.save(job, breakdown, profile)
    return saved.quote_ref


def test_missing_ref_exits_with_error(capsys):
    repo = _repo()
    result = run_pdf_quote(repo, ["GCQ-9999-999999"])
    assert result == 1
    out = capsys.readouterr().out
    assert "GCQ-9999-999999" in out
    assert "not found" in out


def test_valid_ref_exits_zero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo = _repo()
    ref = _save_one(repo)
    result = run_pdf_quote(repo, [ref])
    assert result == 0


def test_valid_ref_creates_pdf_in_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo = _repo()
    ref = _save_one(repo)
    run_pdf_quote(repo, [ref])
    assert (tmp_path / f"{ref}.pdf").exists()


def test_explicit_output_path_is_used(tmp_path):
    repo = _repo()
    ref = _save_one(repo)
    out = tmp_path / "my-quote.pdf"
    result = run_pdf_quote(repo, [ref, "--output", str(out)])
    assert result == 0
    assert out.exists()


def test_explicit_output_short_flag(tmp_path):
    repo = _repo()
    ref = _save_one(repo)
    out = tmp_path / "short.pdf"
    result = run_pdf_quote(repo, [ref, "-o", str(out)])
    assert result == 0
    assert out.exists()


def test_output_message_shows_path(tmp_path, capsys):
    repo = _repo()
    ref = _save_one(repo)
    out = tmp_path / "msg.pdf"
    run_pdf_quote(repo, [ref, "--output", str(out)])
    captured = capsys.readouterr().out
    assert "PDF saved" in captured
    assert str(out) in captured


def test_output_to_existing_directory_creates_file(tmp_path):
    repo = _repo()
    ref = _save_one(repo)
    result = run_pdf_quote(repo, [ref, "--output", str(tmp_path)])
    assert result == 0
    assert (tmp_path / f"{ref}.pdf").exists()


def test_output_with_missing_parent_directories(tmp_path):
    repo = _repo()
    ref = _save_one(repo)
    out = tmp_path / "new" / "sub" / "quote.pdf"
    result = run_pdf_quote(repo, [ref, "--output", str(out)])
    assert result == 0
    assert out.exists()
