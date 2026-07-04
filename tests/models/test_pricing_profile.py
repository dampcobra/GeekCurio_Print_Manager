from decimal import Decimal

import pytest

from geekcurio_print_manager.models.pricing_profile import BUILTIN_PROFILES, get_profile


def test_all_builtin_profile_names_are_unique():
    names = [p.name for p in BUILTIN_PROFILES]
    assert len(names) == len(set(names))


def test_all_profiles_have_non_empty_name_and_label():
    for p in BUILTIN_PROFILES:
        assert p.name.strip()
        assert p.label.strip()


def test_fdm_pla_is_first_profile():
    assert BUILTIN_PROFILES[0].name == "fdm_pla"


def test_get_profile_returns_correct_profile():
    p = get_profile("fdm_pla")
    assert p is not None
    assert p.label == "FDM — PLA (Standard)"
    assert p.config.hourly_machine_rate == Decimal("3.00")
    assert p.config.material_cost_per_gram == Decimal("0.05")


def test_get_profile_returns_none_for_unknown_name():
    assert get_profile("does_not_exist") is None


def test_resin_profile_rates():
    p = get_profile("resin")
    assert p is not None
    assert p.config.hourly_machine_rate == Decimal("4.00")
    assert p.config.material_cost_per_gram == Decimal("0.15")


def test_premium_fdm_has_markup():
    p = get_profile("premium_fdm")
    assert p is not None
    assert p.config.markup_percentage == Decimal("30")


def test_internal_test_profile_exists_with_reduced_rates():
    p = get_profile("internal_test")
    assert p is not None
    assert p.config.hourly_machine_rate == Decimal("1.50")
    assert p.config.material_cost_per_gram == Decimal("0.02")


def test_profiles_are_immutable():
    p = get_profile("fdm_pla")
    with pytest.raises(AttributeError):
        p.name = "changed"  # type: ignore[misc]
