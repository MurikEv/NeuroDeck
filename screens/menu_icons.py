"""Resolution-independent line art for the NeuroDeck main menu."""

import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen


def _path(painter, points):
    path = QPainterPath(QPointF(*points[0]))
    for point in points[1:]:
        path.lineTo(QPointF(*point))
    painter.drawPath(path)


def _node(painter, x, y, radius=3.5):
    painter.drawEllipse(QPointF(x, y), radius, radius)


def _ai(painter):
    head = QPainterPath(QPointF(26, 88))
    head.lineTo(30, 73)
    head.cubicTo(17, 63, 13, 45, 20, 28)
    head.cubicTo(27, 11, 52, 9, 68, 19)
    head.cubicTo(79, 26, 80, 39, 79, 44)
    head.lineTo(88, 57)
    head.quadTo(90, 61, 82, 61)
    head.lineTo(80, 61)
    head.lineTo(81, 69)
    head.quadTo(80, 78, 67, 76)
    head.lineTo(64, 89)
    painter.drawPath(head)

    _path(painter, [(24, 29), (44, 29), (53, 37), (65, 37)])
    _path(painter, [(20, 40), (36, 40), (47, 50), (59, 50)])
    _path(painter, [(23, 51), (30, 51), (37, 58)])
    _path(painter, [(44, 67), (52, 59), (65, 59), (71, 53)])
    for x, y in [(69, 37), (63, 50), (39, 61), (40, 70)]:
        _node(painter, x, y)
    painter.drawLine(QPointF(75, 44), QPointF(79, 44))


def _camera(painter):
    body = QPainterPath(QPointF(12, 31))
    body.lineTo(29, 31)
    body.lineTo(36, 20)
    body.lineTo(63, 20)
    body.lineTo(70, 31)
    body.lineTo(87, 31)
    body.quadTo(92, 31, 92, 36)
    body.lineTo(92, 81)
    body.quadTo(92, 86, 87, 86)
    body.lineTo(12, 86)
    body.quadTo(8, 86, 8, 81)
    body.lineTo(8, 36)
    body.quadTo(8, 31, 12, 31)
    painter.drawPath(body)
    _path(painter, [(17, 31), (17, 25), (25, 25), (25, 31)])
    _node(painter, 50, 58, 23)
    _node(painter, 50, 58, 14)
    lens = QPainterPath(QPointF(55, 49))
    lens.cubicTo(42, 43, 36, 59, 47, 66)
    lens.quadTo(55, 70, 59, 62)
    painter.drawPath(lens)


def _notepad(painter):
    painter.drawRoundedRect(QRectF(21, 20, 59, 70), 3, 3)
    for x in (32, 47, 62):
        loop = QPainterPath(QPointF(x, 24))
        loop.lineTo(x, 13)
        loop.quadTo(x + 3, 8, x + 6, 13)
        loop.lineTo(x + 6, 23)
        painter.drawPath(loop)
    for y in (38, 49, 60, 71, 82):
        painter.drawLine(QPointF(31, y), QPointF(70, y))


def _messenger(painter):
    for angle in (-62, -25, 18, 59):
        painter.save()
        painter.translate(50, 50)
        painter.rotate(angle)
        painter.drawEllipse(QRectF(-39, -13, 78, 26))
        painter.restore()
    _node(painter, 50, 50, 5)
    for x, y in ((24, 24), (82, 57), (46, 88)):
        _node(painter, x, y, 2.5)


def _calculator(painter):
    painter.drawRoundedRect(QRectF(20, 8, 61, 84), 3, 3)
    painter.drawRoundedRect(QRectF(28, 17, 45, 22), 1.5, 1.5)
    for y in (47, 61):
        for x in (28, 45, 62):
            painter.drawRoundedRect(QRectF(x, y, 11, 7), 1, 1)
    painter.drawRoundedRect(QRectF(28, 75, 28, 8), 1, 1)
    painter.drawRoundedRect(QRectF(62, 75, 11, 8), 1, 1)


def _browser(painter):
    _node(painter, 50, 50, 40)
    painter.drawEllipse(QRectF(33, 10, 34, 80))
    painter.drawLine(QPointF(10, 50), QPointF(90, 50))
    for y, control_y in ((25, 44), (75, 56)):
        latitude = QPainterPath(QPointF(19, y))
        latitude.quadTo(50, control_y, 81, y)
        painter.drawPath(latitude)


def _files(painter):
    back = QPainterPath(QPointF(12, 85))
    back.lineTo(12, 23)
    back.quadTo(12, 20, 16, 20)
    back.lineTo(39, 20)
    back.lineTo(46, 29)
    back.lineTo(77, 29)
    back.quadTo(83, 29, 83, 35)
    back.lineTo(83, 38)
    painter.drawPath(back)
    _path(painter, [(23, 29), (23, 17), (45, 17), (52, 26)])
    folder = QPainterPath(QPointF(12, 85))
    folder.lineTo(23, 40)
    folder.lineTo(90, 40)
    folder.lineTo(80, 85)
    folder.closeSubpath()
    painter.drawPath(folder)


def _settings(painter):
    gear = QPainterPath()
    first = True
    for tooth in range(8):
        for offset, radius in (
            (-22.5, 30), (-12, 30), (-12, 41),
            (12, 41), (12, 30), (22.5, 30),
        ):
            angle = math.radians(tooth * 45 + offset)
            point = QPointF(
                50 + math.cos(angle) * radius,
                50 + math.sin(angle) * radius,
            )
            if first:
                gear.moveTo(point)
                first = False
            else:
                gear.lineTo(point)
    gear.closeSubpath()
    painter.drawPath(gear)
    _node(painter, 50, 50, 14)


_ICONS = {
    "ai": _ai,
    "camera": _camera,
    "notepad": _notepad,
    "messenger": _messenger,
    "calculator": _calculator,
    "browser": _browser,
    "files": _files,
    "settings": _settings,
}


def _begin_icon(painter, rect, color):
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.translate(rect.x(), rect.y())
    painter.scale(rect.width() / 100, rect.height() / 100)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(
        color, 2.8, Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin,
    ))


def draw_icon(painter: QPainter, name: str, rect: QRectF, color: QColor):
    """Paint a named outline icon, leaving all caller painter state intact."""
    draw = _ICONS[name]
    if rect.isEmpty():
        return
    painter.save()
    try:
        _begin_icon(painter, rect, color)
        draw(painter)
    finally:
        painter.restore()


def draw_brand_mark(painter: QPainter, rect: QRectF, color: QColor):
    """Paint NeuroDeck's circular, three-node neural circuit mark."""
    if rect.isEmpty():
        return
    painter.save()
    try:
        _begin_icon(painter, rect, color)
        _node(painter, 50, 50, 43)
        _path(painter, [(27, 61), (27, 49), (46, 34)])
        _path(painter, [(54, 34), (73, 49), (73, 61)])
        _path(painter, [(50, 38), (50, 73)])
        _path(painter, [(33, 67), (43, 67), (50, 73), (57, 67), (67, 67)])
        for x, y in ((27, 67), (50, 30), (73, 67)):
            _node(painter, x, y, 6)
    finally:
        painter.restore()
