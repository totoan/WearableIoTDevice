"""Scalable Legacy-style paths and their animated orange glow."""
from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
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
            ((0, .14), (.36, .38), (.62, .38), (1, .15)),
            ((0, .85), (.35, .68), (.62, .68), (1, .86)),
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
        for point in self.button_glows:
            center = QPointF(point)
            painter.setPen(Qt.PenStyle.NoPen)
            for radius, color in [(27, QColor(255, 80, 10, 55)),
                                  (22, QColor(255, 110, 15, 150)),
                                  (15, QColor(255, 190, 20, 180))]:
                painter.setBrush(color)
                painter.drawEllipse(center, radius, radius)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(255, 140, 40, 200), 2))
            painter.drawEllipse(center, 22, 22)

    def set_button_glows(self, points):
        self.button_glows = points
        self.update()
