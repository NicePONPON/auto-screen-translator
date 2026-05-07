from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLabel, QPushButton,
    QApplication, QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QPainter

from settings import Settings
from translation_panel import TranslationPanel
from capture import ScreenCaptureWindow
from languages import FAVORITES, get_all_languages
from ocr_engine import OcrWorker
from translator_client import TranslatorWorker


# ──────────────────────────────────────────── Language search dialog

class LanguageSearchDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Language")
        self.setMinimumWidth(320)
        self.selected_code: str | None = None

        layout = QVBoxLayout(self)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Type to search...")
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._accept_item)
        layout.addWidget(self._list)

        self._langs: dict = {}
        self._populate()

    def _populate(self) -> None:
        self._langs = get_all_languages()
        self._list.clear()
        for name in sorted(self._langs.keys()):
            self._list.addItem(QListWidgetItem(name))

    def _filter(self, text: str) -> None:
        needle = text.lower()
        for i in range(self._list.count()):
            item = self._list.item(i)
            item.setHidden(needle not in item.text().lower())

    def _accept_item(self, item: QListWidgetItem) -> None:
        self.selected_code = self._langs.get(item.text())
        self.accept()


# ──────────────────────────────────────────── Hybrid combo box

class LangCombo(QComboBox):
    _OTHER = "Other..."

    def __init__(self, settings_key: str, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self._key      = settings_key
        self._settings = settings

        for name, code in FAVORITES:
            self.addItem(name, userData=code)
        self.addItem(self._OTHER, userData=None)

        self._restore(settings.get(settings_key))
        self.currentIndexChanged.connect(self._on_change)

    def _restore(self, code: str) -> None:
        for i, (_, c) in enumerate(FAVORITES):
            if c == code:
                self.setCurrentIndex(i)
                return

    def current_code(self) -> str:
        return self.currentData() or "en"

    def _on_change(self, _index: int) -> None:
        if self.currentText() != self._OTHER:
            self._settings.set(self._key, self.current_code())
            return
        dlg = LanguageSearchDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_code:
            code = dlg.selected_code
            all_langs = get_all_languages()
            name = next((n for n, c in all_langs.items() if c == code), code)
            insert_at = self.count() - 1
            self.insertItem(insert_at, name, userData=code)
            self.blockSignals(True)
            self.setCurrentIndex(insert_at)
            self.blockSignals(False)
            self._settings.set(self._key, code)
        else:
            self.blockSignals(True)
            self.setCurrentIndex(0)
            self.blockSignals(False)


# ──────────────────────────────────────────── Toolbar window

class ToolbarWindow(QWidget):
    def __init__(self, settings: Settings, panel: TranslationPanel) -> None:
        super().__init__()
        self._settings      = settings
        self._panel         = panel
        self._drag_pos      = QPoint()
        self._dragging      = False
        self._capture_win:  ScreenCaptureWindow | None = None
        self._ocr_worker:   OcrWorker           | None = None
        self._trans_worker: TranslatorWorker    | None = None
        self._pending_original: str = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedHeight(56)
        self.setStyleSheet("""
            ToolbarWindow { background-color: rgb(28,28,28); }
            QComboBox {
                background: rgb(50,50,50); color: white;
                border: 1px solid rgba(255,255,255,50);
                border-radius: 5px; padding: 3px 8px; font-size: 12px;
            }
            QComboBox::drop-down { border: none; width: 18px; }
            QComboBox QAbstractItemView {
                background: #2a2a2a; color: white;
                selection-background-color: #3a7bd5;
                border: 1px solid rgba(255,255,255,40);
            }
            QLabel { color: white; font-size: 14px; }
        """)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(8)

        self._src_combo = LangCombo("source_lang", self._settings, self)
        self._src_combo.setFixedWidth(148)
        row.addWidget(self._src_combo)

        row.addWidget(QLabel("->"))

        self._tgt_combo = LangCombo("target_lang", self._settings, self)
        self._tgt_combo.setFixedWidth(148)
        row.addWidget(self._tgt_combo)

        row.addSpacing(4)

        capture_btn = QPushButton("Capture")
        capture_btn.setFixedSize(70, 36)
        capture_btn.setStyleSheet(
            "QPushButton {"
            "  background: rgba(58,123,213,210); color: white;"
            "  border: none; border-radius: 6px; font-weight: bold; font-size: 13px;"
            "}"
            "QPushButton:hover   { background: rgba(58,123,213,255); }"
            "QPushButton:pressed { background: rgba(38,99,180,255); }"
        )
        capture_btn.clicked.connect(self._start_capture)
        row.addWidget(capture_btn)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(28, 28, 28))
        painter.end()

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
        if self._dragging:
            self._dragging = False
            self._settings.set("toolbar_x", self.x())
            self._settings.set("toolbar_y", self.y())

    def _start_capture(self) -> None:
        self._capture_win = ScreenCaptureWindow()
        self._capture_win.region_selected.connect(self._on_region)
        self._capture_win.show()

    def _on_region(self, x: int, y: int, w: int, h: int) -> None:
        for w_ in (self._ocr_worker, self._trans_worker):
            if w_:
                w_.blockSignals(True)

        self._panel.add_loading_card()
        self._panel.show()
        self._panel.raise_()

        from PIL import ImageGrab
        dpr   = QApplication.primaryScreen().devicePixelRatio()
        image = ImageGrab.grab(bbox=(
            int(x * dpr), int(y * dpr),
            int((x + w) * dpr), int((y + h) * dpr),
        ))

        self._ocr_worker = OcrWorker(image, self._src_combo.current_code())
        self._ocr_worker.ocr_done.connect(self._on_ocr_done)
        self._ocr_worker.ocr_failed.connect(
            lambda err: self._panel.add_error_card(f"OCR failed: {err}")
        )
        self._ocr_worker.start()

    def _on_ocr_done(self, text: str) -> None:
        if not text:
            self._panel.add_error_card("No text detected")
            return
        self._pending_original = text
        self._trans_worker = TranslatorWorker(
            text,
            self._src_combo.current_code(),
            self._tgt_combo.current_code(),
        )
        self._trans_worker.translation_ready.connect(self._on_translation)
        self._trans_worker.start()

    def _on_translation(self, translation: str, success: bool) -> None:
        self._panel.add_card(self._pending_original, translation)
