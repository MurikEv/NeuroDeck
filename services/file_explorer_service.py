from copy import deepcopy
import errno
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import stat
import tempfile
import time
from uuid import uuid4


DEFAULT_STATE_PATH = Path(__file__).resolve().parents[1] / "data" / "file_explorer" / "state.json"
SORT_MODES = ("latest", "oldest", "name_asc", "name_desc", "size_asc", "size_desc")


def read_disk_usage(path):
    candidate = Path(path).absolute()
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    if candidate.is_file():
        candidate = candidate.parent
    usage = shutil.disk_usage(candidate)
    if usage.total <= 0 or usage.used < 0 or usage.free < 0:
        raise OSError("Invalid disk capacity")
    return {"total": usage.total, "used": usage.used, "free": usage.free}


class FileExplorerStorageError(Exception):
    pass


class FileExplorerStore:
    def __init__(self, roots, state_path=DEFAULT_STATE_PATH):
        try:
            if not isinstance(roots, dict) or not roots or any(not isinstance(key, str) or not key for key in roots):
                raise ValueError("File roots must have non-empty names")
            self.roots = {key: Path(value).resolve() for key, value in roots.items()}
            self.path = Path(state_path).absolute()
            self._reject_symlinks(self.path)
            self.path = self.path.resolve()
            self.state_path = self.path
            self.trash_dir = self.path.parent / "trash"
            self._state = self._load()
        except FileExplorerStorageError:
            raise
        except (OSError, ValueError, TypeError) as exc:
            raise FileExplorerStorageError(f"Cannot initialize File Explorer storage: {exc}") from exc

    @property
    def sort_mode(self):
        return self._state["sort_mode"]

    def is_favorite(self, path):
        try:
            reference = self._reference(path, require_file=False)
        except FileExplorerStorageError:
            return False
        return reference in self._state["favorites"]

    def favorites(self):
        paths = []
        for reference in self._state["favorites"]:
            try:
                path = self._reference_path(reference)
                self._regular_file(path)
            except FileExplorerStorageError:
                continue
            paths.append(path)
        return paths

    def toggle_favorite(self, path):
        reference = self._reference(path)
        data = deepcopy(self._state)
        favorite = reference not in data["favorites"]
        if favorite:
            data["favorites"].append(reference)
        else:
            data["favorites"].remove(reference)
        self._commit(data)
        return favorite

    def set_sort(self, mode):
        if mode not in SORT_MODES:
            raise FileExplorerStorageError(f"Unsupported sort mode: {mode}")
        if mode != self.sort_mode:
            data = deepcopy(self._state)
            data["sort_mode"] = mode
            self._commit(data)

    def trash_entries(self):
        entries = []
        for record in self._state["trash"]:
            try:
                path = self._trash_path(record)
                self._regular_file(path)
                reference = record["original"]
                original = self.roots[reference["root"]].joinpath(*reference["path"].split("/"))
            except FileExplorerStorageError:
                continue
            entries.append({
                "id": record["id"], "path": path, "name": record["name"],
                "original_path": original, "is_favorite": record["favorite"],
                "deleted_ns": record["deleted_ns"],
            })
        return sorted(entries, key=lambda entry: (-entry["deleted_ns"], entry["name"].casefold()))

    def trash_file(self, path):
        reference = self._reference(path)
        source = self._reference_path(reference)
        self._assert_current()
        record = {
            "id": uuid4().hex, "name": source.name, "original": reference,
            "deleted_ns": time.time_ns(), "favorite": self.is_favorite(source),
        }
        destination = self._trash_path(record)
        created_directory = False
        try:
            destination.parent.mkdir(parents=True, exist_ok=False)
            created_directory = True
            self._reject_symlinks(destination)
            self._move_file(source, destination)
        except (OSError, ValueError) as exc:
            if created_directory:
                self._remove_empty_directory(destination.parent)
            raise FileExplorerStorageError(f"Cannot move {source.name} to Trash: {exc}") from exc
        data = deepcopy(self._state)
        data["favorites"] = [value for value in data["favorites"] if value != reference]
        data["trash"].append(record)
        try:
            self._commit(data)
        except FileExplorerStorageError as exc:
            self._rollback_move(destination, source, exc)
            self._remove_empty_directory(destination.parent)
            raise
        return {
            "id": record["id"], "path": destination, "name": record["name"],
            "original_path": source, "is_favorite": record["favorite"],
            "deleted_ns": record["deleted_ns"],
        }

    def restore_file(self, trashpath):
        record = self._find_trash_record(trashpath)
        source = self._trash_path(record)
        self._regular_file(source)
        self._assert_current()
        original = self._reference_path(record["original"])
        destination = self._restore_destination(original)
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            self._reject_symlinks(destination)
            while True:
                try:
                    self._move_file(source, destination)
                    break
                except FileExistsError:
                    destination = self._restore_destination(original)
        except (OSError, ValueError) as exc:
            raise FileExplorerStorageError(f"Cannot restore {record['name']}: {exc}") from exc
        try:
            data = deepcopy(self._state)
            data["trash"] = [value for value in data["trash"] if value["id"] != record["id"]]
            if record["favorite"]:
                reference = self._reference(destination)
                if reference not in data["favorites"]:
                    data["favorites"].append(reference)
            self._commit(data)
        except FileExplorerStorageError as exc:
            self._rollback_move(destination, source, exc)
            raise
        self._remove_empty_directory(source.parent)
        return destination

    def delete_permanently(self, trashpath):
        record = self._find_trash_record(trashpath)
        source = self._trash_path(record)
        try:
            if source.exists():
                self._regular_file(source)
        except OSError as exc:
            raise FileExplorerStorageError(f"Cannot access {record['name']}: {exc}") from exc
        before = deepcopy(self._state)
        data = deepcopy(before)
        data["trash"] = [value for value in data["trash"] if value["id"] != record["id"]]
        self._commit(data)
        try:
            source.unlink(missing_ok=True)
        except OSError as exc:
            try:
                self._commit(before)
            except FileExplorerStorageError as rollback:
                raise FileExplorerStorageError(f"Cannot delete {record['name']}; file remains at {source}. Cannot restore Trash index: {rollback}") from exc
            raise FileExplorerStorageError(f"Cannot delete {record['name']}: {exc}") from exc
        self._remove_empty_directory(source.parent)
        return True

    def _reference(self, path, require_file=True):
        try:
            candidate = Path(path)
            if ".." in candidate.parts:
                raise ValueError("Parent path traversal is not allowed")
            candidate = candidate.absolute()
            self._reject_symlinks(candidate)
            if candidate == self.path or candidate.is_relative_to(self.trash_dir):
                raise ValueError("Storage files are not source files")
            for key, root in sorted(self.roots.items(), key=lambda item: len(item[1].parts), reverse=True):
                if candidate.is_relative_to(root) and candidate != root:
                    if not candidate.resolve().is_relative_to(root):
                        raise ValueError("File resolves outside its root")
                    reference = {"root": key, "path": candidate.relative_to(root).as_posix()}
                    self._validate_reference(reference)
                    if require_file:
                        self._regular_file(candidate)
                    return reference
            raise ValueError("File is outside the configured roots")
        except FileExplorerStorageError:
            raise
        except (OSError, TypeError, ValueError) as exc:
            raise FileExplorerStorageError(f"Invalid file path: {exc}") from exc

    def _reference_path(self, reference):
        self._validate_reference(reference)
        path = self.roots[reference["root"]].joinpath(*reference["path"].split("/"))
        try:
            self._reject_symlinks(path)
            if not path.resolve().is_relative_to(self.roots[reference["root"]]):
                raise ValueError("File resolves outside its root")
        except (OSError, ValueError) as exc:
            raise FileExplorerStorageError(f"Invalid file path: {exc}") from exc
        return path

    def _trash_path(self, record):
        path = self.trash_dir / record["id"] / record["name"]
        try:
            self._reject_symlinks(path)
            if not path.resolve().is_relative_to(self.trash_dir):
                raise ValueError("File resolves outside Trash")
        except (OSError, ValueError) as exc:
            raise FileExplorerStorageError(f"Invalid Trash path: {exc}") from exc
        return path

    def _find_trash_record(self, path):
        try:
            candidate = Path(path)
            if ".." in candidate.parts:
                raise ValueError("Parent path traversal is not allowed")
            candidate = candidate.absolute()
            self._reject_symlinks(candidate)
            for record in self._state["trash"]:
                if candidate == self.trash_dir / record["id"] / record["name"]:
                    self._trash_path(record)
                    return dict(record)
        except (OSError, ValueError, TypeError) as exc:
            raise FileExplorerStorageError(f"Invalid Trash file: {exc}") from exc
        raise FileExplorerStorageError("File is not in Trash")

    def _restore_destination(self, original):
        try:
            destination = original
            counter = 1
            while destination.exists() or destination.is_symlink():
                destination = original.with_name(f"{original.stem} (restored {counter}){original.suffix}")
                counter += 1
            self._reference(destination, require_file=False)
            return destination
        except OSError as exc:
            raise FileExplorerStorageError(f"Cannot choose a restore location for {original.name}: {exc}") from exc

    @staticmethod
    def _regular_file(path):
        try:
            FileExplorerStore._reject_symlinks(path)
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError("Expected a regular file")
        except (OSError, ValueError) as exc:
            raise FileExplorerStorageError(f"File unavailable: {path}: {exc}") from exc

    @staticmethod
    def _reject_symlinks(path):
        for candidate in (path, *path.parents):
            if candidate.is_symlink() or (hasattr(candidate, "is_junction") and candidate.is_junction()):
                raise ValueError("Symbolic links are not supported")

    @staticmethod
    def _move_file(source, destination):
        created = False
        try:
            try:
                os.link(source, destination, follow_symlinks=False)
                created = True
            except OSError as exc:
                if exc.errno not in {errno.EXDEV, errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EMLINK}:
                    raise
                with source.open("rb") as incoming, destination.open("xb") as outgoing:
                    created = True
                    shutil.copyfileobj(incoming, outgoing)
                    outgoing.flush()
                    os.fsync(outgoing.fileno())
                shutil.copystat(source, destination, follow_symlinks=False)
            source.unlink()
        except (OSError, ValueError):
            if created:
                try:
                    destination.unlink(missing_ok=True)
                except OSError:
                    pass
            raise

    @staticmethod
    def _remove_empty_directory(path):
        try:
            path.rmdir()
        except OSError:
            pass

    def _rollback_move(self, source, destination, error):
        try:
            self._move_file(source, destination)
        except (OSError, ValueError) as rollback:
            raise FileExplorerStorageError(f"{error}; file remains at {source}. Cannot move it back: {rollback}") from error

    @staticmethod
    def _default_state():
        return {"version": 1, "sort_mode": "latest", "favorites": [], "trash": []}

    def _validate_reference(self, reference):
        if not isinstance(reference, dict) or set(reference) != {"root", "path"}:
            raise ValueError("Invalid file reference")
        value = reference["path"]
        if not isinstance(reference["root"], str) or reference["root"] not in self.roots:
            raise ValueError("Unknown file root")
        if not isinstance(value, str) or not value or any(part in ("", ".", "..") for part in value.split("/")):
            raise ValueError("File references must be relative paths")
        if "\\" in value or ":" in value or "\x00" in value or PurePosixPath(value).is_absolute() or PureWindowsPath(value).drive:
            raise ValueError("Unsafe file reference")

    def _validate(self, data):
        if not isinstance(data, dict) or set(data) != {"version", "sort_mode", "favorites", "trash"}:
            raise ValueError("Expected version, sort_mode, favorites and trash")
        if type(data["version"]) is not int or data["version"] != 1:
            raise ValueError("Unsupported storage version")
        if data["sort_mode"] not in SORT_MODES:
            raise ValueError("Unsupported sort mode")
        if not isinstance(data["favorites"], list) or not isinstance(data["trash"], list):
            raise ValueError("Favorites and Trash must be lists")
        references = set()
        for reference in data["favorites"]:
            self._validate_reference(reference)
            key = reference["root"], reference["path"]
            if key in references:
                raise ValueError("Duplicate favorite reference")
            references.add(key)
        ids = set()
        for record in data["trash"]:
            if not isinstance(record, dict) or set(record) != {"id", "name", "original", "deleted_ns", "favorite"}:
                raise ValueError("Invalid Trash record")
            if not isinstance(record["id"], str) or len(record["id"]) != 32 or any(character not in "0123456789abcdef" for character in record["id"]):
                raise ValueError("Invalid Trash ID")
            if record["id"] in ids:
                raise ValueError("Duplicate Trash ID")
            ids.add(record["id"])
            self._validate_reference(record["original"])
            if not isinstance(record["name"], str) or record["name"] != PurePosixPath(record["original"]["path"]).name:
                raise ValueError("Invalid Trash filename")
            if type(record["favorite"]) is not bool or type(record["deleted_ns"]) is not int or record["deleted_ns"] <= 0:
                raise ValueError("Invalid Trash metadata")

    def _load(self):
        try:
            self._reject_symlinks(self.path)
            with self.path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
        except FileNotFoundError:
            return self._default_state()
        except (OSError, UnicodeError, ValueError) as exc:
            raise FileExplorerStorageError(f"Cannot read File Explorer storage at {self.path}: {exc}") from exc
        try:
            self._validate(data)
        except (TypeError, ValueError) as exc:
            raise FileExplorerStorageError(f"Invalid File Explorer storage at {self.path}: {exc}") from exc
        return data

    def _assert_current(self):
        if self._load() != self._state:
            raise FileExplorerStorageError("File Explorer settings changed outside the app; restart NeuroDeck before saving")

    def _commit(self, data):
        self._assert_current()
        temporary = None
        try:
            self._validate(data)
            self._reject_symlinks(self.path)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", dir=self.path.parent,
                prefix=f".{self.path.name}.", suffix=".tmp", delete=False,
            ) as stream:
                temporary = Path(stream.name)
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except (OSError, UnicodeError, TypeError, ValueError) as exc:
            raise FileExplorerStorageError(f"Cannot save File Explorer storage at {self.path}: {exc}") from exc
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
        self._state = data
