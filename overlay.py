from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QApplication,
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QColor, QPainter, QPainterPath

from settings import Settings


class OverlayWindow(QWidget):
    """Semi-transparent floating window that shows OCR translation results.

    Call show_at_region() to position and reveal it with loading state.
    Call show_result() to update the displayed text in-place.
    The window is draggable and stays always on top.
    """

    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._drag_pos = QPoint()
        self._dragging = False
        self._setup_ui()
        self.hide()

    # ------------------------------------------------------------------ setup

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(220)
        self.setMaximumWidth(480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 14)
        layout.setSpacing(6)

        # ── header row ──────────────────────────────────────────────────────
        header = QHBoxLayout()

        self._status_label = QLabel("Translating…")
        self._status_label.setStyleSheet(
            "color: rgba(255,255,255,140); font-size: 11px;"
        )
        header.addWidget(self._status_label)
        header.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(
            "QPushButton {"
            "  background: rgba(255,255,255,40); color: white;"
            "  border: none; border-radius: 10px; font-size: 14px;"
            "}"
            "QPushButton:hover { background: rgba(220,60,60,200); }"
        )
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # ── body text ────────────────────────────────────────────────────────
        self._text_label = QLabel()
        self._text_label.setWordWrap(True)
        self._text_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        font = QFont()
        font.setPointSize(13)
        self._text_label.setFont(font)
        self._text_label.setStyleSheet("color: white;")
        layout.addWidget(self._text_label)

    # ------------------------------------------------------------------ paint

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        painter.fillPath(path, QColor(28, 28, 28, 215))
        painter.end()

    # ------------------------------------------------------------------ public API

    def show_at_region(self, rx: int, ry: int, rw: int, rh: int, side: str) -> None:
        """Set loading state, position adjacent to the captured region, then show."""
        self._status_label.setText("Translating…")
        self._text_label.setText("")
        self.setWindowOpacity(float(self._settings.get("overlay_opacity")))
        self.adjustSize()
        self._move_near(rx, ry, rw, rh, side)
        self.show()
        self.raise_()

    def show_result(self, text: str, success: bool) -> None:
        """Update displayed text after OCR/translation completes."""
        self._status_label.setText(
            "Translation" if success else "Translation unavailable — raw OCR:"
        )
        self._text_label.setText(text if text else "No text found")
        self.adjustSize()

    # ------------------------------------------------------------------ positioning

    def _move_near(self, rx: int, ry: int, rw: int, rh: int, side: str) -> None:
        """Position the overlay on the requested side of the capture region.

        If the preferred side has no room, the overlay is clamped to screen bounds.
        """
        ow = self.width()
        oh = self.height()
        gap = 10

        if side == "top":
            x = rx + rw // 2 - ow // 2
            y = ry - oh - gap
        elif side == "left":
            x = rx - ow - gap
            y = ry + rh // 2 - oh // 2
        elif side == "right":
            x = rx + rw + gap
            y = ry + rh // 2 - oh // 2
        else:  # "bottom" (default)
            x = rx + rw // 2 - ow // 2
            y = ry + rh + gap

        # Clamp to primary screen so the overlay is always reachable
        screen = QApplication.primaryScreen().geometry()
        x = max(screen.left() + 4, min(x, screen.right() - ow - 4))
        y = max(screen.top() + 4, min(y, screen.bottom() - oh - 4))
        self.move(x, y)

    # ------------------------------------------------------------------ drag

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            self._dragging = True

    def mouseMoveEvent(self, event) -> None:
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event) -> None:
        self._dragging = False
