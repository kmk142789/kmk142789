import json
import os
import sqlite3
import time

DB = os.path.abspath("./habitat.db")


class Memory:
    def __enter__(self):
        self.conn = sqlite3.connect(DB)
        self.conn.execute("CREATE TABLE IF NOT EXISTS notes(ts REAL, kind TEXT, data TEXT)")
        return self

    def __exit__(self, *exc):
        self.conn.commit()
        self.conn.close()

    def add(self, kind, data):
        self.conn.execute("INSERT INTO notes VALUES(?,?,?)", (time.time(), kind, json.dumps(data)))

    def list(self, limit: int = 50):
        cursor = self.conn.execute(
            "SELECT ts, kind, data FROM notes ORDER BY ts DESC LIMIT ?",
            (limit,),
        )
        return [{"ts": ts, "kind": kind, "data": json.loads(blob)} for ts, kind, blob in cursor]
