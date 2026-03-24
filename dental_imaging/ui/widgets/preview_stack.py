"""Preview area with a child overlay positioned at the top-right."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import QWidget

from dental_imaging.ui.widgets.preview_widget import PreviewWidget


class PreviewStack(QWidget):
    """Fills with live preview; positions ``overlay`` in the top-right corner."""

    def __init__(
        self,
        preview: PreviewWidget,
        overlay: QWidget,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._preview = preview
        self._overlay = overlay
        preview.setParent(self)
        overlay.setParent(self)
        overlay.raise_()

    def preview_widget(self) -> PreviewWidget:
        return self._preview

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self._preview.setGeometry(0, 0, w, h)
        margin = 12
        ow = min(self._overlay.width(), max(120, w - 2 * margin))
        self._overlay.setFixedWidth(ow)
        self._overlay.adjustSize()
        x = w - self._overlay.width() - margin
        y = margin
        self._overlay.move(max(margin, x), y)
