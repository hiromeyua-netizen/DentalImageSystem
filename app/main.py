"""
Dental Imaging System — fresh standalone UI.
Run:  python app/main.py
"""
import os, sys
from pathlib import Path

os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

ROOT = Path(__file__).parent


def main():
    from PyQt6.QtGui import QGuiApplication
    from PyQt6.QtQml import QQmlApplicationEngine
    from PyQt6.QtCore import QUrl
    from bridge import DentalBridge
    from provider import FrameProvider

    app = QGuiApplication(sys.argv)
    app.setApplicationName("Dental Imaging System")

    engine = QQmlApplicationEngine()

    bridge   = DentalBridge()
    provider = FrameProvider()

    engine.addImageProvider("camera", provider)
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(QUrl.fromLocalFile(str(ROOT / "qml" / "main.qml")))

    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
