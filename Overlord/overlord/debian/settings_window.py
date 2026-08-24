import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QFrame,
    QScrollArea,
    QWidget,
    QMessageBox,
)

from ..config import (
    APP_VERSION,
    MAX_URLS,
    DEFAULT_URLS,
    GESTURE_TYPES,
    GESTURE_LABELS,
)
from ..pin_manager import PinManager

logger = logging.getLogger("overlord")

SETTINGS_STYLE = """
    QDialog {
        background-color: #2b2b2b;
    }
    QLabel {
        color: #ddd;
        font-size: 14px;
    }
    QLineEdit {
        background-color: #3a3a3a;
        color: white;
        border: 1px solid #555;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 14px;
        min-height: 32px;
    }
    QLineEdit:focus {
        border: 1px solid #4a90d9;
    }
    QComboBox {
        background-color: #3a3a3a;
        color: white;
        border: 1px solid #555;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 14px;
        min-height: 32px;
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox QAbstractItemView {
        background-color: #3a3a3a;
        color: white;
        selection-background-color: #4a90d9;
    }
"""

SECTION_STYLE = """
    QFrame {
        background-color: #333;
        border-radius: 10px;
        border: 1px solid #444;
    }
"""

BUTTON_STYLE = """
    QPushButton {
        background-color: #4a90d9;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
        padding: 10px 20px;
        min-height: 38px;
    }
    QPushButton:hover {
        background-color: #5aa0e9;
    }
    QPushButton:pressed {
        background-color: #3a80c9;
    }
"""

DANGER_BUTTON_STYLE = """
    QPushButton {
        background-color: #e74c3c;
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 12px;
        padding: 6px 12px;
        min-height: 28px;
    }
    QPushButton:hover {
        background-color: #f05a4a;
    }
"""

SECTION_TITLE_STYLE = "color: #4a90d9; font-size: 16px; font-weight: bold;"


class SettingsWindow(QDialog):

    settings_applied = pyqtSignal()
    update_requested = pyqtSignal()

    def __init__(self, pin_manager: PinManager, update_info=None, parent=None):
        super().__init__(parent)
        self._pin_manager = pin_manager
        self._update_info = update_info
        self._url_entries: list[QLineEdit] = []
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Overlord Settings")
        self.setMinimumSize(480, 600)
        self.setStyleSheet(SETTINGS_STYLE)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        title = QLabel("Overlord Settings")
        title.setStyleSheet("color: #4a90d9; font-size: 22px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        main_layout.addWidget(self._create_pin_section())
        main_layout.addWidget(self._create_url_section())
        main_layout.addWidget(self._create_gesture_section())
        main_layout.addWidget(self._create_update_section())
        main_layout.addStretch(1)

        main_layout.addWidget(self._create_action_buttons())

        scroll.setWidget(container)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

    def _create_section_frame(self, title_text: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setStyleSheet(SECTION_STYLE)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel(title_text)
        title.setStyleSheet(SECTION_TITLE_STYLE)
        layout.addWidget(title)

        return frame, layout

    def _create_pin_section(self):
        frame, layout = self._create_section_frame("PIN Management")

        for pin_name, attr_name in [
            ("Exit PIN", "get_exit_pin"),
            ("Device Settings PIN", "get_settings_pin"),
            ("Kiosk Settings PIN", "get_kiosk_settings_pin"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(pin_name + ":")
            lbl.setMinimumWidth(180)

            current_field = QLineEdit()
            current_field.setPlaceholderText("Current PIN")
            row.addWidget(lbl)
            row.addWidget(current_field)

            new_field = QLineEdit()
            new_field.setPlaceholderText("New 4-digit PIN")
            new_field.setMaxLength(4)
            row.addWidget(new_field)

            confirm_field = QLineEdit()
            confirm_field.setPlaceholderText("Confirm")
            confirm_field.setMaxLength(4)
            row.addWidget(confirm_field)

            save_btn = QPushButton("Save")
            save_btn.setStyleSheet(DANGER_BUTTON_STYLE)
            current_pin = getattr(self._pin_manager, attr_name)()
            save_btn.clicked.connect(
                lambda checked, pn=pin_name, cf=current_field, nf=new_field,
                cfm=confirm_field, cp=current_pin: self._save_pin(
                    pn, cf, nf, cfm, cp
                )
            )
            row.addWidget(save_btn)
            layout.addLayout(row)

        return frame

    def _save_pin(self, pin_name, current_field, new_field, confirm_field, current_pin):
        current = current_field.text().strip()
        new_pin = new_field.text().strip()
        confirm = confirm_field.text().strip()

        if current != current_pin:
            QMessageBox.warning(self, "Error", f"Current {pin_name} is incorrect.")
            return
        if len(new_pin) != 4 or not new_pin.isdigit():
            QMessageBox.warning(self, "Error", "PIN must be exactly 4 digits.")
            return
        if new_pin != confirm:
            QMessageBox.warning(self, "Error", "New PINs do not match.")
            return

        if pin_name == "Exit PIN":
            self._pin_manager.save_exit_pin(new_pin)
        elif pin_name == "Device Settings PIN":
            self._pin_manager.save_settings_pin(new_pin)
        elif pin_name == "Kiosk Settings PIN":
            self._pin_manager.save_kiosk_settings_pin(new_pin)

        QMessageBox.information(self, "Success", f"{pin_name} updated.")
        current_field.clear()
        new_field.clear()
        confirm_field.clear()

    def _create_url_section(self):
        frame, layout = self._create_section_frame("URL Management")

        urls = self._pin_manager.get_urls()
        self._url_entries = []

        for i, url in enumerate(urls):
            layout.addLayout(self._create_url_row(i, url))

        add_btn = QPushButton("+ Add URL")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        add_btn.clicked.connect(self._add_url_row)
        add_btn_container = QHBoxLayout()
        add_btn_container.addStretch()
        add_btn_container.addWidget(add_btn)
        add_btn_container.addStretch()
        layout.addLayout(add_btn_container)

        return frame

    def _create_url_row(self, index: int, url: str) -> QHBoxLayout:
        row = QHBoxLayout()

        num_label = QLabel(f"{index + 1}.")
        num_label.setMinimumWidth(28)
        num_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(num_label)

        entry = QLineEdit(url)
        entry.setPlaceholderText("https://example.com")
        row.addWidget(entry)
        self._url_entries.append(entry)

        remove_btn = QPushButton("X")
        remove_btn.setFixedSize(28, 28)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #f05a4a; }
        """)
        remove_btn.clicked.connect(lambda checked, e=entry, n=num_label: self._remove_url(e, n))
        row.addWidget(remove_btn)

        return row

    def _add_url_row(self):
        if len(self._url_entries) >= MAX_URLS:
            QMessageBox.warning(self, "Limit", f"Maximum {MAX_URLS} URLs allowed.")
            return

        index = len(self._url_entries)
        row = self._create_url_row(index, "")
        frame = self.findChild(QFrame)
        if frame:
            frame.layout().insertLayout(
                frame.layout().count() - 1, row
            )

    def _remove_url(self, entry: QLineEdit, num_label: QLabel):
        parent_layout = entry.parent().layout()
        if parent_layout:
            row = None
            for i in range(parent_layout.count()):
                item = parent_layout.itemAt(i)
                widget = item.widget() if item else None
                if widget == entry:
                    row = parent_layout.takeAt(i)
                    break

        self._url_entries.remove(entry)
        entry.deleteLater()

        self._renumber_urls()

    def _renumber_urls(self):
        for i, entry in enumerate(self._url_entries):
            parent = entry.parent()
            if parent and parent.layout():
                for j in range(parent.layout().count()):
                    item = parent.layout().itemAt(j)
                    if item and item.widget():
                        w = item.widget()
                        if isinstance(w, QLabel) and w.text().endswith("."):
                            w.setText(f"{i + 1}.")
                            break

    def _create_gesture_section(self):
        frame, layout = self._create_section_frame("Gesture Type")

        combo = QComboBox()
        for gt in GESTURE_TYPES:
            combo.addItem(GESTURE_LABELS[gt], gt)

        current = self._pin_manager.get_gesture_type()
        idx = GESTURE_TYPES.index(current) if current in GESTURE_TYPES else 0
        combo.setCurrentIndex(idx)

        layout.addWidget(combo)
        self._gesture_combo = combo

        return frame

    def _create_update_section(self):
        frame, layout = self._create_section_frame("Application Update")

        info = self._update_info
        available = info is not None and info.available

        current_version = APP_VERSION
        latest_version = info.remote_version if info else "unknown"
        local_sha = info.short_local_sha() if info else "unknown"
        remote_sha = info.short_remote_sha() if info else "unknown"

        version_row = QHBoxLayout()
        version_row.setSpacing(8)

        current_lbl = QLabel(
            f"<b>Current:</b> {current_version} ({local_sha})"
        )
        current_lbl.setStyleSheet("color: #ddd; font-size: 13px;")
        version_row.addWidget(current_lbl)
        version_row.addStretch()

        latest_lbl = QLabel(
            f"<b>Latest:</b> {latest_version} ({remote_sha})"
        )
        latest_lbl.setStyleSheet("color: #ddd; font-size: 13px;")
        version_row.addWidget(latest_lbl)
        layout.addLayout(version_row)

        auto_toggle = QCheckBox("Auto-apply updates (no PIN prompt)")
        auto_toggle.setChecked(self._pin_manager.get_auto_update_enabled())
        auto_toggle.setStyleSheet("color: #ddd; font-size: 13px; spacing: 8px;")
        layout.addWidget(auto_toggle)
        self._auto_update_checkbox = auto_toggle

        status_lbl = QLabel()
        status_lbl.setStyleSheet("color: #888; font-size: 12px;")
        if available:
            status_lbl.setText("An update is available. Click below to install now.")
            status_lbl.setStyleSheet("color: #ffd966; font-size: 12px;")
        else:
            status_lbl.setText("Overlord is up to date.")
        layout.addWidget(status_lbl)

        update_btn = QPushButton("Update Overlord Now")
        update_btn.setStyleSheet(BUTTON_STYLE)
        update_btn.setEnabled(available)
        update_btn.clicked.connect(self._on_update_now)
        layout.addWidget(update_btn)

        return frame

    def _on_update_now(self):
        reply = QMessageBox.question(
            self,
            "Update Overlord",
            "Overlord will be updated and the kiosk will restart.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._save_auto_update_pref()
        self.update_requested.emit()
        self.accept()

    def _save_auto_update_pref(self):
        enabled = self._auto_update_checkbox.isChecked()
        self._pin_manager.save_auto_update_enabled(enabled)
        logger.info("Auto-update preference saved: %s", enabled)

    def _create_action_buttons(self):
        row = QHBoxLayout()
        row.setSpacing(12)

        save_btn = QPushButton("Save && Apply")
        save_btn.setStyleSheet(BUTTON_STYLE)
        save_btn.clicked.connect(self._save_and_apply)
        row.addStretch()
        row.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                padding: 10px 20px;
                min-height: 38px;
            }
            QPushButton:hover { background-color: #777; }
        """)
        cancel_btn.clicked.connect(self.reject)
        row.addWidget(cancel_btn)
        row.addStretch()

        container = QWidget()
        container.setLayout(row)
        return container

    def _save_and_apply(self):
        urls = []
        for entry in self._url_entries:
            url = entry.text().strip()
            if url:
                urls.append(url)

        if not urls:
            QMessageBox.warning(self, "Error", "At least one URL is required.")
            return

        self._pin_manager.save_urls(urls)
        gesture = self._gesture_combo.currentData()
        self._pin_manager.save_gesture_type(gesture)
        self._save_auto_update_pref()

        self.settings_applied.emit()
        self.accept()

        logger.info("Settings saved: %d URLs, gesture=%s", len(urls), gesture)
