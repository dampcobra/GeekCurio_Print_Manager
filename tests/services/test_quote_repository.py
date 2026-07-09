import re
import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest

from geekcurio_print_manager.db.schema import initialise_database
from geekcurio_print_manager.models.print_job import FilamentUsage, PlateSummary, PrintJob
from geekcurio_print_manager.models.pricing_config import PricingConfig
from geekcurio_print_manager.models.pricing_profile import PricingProfile
from geekcurio_print_manager.services.quote_repository import QuoteRepository
from geekcurio_print_manager.services.quote_service import QuoteService


@pytest.fixture
def repo() -> QuoteRepository:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    initialise_database(conn)
    return QuoteRepository(conn)


def _profile(name: str = "fdm_pla", label: str = "FDM - PLA") -> PricingProfile:
    return PricingProfile(name=name, label=label, config=PricingConfig())


def _job() -> PrintJob:
    return PrintJob(
        source_path=Path("test-part.3mf"),
        slicer="BambuStudio",
        plates=(
            PlateSummary(
                index=1,
                print_time_s=3600,
                weight_g=50.0,
                filaments=(FilamentUsage(filament_id=1, type="PLA", used_g=50.0, color="#FFFFFF"),),
                support_used=False,
                printer_model_id="Bambu Lab X1 Carbon",
            ),
        ),
    )


def test_save_returns_saved_quote_with_ref(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile)
    assert saved.quote_ref.startswith("GCQ-")


def test_quote_ref_format_matches_pattern(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile)
    assert re.fullmatch(r"GCQ-\d{4}-\d{6}", saved.quote_ref)


def test_quote_ref_sequence_starts_at_one(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile)
    assert saved.quote_ref.endswith("-000001")


def test_quote_ref_sequence_increments(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved1 = repo.save(_job(), breakdown, profile)
    saved2 = repo.save(_job(), breakdown, profile)
    assert saved1.quote_ref.endswith("-000001")
    assert saved2.quote_ref.endswith("-000002")


def test_profile_values_are_snapshotted(repo):
    profile = _profile(name="custom_profile", label="Custom Label")
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile)
    assert saved.profile_name == "custom_profile"
    assert saved.profile_label == "Custom Label"


def test_source_file_is_filename_only(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile)
    assert saved.source_file == "test-part.3mf"
    assert "\\" not in saved.source_file
    assert "/" not in saved.source_file


def test_plates_are_persisted(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile)
    assert len(saved.plates) == 1
    assert saved.plates[0].index == 1
    assert saved.plates[0].print_time_s == 3600
    assert saved.plates[0].weight_g == pytest.approx(50.0)
    assert saved.plates[0].support_used is False
    assert saved.plates[0].printer_model_id == "Bambu Lab X1 Carbon"


def test_filaments_are_persisted(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile)
    filament = saved.plates[0].filaments[0]
    assert filament.type == "PLA"
    assert filament.color == "#FFFFFF"
    assert filament.used_g == pytest.approx(50.0)


def test_monetary_values_are_exact_decimal(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile)
    assert isinstance(saved.breakdown.total, Decimal)
    assert saved.breakdown.total == breakdown.total


def test_get_by_ref_retrieves_saved_quote(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile)
    retrieved = repo.get_by_ref(saved.quote_ref)
    assert retrieved is not None
    assert retrieved.quote_ref == saved.quote_ref
    assert retrieved.source_file == "test-part.3mf"
    assert retrieved.breakdown.total == saved.breakdown.total


def test_get_by_ref_retrieves_plates(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile)
    retrieved = repo.get_by_ref(saved.quote_ref)
    assert len(retrieved.plates) == 1
    assert retrieved.plates[0].filaments[0].type == "PLA"
    assert retrieved.plates[0].filaments[0].color == "#FFFFFF"


def test_get_by_ref_returns_none_for_unknown_ref(repo):
    assert repo.get_by_ref("GCQ-2026-999999") is None


def test_list_recent_returns_newest_first(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved1 = repo.save(_job(), breakdown, profile)
    saved2 = repo.save(_job(), breakdown, profile)
    results = repo.list_recent(10)
    assert results[0].quote_ref == saved2.quote_ref
    assert results[1].quote_ref == saved1.quote_ref


def test_list_recent_respects_limit(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    for _ in range(5):
        repo.save(_job(), breakdown, profile)
    results = repo.list_recent(3)
    assert len(results) == 3


def test_notes_default_to_none(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile)
    assert saved.notes is None


def test_notes_are_persisted_and_retrieved(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile, notes="Rush order — needed by Friday")
    assert saved.notes == "Rush order — needed by Friday"
    retrieved = repo.get_by_ref(saved.quote_ref)
    assert retrieved.notes == "Rush order — needed by Friday"


def test_notes_none_round_trips_as_none(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile, notes=None)
    retrieved = repo.get_by_ref(saved.quote_ref)
    assert retrieved.notes is None


def test_customer_name_defaults_to_none(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile)
    assert saved.customer_name is None


def test_project_name_defaults_to_none(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile)
    assert saved.project_name is None


def test_customer_name_is_persisted_and_retrieved(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile, customer_name="Asim")
    assert saved.customer_name == "Asim"
    retrieved = repo.get_by_ref(saved.quote_ref)
    assert retrieved.customer_name == "Asim"


def test_project_name_is_persisted_and_retrieved(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile, project_name="4th Planet Battle Doggo")
    assert saved.project_name == "4th Planet Battle Doggo"
    retrieved = repo.get_by_ref(saved.quote_ref)
    assert retrieved.project_name == "4th Planet Battle Doggo"


def test_source_file_unchanged_when_project_name_set(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile, project_name="Custom Display Name")
    assert saved.source_file == "test-part.3mf"
    retrieved = repo.get_by_ref(saved.quote_ref)
    assert retrieved.source_file == "test-part.3mf"


def test_customer_and_project_name_none_round_trips(repo):
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(_job())
    saved = repo.save(_job(), breakdown, profile, customer_name=None, project_name=None)
    retrieved = repo.get_by_ref(saved.quote_ref)
    assert retrieved.customer_name is None
    assert retrieved.project_name is None


def test_multiplate_job_persists_all_plates(repo):
    job = PrintJob(
        source_path=Path("multiplate.3mf"),
        slicer="BambuStudio",
        plates=(
            PlateSummary(index=1, print_time_s=1800, weight_g=20.0,
                         filaments=(FilamentUsage(filament_id=1, type="PLA", used_g=20.0),)),
            PlateSummary(index=2, print_time_s=3600, weight_g=30.0,
                         filaments=(FilamentUsage(filament_id=1, type="PETG", used_g=30.0),)),
        ),
    )
    profile = _profile()
    breakdown = QuoteService(profile.config).calculate(job)
    saved = repo.save(job, breakdown, profile)
    retrieved = repo.get_by_ref(saved.quote_ref)
    assert len(retrieved.plates) == 2
    assert retrieved.plates[0].filaments[0].type == "PLA"
    assert retrieved.plates[1].filaments[0].type == "PETG"
