from PyQt6.QtCore import QEvent, QObject, QRect, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPixmap, QRegion
from PyQt6.QtWidgets import (
    QAbstractButton, QAbstractScrollArea, QComboBox, QLabel, QLineEdit,
    QScrollArea, QSlider, QWidget,
)

from screens.menu_screen import menu_font


HEADER_HEIGHT = 26
CONTENT_RECT = QRect(26, 34, 429, 258)
CONTENT_HEIGHT = CONTENT_RECT.height()
CONTENT_SCALE_X = CONTENT_RECT.width() / 480
CONTENT_SCALE = CONTENT_HEIGHT / 320
NETWORK_RECT = QRect(101, 6, 20, 16)
CLOCK_RECT = QRect(387, 6, 42, 16)
FRAME_COLOR = QColor("#ff0000")


class GlobalStatusBar(QWidget):
    def __init__(self, window, status_service):
        super().__init__(window.centralWidget())
        self.setObjectName("globalStatusBar")
        self.setGeometry(0, 0, 480, HEADER_HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAccessibleName("NeuroDeck status")
        self.status_service = status_service
        self.status = status_service.snapshot
        canvas = getattr(window, "menu_canvas", None)
        self._backdrop = canvas.grab(QRect(0, 0, 480, HEADER_HEIGHT)) if canvas else QPixmap()
        status_service.changed.connect(self.set_status)
        self.set_status(self.status)

    def set_status(self, status):
        self.status = dict(status)
        self.setAccessibleDescription(
            f"{status['time_text']}. {status['network_tooltip']} Battery is decorative."
        )
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.fillRect(self.rect(), Qt.GlobalColor.black)
            if not self._backdrop.isNull():
                painter.drawPixmap(0, 0, self._backdrop)
            else:
                painter.setFont(menu_font(13, bold=True))
                painter.setPen(QColor("#ff0000"))
                painter.drawText(QRectF(12, 4, 140, 18), Qt.AlignmentFlag.AlignVCenter, "NeuroDeck")
            painter.fillRect(NETWORK_RECT, Qt.GlobalColor.black)
            painter.fillRect(CLOCK_RECT, Qt.GlobalColor.black)
            state = self.status["network_state"]
            dim = QColor("#48202c" if state == "offline" else "#12343f")
            for index, height in enumerate((4, 7, 10)):
                color = QColor("#16dbef") if index < self.status["network_bars"] else dim
                painter.fillRect(QRect(103 + index * 5, 20 - height, 3, height), color)
            painter.setFont(menu_font(14, bold=True))
            painter.setPen(QColor("#ff0000"))
            painter.drawText(QRectF(CLOCK_RECT), Qt.AlignmentFlag.AlignCenter, self.status["time_text"])
            painter.setPen(QPen(FRAME_COLOR, 1))
            painter.drawLine(8, HEADER_HEIGHT - 1, 471, HEADER_HEIGHT - 1)
        finally:
            painter.end()


class GlobalScreenShell(QWidget):
    def __init__(self, window):
        super().__init__(window.centralWidget())
        self.setObjectName("globalScreenShell")
        self.setGeometry(0, 0, 480, 320)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        canvas = getattr(window, "menu_canvas", None)
        self._backdrop = canvas.grab() if canvas else QPixmap()
        self._chrome_region = (
            QRegion(self.rect())
            - QRegion(CONTENT_RECT)
            - QRegion(QRect(0, 0, 480, HEADER_HEIGHT))
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setClipRegion(self._chrome_region)
            painter.fillRect(self.rect(), Qt.GlobalColor.black)
            if not self._backdrop.isNull():
                painter.drawPixmap(0, 0, self._backdrop)
        finally:
            painter.end()


class GlobalStatusController(QObject):
    def __init__(self, window, status_service):
        super().__init__(window)
        self.window = window
        self.status_service = status_service
        self.bar = GlobalStatusBar(window, status_service)
        self.shell = GlobalScreenShell(window)
        self._raising_chrome = False
        window.global_status_bar = self.bar
        window.global_screen_shell = self.shell
        self._compact_children(window.keyboard_frame)
        window.keyboard_frame.setGeometry(CONTENT_RECT)
        window.keyboard_frame.installEventFilter(self)
        window.stackedWidget.currentChanged.connect(self._page_changed)
        self._page_changed()
        self._raise_chrome()

    def _compact_children(self, parent):
        children = parent.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly)
        for child in children:
            if not child.objectName() or child.objectName().startswith("qt_"):
                continue
            layout = parent.layout()
            managed = layout is not None and layout.indexOf(child) >= 0
            if not managed:
                original = child.property("neurodeckStatusOriginalGeometry")
                if original is None:
                    original = QRect(child.geometry())
                    child.setProperty("neurodeckStatusOriginalGeometry", original)
                # Snapshot descendants before changing parent dimensions/layouts.
                self._compact_children_if_container(child)
                self._compact_metrics(child)
                child.setGeometry(
                    round(original.x() * CONTENT_SCALE_X), round(original.y() * CONTENT_SCALE),
                    max(1, round(original.width() * CONTENT_SCALE_X)), max(1, round(original.height() * CONTENT_SCALE)),
                )
            else:
                self._compact_children_if_container(child)
                self._compact_metrics(child)

    def _compact_metrics(self, widget):
        for key, getter, setter in (
            ("Minimum", widget.minimumSize, widget.setMinimumSize),
            ("Maximum", widget.maximumSize, widget.setMaximumSize),
        ):
            property_name = "neurodeckStatusOriginal" + key
            original = widget.property(property_name)
            if original is None:
                original = QSize(getter())
                widget.setProperty(property_name, original)
            width = original.width()
            height = original.height()
            setter(QSize(
                round(width * CONTENT_SCALE_X) if width < 16777215 else width,
                round(height * CONTENT_SCALE) if height < 16777215 else height,
            ))
        font = widget.property("neurodeckStatusOriginalFont")
        if font is None:
            font = QFont(widget.font())
            widget.setProperty("neurodeckStatusOriginalFont", font)
        scaled = QFont(font)
        if font.pixelSize() > 0:
            scaled.setPixelSize(max(1, round(font.pixelSize() * CONTENT_SCALE)))
        elif font.pointSizeF() > 0:
            scaled.setPointSizeF(font.pointSizeF() * CONTENT_SCALE)
        widget.setFont(scaled)

    def _compact_children_if_container(self, child):
        if isinstance(child, QScrollArea):
            content = child.widget()
            if content is not None:
                self._compact_children(content)
        elif not isinstance(child, (QAbstractButton, QAbstractScrollArea, QComboBox, QLabel, QLineEdit, QSlider)):
            self._compact_children(child)

    def _page_changed(self, *_args):
        page = self.window.stackedWidget.currentWidget()
        fullscreen = page is not None and bool(page.property("fullScreenContent"))
        if page is self.window.menu_screen or fullscreen:
            self.window.stackedWidget.setGeometry(0, 0, 480, 320)
        else:
            if page is not None and not page.property("statusBarResponsive"):
                self._compact_children(page)
            self.window.stackedWidget.setGeometry(CONTENT_RECT)
        self.bar.setVisible(not fullscreen)
        self.shell.setVisible(not fullscreen)
        self._raise_chrome()

    def eventFilter(self, obj, event):
        if obj is self.window.keyboard_frame and event.type() in (QEvent.Type.Show, QEvent.Type.ZOrderChange):
            self._raise_chrome()
        return False

    def _raise_chrome(self):
        if self._raising_chrome:
            return
        self._raising_chrome = True
        try:
            self.bar.raise_()
            self.shell.raise_()
            self.window.brightness_overlay.raise_()
        finally:
            self._raising_chrome = False
