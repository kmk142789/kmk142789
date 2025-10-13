from echo.receipts.receipt import make_receipt, verify_receipt


class DummyKey:
    pub = "dummy"

    def sign(self, msg: str) -> str:
        return "sig:" + msg


class DummyRing:
    def verify(self, pub: str, msg: str, sig: str) -> bool:
        return sig == "sig:" + msg


def test_receipt_roundtrip():
    receipt = make_receipt("run", {"x": 1}, "0x00", DummyKey())
    assert verify_receipt(receipt, DummyRing())
