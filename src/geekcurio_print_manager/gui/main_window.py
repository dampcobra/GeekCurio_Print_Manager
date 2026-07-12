"""M5.0 main window — quote generator."""
from __future__ import annotations

from pathlib import Path

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
    QVBoxLayout,
    QWidget,
)

from geekcurio_print_manager.db.database import open_connection
from geekcurio_print_manager.db.schema import initialise_database
from geekcurio_print_manager.exceptions import PrintManagerError
from geekcurio_print_manager.models.pricing_profile import BUILTIN_PROFILES
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

        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # ── Input form ────────────────────────────────────────────────────────
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

        # ── Result area ───────────────────────────────────────────────────────
        result_form = QFormLayout()
        result_form.setSpacing(6)

        self._ref_label = QLabel("—")
        self._total_label = QLabel("—")
        self._time_label = QLabel("—")
        self._filament_label = QLabel("—")
        self._plates_label = QLabel("—")

        result_form.addRow("Quote Ref:", self._ref_label)
        result_form.addRow("Total:", self._total_label)
        result_form.addRow("Print Time:", self._time_label)
        result_form.addRow("Filament:", self._filament_label)
        result_form.addRow("Plates:", self._plates_label)

        root.addLayout(result_form)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        root.addWidget(self._status_label)

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
        project = self._project_edit.text().strip() or None

        try:
            job = InspectionService().inspect(Path(path_str))
            breakdown = QuoteService(profile.config).calculate(job)
            saved = self._repo.save(
                job,
                breakdown,
                profile,
                customer_name=customer,
                project_name=project,
            )
        except PrintManagerError as exc:
            self._set_error(str(exc))
            return
        except Exception as exc:
            self._set_error(f"Unexpected error: {exc}")
            return

        total_s = sum(p.print_time_s for p in saved.plates)
        total_g = sum(p.weight_g for p in saved.plates)

        self._ref_label.setText(saved.quote_ref)
        self._total_label.setText(f"\xa3{saved.breakdown.total:.2f}")
        self._time_label.setText(format_duration_hm(total_s))
        self._filament_label.setText(format_weight(total_g))
        self._plates_label.setText(str(len(saved.plates)))
        self._status_label.setText("Quote saved successfully.")
        self._status_label.setStyleSheet("color: green;")

    def _clear_status(self) -> None:
        self._status_label.setText("")
        self._status_label.setStyleSheet("")

    def _set_error(self, message: str) -> None:
        self._status_label.setText(message)
        self._status_label.setStyleSheet("color: red;")
