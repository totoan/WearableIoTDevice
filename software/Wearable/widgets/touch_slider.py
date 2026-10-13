"""A horizontal slider that jumps to a tap and commits once an edit finishes."""
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QSlider, QStyle


class TouchSlider(QSlider):
    interaction_started = Signal()
    edit_finished = Signal(int)

    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setMinimumHeight(34)
        self._dragging = False
        self._keyboard_editing = False

    @property
    def is_editing(self):
        return self._dragging or self._keyboard_editing

    def value_at(self, position):
        handle = self.style().pixelMetric(QStyle.PixelMetric.PM_SliderLength, None, self)
        span = max(1, self.width() - handle)
        pixel = max(0, min(span, round(position.x() - handle / 2)))
        return QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), pixel, span)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self._dragging = True
            self.interaction_started.emit()
            self.setSliderDown(True)
            self.setValue(self.value_at(event.position()))
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            self.setValue(self.value_at(event.position()))
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self.setValue(self.value_at(event.position()))
            self._dragging = False
            self.setSliderDown(False)
            self.edit_finished.emit(self.value())
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (
            Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Home, Qt.Key.Key_End,
            Qt.Key.Key_PageUp, Qt.Key.Key_PageDown,
        ) and not self._keyboard_editing:
            self._keyboard_editing = True
            self.interaction_started.emit()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        if self._keyboard_editing and not event.isAutoRepeat():
            self._keyboard_editing = False
            self.edit_finished.emit(self.value())

    def cancel_edit(self):
        self._dragging = False
        self._keyboard_editing = False
        previous = self.blockSignals(True)
        self.setSliderDown(False)
        self.blockSignals(previous)

    def hideEvent(self, event):
        self.cancel_edit()
        super().hideEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.EnabledChange and not self.isEnabled():
            self.cancel_edit()
        super().changeEvent(event)

    def focusOutEvent(self, event):
        if self._keyboard_editing:
            self.cancel_edit()
        super().focusOutEvent(event)
