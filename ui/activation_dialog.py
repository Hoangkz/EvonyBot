"""
activation_dialog.py — asks for the activation code and the customer's details on first launch
(or when the license is no longer valid).
"""
import re

from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout,
)

from .workers import LicenseWorker

_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_ERROR_STYLE = "color: #d32f2f;"   # red text for error messages


class ActivationDialog(QDialog):
    """Accepted once the code is activated; rejected (closed) means the app must exit."""

    def __init__(self, message: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Activate Evony Control App")
        self.setFixedWidth(460)
        self._worker: LicenseWorker | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter your activation code and your details:"))
        form = QFormLayout()
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self.name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit()
        form.addRow("Activation code *", self.code_edit)
        form.addRow("Full name *", self.name_edit)
        form.addRow("Email *", self.email_edit)
        form.addRow("Phone number *", self.phone_edit)
        form.addRow("Address", self.address_edit)
        for edit in (self.code_edit, self.name_edit, self.email_edit, self.phone_edit, self.address_edit):
            edit.returnPressed.connect(self._activate)
        layout.addLayout(form)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self._show(message, error=True)   # a message passed in explains why the code is asked for again
        layout.addWidget(self.status)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.activate_button = QPushButton("Activate")
        self.activate_button.setDefault(True)
        self.activate_button.clicked.connect(self._activate)
        buttons.addWidget(self.activate_button)
        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.reject)
        buttons.addWidget(quit_button)
        layout.addLayout(buttons)

    def _show(self, text: str, error: bool = False):
        """Status line under the form: red for errors, normal for progress."""
        self.status.setStyleSheet(_ERROR_STYLE if error else "")
        self.status.setText(text)

    def _activate(self):
        if self._worker is not None:
            return
        code = self.code_edit.text().strip()
        customer = {
            "full_name": self.name_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "address": self.address_edit.text().strip(),
        }
        if not code or not customer["full_name"] or not customer["phone"]:
            self._show("Please fill in the activation code, full name and phone number.", error=True)
            return
        if not _EMAIL.match(customer["email"]):
            self._show("Please enter a valid email.", error=True)
            return
        self.activate_button.setEnabled(False)
        self._show("Activating...")
        self._worker = LicenseWorker("activate", code, customer, self)
        self._worker.done.connect(self.accept)
        self._worker.refused.connect(self._failed)
        self._worker.offline.connect(lambda m: self._failed(f"Cannot reach the license server: {m}"))
        self._worker.start()

    def _failed(self, message: str):
        self._worker = None
        self._show(message, error=True)
        self.activate_button.setEnabled(True)

    def done(self, result):
        # Don't destroy the dialog while the worker thread still runs.
        if self._worker is not None:
            self._worker.wait()
        super().done(result)
