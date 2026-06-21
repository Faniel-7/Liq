import platform
import subprocess
from pathlib import Path

CURRENT_OS = platform.system().lower()
CURRENT_OS_LABEL = "Zorin OS (Linux)" if CURRENT_OS == "linux" else platform.platform()

HOME_DIR = str(Path.home())


def _launch(commands):
    last_error = None

    for cmd in commands:
        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True, None
        except Exception as e:
            last_error = e

    return False, last_error


def open_app(command: str):
    cmd = command.strip().lower()

    if CURRENT_OS == "windows":
        registry = {
            "vscode": [["code"], ["Code"]],
            "browser": [["cmd", "/c", "start", "", "https://www.google.com"]],
            "file manager": [["explorer"]],
            "terminal": [["cmd"], ["powershell"]],
            "telegram": [["telegram"], ["Telegram"]],
        }

    elif CURRENT_OS == "darwin":
        registry = {
            "vscode": [["open", "-a", "Visual Studio Code"]],
            "browser": [["open", "https://www.google.com"]],
            "file manager": [["open", HOME_DIR]],
            "terminal": [["open", "-a", "Terminal"]],
            "telegram": [["open", "-a", "Telegram"]],
        }

    else:
        registry = {
            "vscode": [["code"], ["flatpak", "run", "com.visualstudio.code"]],
            "browser": [["xdg-open", "https://www.google.com"]],
            "file manager": [["xdg-open", HOME_DIR]],
            "terminal": [["gnome-terminal"], ["x-terminal-emulator"], ["konsole"], ["xfce4-terminal"]],
            "telegram": [["flatpak", "run", "org.telegram.desktop"]],
        }

    aliases = {
        "vscode": ["vscode", "vs code", "visual studio code"],
        "browser": ["browser", "web browser", "internet"],
        "file manager": ["file manager", "files", "folder"],
        "terminal": ["terminal"],
        "telegram": ["telegram"],
    }

    app_key = None
    for key, names in aliases.items():
        if cmd in names:
            app_key = key
            break

    if app_key is None:
        return False, "I do not know how to open that app yet."

    success, error = _launch(registry[app_key])

    if success:
        pretty_name = "VS Code" if app_key == "vscode" else app_key.title()
        return True, f"Opening {pretty_name}."

    pretty_name = "VS Code" if app_key == "vscode" else app_key.title()
    return False, f"Could not open {pretty_name}: {error}"