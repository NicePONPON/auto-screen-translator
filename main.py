import sys
import os
import traceback
import datetime

# All errors are logged here because pythonw.exe has no console output
_APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Embedded Python does not add the script directory to sys.path automatically.
# Insert it so local modules (settings, toolbar, overlay, …) can be imported.
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)
_LOG     = os.path.join(_APP_DIR, "error.log")


def _log(msg: str) -> None:
    try:
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now():%H:%M:%S}] {msg}\n")
    except Exception:
        pass


# ── SSL certs ────────────────────────────────────────────────────────────────
try:
    import certifi
    os.environ["SSL_CERT_FILE"]      = certifi.where()
    os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
    _log("certifi OK")
except ImportError as e:
    _log(f"certifi missing: {e}")

# ── Qt platform plugin path ───────────────────────────────────────────────────
# Without this, PyQt6 on embedded Python silently fails to create any windows.
_plugin_path = os.path.join(
    _APP_DIR, "python", "Lib", "site-packages", "PyQt6", "Qt6", "plugins"
)
if os.path.isdir(_plugin_path):
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = _plugin_path
    _log(f"Qt plugin path: {_plugin_path}")
else:
    _log(f"WARNING: Qt plugin path not found at {_plugin_path}")

# ── DPI awareness ─────────────────────────────────────────────────────────────
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        _log("DPI awareness OK")
    except Exception as e:
        _log(f"DPI awareness skipped: {e}")

# ── Main ──────────────────────────────────────────────────────────────────────
try:
    _log("Importing PyQt6...")
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import QTimer
    _log("PyQt6 OK")

    from settings import Settings
    from overlay import OverlayWindow
    from toolbar import ToolbarWindow
    _log("App modules OK")

    def _place_and_show(toolbar: "ToolbarWindow", settings: "Settings") -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        toolbar.adjustSize()
        w, h = toolbar.width(), toolbar.height()
        _log(f"Screen={screen.width()}x{screen.height()} toolbar={w}x{h}")

        try:
            x = int(settings.get("toolbar_x"))
            y = int(settings.get("toolbar_y"))
            if not (screen.left() <= x <= screen.right() - w and
                    screen.top() <= y <= screen.bottom() - h):
                raise ValueError("saved position off-screen")
        except (TypeError, ValueError):
            x = screen.center().x() - w // 2
            y = screen.top() + 20

        _log(f"Placing toolbar at ({x}, {y})")
        toolbar.move(x, y)
        toolbar.show()
        toolbar.raise_()
        _log("Toolbar shown OK")

    app = QApplication(sys.argv)
    app.setApplicationName("AutoScreenTranslator")
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    _log("QApplication OK")

    settings = Settings()
    overlay  = OverlayWindow(settings)
    toolbar  = ToolbarWindow(settings, overlay)
    _log("Windows created OK")

    QTimer.singleShot(150, lambda: _place_and_show(toolbar, settings))
    _log("Entering event loop")
    sys.exit(app.exec())

except Exception:
    err = traceback.format_exc()
    _log(f"FATAL:\n{err}")
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        _a = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "Auto Screen Translator",
            f"Failed to start. See error.log in the app folder.\n\n{err[:400]}"
        )
    except Exception as e2:
        _log(f"Could not show error dialog: {e2}")
