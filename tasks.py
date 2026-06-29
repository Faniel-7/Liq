from pathlib import Path
from datetime import datetime, timedelta
import json
import re

TASKS_FILE = Path.home() / ".liq_tasks.json"

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).strip(" .!?")

def _load_tasks():
    if not TASKS_FILE.exists():
        return []
    try:
        return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def _save_tasks(tasks):
    TASKS_FILE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")

def _next_id(tasks):
    if not tasks:
        return 1
    return max(item.get("id", 0) for item in tasks) + 1

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

def _priority_from_text(text: str):
    priority_match = re.search(r"\bpriority\s+(high|medium|low)\b", text, re.I)
    if priority_match:
        return priority_match.group(1).lower()
    return "medium"

def _remove_priority_text(text: str):
    return re.sub(r"\bpriority\s+(high|medium|low)\b", "", text, flags=re.I).strip()

def _extract_due_text(text: str):
    due_match = re.search(
        r"\bdue\s+(.+)$",
        text,
        re.I,
    )
    if not due_match:
        return None, text

    due_text = due_match.group(1).strip()
    clean_text = text[:due_match.start()].strip()
    return due_text, clean_text

def _task_message(text: str) -> str:
    t = _clean_text(text)
    low = t.lower()

    if low.startswith("to "):
        t = t[3:].strip()
        low = t.lower()

    if low.startswith(("remember ", "don't forget ", "dont forget ")):
        return f"Hey, {t}."

    return f"Task noted: {t}."

def add_task(text: str, due_at: datetime | None = None, priority: str = "medium"):
    tasks = _load_tasks()
    item = {
        "id": _next_id(tasks),
        "text": _clean_text(text),
        "created_at": datetime.now().isoformat(),
        "done": False,
        "completed_at": None,
        "priority": priority,
        "due_at": due_at.isoformat() if due_at else None,
    }
    tasks.append(item)
    _save_tasks(tasks)

    if due_at:
        return True, f"Task added for {_fmt(due_at)}."
    return True, "Task added."

def _active_tasks(tasks):
    return [item for item in tasks if not item.get("done")]

def _completed_tasks(tasks):
    return [item for item in tasks if item.get("done")]

def _format_task(item, index):
    priority = item.get("priority", "medium")
    due_at = item.get("due_at")
    due_text = ""
    if due_at:
        try:
            due_text = f" — due {_fmt(datetime.fromisoformat(due_at))}"
        except Exception:
            due_text = ""
    status = "done" if item.get("done") else "pending"
    return f"{index}. {item['text']} — {priority}{due_text} — {status}"

def list_tasks(include_completed=False, include_all=False):
    tasks = _load_tasks()
    if not tasks:
        return True, "You have no tasks."

    if include_all:
        filtered = tasks
        title = "All tasks:"
    elif include_completed:
        filtered = _completed_tasks(tasks)
        title = "Completed tasks:"
    else:
        filtered = _active_tasks(tasks)
        title = "Your tasks:"

    if not filtered:
        if include_completed:
            return True, "You have no completed tasks."
        return True, "You have no active tasks."

    lines = [title]
    for i, item in enumerate(filtered, start=1):
        lines.append(_format_task(item, i))
    return True, "\n".join(lines)

def clear_completed_tasks():
    tasks = _load_tasks()
    kept = [item for item in tasks if not item.get("done")]
    removed = len(tasks) - len(kept)
    _save_tasks(kept)

    if removed == 0:
        return True, "You have no completed tasks to clear."
    return True, f"Cleared {removed} completed task{'s' if removed != 1 else ''}."

def clear_all_tasks():
    tasks = _load_tasks()
    removed = len(tasks)
    _save_tasks([])

    if removed == 0:
        return True, "You have no tasks to clear."
    return True, f"Cleared all {removed} task{'s' if removed != 1 else ''}."

def delete_task(index: int):
    tasks = _load_tasks()
    active = _active_tasks(tasks)

    if index < 1 or index > len(active):
        return False, "That task number does not exist."

    target = active[index - 1]
    tasks = [item for item in tasks if item.get("id") != target.get("id")]
    _save_tasks(tasks)
    return True, f"Deleted task {index}: {target['text']}"

def complete_task(index: int):
    tasks = _load_tasks()
    active = _active_tasks(tasks)

    if index < 1 or index > len(active):
        return False, "That task number does not exist."

    target = active[index - 1]
    for item in tasks:
        if item.get("id") == target.get("id"):
            item["done"] = True
            item["completed_at"] = datetime.now().isoformat()
            break

    _save_tasks(tasks)
    return True, f"Marked task {index} as done."

def undo_task(index: int):
    tasks = _load_tasks()
    completed = _completed_tasks(tasks)

    if index < 1 or index > len(completed):
        return False, "That completed task number does not exist."

    target = completed[index - 1]
    for item in tasks:
        if item.get("id") == target.get("id"):
            item["done"] = False
            item["completed_at"] = None
            break

    _save_tasks(tasks)
    return True, f"Moved task {index} back to active tasks."

def add_task_from_text(user_input: str):
    text = user_input.strip()
    match = re.match(r"^(?:add|new|create)\s+(?:a\s+)?task\s+(.+)$", text, re.I)
    if not match:
        return None

    content = match.group(1).strip()

    priority = _priority_from_text(content)
    content = _remove_priority_text(content)

    due_text, task_text = _extract_due_text(content)
    due_at = None
    if due_text:
        due_at = _parse_due_datetime(due_text)
        if due_at is None:
            return False, "I couldn't understand the task due time."

    task_text = _clean_text(task_text)
    if not task_text:
        return False, "Task text cannot be empty."

    return add_task(task_text, due_at=due_at, priority=priority)

def handle_task_command(user_input: str):
    text = _normalize(user_input)

    if text in ["show tasks", "list tasks", "my tasks", "tasks"]:
        return list_tasks()

    if text in ["show completed tasks", "list completed tasks", "completed tasks", "done tasks"]:
        return list_tasks(include_completed=True)

    if text in ["show all tasks", "list all tasks", "all tasks"]:
        return list_tasks(include_all=True)

    if text in ["clear completed tasks", "clear done tasks", "delete completed tasks"]:
        return clear_completed_tasks()

    if text in ["clear all tasks", "delete all tasks", "remove all tasks"]:
        return clear_all_tasks()

    complete_match = re.match(r"^(?:complete task|mark task|done task)\s+(\d+)$", text, re.I)
    if complete_match:
        return complete_task(int(complete_match.group(1)))

    undo_match = re.match(r"^(?:undo task|restore task)\s+(\d+)$", text, re.I)
    if undo_match:
        return undo_task(int(undo_match.group(1)))

    delete_match = re.match(r"^(?:delete task|remove task)\s+(\d+)$", text, re.I)
    if delete_match:
        return delete_task(int(delete_match.group(1)))

    add_result = add_task_from_text(user_input)
    if add_result is not None:
        return add_result

    return None

def check_due_tasks():
    tasks = _load_tasks()
    now = datetime.now()
    overdue = []

    for item in tasks:
        if item.get("done"):
            continue
        due_at = item.get("due_at")
        if not due_at:
            continue
        try:
            due_dt = datetime.fromisoformat(due_at)
        except Exception:
            continue
        if due_dt <= now:
            overdue.append(item)

    return overdue