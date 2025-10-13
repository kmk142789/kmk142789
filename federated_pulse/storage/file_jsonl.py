import json
from pathlib import Path
from typing import Any

from ..lww_map import LWWMap, Dot


class FileJSONLStore:
    """
    Append-only JSONL log: each line is {"k":..., "v":..., "ts":..., "node":...}
    """

    def __init__(self, path: str = ".fpulse/pulse.jsonl", node_id: str = "node"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.node_id = node_id

    def append(self, key: str, value: Any, ts: int) -> None:
        rec = {"k": key, "v": value, "ts": ts, "node": self.node_id}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def load(self, into: LWWMap) -> LWWMap:
        if not self.path.exists():
            return into
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                dot = Dot(ts=int(rec["ts"]), node=rec["node"])
                cur = into._data.get(rec["k"])  # pylint: disable=protected-access
                if cur is None or (dot.ts, dot.node) > (cur[1].ts, cur[1].node):
                    into._data[rec["k"]] = (rec["v"], dot)  # pylint: disable=protected-access
        return into
