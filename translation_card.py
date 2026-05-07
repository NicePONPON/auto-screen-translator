from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath


class TranslationCard(QWidget):
    """One captured region's result: grey original + white translation.

    Clicking anywhere on the card body copies the translation to clipboard.
    The x button dismisses only this card.
    """

    dismissed = pyqtSignal(object)  # emits self so panel can remove it

    def __init__(self, original: str, translation: str, parent=None) -> None:
        super().__init__(parent)
        self.translation = translation
        self._setup_ui(original, translation)

    def _setup_ui(self, original: str, translation: str) -> None:
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 10)
        layout.setSpacing(5)

        # header: original text + dismiss button
        header = QHBoxLayout()
        header.setSpacing(6)

        orig = QLabel(original)
        orig.setWordWrap(True)
        orig.setStyleSheet("color: rgba(255,255,255,130); font-size: 11px;")
        orig.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        header.addWidget(orig, 1)

        close_btn = QPushButton("x")
        close_btn.setFixedSize(18, 18)
        close_btn.setStyleSheet(
            "QPushButton {"
            "  background: rgba(255,255,255,25); color: rgba(255,255,255,160);"
            "  border: none; border-radius: 9px; font-size: 12px;"
            "}"
            "QPushButton:hover { background: rgba(220,60,60,200); color: white; }"
        )
        close_btn.clicked.connect(lambda: self.dismissed.emit(self))
        header.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        # translation text
        self._trans = QLabel(translation)
        self._trans.setWordWrap(True)
        self._trans.setStyleSheet("color: white; font-size: 14px;")
        self._trans.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self._trans)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            QApplication.clipboard().setText(self.translation)
            saved = self._trans.text()
            self._trans.setText("Copied!")
            self._trans.setStyleSheet("color: rgb(100,200,100); font-size: 14px;")
            QTimer.singleShot(900, lambda: (
                self._trans.setText(saved),
                self._trans.setStyleSheet("color: white; font-size: 14px;")
            ))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 8, 8)
        painter.fillPath(path, QColor(45, 45, 45))
        painter.end()
