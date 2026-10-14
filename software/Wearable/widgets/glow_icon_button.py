"""Transparent icon button; the home background draws its breathing light."""
from pathlib import Path

from PySide6.QtCore import QSize, Signal, Qt
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import QPushButton


class GlowIconButton(QPushButton):
    emphasis_changed = Signal()

    def __init__(self, icon_name, label, parent=None):
        super().__init__(parent)
        self.setObjectName("homeIconButton")
        self.setFixedSize(50, 50)
        icon_path = Path(__file__).resolve().parent.parent / "assets" / icon_name
        self.setIcon(QIcon(str(icon_path)))
        self.setIconSize(QSize(42, 42))
        self.setToolTip(label)
        self.setAccessibleName(label)
        self.setMouseTracking(True)
        self._hovered = False
        self._keyboard_focus = False
        self._pointer_at_reset = QCursor.pos()
        self.pressed.connect(self.emphasis_changed.emit)
        self.released.connect(self.emphasis_changed.emit)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.emphasis_changed.emit()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._hovered = False
        self.emphasis_changed.emit()

    @property
    def is_emphasized(self):
        return self.isDown() or self._hovered or self._keyboard_focus

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        # Showing home can synthesize a move at the touchscreen's last position.
        # Highlight only after the pointer actually moves away from that position.
        if event.globalPosition().toPoint() != self._pointer_at_reset:
            self._hovered = True
        self.emphasis_changed.emit()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._hovered = False
        self.emphasis_changed.emit()

    def reset_emphasis(self):
        self._hovered = False
        self._keyboard_focus = False
        self._pointer_at_reset = QCursor.pos()
        self.setDown(False)
        self.emphasis_changed.emit()

    def hideEvent(self, event):
        self.reset_emphasis()
        super().hideEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._keyboard_focus = event.reason() in (
            Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason,
            Qt.FocusReason.ShortcutFocusReason,
        )
        self.emphasis_changed.emit()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self._keyboard_focus = False
        self.emphasis_changed.emit()
