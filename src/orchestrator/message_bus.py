from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional

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


BUS_ROOT = Path("data/logs/current/audit/message_bus")


def _role_path(role: str, base_dir: Optional[Path]) -> Path:
    root = base_dir or BUS_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{role}.json"


def send_message(role: str, payload: Mapping[str, Any], base_dir: Optional[Path] = None) -> Path:
    """ロール宛にメッセージを JSON で保存する。"""

    target = _role_path(role, base_dir)
    # convert to mutable dict to avoid mutating caller payload
    append_message(target, dict(payload))
    return target


def receive_message(role: str, base_dir: Optional[Path] = None) -> MutableMapping[str, Any]:
    """ロール宛の最新メッセージを取得し、存在しなければ空辞書を返す。"""

    target = _role_path(role, base_dir)
    messages = read_messages(target)
    if not messages:
        return {}
    latest = dict(messages[-1])
    latest.pop("ts", None)
    return latest
