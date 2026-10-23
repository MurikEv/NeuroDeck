"""Reference-faithful menu artwork over real touch-operated Qt buttons.

The original reference is displayed without redrawing its text or icons.
Its header is intentionally static in this visual-only version. The previous
vector renderer remains a fallback if the artwork cannot be loaded.
"""

from pathlib import Path

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QColor, QFont, QFontDatabase, QLinearGradient, QPainter, QPainterPath,
    QPen, QPixmap, QPolygonF,
)
from PyQt6.QtWidgets import QAbstractButton, QWidget

from screens.menu_icons import draw_brand_mark, draw_icon


ASSETS = Path(__file__).resolve().parents[1] / "assets"
WORDMARK_TARGET = QRectF(35, 8, 63, 13)
WORDMARK_SOURCE = QRectF(111, 27, 232, 41)
RED = QColor("#ff304b")
CYAN = QColor("#21edfa")
_FONT_FAMILY = None


def menu_font(size, bold=False):
    global _FONT_FAMILY
    if _FONT_FAMILY is None:
        families = []
        for filename in ("Rajdhani-Medium.ttf", "Rajdhani-Bold.ttf"):
            font_id = QFontDatabase.addApplicationFont(str(ASSETS / "fonts" / filename))
            if font_id >= 0:
                families.extend(QFontDatabase.applicationFontFamilies(font_id))
        _FONT_FAMILY = families[0] if families else "DejaVu Sans"
    font = QFont(_FONT_FAMILY)
    font.setPixelSize(size)
    font.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Medium)
    return font


def polygon(points):
    return QPolygonF([QPointF(x, y) for x, y in points])


def path_from(points):
    path = QPainterPath()
    path.addPolygon(polygon(points))
    path.closeSubpath()
    return path


def neon_path(painter, path, color, width=2.0, glow=True):
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if glow:
        for extra, alpha in ((17, 5), (10, 12), (5, 28)):
            halo = QColor(color)
            halo.setAlpha(alpha)
            painter.setPen(QPen(halo, width + extra, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.drawPath(path)
    painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawPath(path)


class MenuCard(QAbstractButton):
    """A real Qt button, with a cached vector face and native drag-out cancel."""

    def __init__(self, title, icon_name, parent):
        super().__init__(parent)
        self.title = title
        self.icon_name = icon_name
        self._selected = False
        self._faces = {}
        self.setText(title)
        self.setAccessibleName(title)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @property
    def highlighted(self):
        return self.isDown() or self._selected

    def set_selected(self, selected):
        if self._selected != selected:
            self._selected = selected
            self.update()

    def paintEvent(self, event):
        if not self.parentWidget().reference_artwork.isNull():
            # Let the parent's exact artwork show through. Only the held card
            # adds feedback; native Qt press/move/release handling is unchanged.
            if self.highlighted:
                painter = QPainter(self)
                try:
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.scale(self.width() / 400, self.height() / 184)
                    outline = path_from([
                        (25, 4), (378, 4), (391, 17), (391, 66), (398, 77),
                        (398, 164), (383, 180), (18, 180), (4, 166), (4, 84),
                        (11, 73), (11, 18),
                    ])
                    painter.fillPath(outline, QColor(18, 234, 250, 25))
                    neon_path(painter, outline, QColor("#70f7ff"), 2.5)
                finally:
                    painter.end()
            return
        ratio = self.devicePixelRatioF()
        key = (self.width(), self.height(), ratio, self.highlighted)
        if key not in self._faces:
            if len(self._faces) > 4:
                self._faces.clear()
            pixmap = QPixmap(round(self.width() * ratio), round(self.height() * ratio))
            pixmap.setDevicePixelRatio(ratio)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            try:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.scale(self.width() / 400, self.height() / 184)
                self._draw_face(painter, self.highlighted)
            finally:
                painter.end()
            self._faces[key] = pixmap
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._faces[key])
        painter.end()

    def _draw_face(self, painter, active):
        outline = path_from([
            (25, 4), (378, 4), (391, 17), (391, 66), (398, 77),
            (398, 164), (383, 180), (18, 180), (4, 166), (4, 84),
            (11, 73), (11, 18),
        ])
        surface = QLinearGradient(0, 8, 0, 180)
        surface.setColorAt(0, QColor("#071c26" if active else "#06121a"))
        surface.setColorAt(0.48, QColor("#092632" if active else "#030c12"))
        surface.setColorAt(1, QColor("#05141d"))
        painter.fillPath(outline, surface)
        neon_path(painter, outline, QColor("#ff5064" if active else "#b22334"), 3 if active else 1.8)
        inner = path_from([
            (28, 13), (373, 13), (383, 23), (383, 71), (389, 80),
            (389, 161), (378, 172), (23, 172), (13, 162), (13, 88),
            (20, 77), (20, 25),
        ])
        neon_path(painter, inner, QColor("#39f6ff" if active else "#157585"), 2 if active else 1.1, glow=active)
        inset = path_from([
            (31, 17), (369, 17), (379, 27), (379, 75), (385, 83),
            (385, 158), (375, 167), (27, 167), (18, 158), (18, 91), (24, 81), (24, 29),
        ])
        neon_path(painter, inset, QColor("#154452"), 0.8, glow=False)
        painter.save()
        painter.setClipPath(inner)
        painter.setPen(QPen(QColor(30, 185, 205, 7), 0.7))
        for y in range(22, 168, 5):
            painter.drawLine(QPointF(24, y), QPointF(380, y))
        strip = QLinearGradient(22, 0, 380, 0)
        strip.setColorAt(0, QColor(8, 61, 76, 155))
        strip.setColorAt(1, QColor(5, 25, 35, 30))
        painter.fillRect(QRectF(21, 148, 361, 22), strip)
        painter.restore()
        for points in (
            [(25, 28), (25, 20), (35, 20)],
            [(373, 29), (373, 20), (362, 20)],
        ):
            painter.setPen(QPen(CYAN, 1.6))
            painter.drawPolyline(polygon(points))
        edge = QPainterPath()
        edge.moveTo(391, 67)
        edge.lineTo(398, 78)
        edge.lineTo(398, 151)
        neon_path(painter, edge, QColor("#ff5266"), 2.2 if active else 1.5)
        icon_color = QColor("#9bfbff" if active else "#19eaf7")
        draw_icon(painter, self.icon_name, QRectF(50, 31, 91, 103), icon_color)
        painter.setFont(menu_font(45, bold=True))
        painter.setPen(icon_color)
        title_rect = QRectF(167, 42, 215, 63)
        metrics = painter.fontMetrics()
        if metrics.horizontalAdvance(self.title) > title_rect.width():
            font = painter.font()
            font.setStretch(max(60, int(title_rect.width() / metrics.horizontalAdvance(self.title) * 100)))
            painter.setFont(font)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.title)
        # Replace fake IDs / Japanese microcopy with graphic ornaments.
        painter.setPen(QPen(QColor("#35c9d6"), 1.5))
        painter.drawPolyline(polygon([(169, 117), (188, 117), (195, 110), (223, 110), (230, 117), (270, 117)]))
        painter.setBrush(QColor("#35c9d6"))
        for x, y in ((169, 117), (223, 110), (270, 117)):
            painter.drawEllipse(QPointF(x, y), 2, 2)
        for index in range(13):
            painter.fillRect(QRectF(325 + index * 2.8, 26, 1 if index % 3 else 1.7, 4), QColor("#288a9b"))
        for index, width in enumerate((17, 4, 7, 3, 11, 5, 3, 8)):
            painter.fillRect(QRectF(28 + index * 10, 157, width / 2, 5), QColor("#26818e"))
        painter.setPen(QPen(QColor("#167688"), 1.1))
        painter.drawLine(QPointF(144, 160), QPointF(326, 160))
        painter.setBrush(CYAN)
        for x in (348, 360):
            painter.drawEllipse(QPointF(x, 160), 3, 3)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(373, 160), 3, 3)


class MenuCanvas(QWidget):
    """Exact reference artwork, with the prior painter design as a fallback."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("neurodeckMenuCanvas")
        self.setFixedSize(480, 320)
        self.reference_artwork = QPixmap(str(ASSETS / "background" / "menu_reference.png"))
        self.wordmark_artwork = QPixmap(str(ASSETS / "background" / "menu_neurodeck_source.png"))
        self.background = QPixmap(str(ASSETS / "background" / "bg_menu.png"))
        self.status = {}
        self.setAccessibleName("NeuroDeck main menu")

    def set_status(self, status):
        if status != self.status:
            self.status = dict(status)
            if not self.reference_artwork.isNull():
                self.setAccessibleDescription("Reference visual. Header numbers, network bars and battery are static artwork.")
            else:
                self.setAccessibleDescription(status["network_tooltip"] + " Battery icon is decorative.")
            self.update(0, 0, 480, 26)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            # Hide the baked-in grey/blue outer chassis outline without
            # changing the artwork, card hitboxes or inner red neon framing.
            painter.fillRect(self.rect(), Qt.GlobalColor.black)
            content_clip = QPainterPath()
            content_clip.addRoundedRect(QRectF(5, 4, 470, 312), 12, 12)
            painter.setClipPath(content_clip)
            if not self.reference_artwork.isNull():
                # Native 480px width: no resampling or distortion. Only the
                # source's last three near-black padding rows lie below 320px.
                painter.drawPixmap(0, 0, self.reference_artwork)
                if not self.wordmark_artwork.isNull():
                    # Use only the edited word, never the generated rest of the
                    # menu: the emblem, signal bars and all other pixels stay original.
                    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                    painter.drawPixmap(WORDMARK_TARGET, self.wordmark_artwork, WORDMARK_SOURCE)
                return
            painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
            painter.fillRect(self.rect(), QColor("#010509"))
            if not self.background.isNull():
                painter.drawPixmap(self.rect(), self.background)
            painter.scale(self.width() / 1536, self.height() / 1024)
            self._draw_header(painter)
            self._draw_chassis_details(painter)
            self._draw_footer(painter)
        finally:
            painter.end()

    def _draw_header(self, painter):
        painter.fillRect(QRectF(25, 12, 1486, 65), QColor("#010407"))
        draw_brand_mark(painter, QRectF(66, 25, 42, 42), RED)
        painter.setFont(menu_font(42, bold=True))
        painter.setPen(RED)
        painter.drawText(QRectF(116, 19, 270, 56), Qt.AlignmentFlag.AlignVCenter, "NeuroDeck")
        state = self.status.get("network_state", "checking")
        bars = self.status.get("network_bars", 0)
        for index, height in enumerate((15, 23, 32)):
            color = QColor("#00c8e6") if index < bars else QColor("#12343f" if state != "offline" else "#48202c")
            gradient = QLinearGradient(0, 64 - height, 0, 64)
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color.darker(140))
            painter.fillRect(QRectF(405 + index * 13, 64 - height, 9, height), gradient)
        painter.setFont(menu_font(21, bold=True))
        painter.setPen(RED if state == "offline" else QColor("#338e9d"))
        painter.drawText(QRectF(456, 33, 50, 32), Qt.AlignmentFlag.AlignVCenter, "NET")
        self._draw_header_ornament(painter)
        painter.setFont(menu_font(44, bold=True))
        painter.setPen(QColor("#ff4055"))
        painter.drawText(QRectF(1210, 19, 149, 55), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self.status.get("time_text", ""))
        self._draw_battery(painter)
        painter.setPen(QPen(RED, 1.7))
        painter.drawLine(QPointF(25, 80), QPointF(1510, 80))

    def _draw_header_ornament(self, painter):
        painter.setPen(QPen(QColor("#a51c32"), 1.5))
        for x in (530, 601, 666):
            painter.drawLine(QPointF(x, 33), QPointF(x, 63))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolyline(polygon([(543, 51), (555, 51), (562, 44), (575, 44), (582, 51), (590, 51)]))
        for index in range(8):
            painter.fillRect(QRectF(614 + index * 4, 45, 1.5, 10 if index % 3 else 16), QColor("#bb2437"))
        painter.drawPolyline(polygon([(682, 42), (690, 49), (682, 56), (699, 56)]))

    def _draw_battery(self, painter):
        # Fixed reference artwork, never a fabricated measured percentage.
        shape = path_from([(1400, 30), (1469, 30), (1478, 38), (1478, 60), (1400, 60)])
        neon_path(painter, shape, RED, 2.5, glow=False)
        painter.fillRect(QRectF(1482, 38, 4, 15), RED)
        for index in range(5):
            painter.fillRect(QRectF(1406 + index * 11, 35, 7, 20), RED)
        painter.setPen(QPen(RED, 3))
        painter.drawLine(QPointF(1462, 53), QPointF(1471, 37))

    def _draw_chassis_details(self, painter):
        for side in (0, 1):
            painter.save()
            if side:
                painter.translate(1536, 0)
                painter.scale(-1, 1)
            painter.setPen(QPen(QColor("#d1283f"), 1.6))
            for y in (126, 710):
                painter.drawPolyline(polygon([(26, y), (26, y + 14), (36, y + 24), (27, y + 33), (38, y + 44)]))
                for index in range(14):
                    painter.drawLine(QPointF(27, y + 63 + index * 5), QPointF(36 if index % 3 else 40, y + 63 + index * 5))
            for y in (302, 672):
                painter.drawPolyline(polygon([(26, y), (36, y + 8), (26, y + 16)]))
                painter.drawLine(QPointF(26, y + 16), QPointF(38, y + 16))
            painter.restore()

    def _draw_footer(self, painter):
        painter.setPen(QPen(QColor("#9d1c2b"), 1.2))
        painter.drawPolyline(polygon([(73, 1005), (73, 955), (91, 938), (1444, 938), (1462, 955), (1462, 1005)]))
        painter.setPen(QPen(RED, 1.8))
        painter.drawLine(QPointF(92, 938), QPointF(1443, 938))
        painter.setFont(menu_font(20, bold=True))
        painter.setPen(RED)
        painter.drawText(QRectF(92, 950, 240, 30), Qt.AlignmentFlag.AlignVCenter, "NEURODECK")
        painter.setPen(QPen(QColor("#9a1e30"), 1.3))
        painter.drawPolyline(polygon([(352, 968), (420, 968), (433, 956), (477, 956), (491, 970), (571, 970)]))
        painter.setBrush(QColor("#e83249"))
        for x, y in ((352, 968), (477, 956), (571, 970)):
            painter.drawEllipse(QPointF(x, y), 3, 3)
        for index in range(7):
            x = 675 + index * 25
            painter.drawPolyline(polygon([(x, 960), (x + 9, 970), (x, 980)]))
        x = 1255
        for index in range(42):
            width = (2, 4, 1, 3, 2, 1, 5)[index % 7]
            painter.fillRect(QRectF(x, 978, width, 19), RED)
            x += width + 2
