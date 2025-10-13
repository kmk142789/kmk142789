from types import SimpleNamespace

from echo.echonet.gossip import Gossip


class FakeReceipts:
    def __init__(self, heights):
        self._heights = heights

    def tip(self):
        return "local"

    def height(self, tip):
        return self._heights.get(tip, 0)


def test_better_tip():
    registry = SimpleNamespace(list=lambda: [], mark_dead=lambda peer_id: None, note_tip=lambda peer_id, tip: None)
    receipts = FakeReceipts({"local": 5, "remote": 7})
    gossip = Gossip(registry=registry, receipts=receipts)
    assert gossip._better("remote") is True
