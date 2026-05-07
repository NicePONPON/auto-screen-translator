import sys
import os
import traceback
import datetime

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

_LOG = os.path.join(_APP_DIR, "error.log")


def _log(msg: str) -> None:
    try:
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now():%H:%M:%S}] {msg}\n")
    except Exception:
        pass


try:
    import certifi
    os.environ["SSL_CERT_FILE"]      = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
    _log("certifi OK")
except ImportError as e:
    _log(f"certifi missing: {e}")

_plugin_path = os.path.join(
    _APP_DIR, "python", "Lib", "site-packages", "PyQt6", "Qt6", "plugins"
)
if os.path.isdir(_plugin_path):
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = _plugin_path
    _log(f"Qt plugin path: {_plugin_path}")
else:
    _log(f"WARNING: Qt plugin path not found: {_plugin_path}")

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        _log("DPI awareness OK")
    except Exception as e:
        _log(f"DPI awareness skipped: {e}")

try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import QTimer
    _log("PyQt6 OK")

    from settings import Settings
    from translation_panel import TranslationPanel
    from toolbar import ToolbarWindow
    _log("Modules OK")

    app = QApplication(sys.argv)
    app.setApplicationName("AutoScreenTranslator")
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    _log("QApplication OK")

    settings = Settings()
    panel    = TranslationPanel(settings)
    toolbar = ToolbarWindow(settings, panel)
    _log("Windows created OK")

    def _place_and_show() -> None:
        screen = QApplication.primaryScreen().availableGeometry()

        # toolbar
        toolbar.adjustSize()
        tw, th = toolbar.width(), toolbar.height()
        try:
            tx = int(settings.get("toolbar_x"))
            ty = int(settings.get("toolbar_y"))
            if not (screen.left() <= tx <= screen.right() - tw and
                    screen.top() <= ty <= screen.bottom() - th):
                raise ValueError
        except (TypeError, ValueError):
            tx = screen.center().x() - tw // 2
            ty = screen.top() + 20

        toolbar.move(tx, ty)
        toolbar.show()
        toolbar.raise_()
        _log(f"Toolbar at ({tx},{ty})")

        # panel
        pw = max(280, int(settings.get("panel_w") or 320))
        ph = max(200, int(settings.get("panel_h") or 500))
        try:
            px = int(settings.get("panel_x"))
            py = int(settings.get("panel_y"))
            if not (screen.left() <= px <= screen.right() - pw and
                    screen.top() <= py <= screen.bottom() - ph):
                raise ValueError
        except (TypeError, ValueError):
            px = min(tx + tw + 10, screen.right() - pw)
            py = ty

        panel.resize(pw, ph)
        panel.move(px, py)
        panel.show()
        panel.raise_()
        _log(f"Panel at ({px},{py}) size {pw}x{ph}")

    QTimer.singleShot(150, _place_and_show)
    _log("Entering event loop")
    sys.exit(app.exec())

except Exception:
    err = traceback.format_exc()
    _log(f"FATAL:\n{err}")
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        _a = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None, "Auto Screen Translator",
            f"Failed to start. See error.log in the app folder.\n\n{err[:500]}"
        )
    except Exception as e2:
        _log(f"Could not show error dialog: {e2}")
