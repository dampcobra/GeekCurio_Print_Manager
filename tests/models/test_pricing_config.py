import pytest

from geekcurio_print_manager.models.pricing_config import PricingConfig


def test_default_rates_match_geekqurio_pricing():
    config = PricingConfig()
    assert config.hourly_machine_rate == pytest.approx(3.0)
    assert config.material_cost_per_gram == pytest.approx(0.05)


def test_default_optional_fields_are_neutral():
    config = PricingConfig()
    assert config.overhead_multiplier == pytest.approx(1.0)
    assert config.markup_percentage == pytest.approx(0.0)


def test_custom_values_are_stored():
    config = PricingConfig(hourly_machine_rate=5.0, material_cost_per_gram=0.05,
                           overhead_multiplier=1.2, markup_percentage=15.0)
    assert config.hourly_machine_rate == pytest.approx(5.0)
    assert config.material_cost_per_gram == pytest.approx(0.05)
    assert config.overhead_multiplier == pytest.approx(1.2)
    assert config.markup_percentage == pytest.approx(15.0)


def test_pricing_config_is_immutable():
    config = PricingConfig()
    with pytest.raises(AttributeError):
        config.hourly_machine_rate = 99.0  # type: ignore[misc]
