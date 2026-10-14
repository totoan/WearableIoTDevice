"""Scalable Legacy-style paths and their animated orange glow."""
from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget


class AnimatedBackground(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.button_glows = []
        self.brightness = 0.0
        self.direction = 1
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def animate(self):
        self.brightness += 0.01 * self.direction
        if self.brightness >= 1:
            self.brightness = 1.0
            self.direction = -1
        elif self.brightness <= 0:
            self.brightness = 0.0
            self.direction = 1
            self.timer.stop()
            QTimer.singleShot(1600, lambda: self.timer.start(30))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(5, 12, 9))
        for points in (
            # Keep the paths in the middle band, clear of the corner icons.
            ((0, .18), (.36, .38), (.62, .38), (1, .18)),
            ((0, .72), (.35, .60), (.62, .60), (1, .72)),
        ):
            path = QPainterPath()
            path.moveTo(points[0][0] * self.width(), points[0][1] * self.height())
            for x, y in points[1:]:
                path.lineTo(x * self.width(), y * self.height())
            strokes = [(QColor(20, 100, 55, 25), 30), (QColor(15, 55, 35), 20), (QColor(1, 6, 4), 15)]
            b = self.brightness
            strokes += [(QColor(255, 80, 10, int(35 * b)), 30),
                        (QColor(255, 110, 15, int(100 * b)), 20),
                        (QColor(255, int(100 + 90 * b), 20, int(230 * b)), 15)]
            for color, width in strokes:
                painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine,
                                    Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                painter.drawPath(path)
        for button in self.button_glows:
            center = QPointF(button.geometry().center())
            strength = 0.25 + 0.75 * self.brightness
            if button.is_emphasized:
                strength = min(1.1, strength + 0.3)
            glow = QRadialGradient(center, 34)
            glow.setColorAt(0, QColor(255, 175, 30, int(225 * strength)))
            glow.setColorAt(0.5, QColor(255, 110, 15, int(190 * strength)))
            glow.setColorAt(0.8, QColor(255, 80, 10, int(75 * strength)))
            glow.setColorAt(1, QColor(255, 80, 10, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(center, 34, 34)

    def set_button_glows(self, buttons):
        self.button_glows = buttons
        self.update()
