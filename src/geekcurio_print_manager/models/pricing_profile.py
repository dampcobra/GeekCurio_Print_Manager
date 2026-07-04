from dataclasses import dataclass

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
        config=PricingConfig(hourly_machine_rate=3.0, material_cost_per_gram=0.05),
    ),
    PricingProfile(
        name="fdm_petg",
        label="FDM — PETG",
        config=PricingConfig(hourly_machine_rate=3.0, material_cost_per_gram=0.04),
    ),
    PricingProfile(
        name="resin",
        label="Resin",
        # £4/hr and £0.15/g cover exposure time only; the rate is set high to also recover
        # cleanup time, IPA, support removal, gloves, and general handling overhead.
        config=PricingConfig(hourly_machine_rate=4.0, material_cost_per_gram=0.15),
    ),
    PricingProfile(
        name="premium_fdm",
        label="Premium FDM / Custom Work",
        config=PricingConfig(hourly_machine_rate=3.0, material_cost_per_gram=0.05, markup_percentage=30.0),
    ),
    PricingProfile(
        name="internal_test",
        label="Internal / Testing",
        config=PricingConfig(hourly_machine_rate=1.5, material_cost_per_gram=0.02),
    ),
)


def get_profile(name: str) -> PricingProfile | None:
    return next((p for p in BUILTIN_PROFILES if p.name == name), None)
