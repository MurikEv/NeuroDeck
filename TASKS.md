# NeuroDeck Tasks

Last updated: 2026-07-16

This file tracks the repository as it exists today. A checked item means the behavior is present in the current code, not that it is fully hardened.

## Current Milestone

Stabilize the existing Menu, Calculator, AI, Camera, Files, and Network functionality before implementing additional modes.

Priority order:

1. Runtime safety and clean shutdown.
2. Calculator safety.
3. AI request lifecycle and history consistency.
4. File persistence and refresh behavior.
5. Automated tests.
6. New modes and hardware integration.

## Foundation and Structure

- [x] Create the PyQt6 application and main window.
- [x] Load the primary UI from `screens/main_window.ui`.
- [x] Use one `QStackedWidget` for primary pages.
- [x] Separate screen modules from reusable services.
- [x] Keep screen-related Python modules under `screens/`.
- [x] Standardize controller class and instance names.
- [x] Standardize `file_explorer` naming in Python code.
- [x] Document the current architecture and limitations.
- [x] Add all current runtime Python packages to `requirements.txt`.
- [ ] Resolve resource and data paths relative to the project directory.
- [ ] Move startup side effects into `main()` and add a main guard.
- [ ] Remove unused state from `state.py`.

## P0: Runtime Safety

- [ ] Fix `CameraWorker.stop()` when camera opening is still blocked.
- [ ] Prevent a running camera worker from being overwritten on restart.
- [ ] Ensure the application never destroys a live QThread.
- [ ] Preserve and join a network monitor that exceeds the stop timeout.
- [ ] Prevent multiple network monitor threads from running concurrently.
- [ ] Stop network monitoring during application shutdown.
- [ ] Unregister the global keyboard hotkey during shutdown.
- [ ] Handle global hotkey registration failure.
- [ ] Add a controlled shutdown path for active AI requests.
- [ ] Add logging for startup, worker, API, camera, and file errors.

## Menu and Navigation

- [x] Display the main menu.
- [x] Navigate menu cards with arrow keys.
- [x] Highlight the selected card.
- [x] Open the selected card with Return.
- [x] Route Menu, Calculator, Camera, AI, and File Explorer actions.
- [x] Return to the menu through the current global `Q` action.
- [ ] Replace the global `Q` letter binding with a scoped Qt shortcut or hardware abstraction.
- [ ] Handle keypad Enter in addition to Return.
- [ ] Keep mouse selection and keyboard highlight synchronized.
- [ ] Define route names in one place instead of repeating strings.
- [ ] Reject or report unknown queue actions.
- [ ] Decide whether Browser, Notepad, Messenger, and Settings should be disabled or implemented.

## Calculator

- [x] Display calculator input and results.
- [x] Connect number buttons.
- [x] Connect addition, subtraction, multiplication, and division.
- [x] Support decimal points and parentheses.
- [x] Add Backspace and Clear.
- [x] Show an error for invalid Python expressions.
- [ ] Replace `eval()` with a restricted arithmetic parser.
- [ ] Reject unintended operations such as `//` and accidental `**`.
- [ ] Prevent excessively expensive calculations from blocking the UI.
- [ ] Implement physical keyboard input in `handle_key()`.
- [ ] Implement percent only after its expected behavior is defined.
- [ ] Implement explicit power support.
- [ ] Implement square root support.
- [ ] Define post-result behavior when the next input is a number or operator.
- [ ] Add unit tests for valid, invalid, and expensive expressions.

## AI Chat

- [x] Create the AI screen controller.
- [x] Connect Send and Clear actions.
- [x] Load `GROQ_API_KEY` through `python-dotenv`.
- [x] Send text prompts through the Groq client.
- [x] Store in-memory chat history.
- [x] Run API requests outside the UI thread.
- [x] Return worker results through a queue.
- [x] Display a loading state.
- [x] Display request exceptions instead of crashing the UI thread.
- [x] Select online or offline behavior from network state.
- [ ] Validate the API key without preventing unrelated modes from starting.
- [ ] Initialize the Groq client lazily when online AI is used.
- [ ] Add an application-level request timeout.
- [ ] Add cancellation or safe detachment during shutdown.
- [ ] Disable or coordinate Clear while a request is active.
- [ ] Keep failed prompts out of future chat history.
- [ ] Limit chat history by messages or token budget.
- [ ] Prevent the status timer from overwriting `Thinking...`.
- [ ] Report API availability separately from basic network status.
- [ ] Implement a real offline AI mode or rename it as a placeholder.
- [ ] Save AI answers to `data/ai_memory/`.
- [ ] Add tests with a mocked Groq client.

## On-Screen Keyboard

- [x] Open the keyboard from the AI input viewport.
- [x] Insert letters, comma, dot, and space.
- [x] Support Backspace and Hide.
- [ ] Synchronize external changes from the AI input back to the keyboard buffer.
- [ ] Preserve cursor position and selection.
- [ ] Preserve undo history where possible.
- [ ] Clear the active widget reference when the keyboard closes.
- [ ] Apply consistent focus policy to Space and Backspace.
- [ ] Support additional text widgets without hard-coded AI ownership.
- [ ] Add shift, uppercase, numbers, and symbols if required by the hardware UI.

## Camera

- [x] Open the default OpenCV camera.
- [x] Display a live preview.
- [x] Capture the current frame.
- [x] Save JPEG files under `data/camera_pictures/`.
- [x] Release the camera after the worker loop exits.
- [x] Display a message when initial camera opening fails.
- [ ] Fix stop-during-open and restart races.
- [ ] Report repeated frame-read failures and camera disconnection.
- [ ] Add backpressure or frame dropping so queued frames cannot grow without bound.
- [ ] Reduce unnecessary frame copies and UI-thread scaling cost.
- [ ] Move slow photo saving away from the UI thread if hardware testing requires it.
- [ ] Display capture and save success or failure.
- [ ] Prevent old preview-resume timers from affecting a new camera session.
- [ ] Validate or clearly report empty and all-black captures.
- [ ] Add tests with a fake camera service.

## Network

- [x] Add a background network monitor.
- [x] Expose Online/Offline state to the AI screen.
- [x] Store last check time and error details.
- [ ] Represent initial state as Unknown rather than Offline.
- [ ] Protect shared status and startup state from concurrent access.
- [ ] Validate monitoring intervals.
- [ ] Use `try/finally` so unexpected worker errors reset monitor state.
- [ ] Do not discard a thread reference while the thread is alive.
- [ ] Decide whether connectivity should test general HTTPS or the actual AI endpoint.
- [ ] Emit status changes instead of polling from the UI where practical.

## Files and Persistence

- [x] Add AI Memory and Pictures folder selectors.
- [x] Display name, type, size, and modified time.
- [x] Open supported image files.
- [x] Add an image viewer page.
- [x] Apply image auto-rotation and aspect-ratio scaling.
- [ ] Create required runtime directories during application initialization.
- [ ] Refresh the active list whenever File Explorer is opened.
- [ ] Catch directory, permission, and file-stat errors.
- [ ] Handle files disappearing while the table is visible.
- [ ] Allow folder navigation or stop displaying folders as openable entries.
- [ ] Add a viewer for saved text and AI answers.
- [ ] Decode large images at an appropriate target size.
- [ ] Decide whether animated GIF support is required.
- [ ] Move slow directory and image work away from the UI thread when necessary.
- [ ] Add storage tests using temporary directories.

## Placeholder Modes

- [ ] Define the purpose and minimum scope of Browser mode.
- [ ] Define the purpose and storage format of Notepad mode.
- [ ] Define whether Messenger is local, external, or removed.
- [ ] Define the available Settings and persistence format.
- [ ] Add routes only after each mode has at least a safe placeholder screen.

## Hardware Preparation

- [x] Keep an experimental ST7796 display test locally.
- [ ] Decide supported SBC and operating-system versions.
- [ ] Document display, GPIO, SPI, camera, and power wiring.
- [ ] Add a separate Linux hardware requirements file after package versions are validated.
- [ ] Update the display test for the selected libgpiod API.
- [ ] Guarantee cleanup when GPIO or SPI setup fails partway through.
- [ ] Verify display color inversion and orientation on target hardware.
- [ ] Test UI layout at the target resolution.
- [ ] Test keyboard-only or physical-button-only operation.
- [ ] Measure camera CPU, memory, and preview latency on the target board.
- [ ] Document required Linux permissions for camera and input devices.

## Testing and Quality

- [x] Parse all project Python files successfully.
- [x] Run an offscreen smoke test that creates all current controllers.
- [ ] Add `pytest` and a test directory.
- [ ] Add formatting and lint configuration.
- [ ] Test startup without `.env` and without `GROQ_API_KEY`.
- [ ] Test startup without camera hardware.
- [ ] Test offline and changing network states.
- [ ] Test rapid screen switching and repeated camera entry.
- [ ] Test application close from every implemented mode.
- [ ] Test long AI responses and failed AI requests.
- [ ] Test missing, empty, and inaccessible data directories.
- [ ] Add continuous integration after tests are deterministic.

## Documentation and Release

- [x] Synchronize README with current behavior.
- [x] Document current architecture and naming conventions.
- [x] Replace stale task status with evidence-based checkboxes.
- [x] Document known limitations.
- [ ] Populate `.env.example` with non-secret variable names.
- [ ] Add screenshots after the main workflows stabilize.
- [ ] Add a short demo after runtime safety issues are resolved.
- [ ] Select and add a license before public distribution.

## Definition of Stable MVP

The current milestone is complete when:

- The application starts with or without network, API key, and camera hardware.
- Menu, Calculator, AI, Camera, and Files can be opened repeatedly without crashes.
- Camera, network, hotkey, and AI background work shut down cleanly.
- Calculator input cannot execute arbitrary Python or unbounded expressions.
- AI failures and file-system failures produce controlled UI errors.
- Runtime paths work independently of the launch directory.
- Core service and lifecycle behavior has automated test coverage.
