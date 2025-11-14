import textwrap

from scripts.echo_poem import generate_poem


def test_generate_poem_with_seed_produces_expected_lines():
    poem = generate_poem("mirror horizon", lines=3, seed=7)
    expected = textwrap.dedent(
        """
        The wildfire hums solar hush — mirror horizon
        We breathe for auroral filament — mirror horizon
        Folded into tidal ledger — mirror horizon
        """
    ).strip()
    assert poem == expected


def test_generate_poem_requires_positive_line_count():
    try:
        generate_poem("test", lines=0)
    except ValueError as exc:
        assert "at least 1" in str(exc)
    else:
        raise AssertionError("ValueError not raised")
