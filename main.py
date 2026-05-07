import sys
import os

try:
    import certifi
    os.environ['SSL_CERT_FILE']      = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
except ImportError:
    pass

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from settings import Settings
from overlay import OverlayWindow
from toolbar import ToolbarWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("AutoScreenTranslator")
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")

    settings = Settings()
    overlay  = OverlayWindow(settings)
    toolbar  = ToolbarWindow(settings, overlay)

    def _place_and_show():
        # Use availableGeometry so the taskbar is excluded from the usable area
        screen = QApplication.primaryScreen().availableGeometry()
        toolbar.adjustSize()
        w, h = toolbar.width(), toolbar.height()

        # Restore saved position; fall back to top-center if missing or off-screen
        sx = settings.get("toolbar_x")
        sy = settings.get("toolbar_y")
        try:
            x, y = int(sx), int(sy)
            on_screen = (screen.left() <= x <= screen.right() - w and
                         screen.top() <= y <= screen.bottom() - h)
            if not on_screen:
                raise ValueError
        except (TypeError, ValueError):
            x = screen.center().x() - w // 2
            y = screen.top() + 20

        toolbar.move(x, y)
        toolbar.show()
        toolbar.raise_()

    # Delay slightly so Qt finishes initialising screen info before we measure
    QTimer.singleShot(150, _place_and_show)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
