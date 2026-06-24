from pathlib import Path
import os
import platform
import re
import shutil
import subprocess

CURRENT_OS = platform.system().lower()
HOME = Path.home()

STANDARD_FOLDERS = {
    "downloads": HOME / "Downloads",
    "documents": HOME / "Documents",
    "desktop": HOME / "Desktop",
    "pictures": HOME / "Pictures",
    "music": HOME / "Music",
    "videos": HOME / "Videos",
    "home": HOME,
    "home folder": HOME,
}

FILE_TYPE_EXTENSIONS = {
    "python": ".py",
    "py": ".py",
    "cpp": ".cpp",
    "c++": ".cpp",
    "c": ".c",
    "java": ".java",
    "javascript": ".js",
    "js": ".js",
    "typescript": ".ts",
    "ts": ".ts",
    "html": ".html",
    "css": ".css",
    "json": ".json",
    "txt": ".txt",
    "text": ".txt",
    "markdown": ".md",
    "md": ".md",
    "yaml": ".yaml",
    "yml": ".yml",
    "xml": ".xml",
    "sh": ".sh",
    "bash": ".sh",
    "go": ".go",
    "rust": ".rs",
    "rs": ".rs",
    "php": ".php",
    "sql": ".sql",
    "csv": ".csv",
    "dart": ".dart",
    "swift": ".swift",
    "kotlin": ".kt",
    "kt": ".kt",
    "ruby": ".rb",
    "rb": ".rb",
    "perl": ".pl",
    "pl": ".pl",
    "lua": ".lua",
    "r": ".r",
    "matlab": ".m",
    "m": ".m",
    "objective-c": ".m",
    "objc": ".m",
    "csharp": ".cs",
    "c#": ".cs",
    "cs": ".cs",
}

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

def _clean_text(value: str) -> str:
    return value.strip().strip('"').strip("'").strip()

def _resolve_standard_folder(name: str):
    return STANDARD_FOLDERS.get(_normalize(name))

def _resolve_any_path(value: str, default_base: Path | None = None):
    value = _clean_text(value)

    standard = _resolve_standard_folder(value)
    if standard is not None:
        return standard

    path = Path(value).expanduser()
    if path.is_absolute():
        return path

    if default_base is None:
        default_base = HOME

    return default_base / path

def _open_path(path: Path):
    try:
        if CURRENT_OS == "windows":
            os.startfile(str(path))
        elif CURRENT_OS == "darwin":
            subprocess.run(
                ["open", str(path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.run(
                ["xdg-open", str(path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return True, f"Opening {path.name if path.name else 'home'}."
    except Exception as e:
        return False, f"I couldn't open it: {e}"

def _create_folder(name: str, location: str | None = None):
    folder_name = _clean_text(name)
    base = HOME if location is None else _resolve_any_path(location, HOME)

    if not base.is_absolute():
        base = HOME / base

    target = Path(folder_name).expanduser()
    final_path = target if target.is_absolute() else base / target

    try:
        final_path.mkdir(parents=True, exist_ok=True)
        return True, f"Created folder {final_path.name}."
    except Exception as e:
        return False, f"I couldn't create the folder: {e}"

def _normalize_file_type(file_type: str | None):
    if not file_type:
        return None

    raw = _clean_text(file_type).lower()

    if raw.startswith(".") and len(raw) > 1:
        return raw

    if raw in FILE_TYPE_EXTENSIONS:
        return FILE_TYPE_EXTENSIONS[raw]

    if re.fullmatch(r"[a-z0-9+#._-]+", raw):
        return f".{raw}"

    return None

def _add_extension_if_missing(name: str, file_type: str | None):
    name = _clean_text(name)

    if "." in Path(name).name:
        return name

    ext = _normalize_file_type(file_type)
    if ext:
        return name + ext

    return name

def _create_file(name: str, location: str | None = None, file_type: str | None = None):
    file_name = _add_extension_if_missing(name, file_type)
    base = HOME if location is None else _resolve_any_path(location, HOME)

    if not base.is_absolute():
        base = HOME / base

    target = Path(file_name).expanduser()
    final_path = target if target.is_absolute() else base / target

    try:
        final_path.parent.mkdir(parents=True, exist_ok=True)
        final_path.touch(exist_ok=True)
        return True, f"Created file {final_path.name}."
    except Exception as e:
        return False, f"I couldn't create the file: {e}"

def _rename_path(source_text: str, target_text: str):
    source = _resolve_any_path(source_text, HOME)
    if not source.is_absolute():
        source = HOME / source

    if not source.exists():
        return False, f"{source.name} does not exist."

    target_text = _clean_text(target_text)
    target_path = Path(target_text).expanduser()

    if not target_path.is_absolute():
        target_path = source.with_name(target_text)

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target_path)
        return True, f"Renamed {source.name} to {target_path.name}."
    except Exception as e:
        return False, f"I couldn't rename it: {e}"

def _move_or_copy(action: str, source_text: str, destination_text: str):
    source = _resolve_any_path(source_text, HOME)
    if not source.is_absolute():
        source = HOME / source

    if not source.exists():
        return False, f"{source.name} does not exist."

    destination_text = _clean_text(destination_text)
    destination = _resolve_any_path(destination_text, HOME)

    if not destination.is_absolute():
        destination = HOME / destination

    try:
        if destination.exists() and destination.is_dir():
            final_path = destination / source.name
        else:
            if (
                not destination.exists()
                and destination.suffix == ""
                and not any(sep in destination_text for sep in ["/", "\\"])
            ):
                destination.mkdir(parents=True, exist_ok=True)
                final_path = destination / source.name
            else:
                final_path = destination

        if action == "move":
            final_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(final_path))
            return True, f"Moved {source.name}."

        if action == "copy":
            final_path.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(str(source), str(final_path), dirs_exist_ok=True)
            else:
                shutil.copy2(str(source), str(final_path))
            return True, f"Copied {source.name}."

        return False, "Unknown action."
    except Exception as e:
        return False, f"I couldn't {action} it: {e}"

def _delete_path(target_text: str):
    text = _normalize(target_text)

    if "confirm" not in text:
        return False, "Say delete confirm followed by the file or folder name."

    cleaned = re.sub(r"\bconfirm\b", "", text).strip()
    cleaned = re.sub(r"^(delete|remove)\s+", "", cleaned).strip()

    target = _resolve_any_path(cleaned, HOME)
    if not target.is_absolute():
        target = HOME / target

    if not target.exists():
        return False, f"{target.name} does not exist."

    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        return True, f"Deleted {target.name}."
    except Exception as e:
        return False, f"I couldn't delete it: {e}"

def handle_file_command(user_input: str):
    text = _normalize(user_input)

    open_match = re.match(r"^(?:open|show|go to)\s+(?:the\s+)?(.+)$", text)
    if open_match:
        target_text = open_match.group(1).strip()
        target = _resolve_standard_folder(target_text)
        if target is not None:
            if not target.exists():
                return False, f"{target.name} does not exist."
            return _open_path(target)

        if "folder" in target_text:
            target_text = target_text.replace("folder", "").strip()

        target_path = _resolve_any_path(target_text, HOME)
        if not target_path.is_absolute():
            target_path = HOME / target_path

        if target_path.exists():
            return _open_path(target_path)

        return False, "I couldn't find that folder or file."

    folder_match = re.match(
        r"^(?:create|make|new)\s+(?:a\s+)?folder(?:\s+(?:called|named)\s+|\s+)(.+?)(?:\s+(?:in|inside|under|at|to)\s+(.+))?$",
        text,
    )
    if folder_match:
        folder_name = folder_match.group(1).strip()
        location = folder_match.group(2).strip() if folder_match.group(2) else None
        return _create_folder(folder_name, location)

    file_match = re.match(
        r"^(?:create|make|new)\s+(?:a\s+)?(?:(?P<type>[a-z0-9+#._-]+)\s+)?file(?:\s+(?:called|named)\s+|\s+)(?P<name>.+?)(?:\s+(?:in|inside|under|at|to)\s+(?P<location>.+))?$",
        text,
    )
    if file_match:
        file_type = file_match.group("type")
        file_name = file_match.group("name").strip()
        location = file_match.group("location").strip() if file_match.group("location") else None
        return _create_file(file_name, location, file_type)

    rename_match = re.match(r"^(?:rename|change name of)\s+(.+?)\s+(?:to|into)\s+(.+)$", text)
    if rename_match:
        return _rename_path(rename_match.group(1), rename_match.group(2))

    move_match = re.match(r"^(?:move)\s+(.+?)\s+(?:to|into)\s+(.+)$", text)
    if move_match:
        return _move_or_copy("move", move_match.group(1), move_match.group(2))

    copy_match = re.match(r"^(?:copy)\s+(.+?)\s+(?:to|into)\s+(.+)$", text)
    if copy_match:
        return _move_or_copy("copy", copy_match.group(1), copy_match.group(2))

    delete_match = re.match(r"^(?:delete|remove)\s+(.+)$", text)
    if delete_match:
        return _delete_path(delete_match.group(0))

    return None