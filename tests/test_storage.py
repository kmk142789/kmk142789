import time

from federated_pulse.lww_map import LWWMap
from federated_pulse.storage.file_jsonl import FileJSONLStore
from federated_pulse.storage.sqlite_store import SQLiteStore


def test_file_jsonl_roundtrip(tmp_path):
    store_path = tmp_path / "pulse.jsonl"
    store = FileJSONLStore(path=str(store_path), node_id="N1")
    ts = int(time.time() * 1000)
    store.append("alpha", "one", ts)

    result = LWWMap("N2")
    store.load(result)
    assert result.get("alpha") == "one"


def test_sqlite_roundtrip(tmp_path):
    db = tmp_path / "pulse.db"
    store = SQLiteStore(str(db))
    ts = int(time.time() * 1000)
    store.upsert("beta", "two", ts, "N1")

    result = LWWMap("N2")
    store.load(result)
    assert result.get("beta") == "two"
