from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QEvent, QObject, QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QImageReader, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QWidget,
)

from screens.menu_icons import draw_icon
from screens.menu_screen import menu_font, path_from, polygon
import state


EXPLORER_CYAN = QColor("#20e5f2")


def explorer_gradient(rect, color):
    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0, QColor(color))
    gradient.setColorAt(1, QColor("#000000"))
    return gradient


def explorer_neon(painter, path, color, width=2.2):
    painter.save()
    painter.setBrush(Qt.BrushStyle.NoBrush)
    bounds = path.boundingRect()
    for extra, alpha in ((10, 7), (5, 18), (2, 42), (0, 255)):
        gradient = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        for position, shade in (
            (0, QColor(color).lighter(145)), (0.38, QColor(color)),
            (0.72, QColor(color).darker(170)), (1, QColor(color).darker(280)),
        ):
            shade.setAlpha(alpha)
            gradient.setColorAt(position, shade)
        painter.setPen(QPen(QBrush(gradient), width + extra, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)
    painter.restore()


def explorer_icon(painter, name, rect, color):
    if name == "files":
        draw_icon(painter, "files", rect, color)
        return
    painter.save()
    painter.translate(rect.x(), rect.y())
    painter.scale(rect.width() / 100, rect.height() / 100)
    painter.setPen(QPen(color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if name == "photos":
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
        painter.drawEllipse(QRectF(17, 14, 66, 22))
        painter.drawArc(QRectF(17, 33, 66, 22), 180 * 16, 180 * 16)
        painter.drawArc(QRectF(17, 52, 66, 22), 180 * 16, 180 * 16)
        painter.drawLine(QPointF(17, 25), QPointF(17, 63))
        painter.drawLine(QPointF(83, 25), QPointF(83, 63))
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
        self.setText(text)
        self.setAccessibleName(text)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.toggled.connect(self.update)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            scale = self.height() / 104
            painter.scale(scale, scale)
            width = self.width() / scale
            active = self.isChecked() or self.isDown()
            shape = path_from([(9, 2), (width - 10, 2), (width - 2, 10), (width - 2, 94), (width - 11, 102), (2, 102), (2, 11)])
            gradient = QLinearGradient(0, 0, 0, 104)
            gradient.setColorAt(0, QColor("#1b0b13" if active else "#04141c"))
            gradient.setColorAt(1, QColor("#000000"))
            painter.fillPath(shape, gradient)
            border = QColor("#ff3b52" if active else "#18d8ed" if self.isEnabled() else "#168b9e")
            explorer_neon(painter, shape, border)
            color = EXPLORER_CYAN if self.isEnabled() else QColor("#27818e")
            explorer_icon(painter, self.icon, QRectF(19, 27, 52, 52), color)
            font = menu_font(31 if self.navigation else 40, bold=True)
            painter.setFont(font)
            text_width = painter.fontMetrics().horizontalAdvance(self.text())
            available = width - 88
            if text_width > available:
                font.setStretch(max(55, int(available / text_width * 100)))
                painter.setFont(font)
            painter.setPen(color)
            painter.drawText(QRectF(82, 17, available, 69), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text())
            painter.setPen(QPen(QColor("#176575"), 1))
            painter.drawLine(QPointF(84, 82), QPointF(131, 82))
        finally:
            painter.end()


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
        self.back_button = ExplorerButton("MENU", "back", self)
        self.back_button.setObjectName("explorer_menu_button")
        self.back_button.clicked.connect(controller.back_to_menu)
        self.actions = {}
        for action, title, icon in (
            ("sort", "SORT", "sort"), ("open", "OPEN", "file"),
            ("delete", "DELETE", "trash"), ("favorite", "FAVORITE", "favorites"),
            ("share", "SHARE", "share"),
        ):
            button = ExplorerButton(title, icon, self)
            button.setObjectName("explorer_" + action + "_button")
            button.setEnabled(False)
            self.actions[action] = button

    def place(self, widget, x, y, width, height):
        widget.setGeometry(
            round(x * self.width() / 1200), round(y * self.height() / 720),
            round(width * self.width() / 1200), round(height * self.height() / 720),
        )

    def resizeEvent(self, event):
        for index, button in enumerate(self.navigation.values()):
            self.place(button, 0, 6 + index * 110, 212, 104)
        self.place(self.back_button, 0, 456, 212, 68)
        self.place(self.actions["sort"], 686, 13, 166, 62)
        self.place(self.actions["open"], 901, 466, 133, 68)
        self.place(self.actions["delete"], 1047, 466, 133, 68)
        self.place(self.actions["favorite"], 901, 548, 279, 68)
        self.place(self.actions["share"], 901, 630, 279, 68)
        super().resizeEvent(event)

    def panel(self, painter, rect, color, fill):
        x, y, width, height = rect.getRect()
        shape = path_from([(x + 10, y), (x + width - 10, y), (x + width, y + 10), (x + width, y + height - 10), (x + width - 10, y + height), (x + 10, y + height), (x, y + height - 10), (x, y + 10)])
        painter.fillPath(shape, explorer_gradient(rect, fill))
        edge = QColor("#ff354e" if color.red() > color.green() else "#18d8ed")
        explorer_neon(painter, shape, edge)
        if width >= 250 and height >= 160:
            painter.save()
            accent = QColor(edge).lighter(140)
            accent.setAlpha(175)
            painter.setPen(QPen(accent, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for corner_x, corner_y, dx, dy in (
                (x + 13, y + 13, 1, 1), (x + width - 13, y + 13, -1, 1),
                (x + 13, y + height - 13, 1, -1),
                (x + width - 13, y + height - 13, -1, -1),
            ):
                painter.drawPolyline(polygon([
                    (corner_x, corner_y + dy * 19), (corner_x, corner_y),
                    (corner_x + dx * 19, corner_y),
                ]))
            painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
            painter.fillRect(self.rect(), explorer_gradient(QRectF(self.rect()), QColor("#01070b")))
            painter.scale(self.width() / 1200, self.height() / 720)
            divider = QPainterPath(QPointF(225, 5))
            divider.lineTo(225, 710)
            explorer_neon(painter, divider, QColor("#ff3049"), width=1.6)
            self.panel(painter, QRectF(238, 5, 629, 80), QColor("#175362"), QColor("#030e14"))
            explorer_icon(painter, "files", QRectF(257, 20, 56, 53), EXPLORER_CYAN)
            painter.setFont(menu_font(47, bold=True))
            painter.setPen(EXPLORER_CYAN)
            painter.drawText(QRectF(336, 15, 340, 59), Qt.AlignmentFlag.AlignVCenter, "EXPLORER")
            main = QRectF(238, 99, 629, 608)
            self.panel(painter, main, QColor("#194c5b"), QColor("#031018"))
            painter.setPen(QPen(QColor(22, 93, 108, 45), 1))
            for x in (447, 657):
                painter.drawLine(QPointF(x, 110), QPointF(x, 696))
            for y in (303, 505):
                painter.drawLine(QPointF(248, y), QPointF(857, y))
            active = next(key for key, button in self.navigation.items() if button.isChecked())
            explorer_icon(painter, active, QRectF(493, 270, 117, 111), QColor("#25909f"))
            painter.setPen(QColor("#86cdd4"))
            painter.setFont(menu_font(32, bold=True))
            painter.drawText(QRectF(260, 403, 585, 51), Qt.AlignmentFlag.AlignCenter, "NO FILES DISPLAYED")
            painter.setFont(menu_font(24))
            painter.setPen(QColor("#4c8190"))
            painter.drawText(QRectF(260, 462, 585, 39), Qt.AlignmentFlag.AlignCenter, "Your files will appear here.")
            painter.setFont(menu_font(19))
            painter.drawText(QRectF(257, 653, 587, 32), Qt.AlignmentFlag.AlignCenter, "VISUAL PREVIEW")
            self.panel(painter, QRectF(884, 5, 313, 702), QColor("#8e2336"), QColor("#030d13"))
            self.panel(painter, QRectF(901, 22, 279, 275), QColor("#1a6473"), QColor("#04151e"))
            explorer_icon(painter, "photos", QRectF(992, 103, 97, 93), QColor("#185e70"))
            painter.setPen(QColor("#4c8b97"))
            painter.setFont(menu_font(23, bold=True))
            painter.drawText(QRectF(913, 225, 255, 44), Qt.AlignmentFlag.AlignCenter, "NO SELECTION")
            painter.setFont(menu_font(29, bold=True))
            painter.setPen(EXPLORER_CYAN)
            painter.drawText(QRectF(904, 315, 278, 48), Qt.AlignmentFlag.AlignVCenter, "FILE DETAILS")
            painter.setFont(menu_font(23))
            painter.setPen(QColor("#578997"))
            painter.drawText(QRectF(905, 371, 269, 36), Qt.AlignmentFlag.AlignVCenter, "Select a file to view")
            painter.drawText(QRectF(905, 405, 269, 36), Qt.AlignmentFlag.AlignVCenter, "its information.")
            self.panel(painter, QRectF(1, 542, 211, 165), QColor("#175362"), QColor("#031018"))
            explorer_icon(painter, "storage", QRectF(17, 567, 48, 55), QColor("#2097a8"))
            painter.setFont(menu_font(29, bold=True))
            painter.setPen(EXPLORER_CYAN)
            painter.drawText(QRectF(76, 565, 130, 53), Qt.AlignmentFlag.AlignVCenter, "STORAGE")
            painter.setFont(menu_font(24))
            painter.setPen(QColor("#4c8190"))
            painter.drawText(QRectF(17, 636, 181, 45), Qt.AlignmentFlag.AlignCenter, "NOT LOADED")
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
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.ai_memory_path = Path("data/ai_memory")
        self.pictures_path = Path("data/camera_pictures")
        self.current_pixmap = None

        self.setup_table()
        self.setup_image_viewer()
        self.window.ai_memory_btn.clicked.connect(self.show_ai_memory)
        self.window.cam_pictures_btn.clicked.connect(self.show_pictures)
        self.window.back_to_menu_btn.clicked.connect(self.back_to_menu)
         
        self.setup_visual_screen()

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
        self.load_files(self.ai_memory_path, "AI Memory")

    def show_pictures(self):
        self.load_files(self.pictures_path, "Pictures")

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
