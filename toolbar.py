from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLabel, QPushButton,
    QApplication, QDialog, QVBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem,
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QPainter, QPainterPath

from settings import Settings
from overlay import OverlayWindow
from capture import ScreenCaptureWindow
from translator import FAVORITES, get_all_languages, TranslatorWorker
from ocr_engine import OcrWorker


# ──────────────────────────────────────────────── Language search dialog

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


# ──────────────────────────────────────────────── Hybrid combo box

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


# ──────────────────────────────────────────────── Auto-position helper

def _best_side(rx: int, ry: int, rw: int, rh: int, ow: int, oh: int) -> str:
    """Pick the side of the capture region with the most available screen space."""
    screen = QApplication.primaryScreen().geometry()
    space = {
        "bottom": screen.bottom() - (ry + rh),
        "top":    ry - screen.top(),
        "right":  screen.right() - (rx + rw),
        "left":   rx - screen.left(),
    }
    return max(space, key=lambda k: space[k])


# ──────────────────────────────────────────────── Toolbar window

class ToolbarWindow(QWidget):
    def __init__(self, settings: Settings, overlay: OverlayWindow) -> None:
        super().__init__()
        self._settings     = settings
        self._overlay      = overlay
        self._drag_pos     = QPoint()
        self._dragging     = False
        self._capture_win: ScreenCaptureWindow | None = None
        self._ocr_worker:   OcrWorker         | None = None
        self._trans_worker: TranslatorWorker  | None = None

        self._setup_ui()

    # ------------------------------------------------------------------ setup

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(56)
        self.setStyleSheet("""
            QComboBox {
                background: rgba(55,55,55,210);
                color: white;
                border: 1px solid rgba(255,255,255,55);
                border-radius: 5px;
                padding: 3px 8px;
                font-size: 12px;
            }
            QComboBox::drop-down { border: none; width: 18px; }
            QComboBox QAbstractItemView {
                background: #2a2a2a;
                color: white;
                selection-background-color: #3a7bd5;
                border: 1px solid rgba(255,255,255,40);
            }
            QLabel { color: white; font-size: 15px; }
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

        row.addSpacing(6)

        capture_btn = QPushButton("Capture")
        capture_btn.setFixedSize(70, 36)
        capture_btn.setStyleSheet(
            "QPushButton {"
            "  background: rgba(58,123,213,210); color: white;"
            "  border: none; border-radius: 6px;"
            "  font-weight: bold; font-size: 13px;"
            "}"
            "QPushButton:hover   { background: rgba(58,123,213,255); }"
            "QPushButton:pressed { background: rgba(38,99,180,255); }"
        )
        capture_btn.clicked.connect(self._start_capture)
        row.addWidget(capture_btn)

    # ------------------------------------------------------------------ paint / drag

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        painter.fillPath(path, QColor(28, 28, 28, 222))
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
        self._dragging = False

    # ------------------------------------------------------------------ capture flow

    def _start_capture(self) -> None:
        self._capture_win = ScreenCaptureWindow()
        self._capture_win.region_selected.connect(self._on_region)
        self._capture_win.show()

    def _on_region(self, x: int, y: int, w: int, h: int) -> None:
        for worker in (self._ocr_worker, self._trans_worker):
            if worker is not None:
                worker.blockSignals(True)

        # Auto-pick the side with the most available screen space
        self._overlay.adjustSize()
        side = _best_side(x, y, w, h, self._overlay.width(), self._overlay.height())
        self._overlay.show_at_region(x, y, w, h, side)

        from PIL import ImageGrab
        dpr  = QApplication.primaryScreen().devicePixelRatio()
        bbox = (int(x * dpr), int(y * dpr), int((x + w) * dpr), int((y + h) * dpr))
        image = ImageGrab.grab(bbox=bbox)

        src = self._src_combo.current_code()
        tgt = self._tgt_combo.current_code()

        self._ocr_worker = OcrWorker(image, src)
        self._ocr_worker.ocr_done.connect(
            lambda text: self._on_ocr_done(text, tgt)
        )
        self._ocr_worker.ocr_failed.connect(
            lambda err: self._overlay.show_result(f"OCR error: {err}", False)
        )
        self._ocr_worker.start()

    def _on_ocr_done(self, text: str, tgt: str) -> None:
        if not text:
            self._overlay.show_result("No text found", True)
            return
        src = self._src_combo.current_code()
        self._trans_worker = TranslatorWorker(text, src, tgt)
        self._trans_worker.translation_ready.connect(self._overlay.show_result)
        self._trans_worker.start()
