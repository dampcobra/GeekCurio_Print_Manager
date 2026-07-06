"""Customer-facing PDF commission quotation generator.

Renders a SavedQuote as a GeekCurio Commission Quotation PDF.
Internal pricing mechanics (markup, overhead, rates) are never exposed.
All monetary values come from the saved record; no recalculation is performed.
"""
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path

from fpdf import FPDF

from geekcurio_print_manager.models.print_job import PlateSummary
from geekcurio_print_manager.models.quote import QuoteBreakdown
from geekcurio_print_manager.models.saved_quote import SavedQuote
from geekcurio_print_manager.utils.formatting import display_project_name, format_weight

# ── Page geometry ──────────────────────────────────────────────────────────────
_A4_W    = 210
_MARGIN  = 20
_USABLE  = _A4_W - 2 * _MARGIN  # 170 mm

# ── Table geometry ─────────────────────────────────────────────────────────────
_SUMMARY_LABEL = 70
_SUMMARY_VALUE = 100   # 70 + 100 = 170

# Plate table: Plate | Description | Qty | Time | Filament | Cost  (sum = 170)
_PLATE_COLS   = (12, 63, 12, 25, 26, 32)
_PLATE_ALIGNS = ("C", "L", "C", "L", "R", "R")
_PLATE_HEADS  = ("Plate", "Description", "Qty", "Time", "Filament", "Cost")

_ROW_H = 7   # standard table row height (mm)

# ── Colours ────────────────────────────────────────────────────────────────────
_C_BLACK    = (0,   0,   0)
_C_MUTED    = (110, 110, 110)
_C_TBL_HDR  = (240, 240, 240)

# ── Copy ───────────────────────────────────────────────────────────────────────
_TAGLINE = "Premium Tabletop Gaming Accessories, Designed and Printed in the UK."
_CLOSING = "Thank you for considering GeekCurio for your project."
_DEFAULT_NOTES = [
    "Printed using high quality filament.",
    "Support removal and visual inspection included where applicable.",
    "Pricing is calculated from slicer estimates for print time and material usage.",
    "Postage and packaging will be confirmed separately based on parcel size and value.",
]

_PENNY = Decimal("0.01")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _format_date(iso_ts: str) -> str:
    from datetime import datetime, timezone
    dt = datetime.strptime(iso_ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return f"{dt.day} {dt.strftime('%B %Y')}"   # "2 July 2026"


def _format_duration(seconds: int) -> str:
    h, rem = divmod(int(seconds), 3600)
    m = rem // 60
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m"


def _load_logo_bytes() -> bytes | None:
    try:
        from importlib.resources import files
        data = (
            files("geekcurio_print_manager")
            / "assets"
            / "branding"
            / "geekcurio-logo.png"
        ).read_bytes()
        return data or None
    except Exception:
        return None


def _allocate_plate_costs(
    plates: tuple[PlateSummary, ...],
    bd: QuoteBreakdown,
) -> list[Decimal]:
    """Split the saved total across plates for display purposes.

    Uses only values already in the saved record — no rates or profiles accessed.
    The last plate absorbs any rounding remainder so the sum equals bd.total exactly.
    """
    if not plates:
        return []
    if len(plates) == 1:
        return [bd.total]

    total_time_s   = sum(p.print_time_s for p in plates)
    total_weight_g = Decimal(str(sum(p.weight_g for p in plates)))

    base_sum = bd.print_time_cost + bd.material_cost
    if base_sum == Decimal("0"):
        return [Decimal("0.00")] * (len(plates) - 1) + [bd.total]

    scale        = bd.total / base_sum
    time_unit    = bd.print_time_cost / Decimal(total_time_s) if total_time_s else Decimal("0")
    material_unit = bd.material_cost / total_weight_g if total_weight_g else Decimal("0")

    costs: list[Decimal] = []
    for plate in plates[:-1]:
        plate_base = (
            time_unit * Decimal(plate.print_time_s)
            + material_unit * Decimal(str(plate.weight_g))
        )
        costs.append((plate_base * scale).quantize(_PENNY, ROUND_HALF_UP))

    costs.append(bd.total - sum(costs))
    return costs


# ── PDF class ──────────────────────────────────────────────────────────────────

class _QuotePDF(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*_C_MUTED)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")
        self.set_text_color(*_C_BLACK)


# ── Section builders ───────────────────────────────────────────────────────────

def _section_heading(pdf: _QuotePDF, title: str) -> None:
    pdf.ln(4)
    pdf.set_x(_MARGIN)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(_USABLE, 8, title, align="L")
    pdf.ln(10)


def _summary_table(
    pdf: _QuotePDF,
    plates: tuple[PlateSummary, ...],
    bd: QuoteBreakdown,
) -> None:
    total_time_s   = sum(p.print_time_s for p in plates)
    total_weight_g = sum(p.weight_g for p in plates)

    pdf.set_x(_MARGIN)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*_C_TBL_HDR)
    pdf.cell(_USABLE, _ROW_H, "Summary", border=1, fill=True, align="L")
    pdf.ln(_ROW_H)

    def _row(label: str, value: str) -> None:
        pdf.set_x(_MARGIN)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(_SUMMARY_LABEL, _ROW_H, label, border=1, align="L")
        pdf.cell(_SUMMARY_VALUE, _ROW_H, value, border=1, align="L")
        pdf.ln(_ROW_H)

    _row("Build Plates",             str(len(plates)))
    _row("Estimated Print Time",     _format_duration(total_time_s))
    _row("Estimated Filament",       f"Approximately {format_weight(total_weight_g)}")
    _row("Estimated Production Cost",
         f"\xa3{bd.total:.2f} (excluding postage)")
    _row("Postage & Packaging",
         "Fully tracked and insured service (carrier to be confirmed)")


def _plate_table(
    pdf: _QuotePDF,
    plates: tuple[PlateSummary, ...],
    plate_costs: list[Decimal],
) -> None:
    # Header row
    pdf.set_x(_MARGIN)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*_C_TBL_HDR)
    for head, w, align in zip(_PLATE_HEADS, _PLATE_COLS, _PLATE_ALIGNS):
        pdf.cell(w, _ROW_H, head, border=1, fill=True, align=align)
    pdf.ln(_ROW_H)

    # Data rows
    pdf.set_font("Helvetica", "", 9)
    for plate, cost in zip(plates, plate_costs):
        row_data = (
            str(plate.index),
            "Printed components",
            "1",
            _format_duration(plate.print_time_s),
            format_weight(plate.weight_g),
            f"\xa3{cost:.2f}",
        )
        pdf.set_x(_MARGIN)
        for val, w, align in zip(row_data, _PLATE_COLS, _PLATE_ALIGNS):
            pdf.cell(w, _ROW_H, val, border=1, align=align)
        pdf.ln(_ROW_H)


def _notes_section(pdf: _QuotePDF, saved_quote: SavedQuote) -> None:
    if saved_quote.notes:
        lines = [ln.strip() for ln in saved_quote.notes.splitlines() if ln.strip()]
    else:
        lines = _DEFAULT_NOTES

    pdf.set_font("Helvetica", "", 9)
    for line in lines:
        # Normalise any pre-existing bullet/dash prefix in saved notes
        clean = line.lstrip("- *").strip()
        pdf.set_x(_MARGIN)
        pdf.multi_cell(_USABLE, 5, f"- {clean}")


# ── Public API ─────────────────────────────────────────────────────────────────

def build_pdf_quote(saved_quote: SavedQuote, output_path: Path) -> None:
    """Write a customer-facing PDF commission quotation to output_path.

    All monetary values come from saved_quote — no recalculation is performed.
    Internal pricing mechanics (markup, overhead, rates) are not exposed.
    Parent directories are created if they do not exist.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bd       = saved_quote.breakdown
    plates   = saved_quote.plates
    src_stem = display_project_name(saved_quote.source_file)

    pdf = _QuotePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── Logo ─────────────────────────────────────────────────────────────────
    logo_bytes = _load_logo_bytes()
    if logo_bytes:
        pdf.image(BytesIO(logo_bytes), x=_A4_W - _MARGIN - 28, y=_MARGIN, w=28)

    # ── Title ────────────────────────────────────────────────────────────────
    pdf.set_xy(_MARGIN, _MARGIN)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(130, 10, "GeekCurio Commission Quotation", align="L")
    pdf.ln(12)

    # ── Metadata block ───────────────────────────────────────────────────────
    def _meta(label: str, value: str) -> None:
        pdf.set_x(_MARGIN)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(22, 5, label, align="L")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(120, 5, value, align="L")
        pdf.ln(5)

    _meta("Project:",   src_stem)
    _meta("Quote Ref:", saved_quote.quote_ref)
    _meta("Issued:",    _format_date(saved_quote.created_at))
    pdf.ln(6)

    # ── Tagline ──────────────────────────────────────────────────────────────
    pdf.set_x(_MARGIN)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*_C_MUTED)
    pdf.cell(_USABLE, 6, _TAGLINE, align="L")
    pdf.set_text_color(*_C_BLACK)
    pdf.ln(8)

    # ── Introduction paragraph ───────────────────────────────────────────────
    intro = (
        f"Thank you for asking GeekCurio to produce your {src_stem}. "
        "Following complete slicing and production planning, the project has been "
        "fully itemised below."
    )
    if len(plates) > 1:
        intro += (
            " The recommendation is to split production into multiple orders "
            "to keep lead times manageable and allow staged delivery."
        )
    pdf.set_x(_MARGIN)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(_USABLE, 5, intro)
    pdf.ln(6)

    # ── Summary table ────────────────────────────────────────────────────────
    _summary_table(pdf, plates, bd)
    pdf.ln(6)

    # ── Plate breakdown table ────────────────────────────────────────────────
    plate_costs = _allocate_plate_costs(plates, bd)
    _plate_table(pdf, plates, plate_costs)
    pdf.ln(6)

    # ── Recommendation (multi-plate only) ────────────────────────────────────
    if len(plates) > 1:
        _section_heading(pdf, "Recommendation")
        pdf.set_x(_MARGIN)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(
            _USABLE, 5,
            "Due to the overall print duration, GeekCurio recommends reviewing "
            "progress at each build plate before proceeding to the next. "
            "This allows each stage to be inspected, keeps lead times realistic, "
            "and reduces risk across the commission.",
        )
        pdf.ln(6)

    # ── Notes ────────────────────────────────────────────────────────────────
    _section_heading(pdf, "Notes")
    _notes_section(pdf, saved_quote)
    pdf.ln(8)

    # ── Closing line ─────────────────────────────────────────────────────────
    pdf.set_x(_MARGIN)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*_C_MUTED)
    pdf.cell(_USABLE, 6, _CLOSING, align="L")
    pdf.set_text_color(*_C_BLACK)

    pdf.output(str(output_path))
