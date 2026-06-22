import platform
import re
import shutil
import subprocess

CURRENT_OS = platform.system().lower()

PLAYER_ALIASES = {
    "vlc": ["vlc", "vlc player"],
    "potplayer": ["potplayer", "pot player"],
    "qqplayer": ["qqplayer", "qq player"],
    "chrome": ["chrome", "google chrome", "youtube on chrome", "youtube in chrome", "chrome youtube"],
    "chromium": ["chromium"],
    "edge": ["edge", "microsoft edge"],
    "firefox": ["firefox", "youtube on firefox", "youtube in firefox"],
    "spotify": ["spotify"],
    "youtube": ["youtube", "youtube music"],
}

def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())

def _extract_action(text: str):
    text = _normalize_text(text)

    if any(phrase in text for phrase in [
        "play music", "resume music", "start music", "play song", "resume song",
        "play", "resume"
    ]):
        return "play"

    if any(phrase in text for phrase in [
        "pause music", "pause song", "stop music", "stop song",
        "pause", "stop"
    ]):
        return "pause"

    if any(phrase in text for phrase in [
        "next song", "next track", "skip song", "skip track", "next"
    ]):
        return "next"

    if any(phrase in text for phrase in [
        "previous song", "previous track", "go back", "back song", "previous", "back"
    ]):
        return "previous"

    return None

def _extract_player_hint(text: str):
    text = _normalize_text(text)

    for canonical, aliases in PLAYER_ALIASES.items():
        for alias in sorted(aliases, key=len, reverse=True):
            alias_norm = _normalize_text(alias)

            if f" on {alias_norm}" in text:
                return canonical
            if f" in {alias_norm}" in text:
                return canonical
            if text == alias_norm:
                return canonical
            if text.endswith(alias_norm):
                return canonical

    return None

def parse_music_command(user_input: str):
    text = _normalize_text(user_input)
    action = _extract_action(text)
    player = _extract_player_hint(text)
    return action, player

def get_available_players():
    if CURRENT_OS != "linux":
        return []

    if shutil.which("playerctl") is None:
        return []

    try:
        result = subprocess.run(
            ["playerctl", "-l"],
            capture_output=True,
            text=True,
            check=True
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []

def _resolve_player_identifier(player_hint: str | None, available_players: list[str]):
    if not player_hint or not available_players:
        return None

    hint = _normalize_text(player_hint)

    
    for candidate in available_players:
        candidate_norm = _normalize_text(candidate)
        if hint == candidate_norm:
            return candidate
        if hint in candidate_norm:
            return candidate
        if candidate_norm in hint:
            return candidate

    
    aliases = PLAYER_ALIASES.get(hint, [hint])
    for candidate in available_players:
        candidate_norm = _normalize_text(candidate)
        for alias in aliases:
            alias_norm = _normalize_text(alias)
            if alias_norm == candidate_norm:
                return candidate
            if alias_norm in candidate_norm:
                return candidate
            if candidate_norm in alias_norm:
                return candidate

    return None

def get_available_players():
    if CURRENT_OS != "linux":
        return []

    if shutil.which("playerctl") is None:
        return []

    try:
        result = subprocess.run(
            ["playerctl", "-l"],
            capture_output=True,
            text=True,
            check=True
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []

def _run_linux(action: str, player: str | None):
    if shutil.which("playerctl") is None:
        return False, "playerctl is not installed."

    available_players = get_available_players()
    resolved_player = _resolve_player_identifier(player, available_players)

    if player and not resolved_player:
        if available_players:
            return False, f"I could not find that player. Available players: {', '.join(available_players)}."
        return False, "I could not find any active media players."

    cmd = ["playerctl"]
    if resolved_player:
        cmd.extend(["-p", resolved_player])
    cmd.append(action)

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        messages = {
            "play-pause": "Playing music.",
            "pause": "Pausing music.",
            "next": "Skipping to the next track.",
            "previous": "Going to the previous track.",
        }
        return True, messages.get(action, "Done.")
    except subprocess.CalledProcessError:
        return False, "I could not control that player right now."
    except Exception as e:
        return False, f"Music control error: {e}"

def _run_windows(action: str, player: str | None):
    key_map = {
        "play-pause": "0xB3",
        "pause": "0xB3",
        "next": "0xB0",
        "previous": "0xB1",
    }

    vk = key_map.get(action)
    if vk is None:
        return False, "Unknown music action."

    ps_script = f'''
$code = @"
using System;
using System.Runtime.InteropServices;
public class K {{
    [DllImport("user32.dll", SetLastError = true)]
    public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
}}
"@
Add-Type $code
[K]::keybd_event({vk}, 0, 0, [UIntPtr]::Zero)
[K]::keybd_event({vk}, 0, 2, [UIntPtr]::Zero)
'''

    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        messages = {
            "play-pause": "Playing music.",
            "pause": "Pausing music.",
            "next": "Skipping to the next track.",
            "previous": "Going to the previous track.",
        }
        return True, messages.get(action, "Done.")
    except Exception as e:
        return False, f"Music control error: {e}"

def _run_macos(action: str, player: str | None):
    if action == "play-pause":
        script_names = ["Music", "Spotify"]
        applescript_action = "playpause"
    elif action == "pause":
        script_names = ["Music", "Spotify"]
        applescript_action = "pause"
    elif action == "next":
        script_names = ["Music", "Spotify"]
        applescript_action = "next track"
    elif action == "previous":
        script_names = ["Music", "Spotify"]
        applescript_action = "previous track"
    else:
        return False, "Unknown music action."

    last_error = None
    for app_name in script_names:
        try:
            subprocess.run(
                ["osascript", "-e", f'tell application "{app_name}" to {applescript_action}'],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            messages = {
                "play-pause": "Playing music.",
                "pause": "Pausing music.",
                "next": "Skipping to the next track.",
                "previous": "Going to the previous track.",
            }
            return True, messages.get(action, "Done.")
        except Exception as e:
            last_error = e

    return False, f"I could not control music right now: {last_error}"

def run_music_command(action: str, player: str | None = None):
    if action == "play":
        action = "play-pause"

    if CURRENT_OS == "linux":
        return _run_linux(action, player)

    if CURRENT_OS == "windows":
        return _run_windows(action, player)

    if CURRENT_OS == "darwin":
        return _run_macos(action, player)

    return False, "Unsupported operating system."

def handle_music_command(user_input: str):
    action, player = parse_music_command(user_input)
    if not action:
        return None

    
    if action == "play" and not player:
        return {
            "needs_player": True,
            "action": "play-pause",
            "player": None,
            "available_players": get_available_players(),
        }

    return {
        "needs_player": False,
        "action": "play-pause" if action == "play" else action,
        "player": player,
    }