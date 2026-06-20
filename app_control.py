import subprocess
from pathlib import Path

HOME_DIR = str(Path.home())

def open_app(command: str):
    cmd = command.strip().lower()

    if cmd in ["vscode", "vs code", "visual studio code", "open vscode", "open vs code"]:
        commands = [
            ["code"],
            ["flatpak", "run", "com.visualstudio.code"],
        ]
        app_name = "VS Code"

    elif cmd in ["browser", "web browser", "internet", "open browser", "open web browser"]:
        commands = [
            ["xdg-open", "https://www.google.com"],
        ]
        app_name = "browser"

    elif cmd in ["file manager", "files", "folder", "open file manager", "open files"]:
        commands = [
            ["xdg-open", HOME_DIR],
        ]
        app_name = "file manager"

    elif cmd in ["terminal", "open terminal"]:
        commands = [
            ["gnome-terminal"],
            ["x-terminal-emulator"],
        ]
        app_name = "terminal"

    elif cmd in ["telegram", "open telegram", "launch telegram"]:
        commands = [
            ["telegram-desktop"],
            ["telegram"],
            ["flatpak", "run", "org.telegram.desktop"],
            ["snap", "run", "telegram-desktop"],
        ]
        app_name = "Telegram"

    else:
        return False, "I do not know how to open that app yet."

    last_error = None
    for c in commands:
        try:
            subprocess.Popen(c)
            return True, f"Opening {app_name}."
        except Exception as e:
            last_error = e

    return False, f"Could not open {app_name}: {last_error}"