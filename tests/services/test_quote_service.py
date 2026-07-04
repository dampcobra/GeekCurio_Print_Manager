from decimal import Decimal
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
    assert config.hourly_machine_rate == Decimal("3.00")
    assert config.material_cost_per_gram == Decimal("0.05")


def test_default_config_optional_fields_are_neutral():
    config = PricingConfig()
    assert config.overhead_multiplier == Decimal("1.0")
    assert config.markup_percentage == Decimal("0")


# --- Normal project ---

def test_normal_job_produces_correct_breakdown():
    # 3600s = 1 hr, 100 g  →  time_cost=£3.00, material=£5.00, total=£8.00
    breakdown = QuoteService().calculate(_job(3600, 100.0))
    assert breakdown.print_time_hours == pytest.approx(1.0)
    assert breakdown.print_time_cost == Decimal("3.00")
    assert breakdown.material_weight_g == pytest.approx(100.0)
    assert breakdown.material_cost == Decimal("5.00")
    assert breakdown.subtotal == Decimal("8.00")
    assert breakdown.markup_amount == Decimal("0.00")
    assert breakdown.total == Decimal("8.00")


def test_custom_rates():
    # £5/hr, £0.05/g, 2 hrs, 200 g  →  time=£10.00, material=£10.00, total=£20.00
    config = PricingConfig(
        hourly_machine_rate=Decimal("5.00"),
        material_cost_per_gram=Decimal("0.05"),
    )
    breakdown = QuoteService(config).calculate(_job(7200, 200.0))
    assert breakdown.print_time_cost == Decimal("10.00")
    assert breakdown.material_cost == Decimal("10.00")
    assert breakdown.total == Decimal("20.00")


# --- Edge cases ---

def test_zero_print_time():
    breakdown = QuoteService().calculate(_job(0, 50.0))
    assert breakdown.print_time_hours == pytest.approx(0.0)
    assert breakdown.print_time_cost == Decimal("0.00")
    assert breakdown.total == Decimal("2.50")  # 50 g × £0.05


def test_zero_material_weight():
    breakdown = QuoteService().calculate(_job(3600, 0.0))
    assert breakdown.material_cost == Decimal("0.00")
    assert breakdown.total == Decimal("3.00")


def test_zero_time_and_zero_weight():
    breakdown = QuoteService().calculate(_job(0, 0.0))
    assert breakdown.print_time_cost == Decimal("0.00")
    assert breakdown.material_cost == Decimal("0.00")
    assert breakdown.subtotal == Decimal("0.00")
    assert breakdown.markup_amount == Decimal("0.00")
    assert breakdown.total == Decimal("0.00")


# --- Overhead multiplier ---

def test_overhead_multiplier_scales_subtotal():
    # 1 hr, 100 g → raw=£8.00, ×1.2 → subtotal=£9.60
    config = PricingConfig(overhead_multiplier=Decimal("1.2"))
    breakdown = QuoteService(config).calculate(_job(3600, 100.0))
    assert breakdown.subtotal == Decimal("9.60")
    assert breakdown.markup_amount == Decimal("0.00")
    assert breakdown.total == Decimal("9.60")


def test_overhead_of_one_is_unchanged():
    bd_default = QuoteService().calculate(_job(3600, 100.0))
    bd_explicit = QuoteService(PricingConfig(overhead_multiplier=Decimal("1.0"))).calculate(_job(3600, 100.0))
    assert bd_default.total == bd_explicit.total


# --- Markup percentage ---

def test_markup_percentage_applied_to_subtotal():
    # 1 hr, 100 g → subtotal=£8.00, markup=25% → +£2.00, total=£10.00
    config = PricingConfig(markup_percentage=Decimal("25"))
    breakdown = QuoteService(config).calculate(_job(3600, 100.0))
    assert breakdown.subtotal == Decimal("8.00")
    assert breakdown.markup_amount == Decimal("2.00")
    assert breakdown.total == Decimal("10.00")


def test_overhead_and_markup_combined():
    # 1 hr, 100 g → raw=£8.00, ×1.2 → subtotal=£9.60, +10% → markup=£0.96, total=£10.56
    config = PricingConfig(overhead_multiplier=Decimal("1.2"), markup_percentage=Decimal("10"))
    breakdown = QuoteService(config).calculate(_job(3600, 100.0))
    assert breakdown.subtotal == Decimal("9.60")
    assert breakdown.markup_amount == Decimal("0.96")
    assert breakdown.total == Decimal("10.56")


# --- Multi-plate job ---

def test_multi_plate_job_totals_across_plates():
    # plate1: 3600s, 50g; plate2: 7200s, 100g → 3 hrs, 150g → £9.00+£7.50=£16.50
    plates = (
        PlateSummary(index=1, print_time_s=3600, weight_g=50.0),
        PlateSummary(index=2, print_time_s=7200, weight_g=100.0),
    )
    job = PrintJob(source_path=Path("multi.3mf"), slicer="test", plates=plates)
    breakdown = QuoteService().calculate(job)
    assert breakdown.print_time_hours == pytest.approx(3.0)
    assert breakdown.material_weight_g == pytest.approx(150.0)
    assert breakdown.total == Decimal("16.50")


# --- Breakdown captures config values ---

def test_breakdown_records_overhead_and_markup_values():
    config = PricingConfig(overhead_multiplier=Decimal("1.15"), markup_percentage=Decimal("20"))
    breakdown = QuoteService(config).calculate(_job(3600, 100.0))
    assert breakdown.overhead_multiplier == Decimal("1.15")
    assert breakdown.markup_percentage == Decimal("20")


# --- Decimal precision ---

def test_decimal_avoids_float_binary_precision_error():
    # With float arithmetic 0.1 + 0.2 = 0.30000000000000004, not 0.3.
    # Decimal arithmetic produces the exact result.
    config = PricingConfig(
        hourly_machine_rate=Decimal("0.10"),
        material_cost_per_gram=Decimal("0.20"),
    )
    breakdown = QuoteService(config).calculate(_job(3600, 1))  # 1 hr, 1 g
    assert breakdown.print_time_cost == Decimal("0.10")
    assert breakdown.material_cost == Decimal("0.20")
    assert breakdown.total == Decimal("0.30")
    assert 0.1 + 0.2 != 0.3  # confirms the float problem exists
