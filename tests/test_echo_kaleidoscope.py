from echo.echo_kaleidoscope import EchoKaleidoscope


def test_generate_frame_is_symmetric():
    kaleidoscope = EchoKaleidoscope(width=7, height=4, palette=("A", "B"))
    rows = kaleidoscope.generate_frame(seed=42)

    for row in rows:
        assert row == row[::-1]


def test_render_is_seed_deterministic():
    kaleidoscope = EchoKaleidoscope(width=6, height=3, palette=("*",))
    first = kaleidoscope.render(seed=7)
    second = kaleidoscope.render(seed=7)

    assert first == second
