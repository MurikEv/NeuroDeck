import socket
import threading
import time

connection = False
_monitor_started = False


def check_internet():
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=2)
        return True
    except OSError:
        return False

def monitor_internet():
    global connection

    while True:
        connection = check_internet()
        time.sleep(5)

def is_online():
    return connection


def start_network_monitoring():
    global _monitor_started

    if _monitor_started:
        return

    network_thread = threading.Thread(target=monitor_internet, daemon=True)
    network_thread.start()
    _monitor_started = True