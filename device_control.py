from pathlib import Path
from datetime import datetime
import os
import platform
import random
import re
import shutil
import signal
import subprocess
import threading
import time

try:
    import psutil
except Exception:
    psutil = None

try:
    import pyautogui
except Exception:
    pyautogui = None

CURRENT_OS = platform.system().lower()
_RECORDING_PROCESS = None
_RECORDING_PATH = None
_RECORDING_TIMER = None

def _run(cmd):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, None
    except Exception as e:
        return False, e

def _short_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.home()))
    except Exception:
        return str(path)

def _screenshot_path():
    folder = Path.home() / "Pictures" / "Liq Screenshots"
    folder.mkdir(parents=True, exist_ok=True)
    name = datetime.now().strftime("shot_%y%m%d-%H%M%S.png")
    return folder / name

def _recording_path():
    folder = Path.home() / "Videos" / "Liq Recordings"
    folder.mkdir(parents=True, exist_ok=True)
    name = datetime.now().strftime("rec_%y%m%d-%H%M%S.mp4")
    return folder / name

def _friendly_battery_message():
    if psutil is None or not hasattr(psutil, "sensors_battery"):
        return False, "I could not read the battery status."

    try:
        battery = psutil.sensors_battery()
    except Exception:
        battery = None

    if battery is None:
        return False, "I could not read the battery status."

    percent = int(round(battery.percent))
    if battery.power_plugged:
        return True, f"Your battery is at {percent}% and it is charging."
    return True, f"Your battery is at {percent}%. You are running on battery power."

def _linux_brightness_set(level):
    level = max(0, min(100, int(level)))

    if shutil.which("brightnessctl"):
        ok, err = _run(["brightnessctl", "set", f"{level}%"])
        if ok:
            return True, f"Brightness set to {level}%."
        if shutil.which("pkexec"):
            ok, err = _run(["pkexec", "brightnessctl", "set", f"{level}%"])
            if ok:
                return True, f"Brightness set to {level}%."
            return False, f"I couldn't change brightness: {err}"
        return False, "I couldn't change brightness because permission is required."

    if shutil.which("xbacklight"):
        ok, err = _run(["xbacklight", "-set", str(level)])
        if ok:
            return True, f"Brightness set to {level}%."
        return False, f"I couldn't change brightness: {err}"

    return False, "I couldn't change brightness because no supported brightness tool is installed."

def _linux_brightness_up():
    if shutil.which("brightnessctl"):
        ok, err = _run(["brightnessctl", "set", "+10%"])
        if ok:
            return True, "Brightness increased."
        if shutil.which("pkexec"):
            ok, err = _run(["pkexec", "brightnessctl", "set", "+10%"])
            if ok:
                return True, "Brightness increased."
            return False, f"I couldn't change brightness: {err}"
        return False, "I couldn't change brightness because permission is required."

    if shutil.which("xbacklight"):
        ok, err = _run(["xbacklight", "-inc", "10"])
        if ok:
            return True, "Brightness increased."
        return False, f"I couldn't change brightness: {err}"

    return False, "I couldn't change brightness because no supported brightness tool is installed."

def _linux_brightness_down():
    if shutil.which("brightnessctl"):
        ok, err = _run(["brightnessctl", "set", "10%-"])
        if ok:
            return True, "Brightness decreased."
        if shutil.which("pkexec"):
            ok, err = _run(["pkexec", "brightnessctl", "set", "10%-"])
            if ok:
                return True, "Brightness decreased."
            return False, f"I couldn't change brightness: {err}"
        return False, "I couldn't change brightness because permission is required."

    if shutil.which("xbacklight"):
        ok, err = _run(["xbacklight", "-dec", "10"])
        if ok:
            return True, "Brightness decreased."
        return False, f"I couldn't change brightness: {err}"

    return False, "I couldn't change brightness because no supported brightness tool is installed."

def _windows_brightness_set(level):
    level = max(0, min(100, int(level)))
    ps_script = f"""
$monitors = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods
foreach ($m in $monitors) {{
    Invoke-CimMethod -InputObject $m -MethodName WmiSetBrightness -Arguments @{{Brightness={level}; Timeout=0}}
}}
"""
    ok, err = _run(["powershell", "-NoProfile", "-Command", ps_script])
    if ok:
        return True, f"Brightness set to {level}%."
    return False, f"I couldn't change brightness: {err}"

def _windows_brightness_up():
    ps_script = """
$monitors = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness
$current = 50
foreach ($m in $monitors) {
    $current = [int]$m.CurrentBrightness
    break
}
$target = [Math]::Min(100, $current + 10)
$methods = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods
foreach ($m in $methods) {
    Invoke-CimMethod -InputObject $m -MethodName WmiSetBrightness -Arguments @{Brightness=$target; Timeout=0}
}
"""
    ok, err = _run(["powershell", "-NoProfile", "-Command", ps_script])
    if ok:
        return True, "Brightness increased."
    return False, f"I couldn't change brightness: {err}"

def _windows_brightness_down():
    ps_script = """
$monitors = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness
$current = 50
foreach ($m in $monitors) {
    $current = [int]$m.CurrentBrightness
    break
}
$target = [Math]::Max(0, $current - 10)
$methods = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods
foreach ($m in $methods) {
    Invoke-CimMethod -InputObject $m -MethodName WmiSetBrightness -Arguments @{Brightness=$target; Timeout=0}
}
"""
    ok, err = _run(["powershell", "-NoProfile", "-Command", ps_script])
    if ok:
        return True, "Brightness decreased."
    return False, f"I couldn't change brightness: {err}"

def _mac_brightness_set(level):
    if shutil.which("brightness"):
        value = max(0.0, min(100.0, float(level))) / 100.0
        ok, err = _run(["brightness", str(value)])
        if ok:
            return True, f"Brightness set to {int(level)}%."
        return False, f"I couldn't change brightness: {err}"
    return False, "I couldn't change brightness because no supported brightness tool is installed."

def _mac_brightness_up():
    if shutil.which("brightness"):
        ok, err = _run(["brightness", "0.6"])
        if ok:
            return True, "Brightness increased."
        return False, f"I couldn't change brightness: {err}"
    return False, "I couldn't change brightness because no supported brightness tool is installed."

def _mac_brightness_down():
    if shutil.which("brightness"):
        ok, err = _run(["brightness", "0.4"])
        if ok:
            return True, "Brightness decreased."
        return False, f"I couldn't change brightness: {err}"
    return False, "I couldn't change brightness because no supported brightness tool is installed."

def _brightness_set(level):
    if CURRENT_OS == "linux":
        return _linux_brightness_set(level)
    if CURRENT_OS == "windows":
        return _windows_brightness_set(level)
    if CURRENT_OS == "darwin":
        return _mac_brightness_set(level)
    return False, "Unsupported operating system."

def _brightness_up():
    if CURRENT_OS == "linux":
        return _linux_brightness_up()
    if CURRENT_OS == "windows":
        return _windows_brightness_up()
    if CURRENT_OS == "darwin":
        return _mac_brightness_up()
    return False, "Unsupported operating system."

def _brightness_down():
    if CURRENT_OS == "linux":
        return _linux_brightness_down()
    if CURRENT_OS == "windows":
        return _windows_brightness_down()
    if CURRENT_OS == "darwin":
        return _mac_brightness_down()
    return False, "Unsupported operating system."

def _screenshot_message():
    return random.choice([
        "Done! I've saved the screenshot in your Liq Screenshots folder.",
        "Got it! Your screenshot has been captured and saved.",
        "Screenshot captured successfully.",
        "All set! Your screenshot is ready.",
        "Done! I saved the screenshot for you."
    ])

def _take_screenshot():
    path = _screenshot_path()

    if pyautogui is not None:
        try:
            image = pyautogui.screenshot()
            image.save(path)
            return True, _screenshot_message()
        except Exception:
            pass

    if CURRENT_OS == "linux":
        if shutil.which("gnome-screenshot"):
            ok, err = _run(["gnome-screenshot", "-f", str(path)])
            if ok:
                return True, _screenshot_message()
            return False, f"I couldn't take a screenshot: {err}"

        if shutil.which("grim"):
            ok, err = _run(["grim", str(path)])
            if ok:
                return True, _screenshot_message()
            return False, f"I couldn't take a screenshot: {err}"

        if shutil.which("spectacle"):
            ok, err = _run(["spectacle", "-b", "-n", "-o", str(path)])
            if ok:
                return True, _screenshot_message()
            return False, f"I couldn't take a screenshot: {err}"

        if shutil.which("scrot"):
            ok, err = _run(["scrot", str(path)])
            if ok:
                return True, _screenshot_message()
            return False, f"I couldn't take a screenshot: {err}"

        if shutil.which("import"):
            ok, err = _run(["import", "-window", "root", str(path)])
            if ok:
                return True, _screenshot_message()
            return False, f"I couldn't take a screenshot: {err}"

        return False, "Screenshot support is not available right now."

    if CURRENT_OS == "windows":
        if pyautogui is not None:
            try:
                pyautogui.hotkey("win", "printscreen")
                return True, _screenshot_message()
            except Exception:
                pass

        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bitmap.Save("{str(path)}", [System.Drawing.Imaging.ImageFormat]::Png)
"""
        ok, err = _run(["powershell", "-NoProfile", "-Command", ps_script])
        if ok:
            return True, _screenshot_message()
        return False, f"I couldn't take a screenshot: {err}"

    if CURRENT_OS == "darwin":
        if pyautogui is not None:
            try:
                pyautogui.hotkey("command", "shift", "3")
                return True, _screenshot_message()
            except Exception:
                pass

        ok, err = _run(["screencapture", str(path)])
        if ok:
            return True, _screenshot_message()
        return False, f"I couldn't take a screenshot: {err}"

    return False, "Screenshot support is not available right now."

def _stop_process(proc):
    if proc is None:
        return

    try:
        if proc.poll() is not None:
            return
    except Exception:
        return

    try:
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=10)
        return
    except Exception:
        pass

    try:
        proc.terminate()
        proc.wait(timeout=5)
        return
    except Exception:
        pass

    try:
        proc.kill()
    except Exception:
        pass

def _ensure_recording_stopped():
    global _RECORDING_PROCESS, _RECORDING_PATH, _RECORDING_TIMER

    if _RECORDING_TIMER is not None:
        try:
            _RECORDING_TIMER.cancel()
        except Exception:
            pass
        _RECORDING_TIMER = None

    proc = _RECORDING_PROCESS
    path = _RECORDING_PATH

    _RECORDING_PROCESS = None
    _RECORDING_PATH = None

    _stop_process(proc)
    return path

def _screen_record_command(path: Path):
    if CURRENT_OS == "linux":
        if shutil.which("wf-recorder"):
            return ["wf-recorder", "-f", str(path)]

        if shutil.which("ffmpeg") and os.environ.get("DISPLAY"):
            return ["ffmpeg", "-y", "-f", "x11grab", "-framerate", "30", "-i", os.environ["DISPLAY"], str(path)]

        return None

    if CURRENT_OS == "windows":
        if shutil.which("ffmpeg"):
            return ["ffmpeg", "-y", "-f", "gdigrab", "-framerate", "30", "-i", "desktop", str(path)]
        return None

    if CURRENT_OS == "darwin":
        if shutil.which("ffmpeg"):
            return ["ffmpeg", "-y", "-f", "avfoundation", "-framerate", "30", "-capture_cursor", "1", "-i", "1:none", str(path)]
        return None

    return None

def _start_screen_recording(duration_seconds=None):
    global _RECORDING_PROCESS, _RECORDING_PATH, _RECORDING_TIMER

    if _RECORDING_PROCESS is not None:
        return False, "A recording is already running."

    path = _recording_path()
    cmd = _screen_record_command(path)

    if cmd is None:
        return False, "I couldn't start screen recording because no supported recorder is installed."

    try:
        _RECORDING_PROCESS = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _RECORDING_PATH = path
    except Exception as e:
        _RECORDING_PROCESS = None
        _RECORDING_PATH = None
        return False, f"I couldn't start screen recording: {e}"

    if duration_seconds and duration_seconds > 0:
        def auto_stop():
            time.sleep(duration_seconds)
            if _RECORDING_PROCESS is not None:
                stop_screen_recording()

        _RECORDING_TIMER = threading.Thread(target=auto_stop, daemon=True)
        _RECORDING_TIMER.start()
        return True, f"Recording started: {_short_path(path)}. It will stop automatically."

    return True, f"Recording started: {_short_path(path)}"

def stop_screen_recording():
    path = _ensure_recording_stopped()
    if path is None:
        return False, "No recording is running."
    return True, f"Recording saved: {_short_path(path)}"

def _lock_screen():
    if CURRENT_OS == "linux":
        if pyautogui is not None:
            try:
                pyautogui.hotkey("ctrl", "alt", "l")
                return True, "Locking screen."
            except Exception:
                pass

        for cmd in [
            ["loginctl", "lock-session"],
            ["xdg-screensaver", "lock"],
            ["gnome-screensaver-command", "-l"],
        ]:
            if shutil.which(cmd[0]):
                ok, err = _run(cmd)
                if ok:
                    return True, "Locking screen."
                return False, f"I couldn't lock the screen: {err}"

        return False, "No lock-screen command found."

    if CURRENT_OS == "windows":
        if pyautogui is not None:
            try:
                pyautogui.hotkey("win", "l")
                return True, "Locking screen."
            except Exception:
                pass

        ok, err = _run(["rundll32.exe", "user32.dll,LockWorkStation"])
        if ok:
            return True, "Locking screen."
        return False, f"I couldn't lock the screen: {err}"

    if CURRENT_OS == "darwin":
        if pyautogui is not None:
            try:
                pyautogui.hotkey("control", "command", "q")
                return True, "Locking screen."
            except Exception:
                pass

        ok, err = _run(["osascript", "-e", 'tell application "System Events" to keystroke "q" using {control down, command down}'])
        if ok:
            return True, "Locking screen."
        return False, f"I couldn't lock the screen: {err}"

    return False, "Unsupported operating system."

def _sleep():
    if CURRENT_OS == "linux":
        for cmd in [["systemctl", "suspend"], ["loginctl", "suspend"]]:
            if shutil.which(cmd[0]):
                ok, err = _run(cmd)
                if ok:
                    return True, "Putting the system to sleep."
                return False, f"I couldn't put the system to sleep: {err}"
        return False, "No sleep command found."

    if CURRENT_OS == "windows":
        ps_script = """
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Power {
    [DllImport("powrprof.dll", SetLastError = true)]
    public static extern bool SetSuspendState(bool Hibernate, bool ForceCritical, bool DisableWakeEvent);
}
"@
[Power]::SetSuspendState($false, $true, $false)
"""
        ok, err = _run(["powershell", "-NoProfile", "-Command", ps_script])
        if ok:
            return True, "Putting the system to sleep."
        return False, f"I couldn't put the system to sleep: {err}"

    if CURRENT_OS == "darwin":
        ok, err = _run(["pmset", "sleepnow"])
        if ok:
            return True, "Putting the system to sleep."
        return False, f"I couldn't put the system to sleep: {err}"

    return False, "Unsupported operating system."

def _restart():
    if CURRENT_OS == "linux":
        for cmd in [["systemctl", "reboot"], ["reboot"]]:
            if shutil.which(cmd[0]):
                ok, err = _run(cmd)
                if ok:
                    return True, "Restarting the system."
                return False, f"I couldn't restart: {err}"
        return False, "No restart command found."

    if CURRENT_OS == "windows":
        ok, err = _run(["shutdown", "/r", "/t", "0"])
        if ok:
            return True, "Restarting the system."
        return False, f"I couldn't restart: {err}"

    if CURRENT_OS == "darwin":
        ok, err = _run(["osascript", "-e", 'tell app "System Events" to restart'])
        if ok:
            return True, "Restarting the system."
        return False, f"I couldn't restart: {err}"

    return False, "Unsupported operating system."

def _shutdown():
    if CURRENT_OS == "linux":
        for cmd in [["systemctl", "poweroff"], ["poweroff"], ["shutdown", "now"]]:
            if shutil.which(cmd[0]):
                ok, err = _run(cmd)
                if ok:
                    return True, "Shutting down the system."
                return False, f"I couldn't shut down: {err}"
        return False, "No shutdown command found."

    if CURRENT_OS == "windows":
        ok, err = _run(["shutdown", "/s", "/t", "0"])
        if ok:
            return True, "Shutting down the system."
        return False, f"I couldn't shut down: {err}"

    if CURRENT_OS == "darwin":
        ok, err = _run(["osascript", "-e", 'tell app "System Events" to shut down'])
        if ok:
            return True, "Shutting down the system."
        return False, f"I couldn't shut down: {err}"

    return False, "Unsupported operating system."

def handle_device_command(user_input: str):
    text = user_input.strip().lower()

    if any(word in text for word in ["battery", "battery status", "check battery"]):
        return _friendly_battery_message()

    if any(word in text for word in ["take screenshot", "screenshot", "capture screen"]):
        return _take_screenshot()

    if any(word in text for word in ["start recording", "record screen", "start screen recording", "start video recording", "record video"]):
        m = re.search(r"\brecord\s+for\s+(\d+)\s*(seconds?|minutes?)\b", text)
        if m:
            amount = int(m.group(1))
            unit = m.group(2).lower()
            seconds = amount if unit.startswith("second") else amount * 60
            return _start_screen_recording(duration_seconds=seconds)
        return _start_screen_recording()

    if any(word in text for word in ["stop recording", "stop screen recording", "stop video recording", "end recording", "finish recording"]):
        return stop_screen_recording()

    if any(word in text for word in ["lock screen", "lock laptop", "lock computer"]):
        return _lock_screen()

    if any(word in text for word in ["sleep", "go to sleep", "suspend"]):
        return _sleep()

    if any(word in text for word in ["restart", "reboot"]):
        return _restart()

    if any(word in text for word in ["shutdown", "shut down", "power off", "turn off"]):
        return _shutdown()

    brightness_set = re.search(r"\b(?:set|change|adjust)\s+brightness\s+to\s+(\d{1,3})\b", text)
    if brightness_set:
        level = max(0, min(100, int(brightness_set.group(1))))
        return _brightness_set(level)

    if any(word in text for word in ["brightness up", "increase brightness", "brighter", "raise brightness"]):
        return _brightness_up()

    if any(word in text for word in ["brightness down", "decrease brightness", "dim screen", "lower brightness"]):
        return _brightness_down()

    return None