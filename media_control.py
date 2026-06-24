import platform
import shutil
import subprocess
import re

CURRENT_OS = platform.system().lower()

def _run(cmd):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def get_players():
    if shutil.which("playerctl") is None:
        return []
    try:
        result = subprocess.run(
            ["playerctl", "-l"],
            capture_output=True,
            text=True,
            check=True
        )
        return [p.strip() for p in result.stdout.splitlines() if p.strip()]
    except Exception:
        return []

def parse_command(text: str):
    text = text.lower().strip()
    action = None
    player = None

    if any(x in text for x in ["play music", "resume", "start music", "play"]):
        action = "play-pause"
    elif any(x in text for x in ["pause", "stop music"]):
        action = "pause"
    elif "next" in text:
        action = "next"
    elif "previous" in text or "back song" in text:
        action = "previous"

    players = get_players()

    for p in players:
        if p.lower() in text:
            player = p
            break

    return action, player

def run_music(action, player=None):
    players = get_players()

    if CURRENT_OS != "linux":
        return False, "Music control is only supported on Linux."

    if shutil.which("playerctl") is None:
        return False, "playerctl is not installed."

    cmd = ["playerctl"]

    if player and player in players:
        cmd += ["-p", player]

    cmd.append(action)

    success = _run(cmd)

    if success:
        messages = {
            "play-pause": "Playing music.",
            "pause": "Paused.",
            "next": "Next track.",
            "previous": "Previous track"
        }
        return True, messages.get(action, "Done.")

    return False, "I couldn't control the media player."

def handle_music_command(user_input: str):
    action, player = parse_command(user_input)

    if not action:
        return None

    players = get_players()

    if not player and action == "play-pause":
        return {
            "ask_player": True,
            "action": action,
            "players": players
        }

    return {
        "ask_player": False,
        "action": action,
        "player": player
    }