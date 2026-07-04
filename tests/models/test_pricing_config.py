from decimal import Decimal

import pytest

from geekcurio_print_manager.models.pricing_config import PricingConfig


def test_default_rates_match_geekurio_pricing():
    config = PricingConfig()
    assert config.hourly_machine_rate == Decimal("3.00")
    assert config.material_cost_per_gram == Decimal("0.05")


def test_default_optional_fields_are_neutral():
    config = PricingConfig()
    assert config.overhead_multiplier == Decimal("1.0")
    assert config.markup_percentage == Decimal("0")


def test_custom_values_are_stored():
    config = PricingConfig(
        hourly_machine_rate=Decimal("5.00"),
        material_cost_per_gram=Decimal("0.05"),
        overhead_multiplier=Decimal("1.2"),
        markup_percentage=Decimal("15"),
    )
    assert config.hourly_machine_rate == Decimal("5.00")
    assert config.material_cost_per_gram == Decimal("0.05")
    assert config.overhead_multiplier == Decimal("1.2")
    assert config.markup_percentage == Decimal("15")


def test_pricing_config_is_immutable():
    config = PricingConfig()
    with pytest.raises(AttributeError):
        config.hourly_machine_rate = Decimal("99.00")  # type: ignore[misc]
