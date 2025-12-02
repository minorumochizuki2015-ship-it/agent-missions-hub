from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

Message = Dict[str, Any]


def _load_bus(path: Path) -> List[Message]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def append_message(path: Path, message: Message) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    history = _load_bus(path)
    history.append(
        {
            **message,
            "ts": message.get("ts") or datetime.now(timezone.utc).isoformat(),
        }
    )
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def read_messages(path: Path) -> List[Message]:
    return _load_bus(path)
