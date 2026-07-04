from dataclasses import dataclass
from decimal import Decimal

from geekcurio_print_manager.models.pricing_config import PricingConfig


@dataclass(frozen=True, slots=True)
class PricingProfile:
    name: str
    label: str
    config: PricingConfig


BUILTIN_PROFILES: tuple[PricingProfile, ...] = (
    PricingProfile(
        name="fdm_pla",
        label="FDM — PLA (Standard)",
        config=PricingConfig(hourly_machine_rate=Decimal("3.00"), material_cost_per_gram=Decimal("0.05")),
    ),
    PricingProfile(
        name="fdm_petg",
        label="FDM — PETG",
        config=PricingConfig(hourly_machine_rate=Decimal("3.00"), material_cost_per_gram=Decimal("0.04")),
    ),
    PricingProfile(
        name="resin",
        label="Resin",
        # £4/hr and £0.15/g cover exposure time only; the rate is set high to also recover
        # cleanup time, IPA, support removal, gloves, and general handling overhead.
        config=PricingConfig(hourly_machine_rate=Decimal("4.00"), material_cost_per_gram=Decimal("0.15")),
    ),
    PricingProfile(
        name="premium_fdm",
        label="Premium FDM / Custom Work",
        config=PricingConfig(
            hourly_machine_rate=Decimal("3.00"),
            material_cost_per_gram=Decimal("0.05"),
            markup_percentage=Decimal("30"),
        ),
    ),
    PricingProfile(
        name="internal_test",
        label="Internal / Testing",
        config=PricingConfig(hourly_machine_rate=Decimal("1.50"), material_cost_per_gram=Decimal("0.02")),
    ),
)


def get_profile(name: str) -> PricingProfile | None:
    return next((p for p in BUILTIN_PROFILES if p.name == name), None)
