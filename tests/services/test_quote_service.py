from pathlib import Path

import pytest

from geekcurio_print_manager.models.pricing_config import PricingConfig
from geekcurio_print_manager.models.print_job import PlateSummary, PrintJob
from geekcurio_print_manager.services.quote_service import QuoteService


def _job(print_time_s: int, weight_g: float) -> PrintJob:
    return PrintJob(
        source_path=Path("test.3mf"),
        slicer="test",
        plates=(PlateSummary(index=1, print_time_s=print_time_s, weight_g=weight_g),),
    )


# --- PricingConfig defaults ---

def test_default_config_rates():
    config = PricingConfig()
    assert config.hourly_machine_rate == pytest.approx(3.0)
    assert config.material_cost_per_gram == pytest.approx(0.03)


def test_default_config_optional_fields_are_neutral():
    config = PricingConfig()
    assert config.overhead_multiplier == pytest.approx(1.0)
    assert config.markup_percentage == pytest.approx(0.0)


# --- Normal project ---

def test_normal_job_produces_correct_breakdown():
    # 3600s = 1 hr, 100 g  →  time_cost=3.00, material=3.00, total=6.00
    breakdown = QuoteService().calculate(_job(3600, 100.0))
    assert breakdown.print_time_hours == pytest.approx(1.0)
    assert breakdown.print_time_cost == pytest.approx(3.0)
    assert breakdown.material_weight_g == pytest.approx(100.0)
    assert breakdown.material_cost == pytest.approx(3.0)
    assert breakdown.subtotal == pytest.approx(6.0)
    assert breakdown.markup_amount == pytest.approx(0.0)
    assert breakdown.total == pytest.approx(6.0)


def test_custom_rates():
    # £5/hr, £0.05/g, 2 hrs, 200 g  →  time=10.00, material=10.00, total=20.00
    config = PricingConfig(hourly_machine_rate=5.0, material_cost_per_gram=0.05)
    breakdown = QuoteService(config).calculate(_job(7200, 200.0))
    assert breakdown.print_time_cost == pytest.approx(10.0)
    assert breakdown.material_cost == pytest.approx(10.0)
    assert breakdown.total == pytest.approx(20.0)


# --- Edge cases ---

def test_zero_print_time():
    breakdown = QuoteService().calculate(_job(0, 50.0))
    assert breakdown.print_time_hours == pytest.approx(0.0)
    assert breakdown.print_time_cost == pytest.approx(0.0)
    assert breakdown.total == pytest.approx(50.0 * 0.03)


def test_zero_material_weight():
    breakdown = QuoteService().calculate(_job(3600, 0.0))
    assert breakdown.material_cost == pytest.approx(0.0)
    assert breakdown.total == pytest.approx(3.0)


def test_zero_time_and_zero_weight():
    breakdown = QuoteService().calculate(_job(0, 0.0))
    assert breakdown.print_time_cost == pytest.approx(0.0)
    assert breakdown.material_cost == pytest.approx(0.0)
    assert breakdown.subtotal == pytest.approx(0.0)
    assert breakdown.markup_amount == pytest.approx(0.0)
    assert breakdown.total == pytest.approx(0.0)


# --- Overhead multiplier ---

def test_overhead_multiplier_scales_subtotal():
    # 1 hr, 100 g → raw=6.00, ×1.2 → subtotal=7.20
    config = PricingConfig(overhead_multiplier=1.2)
    breakdown = QuoteService(config).calculate(_job(3600, 100.0))
    assert breakdown.subtotal == pytest.approx(7.2)
    assert breakdown.markup_amount == pytest.approx(0.0)
    assert breakdown.total == pytest.approx(7.2)


def test_overhead_of_one_is_unchanged():
    bd_default = QuoteService().calculate(_job(3600, 100.0))
    config = PricingConfig(overhead_multiplier=1.0)
    bd_explicit = QuoteService(config).calculate(_job(3600, 100.0))
    assert bd_default.total == pytest.approx(bd_explicit.total)


# --- Markup percentage ---

def test_markup_percentage_applied_to_subtotal():
    # subtotal=6.00, markup=25% → markup_amount=1.50, total=7.50
    config = PricingConfig(markup_percentage=25.0)
    breakdown = QuoteService(config).calculate(_job(3600, 100.0))
    assert breakdown.subtotal == pytest.approx(6.0)
    assert breakdown.markup_amount == pytest.approx(1.5)
    assert breakdown.total == pytest.approx(7.5)


def test_overhead_and_markup_combined():
    # raw=6.00, ×1.2 → subtotal=7.20, +10% → markup=0.72, total=7.92
    config = PricingConfig(overhead_multiplier=1.2, markup_percentage=10.0)
    breakdown = QuoteService(config).calculate(_job(3600, 100.0))
    assert breakdown.subtotal == pytest.approx(7.2)
    assert breakdown.markup_amount == pytest.approx(0.72)
    assert breakdown.total == pytest.approx(7.92)


# --- Multi-plate job ---

def test_multi_plate_job_totals_across_plates():
    # plate1: 3600s, 50g; plate2: 7200s, 100g → 3 hrs, 150g → 9.00+4.50=13.50
    plates = (
        PlateSummary(index=1, print_time_s=3600, weight_g=50.0),
        PlateSummary(index=2, print_time_s=7200, weight_g=100.0),
    )
    job = PrintJob(source_path=Path("multi.3mf"), slicer="test", plates=plates)
    breakdown = QuoteService().calculate(job)
    assert breakdown.print_time_hours == pytest.approx(3.0)
    assert breakdown.material_weight_g == pytest.approx(150.0)
    assert breakdown.total == pytest.approx(13.5)


# --- Breakdown captures config values ---

def test_breakdown_records_overhead_and_markup_values():
    config = PricingConfig(overhead_multiplier=1.15, markup_percentage=20.0)
    breakdown = QuoteService(config).calculate(_job(3600, 100.0))
    assert breakdown.overhead_multiplier == pytest.approx(1.15)
    assert breakdown.markup_percentage == pytest.approx(20.0)
