from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QImageReader, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QWidget,
)

import state


class ImageViewerScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def resizeEvent(self, event):
        self.controller.layout_image_viewer()
        self.controller.update_image()
        super().resizeEvent(event)


class FileExplorerController:
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}

    def __init__(self, window):
        self.window = window
        self.ai_memory_path = Path("data/ai_memory")
        self.pictures_path = Path("data/camera_pictures")
        self.current_pixmap = None

        self.setup_table()
        self.setup_image_viewer()
        self.window.ai_memory_btn.clicked.connect(self.show_ai_memory)
        self.window.cam_pictures_btn.clicked.connect(self.show_pictures)
        self.window.back_to_menu_btn.clicked.connect(self.back_to_menu)
        self.show_ai_memory()

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
