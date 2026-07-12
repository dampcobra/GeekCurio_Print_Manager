"""M5.3 quote history browser widget."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from geekcurio_print_manager.exporters.pdf_quote_export import build_pdf_quote
from geekcurio_print_manager.models.saved_quote import SavedQuote
from geekcurio_print_manager.services.quote_repository import QuoteRepository
from geekcurio_print_manager.utils.formatting import (
    display_project_name,
    format_duration_hm,
    format_weight,
)

_COLUMNS = ("Ref", "Issued", "Customer", "Project", "Total")
_N_RECENT = 20


def _project_display(q: SavedQuote) -> str:
    if q.project_name and q.project_name.strip():
        return q.project_name.strip()
    return display_project_name(q.source_file)


def _fmt_issued(iso_ts: str) -> str:
    from datetime import datetime, timezone
    dt = datetime.strptime(iso_ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return f"{dt.day} {dt.strftime('%b %Y')}"


class QuoteHistoryWidget(QWidget):
    def __init__(self, repo: QuoteRepository) -> None:
        super().__init__()
        self._repo = repo
        self._quotes: list[SavedQuote] = []
        self._selected: SavedQuote | None = None
        self._last_pdf_path: Path | None = None
        self._build_ui()

    def refresh(self) -> None:
        self._quotes = self._repo.list_recent(_N_RECENT)
        self._populate_table()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ── Table ─────────────────────────────────────────────────────────────
        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        root.addWidget(self._table)

        self._empty_label = QLabel("No saved quotes yet.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setVisible(False)
        root.addWidget(self._empty_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(sep)

        # ── Detail area ───────────────────────────────────────────────────────
        detail = QFormLayout()
        detail.setSpacing(6)

        self._d_ref      = QLabel("—")
        self._d_customer = QLabel("—")
        self._d_project  = QLabel("—")
        self._d_total    = QLabel("—")
        self._d_time     = QLabel("—")
        self._d_filament = QLabel("—")
        self._d_plates   = QLabel("—")

        detail.addRow("Quote Ref:",  self._d_ref)
        detail.addRow("Customer:",   self._d_customer)
        detail.addRow("Project:",    self._d_project)
        detail.addRow("Total:",      self._d_total)
        detail.addRow("Print Time:", self._d_time)
        detail.addRow("Filament:",   self._d_filament)
        detail.addRow("Plates:",     self._d_plates)

        root.addLayout(detail)

        self._pdf_btn = QPushButton("Generate PDF")
        self._pdf_btn.setEnabled(False)
        self._pdf_btn.clicked.connect(self._generate_pdf)
        root.addWidget(self._pdf_btn)

        self._open_pdf_btn = QPushButton("Open PDF")
        self._open_pdf_btn.setEnabled(False)
        self._open_pdf_btn.clicked.connect(self._open_pdf)
        root.addWidget(self._open_pdf_btn)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        root.addWidget(self._status_label)

    def _populate_table(self) -> None:
        self._table.setRowCount(0)
        self._selected = None
        self._last_pdf_path = None
        self._pdf_btn.setEnabled(False)
        self._open_pdf_btn.setEnabled(False)
        self._status_label.setText("")

        if not self._quotes:
            self._table.setVisible(False)
            self._empty_label.setVisible(True)
            return

        self._table.setVisible(True)
        self._empty_label.setVisible(False)

        for row, q in enumerate(self._quotes):
            self._table.insertRow(row)

            ref_item = QTableWidgetItem(q.quote_ref)
            ref_item.setData(Qt.ItemDataRole.UserRole, q.quote_ref)
            self._table.setItem(row, 0, ref_item)
            self._table.setItem(row, 1, QTableWidgetItem(_fmt_issued(q.created_at)))
            self._table.setItem(row, 2, QTableWidgetItem(q.customer_name or "—"))
            self._table.setItem(row, 3, QTableWidgetItem(_project_display(q)))

            total_item = QTableWidgetItem(f"\xa3{q.breakdown.total:.2f}")
            total_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self._table.setItem(row, 4, total_item)

    def _on_selection_changed(self) -> None:
        row = self._table.currentRow()
        if row < 0 or row >= len(self._quotes):
            self._selected = None
            self._pdf_btn.setEnabled(False)
            return

        quote_ref = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self._selected = next(
            (q for q in self._quotes if q.quote_ref == quote_ref), None
        )
        if self._selected is None:
            self._pdf_btn.setEnabled(False)
            self._open_pdf_btn.setEnabled(False)
            return

        self._last_pdf_path = None
        self._open_pdf_btn.setEnabled(False)

        q = self._selected
        total_s = sum(p.print_time_s for p in q.plates)
        total_g = sum(p.weight_g for p in q.plates)

        self._d_ref.setText(q.quote_ref)
        self._d_customer.setText(q.customer_name or "—")
        self._d_project.setText(_project_display(q))
        self._d_total.setText(f"\xa3{q.breakdown.total:.2f}")
        self._d_time.setText(format_duration_hm(total_s))
        self._d_filament.setText(format_weight(total_g))
        self._d_plates.setText(str(len(q.plates)))
        self._status_label.setText("")
        self._status_label.setStyleSheet("")
        self._pdf_btn.setEnabled(True)

    def _generate_pdf(self) -> None:
        if self._selected is None:
            return

        default_path = str(Path.cwd() / f"{self._selected.quote_ref}.pdf")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Quote",
            default_path,
            "PDF Files (*.pdf)",
        )
        if not path:
            return

        self._status_label.setText("")
        self._status_label.setStyleSheet("")
        try:
            build_pdf_quote(self._selected, Path(path))
        except Exception as exc:
            self._status_label.setText(f"PDF export failed: {exc}")
            self._status_label.setStyleSheet("color: red;")
            return

        self._last_pdf_path = Path(path)
        self._open_pdf_btn.setEnabled(True)
        self._status_label.setText(f"PDF saved: {Path(path).name}")
        self._status_label.setStyleSheet("color: green;")

    def _open_pdf(self) -> None:
        if self._last_pdf_path is None:
            return
        if not self._last_pdf_path.exists():
            self._status_label.setText("PDF file not found. It may have been moved or deleted.")
            self._status_label.setStyleSheet("color: red;")
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_pdf_path))):
            self._status_label.setText("Could not open PDF. Please open it manually.")
            self._status_label.setStyleSheet("color: red;")
