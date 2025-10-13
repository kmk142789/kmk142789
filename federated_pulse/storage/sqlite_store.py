import sqlite3
from pathlib import Path
from typing import Any

from ..lww_map import LWWMap, Dot

DDL = """
CREATE TABLE IF NOT EXISTS lww (
  k TEXT PRIMARY KEY,
  v BLOB,
  ts INTEGER,
  node TEXT
);
"""


class SQLiteStore:
    def __init__(self, db_path: str = ".fpulse/pulse.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute(DDL)
        self.conn.commit()

    def upsert(self, key: str, value: Any, ts: int, node: str) -> None:
        cur = self.conn.execute("SELECT ts,node FROM lww WHERE k=?", (key,)).fetchone()
        if not cur or (ts, node) > (cur[0], cur[1]):
            self.conn.execute(
                "REPLACE INTO lww(k,v,ts,node) VALUES(?,?,?,?)",
                (key, value, ts, node),
            )
            self.conn.commit()

    def load(self, into: LWWMap) -> LWWMap:
        for k, v, ts, node in self.conn.execute("SELECT k,v,ts,node FROM lww"):
            dot = Dot(ts=int(ts), node=node)
            cur = into._data.get(k)  # pylint: disable=protected-access
            if cur is None or (dot.ts, dot.node) > (cur[1].ts, cur[1].node):
                into._data[k] = (v, dot)  # pylint: disable=protected-access
        return into
