import argparse
from collections.abc import Sequence

from geekcurio_print_manager.exceptions import PrintManagerError
from geekcurio_print_manager.exporters.quote_export import build_quote_report
from geekcurio_print_manager.models.pricing_profile import BUILTIN_PROFILES, get_profile
from geekcurio_print_manager.services.inspection_service import InspectionService
from geekcurio_print_manager.services.quote_service import QuoteService

_DEFAULT_PROFILE = "fdm_pla"


def _list_profiles() -> None:
    print("Available pricing profiles:\n")
    for p in BUILTIN_PROFILES:
        cfg = p.config
        markup_str = f"{cfg.markup_percentage:.0f}% markup" if cfg.markup_percentage else "no markup"
        print(
            f"  {p.name:<14}  {p.label:<30}"
            f"  £{cfg.hourly_machine_rate:.2f}/hr"
            f"  £{cfg.material_cost_per_gram:.2f}/g"
            f"  {markup_str:>10}"
        )


def run_quote(
    inspection_service: InspectionService,
    argv: Sequence[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        prog="geekcurio-quote",
        description="Generate a GeekCurio price quote from a sliced .3mf file.",
    )
    parser.add_argument("path", nargs="?", metavar="FILE", help="Path to a sliced .3mf file")
    parser.add_argument(
        "profile",
        nargs="?",
        default=_DEFAULT_PROFILE,
        metavar="PROFILE",
        help=f"Pricing profile name (default: {_DEFAULT_PROFILE})",
    )
    parser.add_argument(
        "--list", dest="list_profiles", action="store_true",
        help="List available pricing profiles and exit",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.list_profiles:
        _list_profiles()
        return 0

    profile = get_profile(args.profile)
    if profile is None:
        print(f"Error: unknown profile '{args.profile}'. Use --list to see available profiles.")
        return 1

    path_input = args.path or input("Enter the path to a sliced .3mf file: ").strip()

    try:
        job = inspection_service.inspect(path_input)
    except PrintManagerError as exc:
        print(f"Error: {exc}")
        return 1

    breakdown = QuoteService(profile.config).calculate(job)
    print(build_quote_report(job, breakdown, profile_label=profile.label))
    return 0
