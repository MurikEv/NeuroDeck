from state import stop_camera
import state
import cv2
import sys

def camera(path="project_data"):
    
    # state.hide_frames()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Camera not available")

    capture_requested = False
    quit_requested = False

    def request_capture():
        nonlocal capture_requested
        capture_requested = True
    
    while True:
        if stop_camera.is_set():
            cap.release()
            cv2.destroyAllWindows()
            return None

        cap.grab()
        if stop_camera.is_set():
            cap.release()
            cv2.destroyAllWindows()
            return None
        ret, frame = cap.retrieve()
        if not ret:
            continue
        cv2.imshow("VisionCalc Camera", frame)

        if capture_requested:
            cv2.imwrite(path, frame)
            break

        if quit_requested:
            cap.release()
            cv2.destroyAllWindows()
            sys.exit()

        cv2.waitKey(1)
    
    cap.release()
    cv2.destroyAllWindows()

    return path