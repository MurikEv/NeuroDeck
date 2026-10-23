"""Small, local JSON store for Notepad; no Qt or hardware dependencies."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4


DEFAULT_NOTES_PATH = Path(__file__).resolve().parents[1] / "data" / "notepad" / "notes.json"
_NOTE_FIELDS = {"id", "title", "body", "created_at", "updated_at", "favorite", "archived"}


class NotepadStorageError(Exception):
    """Notes could not be read, validated, or safely saved."""


class NotepadStore:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else DEFAULT_NOTES_PATH
        self._notes = self._load()

    @property
    def notes(self):
        """Return independent copies so callers cannot bypass saving."""
        return [dict(note) for note in self._notes]

    def upsert(self, note_id=None, title="", body="", favorite=False, archived=False):
        if not isinstance(title, str) or not isinstance(body, str):
            raise NotepadStorageError("Note title and body must be strings")
        if type(favorite) is not bool or type(archived) is not bool:
            raise NotepadStorageError("Note favorite and archived flags must be booleans")
        if note_id is not None and (not isinstance(note_id, str) or not note_id):
            raise NotepadStorageError("Note ID must be a non-empty string")

        notes = self.notes
        index = next((i for i, note in enumerate(notes) if note["id"] == note_id), None)
        if note_id is not None and index is None:
            raise NotepadStorageError(f"Note not found: {note_id}")
        now = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        note = {
            "id": note_id if index is not None else uuid4().hex,
            "title": title,
            "body": body,
            "created_at": notes[index]["created_at"] if index is not None else now,
            "updated_at": now,
            "favorite": favorite,
            "archived": archived,
        }
        if index is None:
            notes.append(note)
        else:
            notes[index] = note
        self._save(notes)
        self._notes = notes
        return dict(note)

    def delete(self, note_id):
        if not isinstance(note_id, str) or not note_id:
            raise NotepadStorageError("Note ID must be a non-empty string")
        notes = [dict(note) for note in self._notes if note["id"] != note_id]
        if len(notes) == len(self._notes):
            return False
        self._save(notes)
        self._notes = notes
        return True

    def _load(self):
        try:
            with self.path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
        except FileNotFoundError:
            return []
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise NotepadStorageError(f"Cannot read notes at {self.path}: {error}") from error
        try:
            self._validate(data)
        except (ValueError, TypeError) as error:
            raise NotepadStorageError(f"Invalid notes at {self.path}: {error}") from error
        return [dict(note) for note in data["notes"]]

    @staticmethod
    def _validate(data):
        if not isinstance(data, dict) or set(data) != {"version", "notes"}:
            raise ValueError("expected an object with version and notes")
        if type(data["version"]) is not int or data["version"] != 1:
            raise ValueError("unsupported notes version")
        if not isinstance(data["notes"], list):
            raise ValueError("notes must be a list")
        ids = set()
        for note in data["notes"]:
            if not isinstance(note, dict) or set(note) != _NOTE_FIELDS:
                raise ValueError("each note must contain all expected fields")
            if not isinstance(note["id"], str) or not note["id"]:
                raise ValueError("note ID must be a non-empty string")
            if note["id"] in ids:
                raise ValueError(f"duplicate note ID: {note['id']}")
            ids.add(note["id"])
            if not isinstance(note["title"], str) or not isinstance(note["body"], str):
                raise ValueError("note title and body must be strings")
            if type(note["favorite"]) is not bool or type(note["archived"]) is not bool:
                raise ValueError("note flags must be booleans")
            for key in ("created_at", "updated_at"):
                if not isinstance(note[key], str):
                    raise ValueError(f"{key} must be an ISO8601 timestamp")
                stamp = datetime.fromisoformat(note[key].replace("Z", "+00:00"))
                if stamp.tzinfo is None or stamp.utcoffset() is None:
                    raise ValueError(f"{key} must include a timezone")

    def _save(self, notes):
        temporary_path = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", dir=self.path.parent,
                prefix=f".{self.path.name}.", suffix=".tmp", delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                json.dump({"version": 1, "notes": notes}, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self.path)
        except (OSError, UnicodeError, ValueError, TypeError) as error:
            raise NotepadStorageError(f"Cannot save notes at {self.path}: {error}") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
