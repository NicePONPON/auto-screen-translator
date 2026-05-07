from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QCursor


class ScreenCaptureWindow(QWidget):
    """Full-screen transparent mask for rubber-band region selection.

    Emits region_selected(x, y, w, h) in logical screen coordinates on
    mouse release, or cancelled() on Escape.  Closes itself in both cases.
    """

    region_selected = pyqtSignal(int, int, int, int)
    cancelled       = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # Cover the entire virtual desktop (all monitors combined)
        vg = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(vg)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        self.setMouseTracking(True)

        self._origin  = QPoint()
        self._current = QPoint()
        self._active  = False   # True while left mouse button is held

    # ------------------------------------------------------------------ events

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self.close()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin  = event.position().toPoint()
            self._current = event.position().toPoint()
            self._active  = True
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._active:
            self._current = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._active:
            self._active = False
            rect = QRect(self._origin, event.position().toPoint()).normalized()
            if rect.width() >= 10 and rect.height() >= 10:
                global_tl = self.mapToGlobal(rect.topLeft())
                self.region_selected.emit(
                    global_tl.x(), global_tl.y(), rect.width(), rect.height()
                )
            self.close()

    # ------------------------------------------------------------------ paint

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        full = self.rect()

        if not self._active:
            # No selection started yet — dim the whole screen
            painter.fillRect(full, QColor(0, 0, 0, 80))
        else:
            sel = QRect(self._origin, self._current).normalized()

            painter.setBrush(QColor(0, 0, 0, 80))
            painter.setPen(Qt.PenStyle.NoPen)

            # Dim the four regions surrounding the selection (spotlight effect)
            painter.drawRect(
                full.left(), full.top(),
                full.width(), sel.top() - full.top()
            )
            painter.drawRect(
                full.left(), sel.bottom() + 1,
                full.width(), full.bottom() - sel.bottom()
            )
            painter.drawRect(
                full.left(), sel.top(),
                sel.left() - full.left(), sel.height()
            )
            painter.drawRect(
                sel.right() + 1, sel.top(),
                full.right() - sel.right(), sel.height()
            )

            # Selection border
            pen = QPen(QColor(255, 255, 255, 220), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(sel)

        painter.end()
