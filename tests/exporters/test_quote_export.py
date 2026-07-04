from pathlib import Path

from geekcurio_print_manager.exporters.quote_export import build_quote_report
from geekcurio_print_manager.models.print_job import PlateSummary, PrintJob
from geekcurio_print_manager.models.quote import QuoteBreakdown


def _job() -> PrintJob:
    return PrintJob(
        source_path=Path("my-test.3mf"),
        slicer="test",
        plates=(PlateSummary(index=1, print_time_s=3600, weight_g=100.0),),
    )


def _breakdown(**overrides) -> QuoteBreakdown:
    defaults = dict(
        print_time_hours=1.0,
        print_time_cost=3.0,
        material_weight_g=100.0,
        material_cost=3.0,
        overhead_multiplier=1.0,
        markup_percentage=0.0,
        subtotal=6.0,
        markup_amount=0.0,
        total=6.0,
    )
    defaults.update(overrides)
    return QuoteBreakdown(**defaults)


def test_report_contains_filename():
    report = build_quote_report(_job(), _breakdown())
    assert "my-test.3mf" in report


def test_report_contains_total_amount():
    report = build_quote_report(_job(), _breakdown())
    assert "Total" in report
    assert "6.00" in report


def test_markup_lines_shown_when_markup_present():
    bd = _breakdown(subtotal=6.0, markup_percentage=10.0, markup_amount=0.6, total=6.6)
    report = build_quote_report(_job(), bd)
    assert "Subtotal" in report
    assert "Markup" in report
    assert "0.60" in report
    assert "6.60" in report


def test_markup_lines_absent_when_zero():
    report = build_quote_report(_job(), _breakdown())
    assert "Markup" not in report
    assert "Subtotal" not in report


def test_overhead_line_shown_when_applied():
    bd = _breakdown(overhead_multiplier=1.2, subtotal=7.2, total=7.2)
    report = build_quote_report(_job(), bd)
    assert "Overhead" in report


def test_overhead_line_absent_when_default():
    report = build_quote_report(_job(), _breakdown())
    assert "Overhead" not in report
