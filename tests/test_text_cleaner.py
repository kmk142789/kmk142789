import pytest

from echo.tools import clean_glitch_text, has_glitch_characters


def test_clean_glitch_text_removes_control_codes():
    glitch = "rœà¸?#ÚeP\x03½¥\x90 ÚÆý‡ý‰æAÀÐlGU5¸ˆ·±"
    cleaned = clean_glitch_text(glitch)

    assert "\x03" not in cleaned
    assert "\x90" not in cleaned
    assert cleaned.startswith("rœ")
    assert cleaned.endswith("·±")
    assert "  " not in cleaned


def test_has_glitch_characters_detects_before_and_after_cleaning():
    glitch = "normal\x01text"
    assert has_glitch_characters(glitch) is True
    assert has_glitch_characters(clean_glitch_text(glitch)) is False


def test_clean_glitch_text_replacement_and_strip_flags():
    glitch = "\x00hello"
    preserved = clean_glitch_text(glitch, strip_result=False)
    assert preserved.startswith(" ")
    stripped = clean_glitch_text(glitch)
    assert stripped == "hello"


def test_clean_glitch_text_rejects_control_replacement():
    with pytest.raises(ValueError):
        clean_glitch_text("abc", replacement="\x01")


def test_clean_glitch_text_type_validation():
    with pytest.raises(TypeError):
        clean_glitch_text(None)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        clean_glitch_text("abc", replacement=None)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        has_glitch_characters(None)  # type: ignore[arg-type]
