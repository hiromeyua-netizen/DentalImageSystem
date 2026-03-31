"""
Serial service for ESP32 LED controller.

Protocol (115200 baud, newline-terminated):
  DIM:X
  ON
  OFF
  STATUS
"""
from __future__ import annotations

import time
from typing import Any, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSlot

try:
    import serial
    from serial.tools import list_ports

    _HAS_SERIAL = True
except Exception:  # pragma: no cover - environments without pyserial
    serial = None  # type: ignore[assignment]
    list_ports = None  # type: ignore[assignment]
    _HAS_SERIAL = False


class SerialService(QObject):
    """Auto-connects to ESP32 and mirrors bridge brightness to DIM:X."""

    def __init__(self, bridge: Any, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._bridge = bridge
        self._ser = None
        self._port_name = ""
        self._retry = QTimer(self)   # reconnect scheduler
        self._retry.setInterval(2500)
        self._retry.timeout.connect(self._ensure_connected)
        self._poll = QTimer(self)    # lightweight keepalive
        self._poll.setInterval(3000)
        self._poll.timeout.connect(self._poll_status)
        self._dim_flush = QTimer(self)  # throttle rapid slider changes
        self._dim_flush.setSingleShot(True)
        self._dim_flush.setInterval(40)
        self._dim_flush.timeout.connect(self._flush_pending_dim)

        self._last_dim_sent = -1
        self._pending_dim = -1
        self._has_announced_missing = False
        self._was_connected = False
        self._last_status_ok_t = 0.0

        self._bridge.brightnessChanged.connect(self._on_bridge_brightness_changed)
        self._bridge.ledsPresetAutoChanged.connect(self._on_leds_preset_changed)
        self._bridge.set_led_controller_state(False, "")

    def start(self) -> None:
        if not _HAS_SERIAL:
            if not self._has_announced_missing:
                self._bridge.toast("pyserial not available; LED controller disabled.")
                self._bridge.set_led_controller_status_text(
                    "LED controller unavailable: pyserial missing"
                )
                self._has_announced_missing = True
            return
        self._bridge.set_led_controller_status_text("LED controller: scanning serial ports...")
        self._ensure_connected()
        self._retry.start()
        self._poll.start()

    def stop(self) -> None:
        self._retry.stop()
        self._poll.stop()
        self._dim_flush.stop()
        self._close()

    def _close(self) -> None:
        was_connected = self._was_connected
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
        self._ser = None
        self._last_status_ok_t = 0.0
        self._last_dim_sent = -1
        self._port_name = ""
        self._was_connected = False
        self._bridge.set_led_controller_state(False, "")
        self._bridge.set_led_controller_status_text(
            "LED controller disconnected. Retrying..."
        )
        if was_connected:
            self._bridge.toast("LED controller disconnected.")

    def _ensure_connected(self) -> None:
        if self._ser is not None:
            try:
                if bool(getattr(self._ser, "is_open", False)):
                    return
            except Exception:
                pass
            self._close()

        port = self._find_esp32_port()
        if not port:
            self._bridge.set_led_controller_status_text(
                "LED controller not found. Check USB cable/power."
            )
            return
        self._open_port(port)

    def _find_esp32_port(self) -> str:
        if not _HAS_SERIAL or list_ports is None:
            return ""
        try:
            ports = list_ports.comports()
        except Exception:
            return ""

        ranked: list[tuple[int, str]] = []
        for p in ports:
            desc = f"{getattr(p, 'device', '')} {getattr(p, 'description', '')} {getattr(p, 'manufacturer', '')}".lower()
            vid = getattr(p, "vid", None)
            score = 0
            if vid == 0x303A:  # Espressif VID
                score += 6
            if "esp32" in desc:
                score += 5
            if "espressif" in desc:
                score += 4
            if "usb jtag" in desc:
                score += 3
            if "cp210" in desc or "ch340" in desc:
                score += 2
            if score > 0:
                ranked.append((score, p.device))

        if not ranked:
            return ""
        ranked.sort(key=lambda x: x[0], reverse=True)
        return ranked[0][1]

    def _open_port(self, port: str) -> None:
        if not _HAS_SERIAL or serial is None:
            return
        try:
            s = serial.Serial(port, 115200, timeout=0.10, write_timeout=0.15)
            # Give USB CDC a moment to settle.
            time.sleep(0.08)
            s.reset_input_buffer()
            s.reset_output_buffer()
            if not self._handshake_ok(s):
                self._bridge.set_led_controller_status_text(
                    f"LED controller on {port} did not respond to STATUS"
                )
                s.close()
                return
            self._ser = s
            self._port_name = port
            self._was_connected = True
            self._bridge.set_led_controller_state(True, port)
            self._bridge.toast(f"LED controller connected ({port})")
            # Sync LED output immediately based on preset mode.
            self._sync_led_output(force=True)
        except Exception:
            self._bridge.set_led_controller_status_text(
                f"LED controller open failed on {port}. Retrying..."
            )
            self._close()

    def _handshake_ok(self, s) -> bool:
        try:
            s.write(b"STATUS\n")
            deadline = time.monotonic() + 0.7
            while time.monotonic() < deadline:
                line = s.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                if line.startswith("STATUS:") or line.startswith("READY:ESP32_LED_CTRL"):
                    self._last_status_ok_t = time.monotonic()
                    return True
        except Exception:
            return False
        return False

    def _write_line(self, line: str) -> bool:
        if self._ser is None:
            return False
        try:
            self._ser.write((line + "\n").encode("utf-8"))
            return True
        except Exception:
            self._close()
            return False

    def _send_dim(self, pct: int, *, force: bool = False) -> None:
        pct = max(0, min(100, int(pct)))
        if not force and pct == self._last_dim_sent:
            return
        if self._write_line(f"DIM:{pct}"):
            self._last_dim_sent = pct

    def _sync_led_output(self, *, force: bool = False) -> None:
        # AUTO follows brightness slider. Manual preset enforces fixed 50%.
        if bool(self._bridge.ledsPresetAuto):
            target = int(self._bridge.brightness)
        else:
            target = 50
        self._pending_dim = target
        if self._ser is None:
            return
        self._send_dim(target, force=force)

    def _flush_pending_dim(self) -> None:
        if self._pending_dim < 0:
            return
        v = self._pending_dim
        self._pending_dim = -1
        self._send_dim(v)

    def _poll_status(self) -> None:
        if self._ser is None:
            return
        if not self._write_line("STATUS"):
            return
        try:
            deadline = time.monotonic() + 0.20
            while time.monotonic() < deadline:
                line = self._ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                if line.startswith("STATUS:"):
                    self._last_status_ok_t = time.monotonic()
                    self._bridge.set_led_controller_state(True, self._port_name)
                    return
            # Missed response once is acceptable; disconnect after longer silence.
            if self._last_status_ok_t > 0 and (time.monotonic() - self._last_status_ok_t) > 8.0:
                self._close()
        except Exception:
            self._close()

    @pyqtSlot(int)
    def _on_bridge_brightness_changed(self, v: int) -> None:
        if not bool(self._bridge.ledsPresetAuto):
            return
        self._pending_dim = max(0, min(100, int(v)))
        if self._ser is None:
            return
        self._dim_flush.start()

    @pyqtSlot(bool)
    def _on_leds_preset_changed(self, auto_on: bool) -> None:
        # Keep UI and output consistent when entering fixed 50% mode.
        if not bool(auto_on):
            try:
                if int(self._bridge.brightness) != 50:
                    self._bridge.set_brightness(50)
            except Exception:
                pass
        self._sync_led_output(force=True)

