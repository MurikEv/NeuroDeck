# NeuroDeck Architecture

## 1. Project Overview

NeuroDeck is a portable AI assistant system designed to run as a small desktop-style interface on compact hardware.

The project is built around multiple independent screens:

* Main menu
* Calculator
* Camera
* AI assistant
* File viewer
* Notes
* Browser / online tools in the future

The main goal of the architecture is to keep every part of the system separated, so the project does not become one large script with mixed UI, camera logic, AI logic, and state management.

---

## 2. Main Architecture Idea

NeuroDeck uses a screen-based architecture.

The application has one main window.
Different screens are shown or hidden inside this window.

Each screen is responsible only for its own interface and user interaction.

External logic such as camera access, AI API calls, file saving, and data processing should be placed inside service modules.

This keeps the project easier to debug, test, and extend.

---

## 3. Project Structure

```text
NeuroDeck/
│
├── main.py
├── state.py
├── README.md
├── ARCHITECTURE.md
├── TASKS.md
├── requirements.txt
├── .gitignore
├── .env.example
├── .env
│
├── screens/
│   ├── __init__.py
│   ├── menu.py
│   ├── calculator.py
│   ├── camera.py
│   └── ai.py
│
├── services/
│   ├── __init__.py
│   ├── camera.py
│   └── ai.py
│
├── assets/
│   ├── icons/
│   └── backgrounds/
│
└── data/
    ├── photos/
    ├── answers/
    └── logs/
```

---

## 4. File Responsibilities

### `main.py`

Application entry point.

Responsibilities:

* Create the main application window
* Initialize global application state
* Open the first screen

`main.py` should stay small.
It should not contain camera logic, AI logic, or full screen code.

---

### `state.py`

Stores shared application state.

Possible responsibilities:

* Reference to the main root window
* Current active screen
* Shared configuration
* Paths to data folders
* Current mode
* Last AI answer
* Last captured image path

This file exists to avoid passing the same objects through too many functions.

Example state values:

```text
root_window
current_screen
last_photo_path
last_ai_answer
```

---

## 5. Screens Layer

The `screens/` folder contains UI screens.

Each screen should handle:

* Creating its own frame
* Drawing widgets
* Handling user input for that screen
* Calling services when needed

Screens should not directly contain heavy logic.

---

### `screens/menu_screen.py`

Main navigation screen.

Responsibilities:

* Display available modes
* Allow navigation using buttons, arrows, or keyboard
* Open selected screen

Menu options:

* AI
* Camera
* Calculator
* Browser
* Notes
* Files
* Messenger

The menu should not process AI, open the camera directly, or manage files by itself.
It should only navigate to the correct screen.

---

### `screens/calculator_screen.py`

Calculator interface.

Responsibilities:

* Display calculator input
* Handle keyboard input
* Evaluate simple expressions
* Show result

Supported operations:

* Addition
* Subtraction
* Multiplication
* Division
* Brackets
* Powers
* Square root

The calculator screen should not control the main menu or AI logic.

---

### `screens/camera_screen.py`

Camera interface.

Responsibilities:

* Show camera preview
* Capture photo
* Save photo
* Send photo to AI if required

This screen should use `camera_service.py` for camera operations.

---

### `screens/ai_screen.py`

AI answer screen.

Responsibilities:

* Display AI output
* Allow scrolling through long answers
* Keep the answer visible after switching modes
* Possibly allow asking follow-up questions in the future

This screen should not directly call the API.
It should use `ai_service.py`.

---

## 6. Services Layer

The `services/` folder contains logic that does work outside the UI.

Services should be reusable.

---

### `services/camera_service.py`

Responsible for camera operations.

Responsibilities:

* Open camera
* Capture frame
* Save image
* Return image path

Possible functions:

```text
capture_photo()
save_frame()
open_camera()
release_camera()
```

---

### `services/ai_service.py`

Responsible for AI communication.

Responsibilities:

* Load API key
* Encode image
* Send request to AI model
* Return text answer
* Handle API errors

Possible functions:

```text
encode_image()
ask_ai_with_image()
ask_ai_text()
```

The UI should only receive the final answer.
It should not know the details of API requests.

---

## 7. Data Flow

### Camera AI Flow

```text
User opens Camera screen
        ↓
Camera screen shows preview
        ↓
User captures image
        ↓
camera_service saves image
        ↓
ai_service sends image to AI model
        ↓
AI returns answer
        ↓
AI screen displays answer
```

---

### Calculator Flow

```text
User opens Calculator screen
        ↓
Calculator screen receives key input
        ↓
Expression is updated
        ↓
User presses Enter
        ↓
Expression is evaluated
        ↓
Result is shown on screen
```

---

### Menu Flow

```text
User opens NeuroDeck
        ↓
Menu screen appears
        ↓
User selects mode
        ↓
Current screen is hidden or destroyed
        ↓
Selected screen is displayed
```

---

## 8. Screen Management

Only one main root window should exist.

Correct approach:

```text
One root window
Multiple frames
Show one frame at a time
Hide or destroy old frame
```

Wrong approach:

```text
Creating many Tk() windows
Mixing mainloop() in every screen
Running multiple UI loops
```

Recommended rule:

* `tk.Tk()` should be created once in `main.py`
* Screens should use `tk.Frame`
* Each screen should be packed, hidden, or destroyed as needed

---

## 9. Threading Model

Long-running tasks should not block the UI.

Examples of long tasks:

* Camera capture loop
* AI request
* File loading
* Image processing

Recommended approach:

```text
UI thread:
- Qt window
- Button events
- Keyboard events

Worker thread:
- Camera processing
- AI request
- Slow operations

Queue:
- Sends results back to UI thread
```

---

## 10. Keyboard Input

Keyboard handling should be centralized as much as possible.

Recommended rule:

* Use global hotkeys only for system-level actions such as opening menu or exiting

---

## 11. Hardware Direction

Target hardware:

* Small single-board computer
* Small display
* Camera module
* Battery power
* Physical buttons or calculator keypad

The current software should first work on a laptop.
After that, it can be moved to hardware.

Development stages:

```text
Laptop prototype
        ↓
Small screen UI test
        ↓
Camera module test
        ↓
Physical buttons test
        ↓
Battery-powered prototype
        ↓
Calculator-style enclosure
```

---

## 12. Current Development Priority

Current priority is not perfect hardware.

Current priority:

1. Stable screen switching
2. Clean project structure
3. Working calculator screen
4. Working camera capture
5. Working AI image answer
6. Scrollable AI answer screen
7. Saving photos and answers
8. Preparing for hardware buttons

---

## 13. Important Architecture Rules

### Rule 1: UI and logic must be separated

Bad:

```text
Button directly contains camera + AI + file saving + display logic
```

Good:

```text
Button calls screen method
Screen calls service
Service returns result
Screen displays result
```

---

### Rule 2: One file should not do everything

Bad:

```text
main.py contains menu, calculator, camera, AI, file saving, API calls
```

Good:

```text
main.py starts app
menu_screen.py handles menu
calculator_screen.py handles calculator
camera_service.py handles camera
ai_service.py handles AI
```

---

### Rule 3: One root window

Bad:

```text
Every screen creates tk.Tk()
```

Good:

```text
main.py creates one tk.Tk()
Every screen creates tk.Frame()
```

---

### Rule 4: Do not block the UI

Bad:

```text
AI request runs directly inside button command
UI freezes
```

Good:

```text
Button starts worker thread
Worker sends result to queue
UI displays result
```

---

## 14. Future Architecture

Later, NeuroDeck can be extended into a more serious system.

Possible future modules:

```text
core/
├── app.py
├── router.py
├── state.py
└── config.py

screens/
├── base_screen.py
├── menu_screen.py
├── calculator_screen.py
├── camera_screen.py
├── ai_screen.py
├── notes_screen.py
└── files_screen.py

services/
├── ai_service.py
├── camera_service.py
├── storage_service.py
├── speech_service.py
└── network_service.py
```

This should not be built immediately.
The current goal is to keep the project simple but ready for growth.

---

## 15. Engineering Goal

The goal of NeuroDeck is not only to build a device.

The goal is to learn real engineering through one project:

* UI architecture
* File structure
* Camera handling
* AI API integration
* Local-first design
* Hardware integration
* Debugging
* Git workflow
* Documentation
* Project finishing

NeuroDeck should become a portfolio project that shows practical system-building ability, not just copied code.

---

## 16. Next Milestone

The next milestone is:

```text
A clean multi-screen desktop prototype
```

Required features:

* Main menu works
* Arrow navigation works
* Enter opens selected mode
* Calculator screen works
* Camera screen opens
* AI answer screen displays text
* User can return to menu
* Code is split into files
* README and architecture documentation exist

```
```
