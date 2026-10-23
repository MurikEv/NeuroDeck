"""Touch-operated local notes, using the shared on-screen keyboard."""

from datetime import datetime
from pathlib import Path
import sys

from PyQt6.QtCore import QObject, QSize, Qt, QTimer
from PyQt6.QtWidgets import (
    QAbstractItemView, QFrame, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPlainTextEdit, QPushButton, QScroller,
)

from services.notepad_service import NotepadStorageError, NotepadStore
import state


class NotepadController(QObject):
    CATEGORIES = {
        "all": "ALL NOTES", "recent": "RECENT", "favorites": "FAVORITES",
        "archive": "ARCHIVE",
    }
    SORT_MODES = ("updated", "title", "created")

    def __init__(self, window, store=None):
        super().__init__(window)
        self.window = window
        self.screen = window.notepad_screen
        self.keyboard = window.keyboard_controller
        self.category = "all"
        self.sort_mode = "updated"
        self.current_id = None
        self.favorite = False
        self.archived = False
        self.dirty = False
        self._loading = False
        self.storage_error = None
        try:
            self.store = store if store is not None else NotepadStore()
        except NotepadStorageError as exc:
            self.store = None
            self.storage_error = str(exc)
            print(f"Notepad storage unavailable: {exc}", file=sys.stderr)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.setInterval(700)
        self.autosave_timer.timeout.connect(self.save_pending)
        self._build_widgets()
        self._connect_controls()
        self.refresh_list()

    def _button(self, parent, name, text, geometry, callback):
        button = QPushButton(text, parent)
        button.setObjectName(name)
        button.setGeometry(*geometry)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.clicked.connect(callback)
        return button

    def _build_widgets(self):
        style = self.screen.styleSheet().replace(
            "QPushButton#notepadAllNotesButton {",
            'QPushButton[notepadNav="true"][active="true"] {',
        )
        style_path = Path(__file__).resolve().parents[1] / "assets/styles/notepad_screen.qss"
        self.screen.setStyleSheet(style + "\n" + style_path.read_text(encoding="utf-8"))
        content = self.window.notepadContent
        self.search_input = QLineEdit(content)
        self.search_input.setObjectName("notepadSearchInput")
        self.search_input.setGeometry(12, 5, 250, 29)
        self.search_input.setPlaceholderText("Search title or text...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.hide()
        self.search_close = self._button(
            content, "notepadSearchClose", "X", (266, 5, 38, 29), self.close_search,
        )
        self.search_close.setAccessibleName("Close search")
        self.search_close.hide()
        self.note_list = QListWidget(content)
        self.note_list.setObjectName("notepadList")
        self.note_list.setGeometry(12, 93, 292, 123)
        self.note_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.note_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.note_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.note_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        QScroller.grabGesture(self.note_list.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)
        self.list_status = QLabel(content)
        self.list_status.setObjectName("notepadListStatus")
        self.list_status.setGeometry(12, 220, 292, 20)

        self.editor = QFrame(self.screen)
        self.editor.setObjectName("notepadEditor")
        self.editor.setGeometry(6, 6, 468, 308)
        self.editor_back = self._button(
            self.editor, "notepadEditorBack", "< NOTES", (8, 6, 80, 38), self.show_list,
        )
        label = QLabel("EDIT NOTE", self.editor)
        label.setObjectName("notepadEditorHeading")
        label.setGeometry(104, 8, 250, 34)
        self.save_button = self._button(
            self.editor, "notepadSaveButton", "SAVE", (378, 6, 82, 38), self.save_clicked,
        )
        self.discard_button = self._button(
            self.editor, "notepadDiscardButton", "DISCARD", (278, 6, 92, 38), self.request_discard,
        )
        self.discard_button.hide()
        self.title_input = QLineEdit(self.editor)
        self.title_input.setObjectName("notepadTitleInput")
        self.title_input.setGeometry(10, 50, 448, 36)
        self.title_input.setPlaceholderText("Title (Untitled if empty)")
        self.body_input = QPlainTextEdit(self.editor)
        self.body_input.setObjectName("notepadBodyInput")
        self.body_input.setGeometry(10, 94, 448, 146)
        self.body_input.setPlaceholderText("Write a note...")
        self.favorite_button = self._button(
            self.editor, "notepadFavoriteButton", "FAVORITE", (10, 248, 140, 36), self.toggle_favorite,
        )
        self.archive_button = self._button(
            self.editor, "notepadArchiveNoteButton", "ARCHIVE", (160, 248, 140, 36), self.toggle_archive,
        )
        self.delete_button = self._button(
            self.editor, "notepadDeleteButton", "DELETE", (310, 248, 148, 36), self.request_delete,
        )
        self.editor_status = QLabel(self.editor)
        self.editor_status.setObjectName("notepadEditorStatus")
        self.editor_status.setGeometry(10, 286, 448, 18)

        # In-window confirmation: separate native dialogs are not mirrored to SPI.
        self.delete_overlay = QFrame(self.editor)
        self.delete_overlay.setObjectName("notepadDeleteOverlay")
        self.delete_overlay.setGeometry(self.editor.rect())
        self.confirm_prompt = QLabel(self.delete_overlay)
        self.confirm_prompt.setGeometry(20, 64, 428, 70)
        self.confirm_prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._confirmation_mode = "delete"
        self.cancel_delete_button = self._button(
            self.delete_overlay, "notepadCancelDelete", "CANCEL", (56, 164, 160, 44), self.cancel_delete,
        )
        self.confirm_delete_button = self._button(
            self.delete_overlay, "notepadConfirmDelete", "DELETE", (252, 164, 160, 44), self.confirm_action,
        )
        self.delete_overlay.hide()
        self.editor.hide()
        for widget in (self.search_input, self.title_input, self.body_input):
            self.keyboard.register_text_widget(widget)

    def _connect_controls(self):
        self.nav_buttons = {
            "all": self.window.notepadAllNotesButton,
            "recent": self.window.notepadRecentButton,
            "favorites": self.window.notepadFavoritesButton,
            "archive": self.window.notepadArchiveButton,
        }
        for category, button in self.nav_buttons.items():
            button.clicked.connect(lambda _checked=False, category=category: self.select_category(category))
        self.window.notepadBackButton.clicked.connect(self.back_to_menu)
        self.window.notepadCreateButton.clicked.connect(self.new_note)
        self.window.notepadNewNoteButton.clicked.connect(self.new_note)
        self.window.notepadSearchButton.clicked.connect(self.open_search)
        self.window.notepadSortButton.clicked.connect(self.cycle_sort)
        self.search_input.textChanged.connect(self.refresh_list)
        self.note_list.itemClicked.connect(self.open_item)
        self.title_input.textChanged.connect(self._mark_dirty)
        self.body_input.textChanged.connect(self._mark_dirty)
        for button in (self.window.notepadCreateButton, self.window.notepadNewNoteButton):
            button.setEnabled(self.store is not None)

    def select_category(self, category):
        self.category = category
        if category == "recent":
            self.sort_mode = "updated"
        self.refresh_list()

    def visible_notes(self):
        notes = self.store.notes if self.store is not None else []
        notes = [note for note in notes if note["archived"] == (self.category == "archive")]
        if self.category == "favorites":
            notes = [note for note in notes if note["favorite"]]
        if self.category == "recent":
            notes = sorted(notes, key=lambda note: note["updated_at"], reverse=True)[:20]
        query = self.search_input.text().strip().casefold()
        if query:
            notes = [note for note in notes if query in note["title"].casefold() or query in note["body"].casefold()]
        key = {"updated": "updated_at", "created": "created_at", "title": "title"}[self.sort_mode]
        return sorted(notes, key=lambda note: note[key].casefold(), reverse=key != "title")

    def refresh_list(self, *_args):
        notes = self.visible_notes()
        self.note_list.clear()
        for note in notes:
            timestamp = datetime.fromisoformat(note["updated_at"]).astimezone().strftime("%d.%m.%Y %H:%M")
            title = note["title"].replace("\n", " ") or "Untitled"
            item = QListWidgetItem(f"{'* ' if note['favorite'] else ''}{title}\n{timestamp}")
            item.setData(Qt.ItemDataRole.UserRole, note["id"])
            item.setSizeHint(QSize(268, 46))
            self.note_list.addItem(item)
        self.note_list.setVisible(bool(notes))
        for widget in (self.window.notepadEmptyIcon, self.window.notepadEmptyTitle, self.window.notepadEmptyDescription):
            widget.setVisible(not notes)
        if self.storage_error:
            self.window.notepadEmptyTitle.setText("STORAGE UNAVAILABLE")
            self.window.notepadEmptyDescription.setText("Notes were not overwritten. See terminal.")
        else:
            self.window.notepadEmptyTitle.setText("NO MATCHES" if self.search_input.text().strip() else "NO NOTES HERE")
            self.window.notepadEmptyDescription.setText("Try another search or create a note.")
        self.window.notepadSectionTitle.setText(self.CATEGORIES[self.category])
        sort_labels = {"updated": "NEW", "title": "A-Z", "created": "CREATED"}
        self.window.notepadSortButton.setText("SORT: " + sort_labels[self.sort_mode])
        self.list_status.setText("Storage unavailable" if self.storage_error else f"{len(notes)} notes" + (" | Latest 20" if self.category == "recent" else ""))
        for category, button in self.nav_buttons.items():
            button.setProperty("active", category == self.category)
            button.style().unpolish(button)
            button.style().polish(button)

    def open_search(self):
        self.window.notepadSectionTitle.hide()
        self.search_input.show()
        self.search_close.show()
        self.keyboard.open_keyboard(self.search_input)

    def close_search(self):
        self.keyboard.close_keyboard()
        self.search_input.clear()
        self.search_input.hide()
        self.search_close.hide()
        self.window.notepadSectionTitle.show()

    def cycle_sort(self):
        index = (self.SORT_MODES.index(self.sort_mode) + 1) % len(self.SORT_MODES)
        self.sort_mode = self.SORT_MODES[index]
        self.refresh_list()

    def new_note(self):
        if self.store is not None and self.save_pending():
            self._open_editor(None)
            self.keyboard.open_keyboard(self.title_input)

    def open_item(self, item):
        note_id = item.data(Qt.ItemDataRole.UserRole)
        note = next((note for note in self.store.notes if note["id"] == note_id), None)
        if note is not None and self.save_pending():
            self._open_editor(note)

    def _open_editor(self, note):
        self.keyboard.close_keyboard()
        self._loading = True
        self.current_id = note["id"] if note else None
        self.favorite = note["favorite"] if note else False
        self.archived = note["archived"] if note else False
        self.title_input.setText(note["title"] if note else "")
        self.body_input.setPlainText(note["body"] if note else "")
        self._loading = False
        self.dirty = False
        self._update_action_labels()
        self.editor_status.setText("Saved" if note else "New note | Autosave enabled")
        self.discard_button.hide()
        self.delete_overlay.hide()
        self.editor.show()
        self.editor.raise_()

    def _mark_dirty(self, *_args):
        if self._loading:
            return
        self.dirty = True
        self.editor_status.setText("Unsaved changes...")
        self.autosave_timer.start()

    def _update_action_labels(self):
        self.favorite_button.setText("UNFAVORITE" if self.favorite else "FAVORITE")
        self.archive_button.setText("RESTORE" if self.archived else "ARCHIVE")

    def save_pending(self):
        self.autosave_timer.stop()
        if not self.dirty:
            return True
        title = self.title_input.text().strip()
        body = self.body_input.toPlainText()
        if self.current_id is None and not title and not body.strip():
            self.dirty = False
            return True
        try:
            note = self.store.upsert(
                self.current_id, title=title or "Untitled", body=body,
                favorite=self.favorite, archived=self.archived,
            )
        except NotepadStorageError as exc:
            self._show_error("NOT SAVED", exc)
            return False
        self.current_id = note["id"]
        self.dirty = False
        self.discard_button.hide()
        self.editor_status.setText("Saved " + datetime.now().strftime("%H:%M"))
        return True

    def save_clicked(self):
        self.keyboard.close_keyboard()
        self.save_pending()

    def toggle_favorite(self):
        self.favorite = not self.favorite
        self._update_action_labels()
        self.dirty = True
        self.save_pending()

    def toggle_archive(self):
        self.archived = not self.archived
        self._update_action_labels()
        self.dirty = True
        if self.save_pending():
            self.show_list()

    def request_delete(self):
        self._confirmation_mode = "delete"
        self.confirm_prompt.setText("Delete this note?\nThis cannot be undone.")
        self.confirm_delete_button.setText("DELETE")
        self.keyboard.close_keyboard()
        self.autosave_timer.stop()
        self.delete_overlay.show()
        self.delete_overlay.raise_()

    def request_discard(self):
        self._confirmation_mode = "discard"
        self.confirm_prompt.setText("Discard unsaved changes?\nThe last saved version will be kept.")
        self.confirm_delete_button.setText("DISCARD")
        self.keyboard.close_keyboard()
        self.autosave_timer.stop()
        self.delete_overlay.show()
        self.delete_overlay.raise_()

    def confirm_action(self):
        if self._confirmation_mode == "delete":
            self.delete_note()
        else:
            self.dirty = False
            self.current_id = None
            self.discard_button.hide()
            self.delete_overlay.hide()
            self.show_list()

    def cancel_delete(self):
        self.delete_overlay.hide()
        if self.dirty:
            self.autosave_timer.start()

    def delete_note(self):
        try:
            if self.current_id is not None:
                self.store.delete(self.current_id)
        except NotepadStorageError as exc:
            self.delete_overlay.hide()
            self._show_error("NOT DELETED", exc)
            return
        self.dirty = False
        self.current_id = None
        self.delete_overlay.hide()
        self.show_list()

    def _show_error(self, prefix, error):
        advice = "retry SAVE or DISCARD unsaved changes" if prefix == "NOT SAVED" else "check permissions / free space"
        self.editor_status.setText(f"{prefix}: {advice}")
        self.editor_status.setToolTip(str(error))
        if self.dirty:
            self.discard_button.show()
        print(f"Notepad {prefix.lower()}: {error}", file=sys.stderr)

    def show_list(self):
        if not self.save_pending():
            return
        self.keyboard.close_keyboard()
        self.editor.hide()
        self.refresh_list()

    def back_to_menu(self):
        if self.save_pending():
            self.keyboard.close_keyboard()
            self.editor.hide()
            state.ui_queue.put(("menu", None))
