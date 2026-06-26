from pathlib import Path
import json
import re

NOTES_FILE = Path.home() / ".liq_notes.json"

def _load_notes():
    if not NOTES_FILE.exists():
        return []
    try:
        return json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def _save_notes(notes):
    NOTES_FILE.write_text(json.dumps(notes, indent=2), encoding="utf-8")

def add_note(text: str):
    text = text.strip()
    if not text:
        return False, "Note text cannot be empty."

    notes = _load_notes()
    notes.append(text)
    _save_notes(notes)
    return True, "Note saved."

def list_notes():
    notes = _load_notes()
    if not notes:
        return True, "You have no notes."
    result = ["Your notes:"]
    for i, note in enumerate(notes, start=1):
        result.append(f"{i}. {note}")
    return True, "\n".join(result)

def delete_note(index: int):
    notes = _load_notes()
    if index < 1 or index > len(notes):
        return False, "That note number does not exist."

    removed = notes.pop(index - 1)
    _save_notes(notes)
    return True, f"Deleted note {index}: {removed}"

def handle_note_command(user_input: str):
    text = user_input.strip().lower()

    add_match = re.match(r"^(?:take a note|note|remember that|remember)\s+(.+)$", text)
    if add_match:
        original = user_input.strip()
        cleaned = re.sub(r"^(take a note|note|remember that|remember)\s+", "", original, flags=re.I).strip()
        return add_note(cleaned)

    if text in ["show notes", "list notes", "my notes", "notes"]:
        return list_notes()

    delete_match = re.match(r"^(?:delete note|remove note)\s+(\d+)$", text)
    if delete_match:
        return delete_note(int(delete_match.group(1)))

    return None