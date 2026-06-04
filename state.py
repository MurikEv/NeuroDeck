import threading
import queue

ui_queue = queue.Queue()
stop_camera = threading.Event()
main_window = None

ai_input_text = ""