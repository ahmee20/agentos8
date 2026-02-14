from __future__ import annotations
import json, time, hashlib
from dataclasses import dataclass
from typing import Any, Dict

def state_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()[:16]

@dataclass
class TraceLogger:
    path: str
    state_id: str

    def log(self, rec: Dict[str, Any]) -> None:
        r = dict(rec)
        r.setdefault("ts", time.time())
        r.setdefault("state_id", self.state_id)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
