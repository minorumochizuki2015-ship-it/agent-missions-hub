from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

BUS_ROOT = Path("data/logs/current/audit/message_bus")
def _role_path(role: str, base_dir: Path | None) -> Path:
    """ロールごとのファイルパスを返す。"""
    root = base_dir or BUS_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{role}.json"


def send_message(role: str, payload: Mapping[str, str], base_dir: Path | None = None) -> Path:
    """ロール宛にペイロードをJSONで保存する。"""
    target = _role_path(role, base_dir)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(target)
    return target


def receive_message(role: str, base_dir: Path | None = None) -> Mapping[str, str]:
    """ロール宛のペイロードを取得し、存在しなければ空辞書を返す。"""
    target = _role_path(role, base_dir)
    if not target.exists():
        return {}
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
