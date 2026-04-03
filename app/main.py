"""
Dental Imaging System — fresh standalone UI.
Run:  python app/main.py
"""
import os
import sys

os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from runtime_paths import qml_root


def main():
    from PyQt6.QtGui import QGuiApplication
    from PyQt6.QtQml import QQmlApplicationEngine
    from PyQt6.QtCore import QUrl
    from bridge import DentalBridge
    from camera_service import CameraService
    from provider import FrameProvider
    from serial_service import SerialService

    app = QGuiApplication(sys.argv)
    app.setApplicationName("Dental Imaging System")

    engine = QQmlApplicationEngine()

    bridge = DentalBridge()
    provider = FrameProvider()
    camera_service = CameraService(bridge, provider)
    serial_service = SerialService(bridge)

    engine.addImageProvider("camera", provider)
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.rootContext().setContextProperty("cameraService", camera_service)
    bridge.powerClicked.connect(camera_service.toggle_connection)
    engine.load(QUrl.fromLocalFile(str(qml_root() / "main.qml")))

    if not engine.rootObjects():
        return 1

    # Kiosk default: full-screen to hide desktop chrome.
    try:
        root = engine.rootObjects()[0]
        root.showFullScreen()
    except Exception:
        pass

    camera_service.refresh_detection()
    camera_service.auto_connect_if_available()
    serial_service.start()
    app.aboutToQuit.connect(serial_service.stop)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
