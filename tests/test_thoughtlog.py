from echo.thoughtlog import ThoughtLogger, thought_trace
import pathlib


def test_dual_trace(tmp_path: pathlib.Path):
    logdir = tmp_path / "tl"
    tl = ThoughtLogger(dirpath=logdir, session="test-session")
    tl.logic("step", "demo", "A -> B")
    tl.harmonic("reflection", "demo", "bridging uncertainty")
    lines = (logdir / "test-session.jsonl").read_text().splitlines()
    assert any('"channel":"logic"' in line for line in lines)
    assert any('"channel":"harmonic"' in line for line in lines)


def test_context_manager(tmp_path: pathlib.Path):
    with thought_trace(task="cm-demo") as tl:
        tl.logic("step", "cm-demo", "doing work")
        tl.harmonic("reflection", "cm-demo", "feels right")
