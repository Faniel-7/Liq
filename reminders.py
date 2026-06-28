from pathlib import Path
from datetime import datetime, timedelta
import json
import re
import threading
import time
import random

REMINDERS_FILE = Path.home() / ".liq_reminders.json"

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_watcher_started = False

def _load_reminders():
    if not REMINDERS_FILE.exists():
        return []
    try:
        return json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def _save_reminders(reminders):
    REMINDERS_FILE.write_text(json.dumps(reminders, indent=2), encoding="utf-8")

def _next_id(reminders):
    if not reminders:
        return 1
    return max(item.get("id", 0) for item in reminders) + 1

def _fmt(dt: datetime) -> str:
    return dt.strftime("%A, %B %d, %Y at %I:%M %p").replace(" 0", " ")

def _parse_clock_time(text: str):
    value = text.strip().lower().replace(".", "")
    formats = ["%I:%M %p", "%I %p", "%H:%M", "%H"]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).time()
        except Exception:
            pass
    return None

def _combine_date_and_time(base_date, time_text=None):
    if time_text:
        parsed_time = _parse_clock_time(time_text)
        if parsed_time:
            return datetime.combine(base_date, parsed_time)
    return datetime.combine(base_date, datetime.strptime("09:00 AM", "%I:%M %p").time())

def _next_weekday_date(start_date, weekday_name):
    target = _WEEKDAYS.get(weekday_name.lower())
    if target is None:
        return None

    days_ahead = (target - start_date.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    return start_date + timedelta(days=days_ahead)

def _parse_due_datetime(expression: str):
    now = datetime.now()
    text = expression.strip()

    match = re.match(r"^in\s+(\d+)\s*(seconds?|minutes?|hours?|days?|weeks?)$", text, re.I)
    if match:
        amount = int(match.group(1))
        unit = match.group(2).lower()
        if unit.startswith("second"):
            return now + timedelta(seconds=amount)
        if unit.startswith("minute"):
            return now + timedelta(minutes=amount)
        if unit.startswith("hour"):
            return now + timedelta(hours=amount)
        if unit.startswith("day"):
            return now + timedelta(days=amount)
        if unit.startswith("week"):
            return now + timedelta(weeks=amount)

    match = re.match(r"^tomorrow(?:\s+at\s+(.+))?$", text, re.I)
    if match:
        due_date = now.date() + timedelta(days=1)
        return _combine_date_and_time(due_date, match.group(1))

    match = re.match(r"^today(?:\s+at\s+(.+))?$", text, re.I)
    if match:
        due = _combine_date_and_time(now.date(), match.group(1))
        if due <= now:
            due = now + timedelta(minutes=1)
        return due

    match = re.match(
        r"^(?:on\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:\s+at\s+(.+))?$",
        text,
        re.I,
    )
    if match:
        due_date = _next_weekday_date(now.date(), match.group(1))
        if due_date is None:
            return None
        return _combine_date_and_time(due_date, match.group(2))

    match = re.match(r"^at\s+(.+)$", text, re.I)
    if match:
        due = _combine_date_and_time(now.date(), match.group(1))
        if due <= now:
            due = due + timedelta(days=1)
        return due

    return None

def _clean_reminder_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).strip(" .!?")

def _reminder_message(text: str) -> str:
    t = _clean_reminder_text(text)
    low = t.lower()

    if low.startswith("to "):
        t = t[3:].strip()
        low = t.lower()

    if low.startswith(("remember ", "don't forget ", "dont forget ")):
        return f"Hey, {t}."

    templates = [
        f"Hey, time to {t}.",
        f"Just a quick reminder to {t}.",
        f"Don't forget to {t}.",
    ]
    return random.choice(templates)

def add_reminder(text: str, due_at: datetime):
    reminders = _load_reminders()
    item = {
        "id": _next_id(reminders),
        "text": _clean_reminder_text(text),
        "due_at": due_at.isoformat(),
        "created_at": datetime.now().isoformat(),
        "notified": False,
        "done": False,
    }
    reminders.append(item)
    _save_reminders(reminders)
    return True, f"Reminder saved for {_fmt(due_at)}."

def _format_reminder_line(item, index):
    try:
        due_at = datetime.fromisoformat(item["due_at"])
        due_text = _fmt(due_at)
    except Exception:
        due_text = "Unknown time"

    status = "done" if item.get("done") else "pending"
    return f"{index}. {item['text']} — {due_text} — {status}"

def list_reminders(include_completed=False):
    reminders = _load_reminders()
    if not reminders:
        return True, "You have no reminders."

    filtered = []
    for item in reminders:
        if include_completed:
            filtered.append(item)
        elif not item.get("done"):
            filtered.append(item)

    if not filtered:
        return True, "You have no active reminders."

    title = "Your reminders:" if not include_completed else "Your reminders history:"
    lines = [title]
    for i, item in enumerate(filtered, start=1):
        lines.append(_format_reminder_line(item, i))
    return True, "\n".join(lines)

def list_completed_reminders():
    return list_reminders(include_completed=True)

def clear_completed_reminders():
    reminders = _load_reminders()
    kept = [item for item in reminders if not item.get("done")]
    removed = len(reminders) - len(kept)
    _save_reminders(kept)

    if removed == 0:
        return True, "You have no completed reminders to clear."

    return True, f"Cleared {removed} completed reminder{'s' if removed != 1 else ''}."

def clear_all_reminders():
    reminders = _load_reminders()
    removed = len(reminders)
    _save_reminders([])

    if removed == 0:
        return True, "You have no reminders to clear."

    return True, f"Cleared all {removed} reminder{'s' if removed != 1 else ''}."

def delete_reminder(index: int):
    reminders = _load_reminders()
    active = [item for item in reminders if not item.get("done")]

    if index < 1 or index > len(active):
        return False, "That reminder number does not exist."

    target = active[index - 1]
    reminders = [item for item in reminders if item.get("id") != target.get("id")]
    _save_reminders(reminders)
    return True, f"Deleted reminder {index}: {target['text']}"

def mark_reminder_done(index: int):
    reminders = _load_reminders()
    active = [item for item in reminders if not item.get("done")]

    if index < 1 or index > len(active):
        return False, "That reminder number does not exist."

    target = active[index - 1]
    for item in reminders:
        if item.get("id") == target.get("id"):
            item["done"] = True
            item["notified"] = True
            item["completed_at"] = datetime.now().isoformat()
            break

    _save_reminders(reminders)
    return True, f"Marked reminder {index} as done."

def add_reminder_from_text(user_input: str):
    text = user_input.strip()

    patterns = [
        re.compile(r"^(?:remind me|set reminder)\s+in\s+(\d+)\s*(seconds?|minutes?|hours?|days?|weeks?)\s+(?:to|for)\s+(.+)$", re.I),
        re.compile(r"^(?:remind me|set reminder)\s+tomorrow(?:\s+at\s+(.+?))?\s+(?:to|for)\s+(.+)$", re.I),
        re.compile(r"^(?:remind me|set reminder)\s+(?:on\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:\s+at\s+(.+?))?\s+(?:to|for)\s+(.+)$", re.I),
        re.compile(r"^(?:remind me|set reminder)\s+at\s+(.+?)\s+(?:to|for)\s+(.+)$", re.I),
    ]

    m = patterns[0].match(text)
    if m:
        amount = m.group(1)
        unit = m.group(2)
        note = m.group(3).strip()
        due = _parse_due_datetime(f"in {amount} {unit}")
        if due is None:
            return False, "I couldn't understand the reminder time."
        return add_reminder(note, due)

    m = patterns[1].match(text)
    if m:
        clock = m.group(1)
        note = m.group(2).strip()
        expr = "tomorrow" if not clock else f"tomorrow at {clock}"
        due = _parse_due_datetime(expr)
        if due is None:
            return False, "I couldn't understand the reminder time."
        return add_reminder(note, due)

    m = patterns[2].match(text)
    if m:
        weekday = m.group(1)
        clock = m.group(2)
        note = m.group(3).strip()
        expr = weekday if not clock else f"{weekday} at {clock}"
        due = _parse_due_datetime(expr)
        if due is None:
            return False, "I couldn't understand the reminder time."
        return add_reminder(note, due)

    m = patterns[3].match(text)
    if m:
        clock = m.group(1)
        note = m.group(2).strip()
        due = _parse_due_datetime(f"at {clock}")
        if due is None:
            return False, "I couldn't understand the reminder time."
        return add_reminder(note, due)

    return None

def handle_reminder_command(user_input: str):
    text = user_input.strip().lower()

    if text in ["show reminders", "list reminders", "my reminders", "reminders"]:
        return list_reminders()

    if text in ["show completed reminders", "list completed reminders", "completed reminders", "done reminders"]:
        return list_completed_reminders()

    if text in ["clear completed reminders", "clear done reminders", "delete completed reminders"]:
        return clear_completed_reminders()

    if text in ["clear all reminders", "delete all reminders", "remove all reminders"]:
        return clear_all_reminders()

    delete_match = re.match(r"^(?:delete reminder|remove reminder)\s+(\d+)$", text, re.I)
    if delete_match:
        return delete_reminder(int(delete_match.group(1)))

    done_match = re.match(r"^(?:done reminder|mark reminder)\s+(\d+)\s+done$", text, re.I)
    if done_match:
        return mark_reminder_done(int(done_match.group(1)))

    add_result = add_reminder_from_text(user_input)
    if add_result is not None:
        return add_result

    return None

def check_due_reminders():
    reminders = _load_reminders()
    now = datetime.now()
    due_items = []
    changed = False

    for item in reminders:
        if item.get("done") or item.get("notified"):
            continue

        try:
            due_at = datetime.fromisoformat(item["due_at"])
        except Exception:
            continue

        if due_at <= now:
            item["notified"] = True
            item["done"] = True
            item["completed_at"] = now.isoformat()
            due_items.append(item)
            changed = True

    if changed:
        _save_reminders(reminders)

    return due_items

def start_reminder_watcher(on_reminder, interval=15):
    global _watcher_started
    if _watcher_started:
        return

    _watcher_started = True

    def loop():
        while True:
            try:
                due_items = check_due_reminders()
                for item in due_items:
                    on_reminder(item)
            except Exception:
                pass
            time.sleep(interval)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()