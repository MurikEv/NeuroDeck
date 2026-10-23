from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication

from services.menu_status import read_menu_status


class ApplicationStatus(QObject):
    changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._snapshot = {}
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh)
        self.refresh()
        self.timer.start()
        QApplication.instance().aboutToQuit.connect(self.close)

    @property
    def snapshot(self):
        return dict(self._snapshot)

    def refresh(self, now=None, network_status=None):
        snapshot = read_menu_status(now=now, network_status=network_status)
        if snapshot != self._snapshot:
            self._snapshot = snapshot
            self.changed.emit(dict(snapshot))

    def close(self):
        self.timer.stop()
