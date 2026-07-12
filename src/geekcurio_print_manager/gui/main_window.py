"""M5.3 main window — tabbed quote generator and history browser."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from geekcurio_print_manager.db.database import open_connection
from geekcurio_print_manager.db.schema import initialise_database
from geekcurio_print_manager.exceptions import PrintManagerError
from geekcurio_print_manager.exporters.pdf_quote_export import build_pdf_quote
from geekcurio_print_manager.gui.history_widget import QuoteHistoryWidget
from geekcurio_print_manager.models.pricing_profile import BUILTIN_PROFILES
from geekcurio_print_manager.models.saved_quote import SavedQuote
from geekcurio_print_manager.services.inspection_service import InspectionService
from geekcurio_print_manager.services.quote_repository import QuoteRepository
from geekcurio_print_manager.services.quote_service import QuoteService
from geekcurio_print_manager.utils.formatting import format_duration_hm, format_weight


class QuoteGeneratorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GeekCurio Print Manager")
        self.setFixedWidth(540)

        conn = open_connection()
        initialise_database(conn)
        self._repo = QuoteRepository(conn)
        self._last_saved: SavedQuote | None = None
        self._last_pdf_path: Path | None = None

        self._build_ui()

    # ── Shell ──────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        tabs = QTabWidget()
        self.setCentralWidget(tabs)
        tabs.addTab(self._build_new_quote_tab(), "New Quote")
        self._history_widget = QuoteHistoryWidget(self._repo)
        tabs.addTab(self._history_widget, "Quote History")
        tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index: int) -> None:
        if index == 1:
            self._history_widget.refresh()

    # ── New Quote tab ──────────────────────────────────────────────────────────

    def _build_new_quote_tab(self) -> QWidget:
        widget = QWidget()
        root = QVBoxLayout(widget)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # Input form
        form = QFormLayout()
        form.setSpacing(8)

        file_row = QHBoxLayout()
        self._file_edit = QLineEdit()
        self._file_edit.setPlaceholderText("Select a .3mf project file…")
        self._file_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(self._file_edit, stretch=1)
        file_row.addWidget(browse_btn)
        form.addRow("Project File:", file_row)

        self._profile_combo = QComboBox()
        for p in BUILTIN_PROFILES:
            self._profile_combo.addItem(p.label, userData=p.name)
        form.addRow("Profile:", self._profile_combo)

        self._customer_edit = QLineEdit()
        self._customer_edit.setPlaceholderText("Optional")
        form.addRow("Customer:", self._customer_edit)

        self._project_edit = QLineEdit()
        self._project_edit.setPlaceholderText("Optional")
        form.addRow("Project Name:", self._project_edit)

        root.addLayout(form)

        self._generate_btn = QPushButton("Generate Quote")
        self._generate_btn.clicked.connect(self._generate_quote)
        root.addWidget(self._generate_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(sep)

        # Result area
        result_form = QFormLayout()
        result_form.setSpacing(6)

        self._ref_label      = QLabel("—")
        self._total_label    = QLabel("—")
        self._time_label     = QLabel("—")
        self._filament_label = QLabel("—")
        self._plates_label   = QLabel("—")

        result_form.addRow("Quote Ref:",   self._ref_label)
        result_form.addRow("Total:",       self._total_label)
        result_form.addRow("Print Time:",  self._time_label)
        result_form.addRow("Filament:",    self._filament_label)
        result_form.addRow("Plates:",      self._plates_label)

        root.addLayout(result_form)

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

        # Reset displayed quote when any input changes
        self._file_edit.textChanged.connect(self._reset_quote_state)
        self._profile_combo.currentIndexChanged.connect(self._reset_quote_state)
        self._customer_edit.textChanged.connect(self._reset_quote_state)
        self._project_edit.textChanged.connect(self._reset_quote_state)

        return widget

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select 3MF Project File",
            "",
            "3MF Project Files (*.3mf)",
        )
        if path:
            self._file_edit.setText(path)
            self._clear_status()

    def _generate_quote(self) -> None:
        self._clear_status()

        path_str = self._file_edit.text().strip()
        if not path_str:
            self._set_error("Please select a .3mf project file first.")
            return

        profile_name = self._profile_combo.currentData()
        profile = next(p for p in BUILTIN_PROFILES if p.name == profile_name)
        customer = self._customer_edit.text().strip() or None
        project  = self._project_edit.text().strip() or None

        try:
            job       = InspectionService().inspect(Path(path_str))
            breakdown = QuoteService(profile.config).calculate(job)
            saved     = self._repo.save(
                job, breakdown, profile,
                customer_name=customer,
                project_name=project,
            )
        except PrintManagerError as exc:
            self._set_error(str(exc))
            return
        except Exception as exc:
            self._set_error(f"Unexpected error: {exc}")
            return

        self._last_saved = saved
        self._pdf_btn.setEnabled(True)

        total_s = sum(p.print_time_s for p in saved.plates)
        total_g = sum(p.weight_g for p in saved.plates)

        self._ref_label.setText(saved.quote_ref)
        self._total_label.setText(f"\xa3{saved.breakdown.total:.2f}")
        self._time_label.setText(format_duration_hm(total_s))
        self._filament_label.setText(format_weight(total_g))
        self._plates_label.setText(str(len(saved.plates)))
        self._status_label.setText("Quote saved successfully.")
        self._status_label.setStyleSheet("color: green;")

    def _generate_pdf(self) -> None:
        if self._last_saved is None:
            return

        default_path = str(Path.cwd() / f"{self._last_saved.quote_ref}.pdf")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Quote",
            default_path,
            "PDF Files (*.pdf)",
        )
        if not path:
            return

        self._clear_status()
        try:
            build_pdf_quote(self._last_saved, Path(path))
        except Exception as exc:
            self._set_error(f"PDF export failed: {exc}")
            return

        self._last_pdf_path = Path(path)
        self._open_pdf_btn.setEnabled(True)
        self._status_label.setText(f"PDF saved: {Path(path).name}")
        self._status_label.setStyleSheet("color: green;")

    def _open_pdf(self) -> None:
        if self._last_pdf_path is None:
            return
        if not self._last_pdf_path.exists():
            self._set_error("PDF file not found. It may have been moved or deleted.")
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_pdf_path))):
            self._set_error("Could not open PDF. Please open it manually.")

    def _reset_quote_state(self) -> None:
        self._last_saved = None
        self._last_pdf_path = None
        self._pdf_btn.setEnabled(False)
        self._open_pdf_btn.setEnabled(False)
        self._ref_label.setText("—")
        self._total_label.setText("—")
        self._time_label.setText("—")
        self._filament_label.setText("—")
        self._plates_label.setText("—")
        self._clear_status()

    def _clear_status(self) -> None:
        self._status_label.setText("")
        self._status_label.setStyleSheet("")

    def _set_error(self, message: str) -> None:
        self._status_label.setText(message)
        self._status_label.setStyleSheet("color: red;")
