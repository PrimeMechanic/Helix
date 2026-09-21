"""Daily portfolio-value snapshots used by the HELIX performance page."""

import json
from datetime import date
from pathlib import Path


HISTORY_FILE = Path(__file__).resolve().parent.parent / "portfolio_history.json"


def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        entries = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return [entry for entry in entries if isinstance(entry, dict) and "date" in entry and "value" in entry]
    except (OSError, json.JSONDecodeError):
        return []


def record_snapshot(value, cost):
    """Create or refresh today's single portfolio snapshot."""
    today = date.today().isoformat()
    history = load_history()
    snapshot = {"date": today, "value": round(value, 2), "cost": round(cost, 2)}
    if history and history[-1]["date"] == today:
        history[-1] = snapshot
    else:
        history.append(snapshot)
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return history
