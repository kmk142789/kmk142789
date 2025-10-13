from echo.crdt.lww import LWWMap


def test_merge_wins_by_tick():
    a = LWWMap("A")
    b = LWWMap("B")
    a.set("x", 1)
    b.set("x", 2)
    b.set("x", 3)
    a.merge(b)
    assert a.snapshot()["x"] == 3
