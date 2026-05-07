import sys

# SetProcessDpiAwareness(1) = System DPI Aware.
# Must be called before QApplication is constructed so Qt receives
# physical pixel coordinates and no Windows virtualization is applied.
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass  # Non-fatal: older Windows or awareness already set

from PyQt6.QtWidgets import QApplication

from settings import Settings
from overlay import OverlayWindow
from toolbar import ToolbarWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("OCRTranslator")
    # Keep process alive when both windows are hidden (e.g. overlay closed)
    app.setQuitOnLastWindowClosed(False)
    # Fusion looks clean on Windows across all DPI and theme settings
    app.setStyle("Fusion")

    settings = Settings()
    overlay  = OverlayWindow(settings)
    toolbar  = ToolbarWindow(settings, overlay)

    # Default position: horizontally centered, 20px from the top of the screen
    screen = QApplication.primaryScreen().geometry()
    toolbar.adjustSize()
    toolbar.move(
        screen.center().x() - toolbar.width() // 2,
        screen.top() + 20,
    )
    toolbar.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
