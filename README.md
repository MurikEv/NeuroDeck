# NeuroDeck

NeuroDeck is an early MVP of a compact, multi-mode desktop assistant written in Python and PyQt6. The long-term target is a small single-board computer with a display, camera, physical controls, and optional online AI access.

The repository is currently a learning and prototyping project. Features marked as implemented below exist in the current code, but several stability and lifecycle issues are still tracked in `TASKS.md`.

## Current Functionality

Implemented:

- Main menu with arrow-key navigation, selection highlighting, and Return to open a mode.
- Calculator UI with button input, basic arithmetic, decimal points, and parentheses.
- Text-only AI chat through the Groq API when the network monitor reports an online connection.
- Static offline response when no network connection is reported.
- Shared on-screen keyboard for AI input and Notepad search, titles, and note text.
- Local Notepad with editing, autosave, search, favorites, archive, and sorting.
- Camera preview, JPEG capture, and storage in `data/camera_pictures/`.
- File explorer for AI-memory and camera-picture folders.
- Image viewer for supported image files.
- Background network monitoring and an Online/Offline status label.

Partial or placeholder functionality:

- Browser, Messenger, and Settings appear in the menu but do not have implemented routes.
- Offline AI is a placeholder response, not a local model.
- AI answers are not saved to `data/ai_memory/`.
- The file explorer can display directories and non-image files but only opens supported images.
- Camera images cannot yet be sent to the AI mode.
- Calculator keyboard input, percent, power, and square root are not implemented.

## Project Structure

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

The `screens/` directory contains the Qt Designer file and the Python modules responsible for screen-specific interaction. Their main classes use the `Controller` suffix because they connect existing widgets, react to events, call services, and update the UI.

The `services/` directory contains camera, network, and AI integration code that should remain independent from specific widgets.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the current component boundaries and data flows.

## Controls

|       Input        |                   Current behavior                   |
|--------------------|------------------------------------------------------|
|     Arrow keys     |               Move through menu items                |
|       Return       |             Open the selected menu item              |
|         Q          | Queue a return to the menu through the global hotkey |
|   Mouse or touch   |               Activate visible buttons               |
| On-screen keyboard |            Enter text in the AI input field          |

The global `Q` binding is temporary. It also reacts while typing a physical `q` and may require elevated input-device permissions on Linux.

## Modes

### Menu

`MenuController` keeps the existing menu page and its eight real Qt buttons.
The visual-only version displays `assets/background/menu_reference.png` exactly,
without redrawing the reference's lettering, icons or neon. This tracked asset
is a byte-for-byte copy of the local reference. It is displayed at native 480px
width; only three near-black bottom padding rows fall outside the 320px canvas.
Only the upper-left wordmark is replaced with `neurodeck`, matched to the
original geometric lettering. Its edited source is
`assets/background/menu_neurodeck_source.png`; Qt draws only the small wordmark
crop, preserving all other reference pixels. Transparent buttons add feedback
while held. Other screens are unchanged.

The header is intentionally static to match the reference, apart from NeuroDeck:
the original small labels, network bars, battery and `19:77`. These are artwork,
not live readings in this visual-only version. The existing clock/network
snapshot logic is retained, but does not overwrite the reference. The previous
vector menu remains a fallback if the reference asset cannot be loaded.

Cards highlight only while pressed and cancel activation when the finger moves
outside before release. Developer keyboard navigation remains opt-in. AI,
Calculator, Camera, Notepad, Files, and Settings keep their existing routes;
Browser and Messenger remain placeholders.

The bundled Rajdhani typeface comes from
[Google Fonts](https://github.com/google/fonts/tree/main/ofl/rajdhani);
its SIL Open Font License is included in `assets/fonts/OFL-Rajdhani.txt`.

### Calculator

`CalculatorController` connects calculator buttons and maintains the displayed expression. Evaluation currently uses Python `eval()`, which is temporary and must be replaced with a restricted parser before the calculator is considered safe and complete.

### AI

`AIController` sends text prompts through `AIService`. Online requests use `GroqService`; offline requests return a fixed message. Requests run in a background Python thread and answers return to the UI through a queue polled by a Qt timer.

The current AI mode is text-only. Image analysis and a real local model are not implemented.

### Camera

`CameraController` starts a `QThread` worker that reads OpenCV frames through `CameraService`. Captured frames are saved as JPEG files in `data/camera_pictures/`.

### Files

`FileExplorerController` lists entries from `data/ai_memory/` and `data/camera_pictures/`. Supported image formats can be opened in the programmatic `ImageViewerScreen`.

### Notepad

Open Notepad from the menu. Tap `CREATE` or `NEW NOTE`, enter a title and text,
then use `SAVE` or return to the list. Changes also autosave after a short pause;
an empty new draft is not stored. Tap a note to edit it. The editor offers
favorite/unfavorite, archive/restore, and deletion with in-window confirmation.

`SEARCH` opens the existing virtual keyboard and filters titles and note text
in the selected category. `DONE` (or the keyboard's hide key) closes the keyboard;
`X` clears and closes search. The same keyboard opens when a title or note body
is tapped. `SHIFT`, `123/ABC`, and `ENTER/DONE` support capitals, numbers/symbols,
and multiline text without a physical keyboard.

`RECENT` shows the latest 20 non-archived notes. `SORT` cycles through most
recently updated, title A-Z, and newest created. Favorites exclude archived notes;
archived notes can be restored without losing their favorite flag.

Notes are stored locally in `data/notepad/notes.json` (relative to the project,
not the working directory). This private runtime folder is ignored by Git.
Writes use atomic replacement; storage errors keep unsaved edits in the editor
and prevent navigation/normal window close until saving succeeds or the user
explicitly discards changes (with confirmation). Corrupt files
are reported without being overwritten. No new dependencies are required.

## Installation

The current development environment uses Python 3.14. A camera is optional unless Camera mode is being tested.

Create and activate a virtual environment on Windows:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

Install runtime dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create `.env` in the project root for online AI:

```env
GROQ_API_KEY=your_api_key_here
```

Run the application from the project root:

```powershell
python main.py
```

Running from another working directory is not currently supported because UI and data paths are relative to the project root.

## Runtime Data

- Camera captures are written to `data/camera_pictures/`.
- AI-memory storage is planned for `data/ai_memory/`, but no writer exists yet.
- Notepad notes are saved in `data/notepad/notes.json`; copy this file to back up your notes.
- Runtime data directories may be absent in a clean clone and are created only by the code paths that explicitly create them.

## Known Limitations

- Camera shutdown and network-monitor shutdown have known thread lifecycle races.
- AI requests have no application-level cancellation or timeout handling.
- Clearing AI history during a running request can produce inconsistent history.
- Network status is based on a connection test to `1.1.1.1:53`, not direct Groq availability.
- The global `Q` hotkey conflicts with normal text entry.
- File and image loading run synchronously in the UI thread.
- Several paths depend on the current working directory.
- There is no automated test suite yet.

The prioritized fixes are maintained in [TASKS.md](TASKS.md).

## Hardware Direction

The intended hardware is a compact Linux SBC such as a Radxa Zero or Raspberry Pi-class board with a small display, camera, physical controls, and battery power. Experimental SPI/GPIO scripts are not part of the main runtime requirements and must be validated on the target board separately.

## License

The project is currently private and experimental. No redistribution license has been selected.
