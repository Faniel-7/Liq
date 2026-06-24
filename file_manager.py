from pathlib import Path
import platform
import subprocess
import os

CURRENT_OS = platform.system().lower()

FOLDERS = {
    "downloads": Path.home() / "Downloads",
    "documents": Path.home() / "Documents",
    "desktop": Path.home() / "Desktop",
    "pictures": Path.home() / "Pictures",
    "music": Path.home() / "Music",
    "videos": Path.home() / "Videos",
    "home": Path.home(),
    "home folder": Path.home(),
}

def open_folder(name):
    folder = FOLDERS.get(name.lower())

    if folder is None:
        return False, "I don't recognize that folder."

    if not folder.exists():
        return False, f"{folder.name} does not exist."

    try:
        if CURRENT_OS == "windows":
            os.startfile(folder)

        elif CURRENT_OS == "darwin":
            subprocess.run(["open", str(folder)], check=True)

        else:
            subprocess.run(["xdg-open", str(folder)], check=True)

        return True, f"Opening {folder.name}."

    except Exception:
        return False, f"I couldn't open {folder.name}."

def handle_file_command(user_input):
    text = user_input.lower().strip()

    for folder in FOLDERS:
        if f"open {folder}" in text:
            return open_folder(folder)

    return None