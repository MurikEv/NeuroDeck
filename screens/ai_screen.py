from datetime import datetime
from pathlib import Path
import queue
import threading

from PyQt6.QtCore import QEvent, QObject, QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QAbstractTextDocumentLayout, QColor, QFont, QFontDatabase, QLinearGradient, QPainter, QPainterPath, QPalette, QPen, QRadialGradient, QTextCursor, QTextDocument
from PyQt6.QtWidgets import QAbstractButton, QAbstractScrollArea, QApplication, QFrame, QLabel, QListWidget, QPushButton, QTextBrowser, QWidget

from screens.menu_icons import draw_icon
from screens.menu_screen import neon_path, path_from, polygon
from services.ai_service import AIService
from services.groq_service import GroqService
from services.network_service import get_network_status
import state


AI_CYAN = QColor("#20e5f2")
AI_RED = QColor("#ff304b")
AI_DESIGN = (1500, 733)
AI_SIDEBAR_WIDTH = 330
AI_PANEL_LEFT = 396
AI_HEADER_HEIGHT = 90
_AI_FONTS = None


def ai_font(size, bold=False, body=False):
    global _AI_FONTS
    if _AI_FONTS is None:
        _AI_FONTS = {}
        folder = Path(__file__).resolve().parents[1] / "assets" / "fonts"
        for filename in ("BarlowCondensed-Regular.ttf", "BarlowCondensed-Bold.ttf", "NotoSans-Chat-Regular.ttf", "NotoSans-Chat-Bold.ttf"):
            font_id = QFontDatabase.addApplicationFont(str(folder / filename))
            families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
            if families:
                _AI_FONTS["body" if filename.startswith("Noto") else "display"] = families[0]
    font = QFont(_AI_FONTS.get("body" if body else "display", "DejaVu Sans"))
    font.setPixelSize(max(1, round(size)))
    font.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
    return font


def ai_text(painter, rect, text, size, color=AI_CYAN, bold=False, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter):
    painter.setFont(ai_font(size, bold))
    if bold and size >= 20:
        halo = QColor(color)
        halo.setAlpha(22)
        painter.setPen(halo)
        for dx, dy in ((-1.5, 0), (1.5, 0), (0, -1.5), (0, 1.5)):
            painter.drawText(rect.translated(dx, dy), alignment, text)
    painter.setPen(color)
    painter.drawText(rect, alignment, text)


def ai_texture(painter, rect):
    painter.save()
    painter.setClipRect(rect)
    painter.setPen(QPen(QColor(20, 127, 148, 8), 0.7))
    for y in range(round(rect.top()) + 2, round(rect.bottom()), 4):
        painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
    painter.restore()


def ai_marks(painter, x, y):
    for index in range(14):
        painter.fillRect(QRectF(x + index * 2.5, y, 0.8 if index % 3 else 1.6, 4), QColor("#1d8d9d"))
    painter.setPen(QPen(AI_CYAN, 1))
    painter.drawEllipse(QRectF(x + 40, y, 3, 4))
    painter.drawEllipse(QRectF(x + 46, y, 3, 4))


def ai_frame(painter, rect, accent=False, fill=QColor("#03131b")):
    x, y, width, height = rect.getRect()
    outline = path_from([
        (x + 18, y + 2), (x + width - 18, y + 2), (x + width - 5, y + 15),
        (x + width - 5, y + 62), (x + width - 1, y + 69),
        (x + width - 1, y + height - 15), (x + width - 16, y + height - 2),
        (x + 14, y + height - 2), (x + 2, y + height - 14),
        (x + 2, y + 75), (x + 7, y + 66), (x + 7, y + 15),
    ])
    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0, fill)
    gradient.setColorAt(1, QColor("#000305"))
    painter.fillPath(outline, gradient)
    neon_path(painter, outline, QColor("#ff4456" if accent else "#9e2636"), 1.8, glow=True)
    painter.save()
    painter.setBrush(Qt.BrushStyle.NoBrush)
    inner = path_from([
        (x + 21, y + 9), (x + width - 22, y + 9), (x + width - 13, y + 19),
        (x + width - 13, y + height - 20), (x + width - 23, y + height - 10),
        (x + 22, y + height - 10), (x + 12, y + height - 20), (x + 12, y + 20),
    ])
    neon_path(painter, inner, QColor("#168095"), 1, glow=False)
    ai_texture(painter, rect.adjusted(15, 13, -15, -13))
    painter.setPen(QPen(AI_CYAN, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for points in (
        [(x + 21, y + 28), (x + 21, y + 20), (x + 30, y + 20)],
        [(x + width - 23, y + 28), (x + width - 23, y + 20), (x + width - 32, y + 20)],
    ):
        painter.drawPolyline(polygon(points))
    painter.restore()


def ai_icon(painter, name, rect, color=AI_CYAN):
    painter.save()
    halo = QColor(color)
    halo.setAlpha(24)
    glow = QRadialGradient(rect.center(), max(rect.width(), rect.height()) * 0.85)
    glow.setColorAt(0, halo)
    halo.setAlpha(0)
    glow.setColorAt(1, halo)
    painter.fillRect(rect.adjusted(-15, -15, 15, 15), glow)
    painter.restore()
    if name == "ai":
        draw_icon(painter, "ai", rect, color)
        return
    painter.save()
    painter.translate(rect.x(), rect.y())
    painter.scale(rect.width() / 100, rect.height() / 100)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(color, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    if name == "chat":
        painter.drawPolyline(polygon([(73, 14), (18, 14), (11, 21), (11, 66), (23, 66), (23, 85), (44, 66), (73, 66), (79, 60), (79, 20), (73, 14)]))
        painter.drawPolyline(polygon([(86, 35), (94, 41), (94, 81), (84, 81), (84, 94), (68, 81), (51, 81)]))
        painter.drawLine(QPointF(29, 38), QPointF(57, 38))
    elif name == "history":
        painter.drawArc(QRectF(12, 12, 77, 77), 210 * 16, 285 * 16)
        painter.drawPolyline(polygon([(12, 16), (7, 39), (29, 31)]))
        painter.drawPolyline(polygon([(50, 28), (50, 52), (69, 52)]))
    elif name == "trash":
        painter.drawPolyline(polygon([(23, 28), (29, 90), (73, 90), (79, 28)]))
        painter.drawRoundedRect(QRectF(17, 18, 68, 10), 2, 2)
        painter.drawPolyline(polygon([(37, 16), (39, 7), (62, 7), (65, 16)]))
        for x in (42, 60):
            painter.drawLine(QPointF(x, 37), QPointF(x, 78))
    elif name == "back":
        painter.drawPolyline(polygon([(72, 16), (32, 50), (72, 84)]))
        painter.drawLine(QPointF(33, 50), QPointF(90, 50))
    elif name == "send":
        painter.setBrush(color)
        painter.drawPolygon(polygon([(8, 42), (91, 10), (67, 90), (45, 65), (33, 81), (33, 55)]))
        painter.setPen(QPen(QColor("#5e111d"), 3))
        painter.drawLine(QPointF(34, 55), QPointF(78, 23))
    elif name == "user":
        painter.setBrush(color)
        painter.drawEllipse(QRectF(37, 15, 27, 31))
        painter.drawRoundedRect(QRectF(24, 49, 53, 36), 13, 13)
    painter.restore()


class AISideButton(QAbstractButton):
    def __init__(self, title, icon, subtitle, parent):
        super().__init__(parent)
        self.icon = icon
        self.subtitle = subtitle
        self.setText(title)
        self.setAccessibleName(title)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if not self.isEnabled():
                painter.setOpacity(0.45)
            painter.scale(self.width() / 401, self.height() / 176)
            ai_frame(painter, QRectF(0, 0, 401, 176), self.isDown())
            ai_icon(painter, self.icon, QRectF(44, 41, 91, 90))
            ai_text(painter, QRectF(167, 39, 221, 60), self.text(), 42, bold=True)
            ai_text(painter, QRectF(168, 101, 212, 28), self.subtitle, 18)
            strip = QLinearGradient(18, 0, 382, 0)
            strip.setColorAt(0, QColor("#07303c"))
            strip.setColorAt(1, QColor("#02111a"))
            painter.fillRect(QRectF(18, 144, 365, 22), strip)
            ai_text(painter, QRectF(27, 144, 175, 23), "NEURODECK", 17)
            ai_marks(painter, 319, 154)
            ai_marks(painter, 322, 25)
        finally:
            painter.end()


class AIActionButton(QAbstractButton):
    def __init__(self, title, icon, parent, red=False):
        super().__init__(parent)
        self.icon = icon
        self.red = red
        self.setText(title)
        self.setAccessibleName(title)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.scale(self.width() / 205, self.height() / 64)
            rect = QRectF(3, 3, 199, 58)
            color = AI_RED if self.red or self.isDown() else AI_CYAN
            if self.isDown():
                color = color.lighter(145)
            if not self.isEnabled():
                color = color.darker(145)
            gradient = QLinearGradient(0, 0, 205, 64)
            gradient.setColorAt(0, QColor("#531525" if self.isDown() else "#24080d" if self.red else "#041b25"))
            gradient.setColorAt(1, QColor("#020508"))
            painter.setBrush(gradient)
            painter.setPen(QPen(color, 1.5))
            painter.drawRoundedRect(rect, 9, 9)
            if self.red:
                glow = QPainterPath()
                glow.addRoundedRect(rect, 9, 9)
                neon_path(painter, glow, color, 1.5, glow=True)
            ai_icon(painter, self.icon, QRectF(26, 14, 46, 40), color)
            ai_text(painter, QRectF(86, 9, 112, 43), self.text(), 33 if self.red else 27, color, bold=True)
        finally:
            painter.end()


class AIChatView(QAbstractScrollArea):
    def __init__(self, parent):
        super().__init__(parent)
        self.messages = []
        self._rows = []
        self._drag_start = None
        self.setObjectName("aiConversation")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("QAbstractScrollArea { background: transparent; border: none; } QScrollBar:vertical { background: #01090d; width: 3px; } QScrollBar::handle:vertical { background: #16d6e8; min-height: 14px; } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; } QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }")
        self.viewport().setAutoFillBackground(False)

    def set_messages(self, messages):
        self.messages = [dict(message) for message in messages]
        self.layout_messages()
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        self.viewport().update()

    def layout_messages(self):
        scale = self.parentWidget().height() / AI_DESIGN[1]
        width = self.viewport().width()
        padding = max(5, round(15 * scale))
        y = padding
        rows = []
        for message in self.messages:
            left = max(39, round((165 if message["role"] == "user" else 125) * width / 1004))
            time_width = max(29, round(75 * width / 1004))
            bubble_width = max(30, width - left - time_width - 3)
            document = QTextDocument()
            document.setDocumentMargin(0)
            document.setDefaultFont(ai_font(max(9, round(24 * scale)), body=True))
            document.setPlainText(message["text"])
            document.setTextWidth(max(20, bubble_width - 2 * padding))
            height = max(round(48 * scale), round(document.size().height()) + 2 * padding)
            rows.append((message, document, QRectF(left, y, bubble_width, height), padding))
            y += height + max(7, round(16 * scale))
        self._rows = rows
        self.verticalScrollBar().setRange(0, max(0, y - self.viewport().height()))
        self.verticalScrollBar().setPageStep(self.viewport().height())
        self.verticalScrollBar().setSingleStep(25)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.layout_messages()

    def viewportEvent(self, event):
        if event.type() == QEvent.Type.Paint:
            painter = QPainter(self.viewport())
            try:
                painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
                painter.fillRect(self.viewport().rect(), QColor("#01090e"))
                if not self.messages:
                    size = min(46, self.viewport().height() // 3)
                    ai_icon(painter, "ai", QRectF((self.viewport().width() - size) / 2, self.viewport().height() / 2 - size, size, size), QColor("#115265"))
                    ai_text(painter, QRectF(0, self.viewport().height() / 2 + 9, self.viewport().width(), 22), "START A CONVERSATION", 12, QColor("#347f8e"), alignment=Qt.AlignmentFlag.AlignCenter)
                painter.translate(0, -self.verticalScrollBar().value())
                for message, document, bubble, padding in self._rows:
                    if bubble.bottom() < self.verticalScrollBar().value() or bubble.top() > self.verticalScrollBar().value() + self.viewport().height():
                        continue
                    fill = QLinearGradient(bubble.topLeft(), bubble.bottomRight())
                    fill.setColorAt(0, QColor("#05232e"))
                    fill.setColorAt(1, QColor("#03141d"))
                    painter.setBrush(fill)
                    painter.setPen(QPen(QColor("#126378"), 0.8))
                    painter.drawRoundedRect(bubble, 3, 3)
                    assistant = message["role"] != "user"
                    scale_x = self.viewport().width() / 1004
                    scale_y = self.parentWidget().height() / 733
                    icon_x = max(3, round((26 if assistant else 64) * scale_x))
                    icon_width = max(12, round(45 * scale_x))
                    icon_height = max(14, round(55 * scale_y))
                    ai_icon(painter, "ai" if assistant else "user", QRectF(icon_x, bubble.y() + 2, icon_width, icon_height))
                    label_x = icon_x + icon_width + max(3, round(10 * scale_x))
                    label_height = max(16, round(32 * scale_y))
                    ai_text(painter, QRectF(label_x, bubble.y() + 2, max(10, bubble.x() - label_x - 2), label_height), "AI" if assistant else "YOU", max(8, round(22 * scale_y)), bold=True)
                    ai_text(painter, QRectF(bubble.right() + 4, bubble.y() + 2, max(25, round(72 * scale_x)), label_height), message["timestamp"].strftime("%H:%M"), max(8, round(20 * scale_y)), QColor("#1294aa"))
                    painter.save()
                    painter.translate(bubble.x() + padding, bubble.y() + padding)
                    context = QAbstractTextDocumentLayout.PaintContext()
                    context.palette.setColor(QPalette.ColorRole.Text, QColor("#e3f4f7"))
                    document.documentLayout().draw(painter, context)
                    painter.restore()
            finally:
                painter.end()
            return True
        return super().viewportEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition()
            self._scroll_start = self.verticalScrollBar().value()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        self.mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start is not None:
            self.verticalScrollBar().setValue(self._scroll_start - round(event.globalPosition().y() - self._drag_start.y()))
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_start = None
        event.accept()


class AIScreen(QWidget):
    def __init__(self, controller, parent):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("neurodeckAIScreen")
        self.new_chat_button = AISideButton("NEW CHAT", "chat", "START A CONVERSATION", self)
        self.history_button = AISideButton("HISTORY", "history", "THIS SESSION", self)
        self.back_button = AISideButton("MENU", "back", "RETURN TO NEURODECK", self)
        self.clear_chat_button = AISideButton("CLEAR", "trash", "CLEAR CONVERSATION", self)
        self.new_chat_button.setObjectName("aiNewChatButton")
        self.history_button.setObjectName("aiHistoryButton")
        self.back_button.setObjectName("aiBackButton")
        self.clear_chat_button.setObjectName("aiClearChatButton")
        self.new_chat_button.clicked.connect(controller.new_chat)
        self.history_button.clicked.connect(controller.show_history)
        self.back_button.clicked.connect(controller.back_to_menu)
        self.clear_chat_button.clicked.connect(controller.clear_chat)
        self.send_button = AIActionButton("SEND", "send", self, red=True)
        self.send_button.setObjectName("ai_send_btn")
        self.clear_input_button = AIActionButton("CLEAR", "trash", self)
        self.clear_input_button.setObjectName("ai_clear_btn")
        self.send_button.clicked.connect(controller.send_message)
        self.clear_input_button.clicked.connect(controller.clear_input)
        self.chat_view = AIChatView(self)
        self.input = controller.window.ai_input
        self.input.setParent(self)
        self.input.setAcceptRichText(False)
        self.input.setPlaceholderText("")
        self.input.setStyleSheet("QTextEdit { background: transparent; color: #e3f4f7; border: none; padding: 0; selection-background-color: #166779; }")
        self.input.document().setDocumentMargin(0)
        self.input.show()
        self.char_count = QLabel("0 / 2000", self)
        self.char_count.setObjectName("aiPromptCounter")
        self.char_count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.char_count.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.char_count.setStyleSheet("color: #18bfce; background: transparent;")
        self.setup_history()

    def setup_history(self):
        self.history_overlay = QFrame(self)
        self.history_overlay.setObjectName("aiHistoryOverlay")
        self.history_overlay.setStyleSheet("QFrame#aiHistoryOverlay { background: #020d14; border: 1px solid #16859a; border-radius: 5px; } QLabel { color: #20e5f2; background: transparent; border: none; } QListWidget, QTextBrowser { color: #d2f0f5; background: #04141d; border: 1px solid #124b5e; } QListWidget::item { padding: 8px; } QListWidget::item:selected { background: #124a5b; } QPushButton { color: #20e5f2; background: #06202b; border: 1px solid #16859a; border-radius: 3px; } QPushButton:pressed { background: #184f5c; }")
        self.history_title = QLabel("CHAT HISTORY", self.history_overlay)
        self.history_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.history_list = QListWidget(self.history_overlay)
        self.history_list.itemClicked.connect(self.controller.open_history)
        self.history_text = QTextBrowser(self.history_overlay)
        self.history_text.setOpenExternalLinks(False)
        self.history_text.hide()
        self.history_empty = QLabel("No conversations yet.", self.history_overlay)
        self.history_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.history_back_button = QPushButton("BACK", self.history_overlay)
        self.history_back_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.history_back_button.clicked.connect(self.controller.close_history)
        self.history_overlay.hide()

    def place(self, widget, x, y, width, height):
        widget.setGeometry(round(x * self.width() / 1500), round(y * self.height() / 733), round(width * self.width() / 1500), round(height * self.height() / 733))

    def resizeEvent(self, event):
        for button, y, height in (
            (self.new_chat_button, 0, 176), (self.history_button, 192, 176),
            (self.back_button, 382, 174), (self.clear_chat_button, 568, 163),
        ):
            self.place(button, 0, y, AI_SIDEBAR_WIDTH, height)
        self.place(self.chat_view, AI_PANEL_LEFT + 19, AI_HEADER_HEIGHT + 6, 1472 - AI_PANEL_LEFT, 580 - AI_HEADER_HEIGHT)
        self.place(self.input, AI_PANEL_LEFT + 42, 648, 1210 - AI_PANEL_LEFT, 68)
        self.place(self.char_count, 1110, 604, 150, 32)
        self.place(self.send_button, 1282, 595, 205, 64)
        self.place(self.clear_input_button, 1282, 670, 205, 54)
        scale = self.height() / 733
        self.input.setFont(ai_font(max(9, round(24 * scale)), body=True))
        self.char_count.setFont(ai_font(max(8, round(21 * scale))))
        self.place(self.history_overlay, AI_PANEL_LEFT + 16, AI_HEADER_HEIGHT + 7, 1472 - AI_PANEL_LEFT, 720 - AI_HEADER_HEIGHT)
        width, height = self.history_overlay.width(), self.history_overlay.height()
        self.history_title.setGeometry(8, 5, width - 16, 26)
        self.history_title.setFont(ai_font(17, bold=True))
        for widget in (self.history_list, self.history_text, self.history_empty):
            widget.setGeometry(10, 36, width - 20, max(30, height - 83))
            widget.setFont(ai_font(11, body=True))
        self.history_back_button.setGeometry(10, height - 39, width - 20, 30)
        self.history_back_button.setFont(ai_font(15, bold=True))
        self.chat_view.layout_messages()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(self.rect(), QColor("#000407"))
            painter.scale(self.width() / 1500, self.height() / 733)
            rail = QPainterPath(QPointF(AI_PANEL_LEFT - 29, 4))
            rail.lineTo(AI_PANEL_LEFT - 29, 730)
            neon_path(painter, rail, QColor("#ff3448"), 5)
            neon_path(painter, rail, QColor("#ff9b96"), 1.4, glow=False)
            ai_frame(painter, QRectF(AI_PANEL_LEFT, 0, 1499 - AI_PANEL_LEFT, 733))
            ai_icon(painter, "ai", QRectF(AI_PANEL_LEFT + 34, 8, 72, 74))
            ai_text(painter, QRectF(AI_PANEL_LEFT + 124, 3, 190, 45), "AI", 40, bold=True)
            ai_text(painter, QRectF(AI_PANEL_LEFT + 125, 52, 400, 28), "ARTIFICIAL INTELLIGENCE ASSISTANT", 18)
            painter.setPen(QPen(QColor("#146d80"), 1))
            painter.drawLine(QPointF(AI_PANEL_LEFT + 19, AI_HEADER_HEIGHT), QPointF(1487, AI_HEADER_HEIGHT))
            ai_marks(painter, 1410, 14)
            badge = QRectF(1200, 27, 282, 37)
            painter.setBrush(QColor("#03141c"))
            painter.setPen(QPen(QColor("#13a4b8"), 1))
            painter.drawRoundedRect(badge, 5, 5)
            status = self.controller.status_text
            dot = QColor("#00d88d" if status == "ONLINE" else "#e5af42" if status in ("THINKING...", "CONNECTING") else "#eb445e")
            painter.setBrush(dot)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(1230, 45), 8, 8)
            ai_text(painter, QRectF(1254, 27, 220, 37), status, 25, dot, bold=True)
            composer = QRectF(AI_PANEL_LEFT + 16, 591, 1259 - AI_PANEL_LEFT, 136)
            ai_frame(painter, composer)
            painter.setPen(QPen(AI_CYAN, 1))
            painter.drawLine(QPointF(AI_PANEL_LEFT + 26, 637), QPointF(1264, 637))
            ai_text(painter, QRectF(AI_PANEL_LEFT + 47, 605, 300, 30), "PROMPT", 23, bold=True)
        finally:
            painter.end()


class AIController(QObject):
    def __init__(self, window, ai_service=None):
        super().__init__(window)
        self.window = window
        self.messages = []
        self.histories = []
        self.pending = False
        self._closed = False
        self.service_error = ""
        try:
            self.ai_service = ai_service if ai_service is not None else AIService()
        except Exception:
            self.ai_service = None
            self.service_error = "AI service is not configured."
        self.model_name = getattr(self.ai_service, "model_name", GroqService.MODEL_NAME)
        self.status_text = "CONNECTING"
        self._status_source = None
        self.response_queue = queue.Queue()
        self.setup_screen()
        self.response_queue_timer = QTimer(self)
        self.response_queue_timer.timeout.connect(self.process_response_queue)
        self.response_queue_timer.start(100)
        shared = getattr(window, "status_service", None) or getattr(getattr(window, "menu_controller", None), "status_service", None)
        self._status_source = shared
        self._owns_status_timer = shared is None
        if shared is not None:
            self.status_timer = shared.timer
            shared.changed.connect(self.update_status_label)
            self.update_status_label(shared.snapshot)
        else:
            self.status_timer = QTimer(self)
            self.status_timer.timeout.connect(self.update_status_label)
            self.status_timer.start(1000)
            self.update_status_label()
        window.ai_input.textChanged.connect(self.sync_input_state)
        self.sync_input_state()
        QApplication.instance().aboutToQuit.connect(self.close)

    def setup_screen(self):
        page = self.window.ai_screen
        for child in page.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
            if child is not self.window.ai_input:
                child.hide()
        for name in ("ai_send_btn", "ai_clear_btn", "aiBackButton"):
            getattr(self.window, name).setObjectName("legacy_" + name)
        page.setProperty("statusBarResponsive", True)
        page.setProperty("englishChrome", True)
        self.view = AIScreen(self, page)
        self.view.setGeometry(page.rect())
        self.window.ai_send_btn = self.view.send_button
        self.window.ai_clear_btn = self.view.clear_input_button
        self.window.aiBackButton = self.view.back_button
        self.window.aiNewChatButton = self.view.new_chat_button
        self.window.aiHistoryButton = self.view.history_button
        self.window.aiClearChatButton = self.view.clear_chat_button
        page.installEventFilter(self)
        self.view.show()

    def eventFilter(self, obj, event):
        if obj is self.window.ai_screen:
            if event.type() == QEvent.Type.Resize:
                self.view.setGeometry(obj.rect())
            elif event.type() == QEvent.Type.Hide:
                self.close_history()
        return False

    def update_status_label(self, snapshot=None):
        if snapshot is None and self._status_source is not None:
            snapshot = self._status_source.snapshot
        if self.pending:
            self.status_text = "THINKING..."
        elif self.ai_service is None:
            self.status_text = "NOT CONFIGURED"
        else:
            if not isinstance(snapshot, dict):
                network = get_network_status()
                online = network.get("online", False)
                checking = network.get("last_checked_at") is None
            else:
                online = snapshot.get("network_state") == "online"
                checking = snapshot.get("network_state") == "checking"
            self.status_text = "CONNECTING" if checking else "ONLINE" if online else "NO CONNECTION"
        self.window.ai_status_label.setText(self.status_text)
        self.view.update()

    def sync_input_state(self):
        text = self.window.ai_input.toPlainText()
        state.ai_input_text = text
        self.view.char_count.setText(f"{len(text)} / 2000")
        self.view.char_count.setStyleSheet("background: transparent; color: " + ("#ff5269;" if len(text) > 2000 else "#18bfce;"))
        self.window.ai_send_btn.setEnabled(self.ai_service is not None and not self.pending and 0 < len(text.strip()) and len(text) <= 2000)
        self.view.new_chat_button.setEnabled(not self.pending)
        self.view.clear_chat_button.setEnabled(not self.pending)

    def append_message(self, role, text):
        self.messages.append({"role": role, "text": str(text), "timestamp": datetime.now()})
        cursor = self.window.ai_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(("You: " if role == "user" else "AI: ") + str(text) + "\n")
        self.view.chat_view.set_messages(self.messages)

    def run_ai_request(self, prompt):
        try:
            answer = self.ai_service.ask_ai(prompt)
        except Exception as error:
            answer = f"Error: {error}"
        self.response_queue.put(str(answer))

    def process_response_queue(self):
        if self._closed:
            return
        try:
            answer = self.response_queue.get_nowait()
        except queue.Empty:
            return
        self.append_message("assistant", answer)
        self.pending = False
        self.sync_input_state()
        self.update_status_label()

    def send_message(self):
        prompt = self.window.ai_input.toPlainText().strip()
        if self._closed or self.pending or self.ai_service is None or not prompt or len(self.window.ai_input.toPlainText()) > 2000:
            return
        keyboard = getattr(self.window, "keyboard_controller", None)
        if keyboard is not None:
            keyboard.close_keyboard()
        self.close_history()
        self.append_message("user", prompt)
        self.pending = True
        self.window.ai_input.clear()
        self.sync_input_state()
        self.update_status_label()
        try:
            threading.Thread(target=self.run_ai_request, args=(prompt,), daemon=True).start()
        except RuntimeError as error:
            self.response_queue.put(f"Error: {error}")
            self.process_response_queue()

    def clear_input(self):
        self.window.ai_input.clear()

    def clear_chat(self):
        if self.pending:
            return
        self.messages.clear()
        self.window.ai_output.clear()
        self.view.chat_view.set_messages(self.messages)
        if self.ai_service is not None:
            self.ai_service.clear_memory()
        self.close_history()

    def new_chat(self):
        if self.pending:
            return
        if self.messages:
            self.histories.append([dict(message) for message in self.messages])
            self.histories = self.histories[-20:]
        self.clear_chat()
        self.clear_input()

    def show_history(self):
        keyboard = getattr(self.window, "keyboard_controller", None)
        if keyboard is not None:
            keyboard.close_keyboard()
        self._history_items = self.histories + ([list(self.messages)] if self.messages else [])
        self.view.history_list.clear()
        for records in self._history_items:
            prompt = next((record["text"] for record in records if record["role"] == "user"), records[0]["text"])
            self.view.history_list.addItem(records[0]["timestamp"].strftime("%H:%M") + "  " + prompt.replace("\n", " ")[:90])
        self.view.history_list.setVisible(bool(self._history_items))
        self.view.history_empty.setVisible(not self._history_items)
        self.view.history_text.hide()
        self.view.history_overlay.show()
        self.view.history_overlay.raise_()

    def open_history(self, item):
        index = self.view.history_list.row(item)
        if index < 0 or index >= len(self._history_items):
            return
        records = self._history_items[index]
        text = "\n\n".join(("YOU" if record["role"] == "user" else "AI") + "  " + record["timestamp"].strftime("%H:%M") + "\n" + record["text"] for record in records)
        self.view.history_text.setPlainText(text)
        self.view.history_list.hide()
        self.view.history_text.show()

    def close_history(self):
        self.view.history_overlay.hide()

    def back_to_menu(self):
        self.close_history()
        state.ui_queue.put(("menu", None))

    def close(self):
        self._closed = True
        self.response_queue_timer.stop()
        if self._owns_status_timer:
            self.status_timer.stop()

