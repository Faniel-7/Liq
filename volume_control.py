import platform
import re
import shutil
import subprocess

CURRENT_OS = platform.system().lower()

def parse_volume_command(user_input: str):
    text = re.sub(r"\s+", " ", user_input.lower().strip())

    match = re.search(r"\b(?:set|change|adjust)?\s*volume(?:\s+to)?\s+(\d{1,3})\b", text)
    if match:
        level = int(match.group(1))
        if 0 <= level <= 100:
            return "set", level

    if "unmute" in text:
        return "unmute", None

    if "mute" in text:
        return "mute", None

    if any(word in text for word in ["volume up", "turn it up", "louder", "increase volume", "raise volume", "up volume"]):
        return "up", None

    if any(word in text for word in ["volume down", "turn it down", "quieter", "decrease volume", "lower volume", "down volume"]):
        return "down", None

    return None, None

def _linux_volume(action, level):
    if shutil.which("pactl"):
        if action == "mute":
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], check=True)
        elif action == "unmute":
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], check=True)
        elif action == "up":
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"], check=True)
        elif action == "down":
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"], check=True)
        elif action == "set":
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"], check=True)
        else:
            return False, "Unknown volume action."

        return True, {
            "mute": "Muted.",
            "unmute": "Unmuted.",
            "up": "Volume increased.",
            "down": "Volume decreased.",
            "set": f"Volume set to {level} percent."
        }[action]

    if shutil.which("amixer"):
        if action == "mute":
            subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "mute"], check=True)
        elif action == "unmute":
            subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "unmute"], check=True)
        elif action == "up":
            subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%+"], check=True)
        elif action == "down":
            subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%-"], check=True)
        elif action == "set":
            subprocess.run(["amixer", "-D", "pulse", "sset", "Master", f"{level}%"], check=True)
        else:
            return False, "Unknown volume action."

        return True, {
            "mute": "Muted.",
            "unmute": "Unmuted.",
            "up": "Volume increased.",
            "down": "Volume decreased.",
            "set": f"Volume set to {level} percent."
        }[action]

    return False, "No volume tool found."

def _macos_volume(action, level):
    if action == "mute":
        script = "set volume with output muted"
    elif action == "unmute":
        script = "set volume without output muted"
    elif action == "up":
        script = 'set volume output volume ((output volume of (get volume settings)) + 10)'
    elif action == "down":
        script = 'set volume output volume ((output volume of (get volume settings)) - 10)'
    elif action == "set":
        script = f"set volume output volume {level}"
    else:
        return False, "Unknown volume action."

    try:
        subprocess.run(
            ["osascript", "-e", script],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True, {
            "mute": "Muted.",
            "unmute": "Unmuted.",
            "up": "Volume increased.",
            "down": "Volume decreased.",
            "set": f"Volume set to {level} percent."
        }[action]
    except Exception as e:
        return False, f"Could not change volume: {e}"

def _windows_volume(action, level):
    try:
        from ctypes import POINTER, cast
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    except Exception:
        return False, "Windows volume support needs pycaw and comtypes."

    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        if action == "mute":
            volume.SetMute(1, None)
        elif action == "unmute":
            volume.SetMute(0, None)
        elif action == "up":
            current = volume.GetMasterVolumeLevelScalar()
            volume.SetMasterVolumeLevelScalar(min(1.0, current + 0.10), None)
        elif action == "down":
            current = volume.GetMasterVolumeLevelScalar()
            volume.SetMasterVolumeLevelScalar(max(0.0, current - 0.10), None)
        elif action == "set":
            volume.SetMasterVolumeLevelScalar(max(0.0, min(1.0, level / 100.0)), None)
        else:
            return False, "Unknown volume action."

        return True, {
            "mute": "Muted.",
            "unmute": "Unmuted.",
            "up": "Volume increased.",
            "down": "Volume decreased.",
            "set": f"Volume set to {level} percent."
        }[action]
    except Exception as e:
        return False, f"Could not change volume: {e}"

def run_volume(action, level=None):
    if CURRENT_OS == "linux":
        return _linux_volume(action, level)

    if CURRENT_OS == "darwin":
        return _macos_volume(action, level)

    if CURRENT_OS == "windows":
        return _windows_volume(action, level)

    return False, "Unsupported operating system."

def handle_volume_command(user_input: str):
    action, level = parse_volume_command(user_input)

    if not action:
        return None

    return run_volume(action, level)