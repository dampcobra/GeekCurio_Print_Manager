from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from fpdf import FPDF

from geekcurio_print_manager.models.saved_quote import SavedQuote
from geekcurio_print_manager.utils.formatting import format_weight

_A4_W = 210
_MARGIN = 20
_USABLE_W = _A4_W - 2 * _MARGIN

_LABEL_COL = 120  # mm — label column in the pricing section
_AMOUNT_COL = _USABLE_W - _LABEL_COL

_C_HEADER_BG = (35, 35, 35)
_C_HEADER_FG = (255, 255, 255)
_C_RULE = (180, 180, 180)
_C_MUTED = (110, 110, 110)
_C_BLACK = (0, 0, 0)

_HEADER_H = 22  # height of the dark header bar in mm


def _format_date(iso_ts: str) -> str:
    dt = datetime.strptime(iso_ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return dt.strftime("%d %B %Y")


def _format_duration(seconds: int) -> str:
    h, rem = divmod(int(seconds), 3600)
    m = rem // 60
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m"


class _QuotePDF(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*_C_MUTED)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")
        self.set_text_color(*_C_BLACK)


def build_pdf_quote(saved_quote: SavedQuote, output_path: Path) -> None:
    """Write a customer-facing PDF to output_path from a SavedQuote record.

    All monetary values come from saved_quote — no recalculation is performed.
    Parent directories are created if they do not exist.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bd = saved_quote.breakdown

    pdf = _QuotePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── Header bar ─────────────────────────────────────────────────────────────
    pdf.set_fill_color(*_C_HEADER_BG)
    pdf.rect(0, 0, _A4_W, _HEADER_H, style="F")
    pdf.set_xy(_MARGIN, 5)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*_C_HEADER_FG)
    pdf.cell(_USABLE_W, 12, "GeekCurio", align="L")
    pdf.set_text_color(*_C_BLACK)

    pdf.set_xy(_MARGIN, _HEADER_H + 6)

    # ── "PRICE QUOTE" subheading ────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(_USABLE_W, 8, "PRICE QUOTE", align="L")
    pdf.ln(10)

    # ── Metadata block ──────────────────────────────────────────────────────────
    def _meta(label: str, value: str) -> None:
        pdf.set_x(_MARGIN)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*_C_MUTED)
        pdf.cell(40, 6, label, align="L")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*_C_BLACK)
        pdf.cell(_USABLE_W - 40, 6, value, align="L")
        pdf.ln(6)

    _meta("Reference:", saved_quote.quote_ref)
    _meta("Date:", _format_date(saved_quote.created_at))
    _meta("Project:", saved_quote.source_file)
    _meta("Profile:", saved_quote.profile_label)
    pdf.ln(4)

    # ── Helpers ─────────────────────────────────────────────────────────────────
    def _rule(thick: bool = False) -> None:
        pdf.set_draw_color(*_C_RULE)
        pdf.set_line_width(0.6 if thick else 0.3)
        y = pdf.get_y()
        pdf.line(_MARGIN, y, _A4_W - _MARGIN, y)
        pdf.set_line_width(0.2)
        pdf.ln(4)

    def _price_row(label: str, amount: Decimal, bold: bool = False) -> None:
        style = "B" if bold else ""
        pdf.set_x(_MARGIN)
        pdf.set_font("Helvetica", style, 9)
        pdf.cell(_LABEL_COL, 7, label, align="L")
        pdf.cell(_AMOUNT_COL, 7, f"\xa3{amount:.2f}", align="R")
        pdf.ln(7)

    # ── Pricing breakdown ───────────────────────────────────────────────────────
    _rule()

    _price_row(
        f"Print time ({bd.print_time_hours:.2f} hrs)",
        bd.print_time_cost,
    )
    _price_row(
        f"Material ({format_weight(bd.material_weight_g)})",
        bd.material_cost,
    )

    if bd.overhead_multiplier != Decimal("1"):
        overhead = bd.subtotal - bd.print_time_cost - bd.material_cost
        _price_row(f"Overhead (x{bd.overhead_multiplier:.2f})", overhead)

    if bd.markup_amount > Decimal("0"):
        _rule()
        _price_row("Subtotal", bd.subtotal)
        _price_row(f"Markup ({bd.markup_percentage:.1f}%)", bd.markup_amount)

    _rule(thick=True)
    _price_row("Total", bd.total, bold=True)
    pdf.ln(4)

    # ── Plate breakdown ─────────────────────────────────────────────────────────
    if saved_quote.plates:
        _rule()
        pdf.set_x(_MARGIN)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(_USABLE_W, 6, "PLATE BREAKDOWN", align="L")
        pdf.ln(8)

        for plate in saved_quote.plates:
            types = ", ".join(
                {f.type for f in plate.filaments if f.type}
            ) if plate.filaments else ""

            pdf.set_x(_MARGIN)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(18, 6, f"Plate {plate.index}", align="L")
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(22, 6, _format_duration(plate.print_time_s), align="L")
            pdf.cell(22, 6, format_weight(plate.weight_g), align="L")
            if types:
                pdf.cell(_USABLE_W - 62, 6, types, align="L")
            pdf.ln(6)

        pdf.ln(2)

    # ── Notes ───────────────────────────────────────────────────────────────────
    if saved_quote.notes:
        _rule()
        pdf.set_x(_MARGIN)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(_USABLE_W, 6, "NOTES", align="L")
        pdf.ln(8)
        pdf.set_x(_MARGIN)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(_USABLE_W, 6, saved_quote.notes)

    pdf.output(str(output_path))
