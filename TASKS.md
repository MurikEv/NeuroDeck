# NeuroDeck Tasks

## Current Goal

Build a working portable AI assistant prototype with a simple UI system, multiple screens, camera support, calculator mode, and AI response mode.

The project should grow step by step.
Do not add advanced features before the base system is stable.

---

## Phase 1 — Project Structure

### Goal

Make the project clean, understandable, and easy to expand.

### Tasks

* ☑ Create basic project structure
* ☑ Create `main.py`
* ☑ Create `screens/` folder
* ☑ Create `services/` folder
* ☑ Create `README.md`
* ☑ Create `ARCHITECTURE.md`
* ☑ Create `TASKS.md`
* ☑ Create `requirements.txt`
* ☑ Create `.env.example`
* ☑ Create `.gitignore`

### Done When

* Project can be opened and understood without reading all code.
* Every file has a clear responsibility.
* Main application starts from `main.py`.

---

## Phase 2 — Main UI System

### Goal

Build a basic multi-screen application.

### Tasks

* ☑ Create main window
* ☑ Create menu screen
* ☑ Add menu buttons:
  * AI
  * Camera
  * Calculator
  * Browser
  * Notes
  * Files
  * Messenger
* ☑ Add keyboard navigation
* ☑ Add selected button highlight
* ☑ Add Enter key to open selected mode
* ☑ Add key to return to menu
* ☑ Make screen switching stable

### Done When

* User can move through menu using keyboard.
* Enter opens selected screen.
* User can return to menu.
* Old screens do not stay active in background.

---

## Phase 3 — Calculator Mode

### Goal

Create a working calculator screen.

### Tasks

* ☑ Create calculator screen
* [ ] Show calculator display
* [ ] Allow number input
* [ ] Allow basic operators:

  * `+`
  * `-`
  * `*`
  * `/`
* [ ] Add decimal point support
* [ ] Add brackets support
* [ ] Add power operator
* [ ] Add square root support
* [ ] Add Backspace
* [ ] Add Clear
* [ ] Add error handling

### Done When

* Calculator can calculate basic expressions.
* Invalid input shows error instead of crashing.
* Calculator screen works after switching from other screens.

---

## Phase 4 — Camera Mode

### Goal

Create a stable camera preview and photo capture system.

### Tasks

* [ ] Create camera service
* [ ] Open camera preview
* [ ] Capture image on key press
* [ ] Save captured image to project data folder
* [ ] Close camera safely
* [ ] Return to menu without freezing
* [ ] Handle camera not found error

### Done When

* Camera preview opens.
* User can take a photo.
* Photo is saved correctly.
* Camera closes cleanly when leaving the mode.

---

## Phase 5 — AI Image Answer Mode

### Goal

Send captured image to AI and show answer on screen.

### Tasks

* [ ] Create AI service
* [ ] Load API key from `.env`
* [ ] Encode image to base64
* [ ] Send image to AI model
* [ ] Create clean prompt for Polish school-style answers
* [ ] Show AI answer in UI
* [ ] Add loading state
* [ ] Add error handling for API problems
* [ ] Add scroll support for long answers

### Done When

* User can take a photo.
* AI receives the image.
* AI answer appears in the app.
* Long answers can be read.
* API errors do not crash the program.

---

## Phase 6 — Files System

### Goal

Save useful project outputs.

### Tasks

* [ ] Create `data/` folder
* [ ] Save captured photos
* [ ] Save AI answers
* [ ] Save timestamp with each result
* [ ] Create simple file list screen
* [ ] Allow opening old answers

### Done When

* User can see previous photos and answers.
* Data is not lost after closing the app.

---

## Phase 7 — Notes Mode

### Goal

Create a simple note-taking screen.

### Tasks

* [ ] Create notes screen
* [ ] Add text input
* [ ] Save notes to file
* [ ] Load existing notes
* [ ] Add simple keyboard navigation

### Done When

* User can write and save notes.
* Notes are available after restarting the app.

---

## Phase 8 — Browser / Online Mode

### Goal

Add online tools only after offline screens are stable.

### Tasks

* [ ] Decide if browser mode is really needed
* [ ] Research simple embedded browser options
* [ ] Add placeholder screen first
* [ ] Add real browser only if it fits the project

### Done When

* Browser mode has a clear purpose.
* It does not break the main app.

---

## Phase 9 — Hardware Preparation

### Goal

Prepare the app for running on small hardware.

### Tasks

* [ ] Test UI at small resolution
* [ ] Test fullscreen mode
* [ ] Test keyboard-only navigation
* [ ] Reduce unnecessary UI elements
* [ ] Test camera module
* [ ] Test display size
* [ ] Test boot behavior
* [ ] Document hardware requirements

### Done When

* App can run on a small screen.
* App can be controlled without mouse.
* Hardware limitations are documented.

---

## Phase 10 — Refactoring

### Goal

Make the code cleaner and easier to maintain.

### Tasks

* [ ] Move menu code to `screens/menu_screen.py`
* [ ] Move calculator code to `screens/calculator_screen.py`
* [ ] Move camera UI code to `screens/camera_screen.py`
* [ ] Move AI screen code to `screens/ai_screen.py`
* [ ] Move camera logic to `services/camera_service.py`
* [ ] Move AI API logic to `services/ai_service.py`
* [ ] Remove duplicated code
* [ ] Replace global variables where possible
* [ ] Add comments only where they explain important logic

### Done When

* Each file has one main responsibility.
* Main file is small.
* Screens do not contain API logic.
* Services do not contain UI logic.

---

## Phase 11 — Testing

### Goal

Make the project more reliable.

### Tasks

* [ ] Test unsupported camera
* [ ] Test missing API key
* [ ] Test no internet
* [ ] Test invalid calculator input
* [ ] Test screen switching many times
* [ ] Test closing app from every screen
* [ ] Test missing data folder
* [ ] Test long AI answer

### Done When

* Common errors are handled.
* App does not randomly freeze or crash.

---

## Phase 12 — Portfolio Polish

### Goal

Make the project presentable for GitHub and future job applications.

### Tasks

* [ ] Clean README
* [ ] Add screenshots
* [ ] Add architecture explanation
* [ ] Add installation instructions
* [ ] Add usage instructions
* [ ] Add project status
* [ ] Add known limitations
* [ ] Add future improvements
* [ ] Record short demo video

### Done When

* A stranger can understand what the project does.
* A recruiter or developer can see engineering progress.
* Project looks like a real prototype, not random scripts.

---

# Current Priority

Do not build everything at once.

Current focus:

1. Stable menu
2. Stable screen switching
3. Working calculator
4. Working camera
5. AI answer mode

Only after that move to notes, files, browser, and hardware polish.

---

# Rules

* One task at a time.
* Do not add new features before the current feature works.
* Do not rewrite everything without a reason.
* Keep UI logic separate from service logic.
* Commit after every stable improvement.
* If something breaks, fix it before moving forward.
