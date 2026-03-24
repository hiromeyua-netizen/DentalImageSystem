"""
Main application window.
"""

from typing import Optional

import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStatusBar,
    QMessageBox,
    QSlider,
    QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices
from dental_imaging.ui.clinical_shell import ClinicalViewport
from dental_imaging.ui.clinical_settings_panel import ClinicalSettingsPanel
from dental_imaging.ui.widgets.preview_widget import PreviewWidget
from dental_imaging.hardware.camera import BaslerCamera
from dental_imaging.models.camera_config import CameraConfig
from dental_imaging.exceptions import (
    CameraNotFoundError,
    CameraConnectionError,
    CameraConfigurationError,
    CameraGrabError,
)
from dental_imaging.settings import (
    ApplicationSettings,
    load_app_settings,
    resolve_default_config_path,
    resolve_storage_directory,
)
from dental_imaging.storage.snapshot_writer import SnapshotWriter
from dental_imaging.hardware.camera.camera_settings_helper import print_camera_settings
from dental_imaging.hardware.camera.focus_helper import diagnose_blur_issues
from dental_imaging.ui.widgets.image_settings_component import ImageSettingsComponent


class MainWindow(QMainWindow):
    """
    Main application window for dental imaging system.
    """
    
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        app_settings: Optional[ApplicationSettings] = None,
    ):
        """
        Initialize main window.
        
        Args:
            parent: Parent widget
            app_settings: Loaded application config; if omitted, loads from the default path.
        """
        super().__init__(parent)

        self._app_settings = app_settings or load_app_settings(
            resolve_default_config_path()
        )
        storage_dir = resolve_storage_directory(self._app_settings)
        self._snapshot_writer = SnapshotWriter(
            storage_dir,
            self._app_settings.storage.default_format,
            jpeg_quality=94,
        )
        self._preview_width = self._app_settings.preview.width
        self._preview_height = self._app_settings.preview.height
        
        self.camera: Optional[BaslerCamera] = None
        self.camera_config: Optional[CameraConfig] = None
        self.preview_timer: Optional[QTimer] = None
        self.image_settings = ImageSettingsComponent()
        # After Reset, or while camera reports AE/AGC, we skip pushing manual slider values.
        self._camera_auto_exposure = True
        self._camera_auto_gain = True
        self._flip_h = False
        self._flip_v = False
        self._rotate_quarter_turns = 0  # 0–3 clockwise steps
        self._export_full_resolution = True
        self._burst_capture_mode = False
        self._burst_delay_sec = 10
        self._camera_sound_enabled = True
        self._storage_sd_selected = False
        self._show_preview_grid = False
        self._show_preview_crosshair = False
        self._preview_auto_scale = True

        self._hidden_tuning = QWidget()
        self.frame_rate_spinbox = QDoubleSpinBox(self._hidden_tuning)
        self.frame_rate_spinbox.setRange(1.0, 60.0)
        self.frame_rate_spinbox.setValue(30.0)
        self.frame_rate_spinbox.setSuffix(" fps")
        self.frame_rate_spinbox.setDecimals(1)
        self.frame_rate_spinbox.setSingleStep(1.0)
        self.gamma_slider = QSlider(Qt.Orientation.Horizontal, self._hidden_tuning)
        self.gamma_slider.setRange(50, 300)
        self.gamma_slider.setValue(100)
        self.gamma_spinbox = QDoubleSpinBox(self._hidden_tuning)
        self.gamma_spinbox.setRange(0.5, 3.0)
        self.gamma_spinbox.setValue(1.0)
        self.gamma_spinbox.setSingleStep(0.1)
        self.gamma_spinbox.setDecimals(2)

        self._setup_ui()
        self._setup_timers()
        
    def _setup_ui(self) -> None:
        """Kiosk-style layout: full-screen live view + top / right / bottom chrome."""
        self.setWindowTitle(f"{self._app_settings.application.name} — Camera")
        self.setMinimumSize(1280, 720)

        brand = self._app_settings.application.name.upper().replace(" ", "\n", 1)
        if "\n" not in brand:
            brand = self._app_settings.application.name.upper()

        self.preview_widget = PreviewWidget()
        self.image_settings.settings_changed.connect(
            self._on_image_settings_hardware_push
        )
        self.image_settings.defaults_restored.connect(
            self._on_image_settings_defaults_restored
        )
        self.image_settings.exposure_slider_user_changed.connect(
            self._on_exposure_slider_manual
        )
        self.image_settings.gain_slider_user_changed.connect(
            self._on_gain_slider_manual
        )

        self._settings_panel = ClinicalSettingsPanel(
            self._app_settings.application.name,
            f"v{self._app_settings.application.version}",
        )
        self._clinical = ClinicalViewport(
            self.preview_widget,
            self.image_settings,
            brand_title=brand,
            settings_panel=self._settings_panel,
        )
        self.setCentralWidget(self._clinical)

        self.frame_rate_spinbox.valueChanged.connect(self.on_frame_rate_changed)
        self.gamma_slider.valueChanged.connect(self.on_gamma_changed)
        self.gamma_spinbox.valueChanged.connect(self.on_gamma_spinbox_changed)

        rail = self._clinical.right_rail()
        self.image_settings.wire_toggle_button(rail.image_settings_button())
        rail.image_settings_button().toggled.connect(self._on_image_settings_toggled)
        rail.capture_clicked.connect(self.capture_image)
        rail.settings_toggled.connect(self._on_settings_toggled)
        self._clinical.top_bar().power_clicked.connect(self._on_power_clicked)

        self._wire_settings_panel()

        rail.flip_horizontal_clicked.connect(self._toggle_flip_h)
        rail.flip_vertical_clicked.connect(self._toggle_flip_v)
        rail.rotate_ccw_clicked.connect(self._rotate_ccw)
        rail.rotate_cw_clicked.connect(self._rotate_cw)
        rail.auto_color_clicked.connect(self._stub_auto_color)
        rail.recenter_roi_clicked.connect(self._stub_recenter_roi)
        rail.roi_mode_clicked.connect(self._stub_roi_mode)

        bb = self._clinical.bottom_bar()
        bb.brightness_changed.connect(lambda _v: self._refresh_preview_if_idle())
        bb.zoom_changed.connect(lambda _v: self._refresh_preview_if_idle())
        bb.preset_clicked.connect(self._on_preset_clicked)

        self._sync_top_chrome()

        self._updating_settings = False
        self.statusBar().showMessage("Ready")
        
    def _setup_timers(self) -> None:
        """Set up timers for preview updates."""
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        fps = max(1.0, float(self._app_settings.preview.fps))
        self.preview_timer.setInterval(max(1, int(round(1000.0 / fps))))

    def _wire_settings_panel(self) -> None:
        sp = self._settings_panel

        sp.close_requested.connect(self._close_settings_panel)
        sp.show_grid_changed.connect(self._on_show_grid_changed)
        sp.show_crosshair_changed.connect(self._on_show_crosshair_changed)
        sp.auto_scale_preview_changed.connect(self._on_auto_scale_preview_changed)
        sp.export_scope_changed.connect(self._on_export_scope_changed)
        sp.capture_format_changed.connect(self._on_capture_format_changed)
        sp.jpeg_quality_changed.connect(self._on_jpeg_quality_changed)
        sp.capture_mode_changed.connect(self._on_capture_mode_changed)
        sp.burst_delay_sec_changed.connect(self._on_burst_delay_changed)
        sp.camera_sound_changed.connect(self._on_camera_sound_changed)
        sp.storage_target_changed.connect(self._on_storage_target_changed)
        sp.sd_card_requested.connect(self._on_sd_card_stub)

    def _on_settings_toggled(self, open_: bool) -> None:
        rail = self._clinical.right_rail()
        if open_:
            # Avoid overlay stacking artifacts: Settings and Image Settings should not be open together.
            img_btn = rail.image_settings_button()
            if img_btn.isChecked():
                img_btn.setChecked(False)
            self.image_settings.hide()
            self._sync_settings_panel_from_state()
            self._settings_panel.show()
        else:
            self._settings_panel.hide()
            if rail.image_settings_button().isChecked():
                self.image_settings.show()
        self._clinical.layout_chrome()

    def _on_image_settings_toggled(self, open_: bool) -> None:
        """Keep Settings and Image Settings mutually exclusive."""
        if not open_:
            return
        settings_btn = self._clinical.right_rail().settings_tool_button()
        if settings_btn.isChecked():
            settings_btn.setChecked(False)
        self._settings_panel.hide()
        self._clinical.layout_chrome()

    def _close_settings_panel(self) -> None:
        self._settings_panel.hide()
        self._clinical.right_rail().settings_tool_button().setChecked(False)
        self._clinical.layout_chrome()

    def _sync_settings_panel_from_state(self) -> None:
        fmt = self._snapshot_writer.image_format
        self._settings_panel.sync_from_main_window(
            show_grid=self._show_preview_grid,
            show_crosshair=self._show_preview_crosshair,
            auto_scale=self._preview_auto_scale,
            export_full_resolution=self._export_full_resolution,
            image_format=fmt,
            jpeg_quality=self._snapshot_writer.jpeg_quality,
            capture_mode_burst=self._burst_capture_mode,
            burst_delay_sec=self._burst_delay_sec,
            camera_sound=self._camera_sound_enabled,
            storage_sd_selected=self._storage_sd_selected,
        )

    def _on_show_grid_changed(self, on: bool) -> None:
        self._show_preview_grid = on
        self.preview_widget.set_show_grid(on)
        self._redraw_preview_if_possible()

    def _on_show_crosshair_changed(self, on: bool) -> None:
        self._show_preview_crosshair = on
        self.preview_widget.set_show_crosshair(on)
        self._redraw_preview_if_possible()

    def _on_auto_scale_preview_changed(self, on: bool) -> None:
        self._preview_auto_scale = on
        self.preview_widget.set_auto_scale_preview(on)
        self._redraw_preview_if_possible()

    def _redraw_preview_if_possible(self) -> None:
        if self.preview_widget.current_frame is not None:
            self.preview_widget.display_frame(self.preview_widget.current_frame)

    def _on_export_scope_changed(self, scope: str) -> None:
        self._export_full_resolution = scope == "full"

    def _on_capture_format_changed(self, fmt: str) -> None:
        self._snapshot_writer.set_image_format(fmt)

    def _on_jpeg_quality_changed(self, quality: int) -> None:
        self._snapshot_writer.set_jpeg_quality(quality)

    def _on_capture_mode_changed(self, mode: str) -> None:
        self._burst_capture_mode = mode == "burst"

    def _on_burst_delay_changed(self, sec: int) -> None:
        self._burst_delay_sec = sec

    def _on_camera_sound_changed(self, on: bool) -> None:
        self._camera_sound_enabled = on

    def _on_storage_target_changed(self, target: str) -> None:
        self._storage_sd_selected = target == "sd"

    def _on_sd_card_stub(self) -> None:
        QMessageBox.information(
            self,
            "Storage",
            "SD card storage is not available on this system.",
        )
        self._storage_sd_selected = False
        self._sync_settings_panel_from_state()

    def _on_power_clicked(self) -> None:
        if self.camera is not None and self.camera.is_connected:
            self.stop_preview()
            try:
                self.camera.disconnect()
            except Exception:
                pass
            self.camera = None
            self._sync_top_chrome()
            self.statusBar().showMessage("Camera disconnected")
            return
        if self.camera_config:
            if self.initialize_camera(self.camera_config):
                self.start_preview()
            self._sync_top_chrome()
        else:
            QMessageBox.information(
                self,
                "Camera",
                "No camera configuration loaded.",
            )

    def _toggle_flip_h(self) -> None:
        self._flip_h = not self._flip_h

    def _toggle_flip_v(self) -> None:
        self._flip_v = not self._flip_v

    def _rotate_ccw(self) -> None:
        self._rotate_quarter_turns = (self._rotate_quarter_turns - 1) % 4

    def _rotate_cw(self) -> None:
        self._rotate_quarter_turns = (self._rotate_quarter_turns + 1) % 4

    def _stub_auto_color(self) -> None:
        QMessageBox.information(
            self,
            "Auto color balance",
            "This tool will be available in a future update.",
        )

    def _stub_recenter_roi(self) -> None:
        QMessageBox.information(
            self,
            "Recenter ROI",
            "This tool will be available in a future update.",
        )

    def _stub_roi_mode(self) -> None:
        QMessageBox.information(
            self,
            "ROI mode",
            "This tool will be available in a future update.",
        )

    def _on_preset_clicked(self, index: int) -> None:
        QMessageBox.information(
            self,
            "Presets",
            f"Preset {index + 1} will be configurable in a future update.",
        )

    def _refresh_preview_if_idle(self) -> None:
        pass

    def _sync_top_chrome(self) -> None:
        """Keep top status pill, power label, and capture button aligned with camera state."""
        c = self.camera
        connected = c is not None and c.is_connected
        grabbing = connected and c.is_grabbing
        self._clinical.top_bar().set_connected(connected)
        self._clinical.top_bar().set_power_primary_text(
            "Power Off" if connected else "Connect"
        )
        self._clinical.right_rail().set_capture_enabled(grabbing)

    @staticmethod
    def _zoom_crop(bgr: np.ndarray, pct: int) -> np.ndarray:
        if pct <= 2 or bgr is None or bgr.size == 0:
            return bgr
        fh, fw = bgr.shape[:2]
        t = pct / 100.0
        cw = max(32, int(fw * (1.0 - 0.7 * t)))
        ch = max(32, int(fh * (1.0 - 0.7 * t)))
        cw = min(cw, fw)
        ch = min(ch, fh)
        x0 = (fw - cw) // 2
        y0 = (fh - ch) // 2
        return bgr[y0 : y0 + ch, x0 : x0 + cw].copy()

    @staticmethod
    def _brightness_adjust(bgr: np.ndarray, pct: int) -> np.ndarray:
        if bgr is None or bgr.size == 0:
            return bgr
        alpha = max(0.2, min(1.8, 0.2 + 1.6 * (pct / 100.0)))
        beta = (pct - 50.0) * 2.0
        return cv2.convertScaleAbs(bgr, alpha=alpha, beta=beta)

    def _apply_view_transforms(self, bgr: np.ndarray) -> np.ndarray:
        if bgr is None or bgr.size == 0:
            return bgr
        z = self._clinical.bottom_bar().zoom_percent()
        br = self._clinical.bottom_bar().brightness_percent()
        out = self._zoom_crop(bgr, z)
        out = self._brightness_adjust(out, br)
        if self._flip_h:
            out = cv2.flip(out, 1)
        if self._flip_v:
            out = cv2.flip(out, 0)
        for _ in range(self._rotate_quarter_turns % 4):
            out = cv2.rotate(out, cv2.ROTATE_90_CLOCKWISE)
        return out

    def _update_stream_stats(self, frame_w: int, frame_h: int) -> None:
        interval_ms = max(1, self.preview_timer.interval())
        fps = 1000.0 / interval_ms
        mbps = (frame_w * frame_h * 3.0 * fps) / 1_000_000.0
        self._clinical.top_bar().set_stats_text(frame_w, frame_h, fps, mbps)

    def _on_image_settings_hardware_push(self) -> None:
        """Apply exposure/gain sliders when those channels are in manual mode."""
        if self._updating_settings or not self.camera or not self.camera.is_connected:
            return
        try:
            if not self._camera_auto_exposure:
                us = self.image_settings.exposure_time_microseconds()
                self.camera.set_exposure(us, auto=False)
                self.statusBar().showMessage(f"Exposure: {us / 1000:.1f} ms (manual)")
            if not self._camera_auto_gain:
                g = self.image_settings.analog_gain()
                self.camera.set_gain(g, auto=False)
                self.statusBar().showMessage(f"Gain: {g:.1f} (manual)")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Camera",
                f"Could not apply exposure or gain.\n\n{str(e)}",
            )

    def _on_image_settings_defaults_restored(self) -> None:
        """Match previous 'all Auto on': AE, AGC, AWB, neutral sliders."""
        self._camera_auto_exposure = True
        self._camera_auto_gain = True
        if not self.camera or not self.camera.is_connected:
            self.statusBar().showMessage("Image settings reset (connect camera to apply auto modes)")
            return
        try:
            self.camera.set_exposure(0, auto=True)
            self.camera.set_gain(0.0, auto=True)
            self.camera.set_white_balance(auto=True)
            self.statusBar().showMessage(
                "Image settings reset — auto exposure, gain, and white balance"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Camera",
                f"Could not restore automatic exposure, gain, or white balance.\n\n{str(e)}",
            )

    def _on_exposure_slider_manual(self) -> None:
        self._camera_auto_exposure = False

    def _on_gain_slider_manual(self) -> None:
        self._camera_auto_gain = False

    def initialize_camera(self, config: CameraConfig) -> bool:
        """
        Initialize camera with configuration.
        
        Args:
            config: Camera configuration
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.statusBar().showMessage("Connecting to camera...")
            
            # Create and connect camera
            self.camera = BaslerCamera()
            self.camera.connect()
            
            # Configure camera
            self.camera.configure(config)
            self.camera_config = config
            
            # Update UI controls with current settings
            self._update_settings_ui()
            
            # Print camera settings for diagnostics
            print_camera_settings(self.camera)
            
            self.statusBar().showMessage("Camera connected successfully")
            self._sync_top_chrome()

            return True
            
        except CameraNotFoundError as e:
            QMessageBox.critical(
                self,
                "Camera Not Found",
                f"No camera detected.\n\n{str(e)}\n\nPlease ensure:\n"
                "1. Camera is connected via USB\n"
                "2. Basler Pylon SDK is installed\n"
                "3. Camera drivers are installed"
            )
            self.statusBar().showMessage("Camera not found")
            return False
            
        except CameraConnectionError as e:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Failed to connect to camera.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Connection failed")
            return False

        except CameraConfigurationError as e:
            QMessageBox.critical(
                self,
                "Camera Configuration",
                f"The camera connected but settings could not be applied.\n\n{str(e)}\n\n"
                "Try adjusting resolution or exposure in config/camera_defaults.json "
                "to match your camera model.",
            )
            self.statusBar().showMessage("Camera configuration failed")
            if self.camera:
                try:
                    self.camera.disconnect()
                except Exception:
                    pass
                self.camera = None
            return False
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Unexpected error during camera initialization.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Initialization error")
            return False
    
    def start_preview(self) -> None:
        """Start camera preview."""
        if not self.camera or not self.camera.is_connected:
            QMessageBox.warning(
                self,
                "Camera Not Ready",
                "Camera is not connected. Please initialize camera first."
            )
            return
        
        try:
            self.camera.start_grabbing()
            self.preview_timer.start()

            self._sync_top_chrome()

            self.statusBar().showMessage("Preview running...")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to start preview.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Preview start failed")
    
    def stop_preview(self) -> None:
        """Stop camera preview."""
        if self.preview_timer:
            self.preview_timer.stop()
        
        if self.camera:
            try:
                self.camera.stop_grabbing()
            except Exception:
                pass
        
        self.preview_widget.clear_display()

        self._sync_top_chrome()

        self.statusBar().showMessage("Preview stopped")
    
    def update_preview(self) -> None:
        """Update preview with latest frame."""
        if not self.camera or not self.camera.is_grabbing:
            return
        
        try:
            # Grab preview frame (1920x1080)
            frame = self.camera.grab_preview_frame(
                self._preview_width, self._preview_height
            )
            
            if frame is not None:
                frame = self.image_settings.apply_postprocess(frame)
                h, w = frame.shape[:2]
                self._update_stream_stats(w, h)
                frame = self._apply_view_transforms(frame)
                self.preview_widget.display_frame(frame)
            else:
                # Frame grab failed, but don't show error for every failed frame
                pass
                
        except CameraGrabError:
            # Handle grab errors silently during preview
            pass
        except Exception:
            # Other errors - stop preview
            self.stop_preview()
            QMessageBox.warning(
                self,
                "Preview Error",
                "An error occurred during preview. Preview stopped."
            )
    
    def capture_image(self) -> None:
        """Capture a full-resolution image and save it under the configured storage folder."""
        if not self.camera or not self.camera.is_connected:
            QMessageBox.warning(
                self,
                "Camera Not Ready",
                "Camera is not connected."
            )
            return
        
        timer_was_running = (
            self.preview_timer is not None and self.preview_timer.isActive()
        )
        if timer_was_running:
            self.preview_timer.stop()

        try:
            self.statusBar().showMessage("Capturing image...")
            if self._camera_sound_enabled:
                QApplication.beep()
            if self._burst_capture_mode:
                self.statusBar().showMessage(
                    "Burst mode is not implemented yet — saved a single frame."
                )
            # GrabOne after stopping the stream avoids NULL GrabResultPtr with
            # LatestImageOnly + RetrieveResult on some cameras.
            frame = self.camera.grab_still_frame()

            if frame is None:
                self.statusBar().showMessage("Capture failed")
                QMessageBox.warning(
                    self,
                    "Capture Failed",
                    "Failed to capture image. Please try again."
                )
                return

            frame = self.image_settings.apply_postprocess(frame)
            if self._export_full_resolution:
                frame_to_save = frame
            else:
                frame_to_save = self._apply_view_transforms(frame)
                frame_to_save = cv2.resize(
                    frame_to_save,
                    (self._preview_width, self._preview_height),
                    interpolation=cv2.INTER_AREA,
                )

            result = self._snapshot_writer.save_bgr(frame_to_save, prefix="capture")
            self.statusBar().showMessage(f"Saved: {result.path.name}")

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Capture saved")
            msg.setText(
                f"Resolution: {result.width}×{result.height}\n\n"
                f"{result.path}"
            )
            open_folder = msg.addButton("Open Folder", QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Ok)
            msg.exec()
            if msg.clickedButton() == open_folder:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(result.path.parent)))
                
        except CameraGrabError as e:
            QMessageBox.warning(
                self,
                "Capture Error",
                f"Failed to capture image.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Capture error")
        except (OSError, ValueError, RuntimeError) as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"The image was grabbed but could not be saved.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Save error")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Unexpected error during capture.\n\n{str(e)}"
            )
            self.statusBar().showMessage("Capture error")
        finally:
            if (
                timer_was_running
                and self.preview_timer is not None
                and self.camera is not None
                and self.camera.is_grabbing
            ):
                self.preview_timer.start()

    def reconnect_camera(self) -> None:
        """Disconnect and reconnect the camera using the last successful configuration."""
        if not self.camera_config:
            QMessageBox.warning(
                self,
                "Reconnect",
                "No camera configuration is loaded.",
            )
            return

        was_preview = self.camera is not None and self.camera.is_grabbing
        self.stop_preview()

        if self.camera:
            try:
                self.camera.disconnect()
            except Exception:
                pass
            self.camera = None

        self._sync_top_chrome()
        self.statusBar().showMessage("Reconnecting…")

        if self.initialize_camera(self.camera_config) and was_preview:
            self.start_preview()
        else:
            self._sync_top_chrome()
    
    def _update_settings_ui(self) -> None:
        """Update UI controls with current camera settings."""
        if not self.camera or not self.camera.is_connected:
            return
        
        self._updating_settings = True
        
        try:
            exp_auto, exp_value = self.camera.get_exposure()
            self._camera_auto_exposure = exp_auto
            if not exp_auto and exp_value > 0:
                self.image_settings.set_exposure_percent(
                    self.image_settings.exposure_percent_from_microseconds(exp_value),
                    block_signals=True,
                )

            gain_auto, gain_value = self.camera.get_gain()
            self._camera_auto_gain = gain_auto
            if not gain_auto:
                self.image_settings.set_gain_percent(
                    self.image_settings.gain_percent_from_analog(gain_value),
                    block_signals=True,
                )

            
            try:
                frame_rate = self.camera.get_frame_rate()
                if frame_rate > 0:
                    self.frame_rate_spinbox.setValue(frame_rate)
            except Exception:
                pass
            
            try:
                gamma = self.camera.get_gamma()
                if gamma is not None:
                    self.gamma_slider.setValue(int(gamma * 100))
                    self.gamma_spinbox.setValue(gamma)
            except Exception:
                self.gamma_slider.setEnabled(False)
                self.gamma_spinbox.setEnabled(False)
            
        finally:
            self._updating_settings = False
    
    def on_frame_rate_changed(self, value: float) -> None:
        """Handle frame rate spinbox change."""
        if self._updating_settings or not self.camera or not self.camera.is_connected:
            return
        
        try:
            self.camera.set_frame_rate(value)
            self.statusBar().showMessage(f"Frame Rate: {value:.1f} fps")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to set frame rate: {e}")
    
    def on_gamma_changed(self, value: int) -> None:
        """Handle gamma slider change."""
        if self._updating_settings:
            return
        
        gamma_value = value / 100.0
        self.gamma_spinbox.blockSignals(True)
        self.gamma_spinbox.setValue(gamma_value)
        self.gamma_spinbox.blockSignals(False)
        
        if self.camera and self.camera.is_connected:
            try:
                self.camera.set_gamma(gamma_value)
                self.statusBar().showMessage(f"Gamma: {gamma_value:.2f}")
            except Exception as e:
                # Gamma not supported, silently fail
                pass
    
    def on_gamma_spinbox_changed(self, value: float) -> None:
        """Handle gamma spinbox change."""
        if self._updating_settings:
            return
        
        slider_value = int(value * 100)
        self.gamma_slider.blockSignals(True)
        self.gamma_slider.setValue(slider_value)
        self.gamma_slider.blockSignals(False)
        
        if self.camera and self.camera.is_connected:
            try:
                self.camera.set_gamma(value)
                self.statusBar().showMessage(f"Gamma: {value:.2f}")
            except Exception as e:
                # Gamma not supported, silently fail
                pass
    
    def diagnose_blur(self) -> None:
        """Diagnose potential blur issues."""
        if not self.camera or not self.camera.is_connected:
            QMessageBox.warning(
                self,
                "Camera Not Ready",
                "Camera is not connected."
            )
            return
        
        issues = diagnose_blur_issues(self.camera)
        
        message = "Blur Diagnosis:\n\n"
        if len(issues) == 1 and "No obvious software issues" in issues[0]:
            message += "✓ " + issues[0] + "\n\n"
            message += "Recommendations:\n"
            message += "1. Check physical camera lens focus\n"
            message += "2. Ensure camera is stable (no vibration)\n"
            message += "3. Check if lens cap is removed\n"
            message += "4. Verify camera is at correct distance from subject"
        else:
            message += "Potential Issues:\n"
            for issue in issues:
                message += f"• {issue}\n"
            message += "\nRecommendations:\n"
            message += "1. Adjust exposure time if motion blur detected\n"
            message += "2. Check physical camera lens focus\n"
            message += "3. Ensure adequate lighting\n"
            message += "4. Verify camera resolution settings"
        
        QMessageBox.information(self, "Blur Diagnosis", message)
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.stop_preview()
        
        if self.camera:
            try:
                self.camera.disconnect()
            except Exception:
                pass
        
        event.accept()
