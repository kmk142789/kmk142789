from __future__ import annotations

import hashlib

from echo.glyphnet_decoder import GlyphnetKeyDecoder


def test_decoder_extracts_entropy_and_ascii_ratio() -> None:
    decoder = GlyphnetKeyDecoder()
    features = decoder.decode_tokens(["QUJDRA", "AAAAAAAAAA=="])

    text_feature = features[0]
    assert text_feature.preview == "ABCD"
    assert text_feature.is_text
    assert text_feature.ascii_ratio == 1.0
    assert "lexical-glyph" in text_feature.tags

    binary_feature = features[1]
    assert not binary_feature.is_text
    assert binary_feature.entropy == 0.0
    assert binary_feature.fingerprint == hashlib.sha256(binary_feature.payload).hexdigest()
    assert "binary-glyph" in binary_feature.tags


def test_protocol_report_evolves_glyphnet_summary() -> None:
    decoder = GlyphnetKeyDecoder()
    features = decoder.decode_tokens(["AAAA", "QUJD"])

    report = decoder.build_protocol_report(features)
    assert report["count"] == 2
    assert report["binary"] >= 1
    assert report["lexical"] >= 0
    assert len(report["fingerprints"]) == 2
