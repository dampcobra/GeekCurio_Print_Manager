import argparse
from collections.abc import Sequence
from pathlib import Path

from geekcurio_print_manager.exporters.pdf_quote_export import build_pdf_quote
from geekcurio_print_manager.services.quote_repository import QuoteRepository


def run_pdf_quote(
    repository: QuoteRepository,
    argv: Sequence[str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        prog="geekcurio-quote-pdf",
        description="Generate a PDF quote from a saved quote reference.",
    )
    parser.add_argument(
        "quote_ref",
        metavar="REF",
        help="Quote reference (e.g. GCQ-2026-000001)",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="PATH",
        help="Output path for the PDF (default: REF.pdf in the current directory)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    saved = repository.get_by_ref(args.quote_ref)
    if saved is None:
        print(f"Error: quote {args.quote_ref} not found.")
        return 1

    if args.output:
        output_path = Path(args.output)
        if output_path.is_dir():
            output_path = output_path / f"{args.quote_ref}.pdf"
    else:
        output_path = Path.cwd() / f"{args.quote_ref}.pdf"

    build_pdf_quote(saved, output_path)
    print(f"PDF saved: {output_path}")
    return 0
