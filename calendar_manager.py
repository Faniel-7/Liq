from pathlib import Path
from datetime import datetime, timedelta, date
import json
import re
import threading
import time

EVENTS_FILE = Path.home() / ".liq_events.json"

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

_watcher_started = False

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).strip(" .!?")

def _load_events():
    if not EVENTS_FILE.exists():
        return []
    try:
        return json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def _save_events(events):
    EVENTS_FILE.write_text(json.dumps(events, indent=2), encoding="utf-8")

def _next_id(events):
    if not events:
        return 1
    return max(item.get("id", 0) for item in events) + 1

def _fmt(dt: datetime) -> str:
    return dt.strftime("%A, %B %d, %Y at %I:%M %p").replace(" 0", " ")

def _parse_clock_time(text: str):
    value = text.strip().lower().replace(".", "")
    for fmt in ["%I:%M %p", "%I %p", "%H:%M", "%H"]:
        try:
            return datetime.strptime(value, fmt).time()
        except Exception:
            pass
    return None

def _combine_date_and_time(base_date: date, time_text=None):
    if time_text:
        parsed_time = _parse_clock_time(time_text)
        if parsed_time:
            return datetime.combine(base_date, parsed_time)
    return datetime.combine(base_date, datetime.strptime("09:00 AM", "%I:%M %p").time())

def _next_weekday_date(start_date: date, weekday_name: str, force_next=False):
    target = _WEEKDAYS.get(weekday_name.lower())
    if target is None:
        return None
    days_ahead = (target - start_date.weekday() + 7) % 7
    if days_ahead == 0 or force_next:
        days_ahead = 7 if days_ahead == 0 else days_ahead + 7
    return start_date + timedelta(days=days_ahead)

def _parse_absolute_date(date_text: str):
    raw = _clean_text(date_text).lower().replace(",", "")
    today = datetime.now().date()

    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", raw)
    if m:
        try:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return date(y, mo, d)
        except Exception:
            return None

    m = re.match(
        r"^(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:\s+(\d{4}))?$",
        raw,
    )
    if m:
        month_name = m.group(1)
        day_num = int(m.group(2))
        year_num = int(m.group(3)) if m.group(3) else today.year
        month_num = _MONTHS[next(k for k in _MONTHS if k.startswith(month_name[:3]))]
        try:
            d = date(year_num, month_num, day_num)
        except Exception:
            return None
        if not m.group(3) and d < today:
            try:
                d = date(today.year + 1, month_num, day_num)
            except Exception:
                return None
        return d

    m = re.match(
        r"^(\d{1,2})\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:\s+(\d{4}))?$",
        raw,
    )
    if m:
        day_num = int(m.group(1))
        month_name = m.group(2)
        year_num = int(m.group(3)) if m.group(3) else today.year
        month_num = _MONTHS[next(k for k in _MONTHS if k.startswith(month_name[:3]))]
        try:
            d = date(year_num, month_num, day_num)
        except Exception:
            return None
        if not m.group(3) and d < today:
            try:
                d = date(today.year + 1, month_num, day_num)
            except Exception:
                return None
        return d

    return None

def _parse_due_datetime(expression: str):
    now = datetime.now()
    text = _clean_text(expression)

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

    match = re.match(r"^(?:on\s+)?(today|tomorrow)(?:\s+at\s+(.+))?$", text, re.I)
    if match:
        keyword = match.group(1).lower()
        clock = match.group(2)
        base = now.date() + timedelta(days=1 if keyword == "tomorrow" else 0)
        due = _combine_date_and_time(base, clock)
        if keyword == "today" and due <= now:
            due = now + timedelta(minutes=1)
        return due

    match = re.match(r"^(?:next\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:\s+at\s+(.+))?$", text, re.I)
    if match:
        force_next = text.lower().startswith("next ")
        due_date = _next_weekday_date(now.date(), match.group(1), force_next=force_next)
        if due_date is None:
            return None
        return _combine_date_and_time(due_date, match.group(2))

    match = re.match(r"^(?:on\s+)?(.+?)(?:\s+at\s+(.+))?$", text, re.I)
    if match:
        date_text = match.group(1)
        clock = match.group(2)
        parsed_date = _parse_absolute_date(date_text)
        if parsed_date is not None:
            due = _combine_date_and_time(parsed_date, clock)
            return due

    match = re.match(r"^at\s+(.+)$", text, re.I)
    if match:
        due = _combine_date_and_time(now.date(), match.group(1))
        if due <= now:
            due = due + timedelta(days=1)
        return due

    return None

def _event_datetime(item):
    try:
        return datetime.fromisoformat(item["due_at"])
    except Exception:
        return None

def _event_date(item):
    due = _event_datetime(item)
    return due.date() if due else None

def _event_message(title: str) -> str:
    title = _clean_text(title)
    low = title.lower()
    if low.startswith("to "):
        title = title[3:].strip()
    return f"Hey, it is time for {title}."

def add_event(title: str, due_at: datetime):
    events = _load_events()
    item = {
        "id": _next_id(events),
        "title": _clean_text(title),
        "due_at": due_at.isoformat(),
        "created_at": datetime.now().isoformat(),
        "notified": False,
        "done": False,
    }
    events.append(item)
    _save_events(events)
    return True, f"Event saved for {_fmt(due_at)}."

def _active_events(events):
    return [item for item in events if not item.get("done")]

def _completed_events(events):
    return [item for item in events if item.get("done")]

def _format_event_line(item, index):
    due_at = _event_datetime(item)
    due_text = _fmt(due_at) if due_at else "Unknown time"
    status = "done" if item.get("done") else "pending"
    return f"{index}. {item['title']} — {due_text} — {status}"

def list_events(include_completed=False, include_all=False, only_today=False, only_week=False):
    events = _load_events()
    if not events:
        return True, "You have no events."

    now = datetime.now()
    today = now.date()
    week_end = now + timedelta(days=7)

    if include_all:
        filtered = events
        title = "All events:"
    elif include_completed:
        filtered = _completed_events(events)
        title = "Past events:"
    else:
        filtered = _active_events(events)
        title = "Your events:"
        if only_today:
            filtered = [e for e in filtered if _event_date(e) == today]
            title = "Today's events:"
        elif only_week:
            filtered = [
                e for e in filtered
                if _event_datetime(e) is not None and now <= _event_datetime(e) <= week_end
            ]
            title = "This week's events:"

    if not filtered:
        if include_completed:
            return True, "You have no past events."
        if only_today:
            return True, "You have no events for today."
        if only_week:
            return True, "You have no events this week."
        return True, "You have no active events."

    lines = [title]
    for i, item in enumerate(filtered, start=1):
        lines.append(_format_event_line(item, i))
    return True, "\n".join(lines)

def list_past_events():
    return list_events(include_completed=True)

def delete_event(index: int):
    events = _load_events()
    active = _active_events(events)
    if index < 1 or index > len(active):
        return False, "That event number does not exist."

    target = active[index - 1]
    events = [item for item in events if item.get("id") != target.get("id")]
    _save_events(events)
    return True, f"Deleted event {index}: {target['title']}"

def complete_event(index: int):
    events = _load_events()
    active = _active_events(events)
    if index < 1 or index > len(active):
        return False, "That event number does not exist."

    target = active[index - 1]
    for item in events:
        if item.get("id") == target.get("id"):
            item["done"] = True
            item["notified"] = True
            item["completed_at"] = datetime.now().isoformat()
            break
    _save_events(events)
    return True, f"Marked event {index} as done."

def move_event(index: int, new_due_at: datetime):
    events = _load_events()
    active = _active_events(events)
    if index < 1 or index > len(active):
        return False, "That event number does not exist."

    target = active[index - 1]
    for item in events:
        if item.get("id") == target.get("id"):
            item["due_at"] = new_due_at.isoformat()
            item["notified"] = False
            item["done"] = False
            item["moved_at"] = datetime.now().isoformat()
            break
    _save_events(events)
    return True, f"Moved event {index} to {_fmt(new_due_at)}."

def _split_title_and_due(text: str):
    patterns = [
        r"^(?P<title>.+?)\s+in\s+(?P<amount>\d+\s*(?:seconds?|minutes?|hours?|days?|weeks?))$",
        r"^(?P<title>.+?)\s+(?P<when>tomorrow(?:\s+at\s+.+)?|today(?:\s+at\s+.+)?|(?:next\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:\s+at\s+.+)?|(?:on\s+)?(?:\d{4}-\d{2}-\d{2}|(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:\s+\d{4})?|\d{1,2}\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?))(?:\s+at\s+.+)?|at\s+.+)$",
    ]
    for pattern in patterns:
        m = re.match(pattern, text, re.I)
        if m:
            gd = m.groupdict()
            title = gd.get("title", "").strip()
            due = gd.get("amount") or gd.get("when")
            return title, due
    return None, None

def add_event_from_text(user_input: str):
    text = user_input.strip()
    m = re.match(r"^(?:add|create|schedule)\s+(?:an?\s+)?event\s+(.+)$", text, re.I)
    if not m:
        return None

    body = m.group(1).strip()
    title, due_expr = _split_title_and_due(body)

    if not title or not due_expr:
        return False, "I couldn't understand the event title or time."

    due_at = _parse_due_datetime(due_expr)
    if due_at is None:
        return False, "I couldn't understand the event time."

    return add_event(title, due_at)

def handle_calendar_command(user_input: str):
    text = _normalize(user_input)

    if text in ["show events", "list events", "my events", "calendar", "show calendar"]:
        return list_events()

    if text in ["show today's events", "today events", "what is on my calendar today", "events today"]:
        return list_events(only_today=True)

    if text in ["show this week", "this week events", "week events", "upcoming events", "show upcoming events"]:
        return list_events(only_week=True)

    if text in ["show past events", "list past events", "past events", "completed events"]:
        return list_past_events()

    if text in ["clear past events", "clear completed events", "delete past events"]:
        events = _load_events()
        kept = [item for item in events if not item.get("done")]
        removed = len(events) - len(kept)
        _save_events(kept)
        if removed == 0:
            return True, "You have no past events to clear."
        return True, f"Cleared {removed} past event{'s' if removed != 1 else ''}."

    if text in ["clear all events", "delete all events", "remove all events"]:
        events = _load_events()
        removed = len(events)
        _save_events([])
        if removed == 0:
            return True, "You have no events to clear."
        return True, f"Cleared all {removed} event{'s' if removed != 1 else ''}."

    delete_match = re.match(r"^(?:delete event|remove event)\s+(\d+)$", text, re.I)
    if delete_match:
        return delete_event(int(delete_match.group(1)))

    done_match = re.match(r"^(?:done event|mark event)\s+(\d+)\s+done$", text, re.I)
    if done_match:
        return complete_event(int(done_match.group(1)))

    move_match = re.match(r"^(?:move event|reschedule event)\s+(\d+)\s+(?:to|for)\s+(.+)$", text, re.I)
    if move_match:
        index = int(move_match.group(1))
        due_expr = move_match.group(2).strip()
        due_at = _parse_due_datetime(due_expr)
        if due_at is None:
            return False, "I couldn't understand the new event time."
        return move_event(index, due_at)

    add_result = add_event_from_text(user_input)
    if add_result is not None:
        return add_result

    return None

def check_due_events():
    events = _load_events()
    now = datetime.now()
    due_items = []
    changed = False

    for item in events:
        if item.get("done") or item.get("notified"):
            continue
        due_at = _event_datetime(item)
        if due_at is None:
            continue
        if due_at <= now:
            item["notified"] = True
            item["done"] = True
            item["completed_at"] = now.isoformat()
            due_items.append(item)
            changed = True

    if changed:
        _save_events(events)

    return due_items

def start_event_watcher(on_event, interval=15):
    global _watcher_started
    if _watcher_started:
        return

    _watcher_started = True

    def loop():
        while True:
            try:
                due_items = check_due_events()
                for item in due_items:
                    on_event(item)
            except Exception:
                pass
            time.sleep(interval)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()