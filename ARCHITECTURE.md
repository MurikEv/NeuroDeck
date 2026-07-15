# NeuroDeck Architecture

This document describes the architecture that exists in the repository today. Planned improvements are listed separately in `TASKS.md`.

## 1. System Overview

NeuroDeck is a single-window PyQt6 application. `MainWindow` loads one Qt Designer file containing the primary pages, and a `QStackedWidget` selects the visible page.

The current application is divided into four practical areas:

1. Application bootstrap and routing in `main.py` and `main_window.py`.
2. Screen-specific interaction modules in `screens/`.
3. External and reusable operations in `services/`.
4. Small shared state in `state.py`.

This is a screen-oriented architecture, not a strict MVC implementation.

## 2. Project Structure

```text
NeuroDeck/
|-- main.py
|-- main_window.py
|-- state.py
|-- requirements.txt
|-- README.md
|-- ARCHITECTURE.md
|-- TASKS.md
|
|-- screens/
|   |-- main_window.ui
|   |-- menu_screen.py
|   |-- keyboard_controller.py
|   |-- ai_screen.py
|   |-- calculator_screen.py
|   |-- camera_screen.py
|   `-- file_explorer_screen.py
|
|-- services/
|   |-- ai_service.py
|   |-- groq_service.py
|   |-- camera_service.py
|   `-- network_service.py
|
|-- assets/
|   |-- background/
|   `-- btn_photo/
|
`-- data/
    |-- ai_memory/
    `-- camera_pictures/
```

## 3. Naming and Folder Meaning

The `screens/` directory is a feature-oriented UI layer. It contains both the Qt Designer view and Python modules associated with individual screens.

The Python classes use the `Controller` suffix when they do not represent a QWidget themselves. A controller receives the main window, connects signals, handles user interaction, calls services, and updates existing widgets.

Examples:

- `screens/ai_screen.py` contains `AIController`.
- `screens/camera_screen.py` contains `CameraController` and `CameraWorker`.
- `screens/file_explorer_screen.py` contains `FileExplorerController`.
- `ImageViewerScreen` keeps the `Screen` suffix because it is an actual QWidget.

Instance names follow the same convention:

```python
menu_controller
keyboard_controller
ai_controller
calculator_controller
camera_controller
file_explorer_controller
```

Names loaded from `main_window.ui`, such as `menu_screen` and `fileexplorer_screen`, remain view object names.

## 4. Bootstrap and Routing

### `main.py`

`main.py` currently performs all startup work at module level:

- Creates `QApplication` and `MainWindow`.
- Creates each screen controller.
- Stores controller references on `MainWindow`.
- Starts network monitoring.
- Registers the global `Q` hotkey.
- Polls `state.ui_queue` with a Qt timer.
- Switches the active page according to queued actions.

Current routed actions are:

- `menu`
- `calculator`
- `camera`
- `ai`
- `file_explorer`

Browser, Notepad, Messenger, and Settings actions are produced by the menu but are not handled by the router yet.

### `main_window.py`

`MainWindow` is the root QWidget owner. It:

- Loads `screens/main_window.ui`.
- Hides the on-screen keyboard initially.
- Selects the menu page.
- Stores controller references.
- Forwards key events to the active Menu or Calculator controller.
- Stops the camera controller during window close.

`switch_to(screen_name)` resolves a QWidget by its Qt object name and selects it in the stacked widget.

## 5. Screen Modules

### Menu

`MenuController` owns the menu selection coordinates and card metadata. It applies highlight styles, handles arrow keys and Return, and queues mode actions.

It does not perform camera, AI, or file operations directly.

### On-Screen Keyboard

`KeyboardController` is shared UI behavior rather than a standalone page. It mirrors text between the keyboard input widget and the active AI input widget, handles virtual key buttons, and shows or hides the keyboard frame.

The current implementation supports only the AI text input.

### Calculator

`CalculatorController` connects calculator buttons, stores the expression string, updates the display, and evaluates the expression.

Expression evaluation is currently inside the controller and uses `eval()`. A future parser or calculator service should own restricted expression evaluation.

### AI

`AIController` connects Send and Clear actions, owns the response queue and Qt polling timers, starts background requests, and updates the chat widgets.

It delegates online/offline selection to `AIService`.

### Camera

`CameraController` owns screen-level camera state and preview behavior. `CameraWorker` is a `QThread` that repeatedly asks `CameraService` for frames and emits them to the UI thread.

Photo copying and saving are delegated to `CameraService`, although saving is currently initiated from the UI thread.

### File Explorer

`FileExplorerController` loads directory entries into the table and opens supported images. It also creates `ImageViewerScreen` programmatically and adds it to the existing stacked widget.

Directory scanning and image decoding currently run in the UI thread.

## 6. Services

### `AIService`

`AIService` selects between online and offline behavior:

- Online: forwards the prompt to `GroqService`.
- Offline: returns a fixed placeholder response.

It also resets Groq chat history when Clear is requested.

### `GroqService`

`GroqService` loads environment variables, creates the Groq client, stores chat history, sends text completion requests, and returns response text.

The current model is `llama-3.1-8b-instant`.

### `CameraService`

`CameraService` owns the OpenCV `VideoCapture`, reads frames, copies captured frames, saves JPEG files, and releases the camera.

The default camera index is `0` and the default output directory is `data/camera_pictures/`.

### `network_service`

The network service is a module-level singleton implemented with globals and a daemon thread. It tests connectivity, stores the last status, and exposes start, stop, and status functions.

Connectivity currently means that a TCP connection to `1.1.1.1:53` succeeds.

## 7. Shared State

`state.py` currently contains:

- `ui_queue`: cross-component navigation queue.
- `stop_camera`: an unused camera stop event.
- `main_window`: a global reference assigned during startup.
- `ai_input_text`: an unused shared AI input value.

Controller references also live on `MainWindow`, while network state lives in `network_service`. This means shared state is currently distributed across several locations.

## 8. Runtime Flows

### Navigation

```text
Button, key, or hotkey
        |
        v
state.ui_queue receives (action, payload)
        |
        v
process_ui_queue() in main.py
        |
        v
MainWindow.switch_to(Qt object name)
```

Camera start and stop are additional side effects performed by the router when entering or leaving Camera mode.

### AI Request

```text
AI Send button
        |
        v
AIController reads and displays the prompt
        |
        v
Background threading.Thread
        |
        v
AIService -> GroqService or offline placeholder
        |
        v
response_queue
        |
        v
Qt timer updates the chat output
```

### Camera Preview and Capture

```text
Camera route
        |
        v
CameraController starts CameraWorker
        |
        v
CameraService opens and reads the camera
        |
        v
frame_ready signal
        |
        v
CameraController converts and displays the frame

Capture button -> frame copy -> JPEG save -> temporary paused preview
```

### File Explorer

```text
AI Memory or Pictures button
        |
        v
FileExplorerController scans the selected directory
        |
        v
Rows are added to the table
        |
        v
Double-click supported image
        |
        v
ImageViewerScreen
```

## 9. Threading Model

The application currently uses three background-work patterns:

| Component | Mechanism | UI result path |
|---|---|---|
| Camera | `QThread` subclass | Qt signal |
| AI | daemon `threading.Thread` | Python queue plus Qt timer |
| Network | daemon `threading.Thread` | shared module state polled by UI |

Only the main Qt thread should modify widgets.

Known lifecycle risks include camera stop during device opening, network stop after a join timeout, and AI requests that cannot be cancelled during shutdown.

## 10. Runtime Data and Configuration

- Online AI key: `.env`, variable `GROQ_API_KEY`.
- Camera pictures: `data/camera_pictures/`.
- Planned AI history files: `data/ai_memory/`.
- UI definition: `screens/main_window.ui`.
- Visual assets: `assets/background/` and `assets/btn_photo/`.

Several paths are relative to the process working directory, so the application currently must be launched from the repository root.

## 11. Current Technical Debt

The highest-priority architecture and reliability issues are:

1. Replace calculator `eval()` with a restricted evaluator.
2. Fix camera and network shutdown races.
3. Replace or scope the global `Q` hotkey and unregister it on exit.
4. Add AI request timeout, cancellation, and safe history synchronization.
5. Move blocking file and image work away from the UI thread where needed.
6. Replace stringly typed routes with a defined routing contract.
7. Resolve paths from the project directory rather than the working directory.
8. Remove unused shared state and clarify ownership.
9. Add automated tests for services and lifecycle behavior.

## 12. Extension Rules

When adding a new mode:

1. Add or reuse a page in `main_window.ui`.
2. Add a screen module under `screens/`.
3. Use a `Controller` class when the object manages existing widgets rather than being a QWidget itself.
4. Put reusable hardware, API, storage, or domain operations under `services/`.
5. Register the controller in `main.py` and on `MainWindow`.
6. Add an explicit route and lifecycle behavior.
7. Add focused tests before marking the mode complete.

Avoid adding another architectural layer until it removes real complexity from the current code.
