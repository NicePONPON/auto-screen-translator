from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizeGrip,
)
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QColor, QPainter

from settings import Settings
from translation_card import TranslationCard


class _LoadingCard(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        lbl = QLabel("Translating...")
        lbl.setStyleSheet("color: rgba(255,255,255,130); font-size: 12px;")
        layout.addWidget(lbl)
        self.setStyleSheet(
            "_LoadingCard { background-color: rgb(40,40,40); border-radius: 8px; }"
        )


class TranslationPanel(QWidget):
    """Persistent scrollable panel that accumulates TranslationCards."""

    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self._settings      = settings
        self._loading_card: _LoadingCard | None = None
        self._drag_pos      = QPoint()
        self._dragging      = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setMinimumSize(280, 200)
        self.setStyleSheet("TranslationPanel { background-color: rgb(28,28,28); }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # header bar (drag handle)
        header = QWidget()
        header.setFixedHeight(36)
        header.setObjectName("header")
        header.setStyleSheet("#header { background-color: rgb(22,22,22); }")
        hrow = QHBoxLayout(header)
        hrow.setContentsMargins(10, 0, 8, 0)

        title = QLabel("Translations")
        title.setStyleSheet("color: rgba(255,255,255,150); font-size: 12px;")
        hrow.addWidget(title)
        hrow.addStretch()

        clear_btn = QPushButton("Clear all")
        clear_btn.setStyleSheet(
            "QPushButton { background: transparent; color: rgba(255,255,255,110);"
            " border: none; font-size: 11px; }"
            "QPushButton:hover { color: white; }"
        )
        clear_btn.clicked.connect(self.clear_all)
        hrow.addWidget(clear_btn)
        outer.addWidget(header)

        # scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollBar:vertical { width: 6px; background: rgb(35,35,35); }"
            "QScrollBar::handle:vertical {"
            "  background: rgb(75,75,75); border-radius: 3px; min-height: 20px;"
            "}"
        )

        self._cards_widget = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(8, 8, 8, 8)
        self._cards_layout.setSpacing(8)
        self._cards_layout.addStretch()

        self._scroll.setWidget(self._cards_widget)
        outer.addWidget(self._scroll, 1)

        # size grip
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 2, 2)
        grip_row.addStretch()
        grip_row.addWidget(QSizeGrip(self))
        outer.addLayout(grip_row)

    # public API

    def add_loading_card(self) -> None:
        self._remove_loading()
        self._loading_card = _LoadingCard()
        self._insert(self._loading_card)
        self._scroll_bottom()

    def add_card(self, original: str, translation: str) -> None:
        self._remove_loading()
        card = TranslationCard(original, translation)
        card.dismissed.connect(self._on_dismiss)
        self._insert(card)
        self._scroll_bottom()

    def add_error_card(self, error: str) -> None:
        self._remove_loading()
        card = TranslationCard("Error", f"Translation failed: {error}")
        card.dismissed.connect(self._on_dismiss)
        self._insert(card)

    def clear_all(self) -> None:
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._loading_card = None

    # internal helpers

    def _insert(self, widget: QWidget) -> None:
        self._cards_layout.insertWidget(self._cards_layout.count() - 1, widget)

    def _remove_loading(self) -> None:
        if self._loading_card:
            self._cards_layout.removeWidget(self._loading_card)
            self._loading_card.deleteLater()
            self._loading_card = None

    def _on_dismiss(self, card: TranslationCard) -> None:
        self._cards_layout.removeWidget(card)
        card.deleteLater()

    def _scroll_bottom(self) -> None:
        QTimer.singleShot(
            50,
            lambda: self._scroll.verticalScrollBar().setValue(
                self._scroll.verticalScrollBar().maximum()
            ),
        )

    # paint / drag / resize

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(28, 28, 28))
        painter.end()

    def mousePressEvent(self, event) -> None:
        if (event.button() == Qt.MouseButton.LeftButton
                and event.position().y() <= 36):
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            self._dragging = True

    def mouseMoveEvent(self, event) -> None:
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event) -> None:
        if self._dragging:
            self._dragging = False
            self._settings.set("panel_x", self.x())
            self._settings.set("panel_y", self.y())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._settings.set("panel_w", self.width())
        self._settings.set("panel_h", self.height())
