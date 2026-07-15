import socket
import threading
from datetime import datetime

connection = False
monitor_started = False
last_checked_at = None
last_error = None
_monitor_thread = None
_stop_event = threading.Event()


def check_internet():
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=2):
            return True, None
    except OSError as error:
        return False, str(error)


def monitor_internet(interval=5):
    global connection, last_checked_at, last_error, monitor_started

    while not _stop_event.is_set():
        connection, last_error = check_internet()
        last_checked_at = datetime.now()
        _stop_event.wait(interval)

    monitor_started = False


def is_online():
    return connection


def get_network_status():
    return {
        "online": connection,
        "last_checked_at": last_checked_at,
        "last_error": last_error,
        "monitor_started": monitor_started,
    }


def start_network_monitoring():
    global monitor_started, _monitor_thread

    if monitor_started:
        return

    _stop_event.clear()
    _monitor_thread = threading.Thread(target=monitor_internet, daemon=True)
    _monitor_thread.start()
    monitor_started = True


def stop_network_monitoring():
    global _monitor_thread, monitor_started

    _stop_event.set()
    if _monitor_thread is not None and _monitor_thread.is_alive():
        _monitor_thread.join(timeout=1)

    _monitor_thread = None
    monitor_started = False
