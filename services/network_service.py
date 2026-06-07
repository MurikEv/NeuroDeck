import socket
import threading
import time

connection = False
monitor_started = False


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
    global monitor_started

    if monitor_started:
        return

    threading.Thread(target=monitor_internet, daemon=True).start()

    monitor_started = True