from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout,
)
from PyQt6.QtCore import Qt


class ApiKeyDialog(QDialog):
    """First-launch dialog and settings dialog for the Gemini API key."""

    def __init__(self, current_key: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Gemini API Key")
        self.setMinimumWidth(420)
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Enter your Gemini API key:"))

        link = QLabel(
            'Get a free key at '
            '<a href="https://aistudio.google.com/apikey">'
            'aistudio.google.com/apikey</a> '
            '(free tier: 1,500 requests/day, no billing needed)'
        )
        link.setOpenExternalLinks(True)
        link.setWordWrap(True)
        layout.addWidget(link)

        self._input = QLineEdit()
        self._input.setEchoMode(QLineEdit.EchoMode.Password)
        self._input.setPlaceholderText("AIza...")
        self._input.setText(current_key)
        layout.addWidget(self._input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _on_save(self) -> None:
        if self._input.text().strip():
            self.accept()

    def key(self) -> str:
        return self._input.text().strip()
