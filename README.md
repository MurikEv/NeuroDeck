# NeuroDeck

NeuroDeck is a portable AI assistant system built with Python.

The goal of this project is to create a small device-style interface with multiple modes, including menu navigation, calculator mode, camera mode, and AI-powered image answering.

This project is also a learning project focused on software engineering, UI architecture, hardware integration, and AI engineering.

## Current Status

The project is in early MVP development.

Currently implemented or being developed:

* Main menu interface
* Keyboard navigation between menu buttons
* Calculator screen
* Camera screen prototype
* AI image question answering prototype
* Basic multi-screen structure using Qt Designer and PyQt6
* Early hardware planning for Radxa Zero 3 / Raspberry Pi-style SBC

## Planned Features

### Offline Modes

* Main menu
* Calculator
* Camera
* Simple AI chat
* Notes
* Files / saved answers
* Local AI support in the future

### Online Modes

* Browser
* ChatGPT / external AI API
* Messenger-style interface

## Project Structure

```text
NeuroDeck/
│
├── main.py
├── state.py
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
├── data/
│   ├── images/
│   └── answers/
│
└── assets/
    ├── icons/
    └── backgrounds/
```

## Main Idea

NeuroDeck works like a small portable terminal.

The user can open the main menu, choose a mode, use the camera, calculate expressions, or send images to an AI model for analysis.

The final target is to run the system on a small single-board computer with a small display, camera, buttons, and battery.

## Controls

Current planned controls:

| Key         | Action                       |
| ----------- | ---------------------------- |
| Q           | Open menu                    |
| Arrow Right | Move selection right  MENU       |
| Arrow Left  | Move selection left          |
| Arrow Up    | Move selection up            |
| Arrow Down  | Move selection down          |
| Enter       | Open selected mode           |
| Esc         | Exit program                 |

## Modes

### Menu

The central screen of the system.
It allows the user to choose between available modes.

### Calculator

A simple calculator interface designed to look like a small device display.

Planned functions:

* Basic arithmetic
* Parentheses
* Powers
* Square root
* Cleaner display formatting

### Camera

Camera mode allows the device to preview the camera image and capture a photo.

Planned functions:

* Camera preview
* Take photo
* Save photo
* Send photo to AI mode

### AI Mode

AI mode sends an image or prompt to an AI model and displays the response.

Current prototype uses an external AI API.

Future goal:

* Add local AI support
* Add better prompt control
* Add saved answer history
* Add scrolling for long answers

### Notes

Planned mode for writing notes.

Possible future features:

* Keyboard text input
* Voice-to-text
* Saved notes

### Files

Planned mode for viewing saved images, AI answers, and notes.

## Technologies

Current technologies:

* Python
* Qt Designer
* PyQt6
* OpenCV
* Groq API
* threading
* queue
* dotenv

Possible future technologies:

* FastAPI
* PySide6 / Qt
* Local LLMs
* Whisper / speech recognition
* Linux GPIO
* Touchscreen support

## Hardware Target

Possible hardware:

* Radxa Zero 3
* Raspberry Pi Zero 2 W
* Small SPI display
* Small camera module
* Calculator-style case
* Physical buttons
* Battery module

The project is currently developed and tested on a normal computer first.

## Development Goals

This project is not only about making the device work.

The engineering goals are:

* Build a clean multi-screen architecture
* Separate UI code from service logic
* Avoid spaghetti code
* Learn real debugging
* Learn project structure
* Learn hardware/software integration
* Build a portfolio-level AI engineering project

## Installation

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
GROQ_API_KEY=your_api_key_here
```

Run the project:

```bash
python main.py
```

## Current Problems / TODO

* Create calculator UI
* Create calculator logic

## Learning Focus

This project is used to learn:

* Python project architecture
* UI systems
* State management
* Camera integration
* AI API integration
* Local AI concepts
* Hardware planning
* GitHub workflow
* Clean code

## License

This project is currently private / experimental.

License will be decided later.
