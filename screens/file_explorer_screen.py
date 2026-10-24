from collections import OrderedDict
from datetime import datetime
from pathlib import Path
import time

from PyQt6.QtCore import QEvent, QFileSystemWatcher, QObject, QPointF, QRectF, QSize, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont, QFontDatabase, QImage, QImageReader, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from PyQt6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QApplication,
    QFrame,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidgetItem,
    QWidget,
)

from screens.menu_screen import path_from, polygon
import state


EXPLORER_CYAN = QColor("#20e5f2")
EXPLORER_SIZE = (1515, 729)
_EXPLORER_FONTS = None


def explorer_font(size, bold=False, japanese=False):
    global _EXPLORER_FONTS
    if _EXPLORER_FONTS is None:
        _EXPLORER_FONTS = {}
        folder = Path(__file__).resolve().parents[1] / "assets" / "fonts"
        for filename in ("BarlowCondensed-Regular.ttf", "BarlowCondensed-Bold.ttf", "NotoSansJP-Explorer.ttf"):
            font_id = QFontDatabase.addApplicationFont(str(folder / filename))
            families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
            if families:
                _EXPLORER_FONTS["japanese" if filename.startswith("Noto") else "latin"] = families[0]
    font = QFont(_EXPLORER_FONTS.get("japanese" if japanese else "latin", "DejaVu Sans"))
    font.setPixelSize(size)
    font.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
    return font


def explorer_text(painter, rect, text, size, color=EXPLORER_CYAN, bold=False, japanese=False, glow=False, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter):
    painter.save()
    painter.setFont(explorer_font(size, bold, japanese))
    if glow:
        halo = QColor(color)
        halo.setAlpha(28)
        painter.setPen(halo)
        for dx, dy in ((-1.2, 0), (1.2, 0), (0, -1.2), (0, 1.2)):
            painter.drawText(rect.translated(dx, dy), alignment, text)
    painter.setPen(color)
    painter.drawText(rect, alignment, text)
    painter.restore()


def explorer_shape(rect, cut=7):
    x, y, width, height = rect.getRect()
    return path_from([
        (x + cut, y), (x + width - cut, y), (x + width, y + cut),
        (x + width, y + height - cut), (x + width - cut, y + height),
        (x + cut, y + height), (x, y + height - cut), (x, y + cut),
    ])


def explorer_micro_marks(painter, x, y, color=EXPLORER_CYAN):
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    for index, height in enumerate((3, 4, 2, 4, 3, 2, 4, 4, 2, 3, 4, 2)):
        shade = QColor(color)
        shade.setAlpha(80 + index % 4 * 20)
        painter.setBrush(shade)
        painter.drawRect(QRectF(x + index * 2.2, y + 4 - height, 0.9, height))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(QColor(color), 0.7))
    painter.drawPolyline(polygon([(x + 30, y + 4), (x + 30, y), (x + 35, y), (x + 35, y + 4), (x + 30, y + 4)]))
    painter.drawLine(QPointF(x + 38, y), QPointF(x + 38, y + 4))
    painter.restore()


def explorer_corner_marks(painter, rect, color=EXPLORER_CYAN, length=13):
    painter.save()
    painter.setPen(QPen(color, 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    x, y, width, height = rect.getRect()
    for corner_x, corner_y, dx, dy in (
        (x, y, 1, 1), (x + width, y, -1, 1),
        (x, y + height, 1, -1), (x + width, y + height, -1, -1),
    ):
        painter.drawPolyline(polygon([
            (corner_x, corner_y + dy * length), (corner_x, corner_y + dy * 2),
            (corner_x + dx * 2, corner_y), (corner_x + dx * length, corner_y),
        ]))
    painter.restore()


def explorer_texture(painter, rect):
    painter.save()
    painter.setClipRect(rect)
    painter.setPen(QPen(QColor(18, 115, 133, 10), 0.6))
    for y in range(round(rect.top()) + 3, round(rect.bottom()), 4):
        painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
    painter.setPen(QPen(QColor(40, 151, 169, 17), 0.65))
    for index in range(45):
        x = rect.x() + (index * 73 + 19) % max(1, int(rect.width()))
        y = rect.y() + (index * 41 + 7) % max(1, int(rect.height()))
        painter.drawLine(QPointF(x, y), QPointF(x + 1.4, y))
    painter.restore()


def explorer_gradient(rect, color):
    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0, QColor(color))
    gradient.setColorAt(1, QColor("#000000"))
    return gradient


def explorer_neon(painter, path, color, width=2.2, glow=1.0):
    painter.save()
    painter.setBrush(Qt.BrushStyle.NoBrush)
    bounds = path.boundingRect()
    for extra, alpha in ((10, 7), (5, 18), (2, 42), (0, 255)):
        if extra:
            alpha = round(alpha * glow)
        gradient = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        for position, shade in (
            (0, QColor(color).lighter(115)), (0.38, QColor(color)),
            (0.72, QColor(color).darker(170)), (1, QColor(color).darker(280)),
        ):
            shade.setAlpha(alpha)
            gradient.setColorAt(position, shade)
        painter.setPen(QPen(QBrush(gradient), width + extra, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)
    painter.restore()


def explorer_icon(painter, name, rect, color):
    painter.save()
    painter.translate(rect.x(), rect.y())
    painter.scale(rect.width() / 100, rect.height() / 100)
    painter.setPen(QPen(color, 4.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if name == "files":
        painter.drawPolyline(polygon([(10, 31), (10, 22), (37, 22), (46, 32), (81, 32), (88, 40)]))
        painter.drawPolygon(polygon([(10, 40), (91, 40), (81, 85), (10, 85)]))
    elif name == "photos":
        painter.drawRoundedRect(QRectF(11, 14, 78, 72), 3, 3)
        painter.drawEllipse(QPointF(33, 34), 7, 7)
        painter.drawPolyline(polygon([(16, 73), (40, 49), (55, 63), (68, 48), (86, 70)]))
    elif name == "favorites":
        painter.drawPolygon(polygon([(50, 9), (62, 35), (91, 39), (70, 59), (75, 89), (50, 75), (25, 89), (30, 59), (9, 39), (38, 35)]))
    elif name == "trash":
        painter.drawPolyline(polygon([(25, 28), (30, 88), (70, 88), (75, 28)]))
        painter.drawLine(QPointF(16, 23), QPointF(84, 23))
        painter.drawPolyline(polygon([(38, 20), (38, 10), (62, 10), (62, 20)]))
        for x in (43, 57):
            painter.drawLine(QPointF(x, 36), QPointF(x, 76))
    elif name == "storage":
        painter.setBrush(color)
        painter.drawEllipse(QRectF(17, 14, 66, 22))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for y in (29, 44, 59):
            painter.drawArc(QRectF(17, y, 66, 22), 180 * 16, 180 * 16)
            painter.drawLine(QPointF(17, y + 3), QPointF(17, y + 11))
            painter.drawLine(QPointF(83, y + 3), QPointF(83, y + 11))
    elif name == "share":
        painter.drawPolyline(polygon([(63, 49), (63, 83), (17, 83), (17, 34), (42, 34)]))
        painter.drawPolyline(polygon([(45, 18), (80, 18), (80, 53)]))
        painter.drawLine(QPointF(35, 63), QPointF(80, 18))
    elif name == "sort":
        painter.drawLine(QPointF(30, 15), QPointF(30, 84))
        painter.drawPolyline(polygon([(17, 70), (30, 85), (43, 70)]))
        painter.drawLine(QPointF(70, 85), QPointF(70, 16))
        painter.drawPolyline(polygon([(57, 30), (70, 15), (83, 30)]))
    elif name == "back":
        painter.drawPolyline(polygon([(66, 18), (30, 50), (66, 82)]))
    else:
        painter.drawPolyline(polygon([(26, 12), (65, 12), (80, 28), (80, 87), (26, 87), (26, 12)]))
        for y in (41, 55, 69):
            painter.drawLine(QPointF(37, y), QPointF(68, y))
    painter.restore()


class ExplorerButton(QAbstractButton):
    def __init__(self, text, icon, parent, navigation=False):
        super().__init__(parent)
        self.icon = icon
        self.navigation = navigation
        self.reference_size = (272, 116) if navigation else (177, 71)
        self.subtitle = {
            "files": "ファイル", "photos": "写真", "favorites": "お気に入り",
            "trash": "ゴミ箱", "back": "メニュー", "sort": "並べ替え",
            "file": "開く", "share": "共有",
        }.get(icon, "")
        self.setText(text)
        self.setAccessibleName(text)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.toggled.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            width, height = self.reference_size
            painter.scale(self.width() / width, self.height() / height)
            active = self.isChecked() or self.isDown()
            rect = QRectF(1.5, 1.5, width - 3, height - 3)
            shape = explorer_shape(rect)
            painter.fillPath(shape, explorer_gradient(rect, QColor("#140c12" if active else "#041117")))
            explorer_texture(painter, rect.adjusted(3, 3, -3, -3))
            border = QColor("#ff384b" if active else "#1496aa")
            explorer_neon(painter, shape, border, 1.9 if active else 1.1, glow=1.0 if active else 0.5)
            inner = explorer_shape(rect.adjusted(3, 3, -3, -3), 5)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#8d2734" if active else "#0b3c48"), 0.8))
            painter.drawPath(inner)
            painter.setPen(QPen(QColor("#ff4858" if active else "#854047"), 1.2))
            for points in (
                [(2, 18), (2, 8), (8, 2), (22, 2)],
                [(width - 23, 2), (width - 8, 2), (width - 2, 8), (width - 2, 18)],
                [(2, height - 17), (2, height - 8), (8, height - 2), (22, height - 2)],
                [(width - 23, height - 2), (width - 8, height - 2), (width - 2, height - 8)],
            ):
                painter.drawPolyline(polygon(points))
            if self.navigation:
                glow = QRadialGradient(QPointF(52, 53), 65)
                glow.setColorAt(0, QColor(16, 213, 237, 23))
                glow.setColorAt(1, QColor(16, 213, 237, 0))
                painter.fillRect(QRectF(4, 4, 112, height - 8), glow)
                explorer_icon(painter, self.icon, QRectF(23, 26, 57, 57), EXPLORER_CYAN)
                explorer_text(painter, QRectF(111, 20, width - 119, 40), self.text(), 30, bold=True, glow=True)
                explorer_text(painter, QRectF(111, 66, width - 119, 30), self.subtitle, 22, japanese=True)
                if active:
                    explorer_corner_marks(painter, QRectF(10, 9, width - 20, height - 18), QColor("#18a1b3"), 9)
            else:
                explorer_icon(painter, self.icon, QRectF(16, (height - 43) / 2, 43, 43), EXPLORER_CYAN)
                explorer_text(painter, QRectF(74, 4 if height < 70 else 7, width - 79, 31), self.text(), 23, bold=True, glow=True)
                explorer_text(painter, QRectF(74, 33 if height < 70 else 39, width - 79, 23), self.subtitle, 17, japanese=True)
                if self.icon == "sort":
                    painter.setPen(QPen(EXPLORER_CYAN, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                    painter.drawPolyline(polygon([(width - 34, 27), (width - 27, 34), (width - 20, 27)]))
        finally:
            painter.end()


class ExplorerFileCard(QAbstractButton):
    def __init__(self, entry, gallery):
        super().__init__(gallery.content)
        self.entry = entry
        self.gallery = gallery
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setText(entry["name"])
        self.setAccessibleName(entry["name"])
        self.setToolTip(entry["name"])
        self.clicked.connect(lambda: gallery.view.controller.select_file(self.entry["path"]))
        self.installEventFilter(gallery)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
            painter.scale(self.width() / 245, self.height() / 194)
            rect = QRectF(1, 1, 243, 192)
            selected = self.gallery.view.controller.selected_path == self.entry["path"]
            color = QColor("#ff384b") if selected or self.isDown() else QColor("#0cbfd2")
            painter.fillPath(explorer_shape(rect, 5), explorer_gradient(rect, QColor("#031016")))
            explorer_neon(painter, explorer_shape(rect, 5), color, width=1.5 if selected else 1.1, glow=0.4)
            preview = QRectF(6, 5, 233, 134)
            image = self.gallery.view.controller.thumbnail_for(self.entry)
            if image.isNull():
                explorer_icon(painter, "photos" if self.entry["is_image"] else "file", QRectF(93, 44, 58, 57), QColor("#248493"))
            else:
                painter.save()
                painter.setClipPath(explorer_shape(preview, 5))
                source = QRectF(image.rect())
                aspect = preview.width() / preview.height()
                if source.width() / source.height() > aspect:
                    width = source.height() * aspect
                    source.setLeft((source.width() - width) / 2)
                    source.setWidth(width)
                else:
                    height = source.width() / aspect
                    source.setTop((source.height() - height) / 2)
                    source.setHeight(height)
                painter.drawImage(preview, image, source)
                painter.restore()
            explorer_corner_marks(painter, preview.adjusted(3, 3, -3, -3), EXPLORER_CYAN, 10)
            explorer_micro_marks(painter, preview.right() - 46, preview.top() + 7, QColor("#168c9e"))
            painter.setFont(explorer_font(21))
            name = painter.fontMetrics().elidedText(self.entry["name"], Qt.TextElideMode.ElideMiddle, 226)
            explorer_text(painter, QRectF(10, 141, 226, 27), name, 21)
            modified = datetime.fromtimestamp(self.entry["modified_ns"] / 1_000_000_000).strftime("%Y.%m.%d  %H:%M")
            explorer_text(painter, QRectF(10, 168, 226, 22), modified, 18, QColor("#17becf"))
        finally:
            painter.end()


class ExplorerGallery(QScrollArea):
    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self.cards = []
        self._drag_source = None
        self._dragging = False
        self.setObjectName("explorerGallery")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { background: #01070b; width: 4px; margin: 0; }"
            "QScrollBar::handle:vertical { background: #157c8c; min-height: 12px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }"
        )
        self.viewport().setAutoFillBackground(False)
        self.content = QWidget()
        self.setWidget(self.content)
        self.content.setAutoFillBackground(False)
        self.content.installEventFilter(self)
        self.viewport().installEventFilter(self)

    def set_entries(self, entries):
        previous = {card.entry["path"]: card for card in self.cards}
        self.cards = []
        for entry in entries:
            card = previous.pop(entry["path"], None)
            if card is None:
                card = ExplorerFileCard(entry, self)
            else:
                card.entry = entry
                card.update()
            self.cards.append(card)
            card.show()
        for card in previous.values():
            if self._drag_source is card:
                self._drag_source = None
                self._dragging = False
            card.hide()
            card.deleteLater()
        self.layout_cards()

    def layout_cards(self):
        width = max(1, self.viewport().width())
        scale_x = width / 780
        scale_y = self.view.height() / EXPLORER_SIZE[1]
        rows = (len(self.cards) + 2) // 3
        height = max(self.viewport().height(), round((max(0, rows - 1) * 205 + (196 if rows else 0)) * scale_y))
        self.content.resize(width, height)
        for index, card in enumerate(self.cards):
            column, row = index % 3, index // 3
            card.setGeometry(
                round((10 + column * 260) * scale_x), round((2 + row * 205) * scale_y),
                max(1, round(245 * scale_x)), max(1, round(194 * scale_y)),
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.layout_cards()

    def eventFilter(self, obj, event):
        if obj is self.viewport() and event.type() == QEvent.Type.Resize:
            QTimer.singleShot(0, self.layout_cards)
        elif event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick) and event.button() == Qt.MouseButton.LeftButton:
            self._drag_source = obj
            self._drag_start = event.globalPosition()
            self._scroll_start = self.verticalScrollBar().value()
            self._dragging = False
        elif event.type() == QEvent.Type.MouseMove and self._drag_source is obj:
            delta = event.globalPosition() - self._drag_start
            if self.verticalScrollBar().maximum() > 0 and abs(delta.y()) >= QApplication.startDragDistance() and abs(delta.y()) > abs(delta.x()):
                self._dragging = True
            if self._dragging:
                if isinstance(obj, QAbstractButton):
                    obj.setDown(False)
                self.verticalScrollBar().setValue(self._scroll_start - round(delta.y()))
                return True
        elif event.type() == QEvent.Type.MouseButtonRelease and self._drag_source is obj:
            cancelled = self._dragging
            self._drag_source = None
            self._dragging = False
            if cancelled:
                if isinstance(obj, QAbstractButton):
                    obj.setDown(False)
                return True
        return False


class FileExplorerScreen(QWidget):
    def __init__(self, controller, parent):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("fileExplorerVisual")
        self.navigation = {}
        for category, text in (("files", "FILES"), ("photos", "PHOTOS"), ("favorites", "FAVORITES"), ("trash", "TRASH")):
            button = ExplorerButton(text, category, self, navigation=True)
            button.setObjectName("explorer_" + category + "_button")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.toggled.connect(self.update)
            self.navigation[category] = button
        self.navigation["files"].setChecked(True)
        for category, button in self.navigation.items():
            button.toggled.connect(lambda checked, category=category: controller.select_category(category) if checked else None)
        self.gallery = ExplorerGallery(self)
        self.back_button = ExplorerButton("MENU", "back", self)
        self.back_button.setObjectName("explorer_menu_button")
        self.back_button.clicked.connect(controller.back_to_menu)
        self.actions = {}
        for action, title, icon in (
            ("sort", "SORT", "sort"), ("open", "OPEN", "file"),
            ("delete", "DELETE", "trash"), ("favorite", "ADD TO FAVORITES", "favorites"),
            ("share", "SHARE", "share"),
        ):
            button = ExplorerButton(title, icon, self)
            button.setObjectName("explorer_" + action + "_button")
            if action == "delete":
                button.subtitle = "削除"
            elif action == "favorite":
                button.subtitle = "お気に入りに追加"
            button.setEnabled(False)
            self.actions[action] = button
        self.actions["open"].clicked.connect(controller.open_selected)

    def place(self, widget, x, y, width, height):
        widget.reference_size = (width, height)
        widget.setGeometry(
            round(x * self.width() / EXPLORER_SIZE[0]), round(y * self.height() / EXPLORER_SIZE[1]),
            round(width * self.width() / EXPLORER_SIZE[0]), round(height * self.height() / EXPLORER_SIZE[1]),
        )

    def resizeEvent(self, event):
        for button, y, height in zip(self.navigation.values(), (5, 133, 258, 385), (116, 115, 116, 116)):
            self.place(button, 0, y, 272, height)
        self.place(self.back_button, 0, 515, 272, 64)
        self.place(self.actions["sort"], 881, 16, 207, 62)
        self.place(self.actions["open"], 1133, 464, 177, 71)
        self.place(self.actions["delete"], 1321, 464, 177, 71)
        self.place(self.actions["favorite"], 1133, 550, 365, 71)
        self.place(self.actions["share"], 1133, 635, 365, 71)
        self.place(self.gallery, 313, 103, 780, 609)
        self.gallery.layout_cards()
        super().resizeEvent(event)

    def panel(self, painter, rect, color, fill):
        shape = explorer_shape(rect)
        painter.fillPath(shape, explorer_gradient(rect, fill))
        explorer_texture(painter, rect.adjusted(2, 2, -2, -2))
        explorer_neon(painter, shape, color, width=1.1, glow=0.5)
        painter.save()
        painter.setPen(QPen(QColor("#75303b"), 1.0))
        x, y, width, height = rect.getRect()
        for points in (
            [(x, y + 18), (x, y + 7), (x + 7, y), (x + 22, y)],
            [(x + width - 23, y + height), (x + width - 7, y + height), (x + width, y + height - 7), (x + width, y + height - 20)],
        ):
            painter.drawPolyline(polygon(points))
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
            painter.fillRect(self.rect(), explorer_gradient(QRectF(self.rect()), QColor("#01080c")))
            painter.scale(self.width() / EXPLORER_SIZE[0], self.height() / EXPLORER_SIZE[1])
            painter.setPen(QPen(QColor("#06202a"), 0.8))
            for y in (521, 547, 567, 585):
                painter.drawPolyline(polygon([(4, y + 9), (46, y - 4), (136, y + 3), (260, y - 7)]))
            divider = QPainterPath(QPointF(287, 0))
            divider.lineTo(287, 729)
            explorer_neon(painter, divider, QColor("#ff3049"), width=1.6)
            painter.setPen(QPen(QColor("#ff5360"), 2))
            for y1, y2 in ((0, 13), (238, 249), (507, 519), (715, 729)):
                painter.drawLine(QPointF(287, y1), QPointF(287, y2))
            self.panel(painter, QRectF(302, 0.8, 801, 88), QColor("#155464"), QColor("#030e14"))
            explorer_icon(painter, "photos", QRectF(321, 16, 55, 54), EXPLORER_CYAN)
            explorer_text(painter, QRectF(403, 9, 162, 63), "GALLERY", 42, bold=True, glow=True)
            explorer_text(painter, QRectF(564, 25, 230, 38), "ギャラリー", 25, japanese=True)
            self.panel(painter, QRectF(302, 101, 801, 624), QColor("#123e4b"), QColor("#01090e"))
            if not self.controller.entries:
                text = self.controller.error_message or "NO FILES"
                explorer_text(painter, QRectF(343, 353, 719, 48), text, 26, QColor("#3b8996"), alignment=Qt.AlignmentFlag.AlignCenter)
            self.panel(painter, QRectF(1113, 0.8, 401, 725), QColor("#8a2636"), QColor("#030d13"))
            preview = QRectF(1127, 16, 374, 301)
            self.panel(painter, preview, QColor("#377d8d"), QColor("#04151e"))
            painter.setPen(QPen(QColor("#10404d"), 0.8))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(explorer_shape(preview.adjusted(4, 4, -4, -4), 6))
            explorer_corner_marks(painter, preview.adjusted(11, 9, -11, -9), EXPLORER_CYAN, 12)
            explorer_micro_marks(painter, preview.right() - 73, preview.top() + 17, QColor("#168c9e"))
            selected = self.controller.selected_entry()
            image = self.controller.preview_image
            if selected is not None and not image.isNull():
                target = QRectF(preview)
                size = QSize(round(target.width() - 12), round(target.height() - 12))
                fitted = image.size().scaled(size, Qt.AspectRatioMode.KeepAspectRatio)
                target = QRectF(target.center().x() - fitted.width() / 2, target.center().y() - fitted.height() / 2, fitted.width(), fitted.height())
                painter.drawImage(target, image)
            else:
                explorer_icon(painter, "photos" if selected is None or selected["is_image"] else "file", QRectF(1270, 118, 88, 83), QColor("#154454"))
            if selected is None:
                explorer_text(painter, QRectF(1137, 331, 352, 43), "NO SELECTION", 28, bold=True, glow=True)
                explorer_text(painter, QRectF(1138, 374, 345, 32), "Select a file to view its details.", 22, QColor("#4b939e"))
            else:
                painter.setFont(explorer_font(28))
                name = painter.fontMetrics().elidedText(selected["name"], Qt.TextElideMode.ElideMiddle, 348)
                explorer_text(painter, QRectF(1137, 331, 352, 43), name, 28, glow=True)
                modified = datetime.fromtimestamp(selected["modified_ns"] / 1_000_000_000).strftime("%Y.%m.%d   %H:%M")
                explorer_text(painter, QRectF(1138, 374, 345, 30), modified, 22)
                explorer_text(painter, QRectF(1138, 404, 345, 27), self.controller.format_size(selected["size"]), 22)
                dimensions = self.controller.preview_size
                if dimensions.isValid():
                    explorer_text(painter, QRectF(1138, 432, 345, 27), f"{dimensions.width()} × {dimensions.height()}", 22)
            self.panel(painter, QRectF(0.8, 599, 271, 129), QColor("#17798b"), QColor("#031018"))
            explorer_icon(painter, "storage", QRectF(17, 613, 45, 48), EXPLORER_CYAN)
            explorer_text(painter, QRectF(75, 609, 177, 36), "STORAGE", 24, bold=True, glow=True)
            explorer_text(painter, QRectF(75, 646, 177, 25), "ストレージ", 18, japanese=True)
            painter.setPen(QPen(QColor("#0c3540"), 0.8))
            painter.setBrush(QColor("#061c25"))
            painter.drawRoundedRect(QRectF(21, 670, 227, 13), 6, 6)
            explorer_text(painter, QRectF(21, 695, 227, 28), "NOT LOADED", 19, QColor("#52b7c4"))
        finally:
            painter.end()


class ImageViewerScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setProperty("statusBarResponsive", True)

    def resizeEvent(self, event):
        self.controller.layout_image_viewer()
        self.controller.update_image()
        super().resizeEvent(event)


class FileExplorerController(QObject):
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tif", ".tiff"}

    def __init__(self, window, pictures_path=None, ai_memory_path=None):
        super().__init__(window)
        self.window = window
        root = Path(__file__).resolve().parents[1] / "data"
        self.ai_memory_path = Path(ai_memory_path) if ai_memory_path is not None else root / "ai_memory"
        self.pictures_path = Path(pictures_path) if pictures_path is not None else root / "camera_pictures"
        self.current_pixmap = None
        self.category = "files"
        self.entries = []
        self.selected_path = None
        self.preview_image = QImage()
        self.preview_size = QSize()
        self.error_message = ""
        self._snapshot = None
        self._preview_key = None
        self._thumbnails = OrderedDict()
        self._failed_thumbnails = set()
        self._closed = False

        self.file_watcher = QFileSystemWatcher(self)
        self.refresh_debounce = QTimer(self)
        self.refresh_debounce.setSingleShot(True)
        self.refresh_debounce.setInterval(120)
        self.refresh_debounce.timeout.connect(self.refresh_files)
        self.file_watcher.directoryChanged.connect(self.schedule_refresh)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(1000)
        self.refresh_timer.timeout.connect(self.poll_files)

        self.setup_table()
        self.setup_image_viewer()
        self.window.ai_memory_btn.clicked.connect(self.show_ai_memory)
        self.window.cam_pictures_btn.clicked.connect(self.show_pictures)
        self.window.back_to_menu_btn.clicked.connect(self.back_to_menu)
         
        self.setup_visual_screen()
        self.refresh_files()
        self.refresh_timer.start()
        QApplication.instance().aboutToQuit.connect(self.close)

    def close(self):
        self._closed = True
        self.refresh_timer.stop()
        self.refresh_debounce.stop()
        watched = self.file_watcher.directories()
        if watched:
            self.file_watcher.removePaths(watched)

    def schedule_refresh(self, *_args):
        if not self._closed:
            self.refresh_debounce.start()

    def poll_files(self):
        if self.view.isVisible():
            self.refresh_files()

    def watch_directories(self):
        paths = set()
        for folder in (self.ai_memory_path, self.pictures_path):
            try:
                candidate = folder
                while not candidate.is_dir() and candidate != candidate.parent:
                    candidate = candidate.parent
                if candidate.is_dir():
                    paths.add(str(candidate))
                if folder.parent.is_dir():
                    paths.add(str(folder.parent))
            except OSError:
                continue
        watched = set(self.file_watcher.directories())
        if watched - paths:
            self.file_watcher.removePaths(sorted(watched - paths))
        if paths - watched:
            self.file_watcher.addPaths(sorted(paths - watched))

    def select_category(self, category):
        if category not in self.view.navigation:
            return
        if not self.view.navigation[category].isChecked():
            self.view.navigation[category].setChecked(True)
            return
        changed = self.category != category
        self.category = category
        if changed:
            self.selected_path = None
            self._snapshot = None
            self.view.gallery.verticalScrollBar().setValue(0)
        self.refresh_files()

    def refresh_files(self):
        if self._closed:
            return
        self.watch_directories()
        entries = []
        error_message = ""
        folder = {"files": self.ai_memory_path, "photos": self.pictures_path}.get(self.category)
        if folder is not None:
            try:
                for path in folder.iterdir():
                    try:
                        if not path.is_file():
                            continue
                        is_image = path.suffix.lower() in self.image_extensions
                        if self.category == "photos" and not is_image:
                            continue
                        stat = path.stat()
                    except OSError:
                        continue
                    entries.append({
                        "path": path, "name": path.name, "size": stat.st_size,
                        "modified_ns": stat.st_mtime_ns, "is_image": is_image,
                    })
            except FileNotFoundError:
                pass
            except OSError as exc:
                error_message = "FOLDER UNAVAILABLE"
                if error_message != self.error_message:
                    print(f"File Explorer unavailable: {folder}: {exc}")
        entries.sort(key=lambda entry: (-entry["modified_ns"], entry["name"].casefold()))
        snapshot = (self.category, error_message, tuple((entry["path"], entry["modified_ns"], entry["size"]) for entry in entries))
        self.error_message = error_message
        if snapshot != self._snapshot:
            self._snapshot = snapshot
            self.entries = entries
            available = {entry["path"] for entry in entries}
            if self.selected_path not in available:
                self.selected_path = None
            keys = {self.entry_key(entry) for entry in entries}
            self._thumbnails = OrderedDict((key, value) for key, value in self._thumbnails.items() if key in keys)
            self._failed_thumbnails.intersection_update(available)
            self.view.gallery.set_entries(entries)
            self.update_selection()
            self.view.update()
        else:
            for card in self.view.gallery.cards:
                if card.entry["path"] in self._failed_thumbnails:
                    card.update()
            if self.selected_path is not None and self.preview_image.isNull():
                self.update_selection()

    @staticmethod
    def entry_key(entry):
        return entry["path"], entry["modified_ns"], entry["size"]

    @staticmethod
    def read_scaled_image(path, target):
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        original_size = reader.size()
        if original_size.isValid():
            scaled = original_size.scaled(target, Qt.AspectRatioMode.KeepAspectRatio)
            if scaled.width() < original_size.width() or scaled.height() < original_size.height():
                reader.setScaledSize(scaled)
        return reader.read(), original_size

    def thumbnail_for(self, entry):
        if not entry["is_image"]:
            return QImage()
        key = self.entry_key(entry)
        cached = self._thumbnails.get(key)
        if cached is not None and (not cached[0].isNull() or time.monotonic() - cached[1] < 1):
            self._thumbnails.move_to_end(key)
            return cached[0]
        image, _size = self.read_scaled_image(entry["path"], QSize(320, 240))
        if image.isNull():
            self._failed_thumbnails.add(entry["path"])
        else:
            self._failed_thumbnails.discard(entry["path"])
        self._thumbnails[key] = image, time.monotonic()
        self._thumbnails.move_to_end(key)
        while len(self._thumbnails) > 64:
            self._thumbnails.popitem(last=False)
        return image

    def selected_entry(self):
        return next((entry for entry in self.entries if entry["path"] == self.selected_path), None)

    def select_file(self, path):
        if any(entry["path"] == path for entry in self.entries):
            self.selected_path = path
            self.update_selection()

    def update_selection(self):
        selected = self.selected_entry()
        key = self.entry_key(selected) if selected is not None else None
        if key != self._preview_key or (selected is not None and selected["is_image"] and self.preview_image.isNull()):
            self._preview_key = key
            self.preview_image = QImage()
            self.preview_size = QSize()
            if selected is not None and selected["is_image"]:
                self.preview_image, self.preview_size = self.read_scaled_image(selected["path"], QSize(640, 480))
        self.view.actions["open"].setEnabled(selected is not None and selected["is_image"] and not self.preview_image.isNull())
        for card in self.view.gallery.cards:
            card.update()
        self.view.update()

    def open_selected(self):
        selected = self.selected_entry()
        if selected is not None and selected["is_image"]:
            self.open_image(selected["path"])

    @staticmethod
    def format_size(size):
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"

    def setup_visual_screen(self):
        screen = self.window.fileexplorer_screen
        for widget in screen.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
            widget.hide()
        screen.setProperty("statusBarResponsive", True)
        self.view = FileExplorerScreen(self, screen)
        self.view.setGeometry(screen.rect())
        screen.installEventFilter(self)
        self.view.show()

    def eventFilter(self, obj, event):
        if obj is self.window.fileexplorer_screen and event.type() == QEvent.Type.Resize:
            self.view.setGeometry(obj.rect())
        elif obj is self.window.fileexplorer_screen and event.type() == QEvent.Type.Show:
            self.refresh_files()
        return False

    def setup_table(self):
        table = self.window.file_table
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Name", "Type", "Size", "Modified"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(1, 70)
        table.setColumnWidth(2, 70)
        table.itemDoubleClicked.connect(self.open_file)

    def setup_image_viewer(self):
        self.image_viewer_screen = ImageViewerScreen(self)
        self.image_viewer_screen.setObjectName("image_viewer_screen")
        self.image_viewer_screen.setStyleSheet("background-color: black;")

        self.image_label = QLabel(self.image_viewer_screen)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: black; color: white;")

        self.image_back_btn = QPushButton("BACK", self.image_viewer_screen)
        self.image_back_btn.clicked.connect(self.back_to_file_explorer)

        self.window.stackedWidget.addWidget(self.image_viewer_screen)
        self.window.image_viewer_screen = self.image_viewer_screen
        self.layout_image_viewer()

    def layout_image_viewer(self):
        button_height = 44
        width = self.image_viewer_screen.width()
        height = self.image_viewer_screen.height()
        image_height = max(0, height - button_height)

        self.image_label.setGeometry(0, 0, width, image_height)
        self.image_back_btn.setGeometry(0, image_height, width, button_height)

    def show_ai_memory(self):
        self.select_category("files")

    def show_pictures(self):
        self.select_category("photos")

    def load_files(self, folder_path, title):
        self.window.fileexplorer_path_label.setText(str(folder_path))
        table = self.window.file_table
        table.setRowCount(0)

        if not folder_path.exists():
            self.add_message_row(f"{title} folder not found")
            return

        if not folder_path.is_dir():
            self.add_message_row(f"{title} is not a folder")
            return

        files = sorted(folder_path.iterdir(), key=lambda path: (path.is_file(), path.name.lower()))
        if not files:
            self.add_message_row(f"{title} folder is empty")
            return

        for row, file_path in enumerate(files):
            table.insertRow(row)
            name_item = QTableWidgetItem(file_path.name)
            name_item.setData(Qt.ItemDataRole.UserRole, str(file_path))
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, QTableWidgetItem(self.file_type(file_path)))
            table.setItem(row, 2, QTableWidgetItem(self.file_size(file_path)))
            table.setItem(row, 3, QTableWidgetItem(self.modified_time(file_path)))

    def add_message_row(self, message):
        table = self.window.file_table
        table.insertRow(0)
        table.setItem(0, 0, QTableWidgetItem(message))
        table.setItem(0, 1, QTableWidgetItem(""))
        table.setItem(0, 2, QTableWidgetItem(""))
        table.setItem(0, 3, QTableWidgetItem(""))

    def file_type(self, file_path):
        if file_path.is_dir():
            return "Folder"

        suffix = file_path.suffix.replace(".", "").upper()
        return suffix if suffix else "File"

    def file_size(self, file_path):
        if file_path.is_dir():
            return ""

        size = file_path.stat().st_size
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"

    def modified_time(self, file_path):
        modified = datetime.fromtimestamp(file_path.stat().st_mtime)
        return modified.strftime("%Y-%m-%d %H:%M")

    def open_file(self, item):
        path_item = self.window.file_table.item(item.row(), 0)
        if path_item is None:
            return

        file_path_text = path_item.data(Qt.ItemDataRole.UserRole)
        if not file_path_text:
            return

        file_path = Path(file_path_text)
        if file_path.suffix.lower() in self.image_extensions:
            self.open_image(file_path)

    def open_image(self, file_path):
        reader = QImageReader(str(file_path))
        reader.setAutoTransform(True)
        image = reader.read()
        self.window.switch_to("image_viewer_screen")

        if image.isNull():
            self.current_pixmap = None
            self.image_label.setText("Image cannot be opened")
            return

        self.current_pixmap = QPixmap.fromImage(image)
        self.image_label.setText("")
        self.layout_image_viewer()
        self.update_image()
        QTimer.singleShot(0, self.update_image)
        QTimer.singleShot(50, self.update_image)

    def update_image(self):
        if self.current_pixmap is None:
            return

        target_size = self.image_label.size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return

        canvas = QPixmap(target_size)
        canvas.fill(QColor("black"))

        scaled_image = self.current_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        x = (target_size.width() - scaled_image.width()) // 2
        y = (target_size.height() - scaled_image.height()) // 2

        painter = QPainter(canvas)
        painter.drawPixmap(x, y, scaled_image)
        painter.end()

        self.image_label.setPixmap(canvas)

    def back_to_file_explorer(self):
        self.current_pixmap = None
        self.image_label.clear()
        self.window.switch_to("fileexplorer_screen")

    def back_to_menu(self):
        state.ui_queue.put(("menu", None))
