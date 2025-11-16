from src.creative_loop import LoopSeed, compose_loop, summarise_loop_suite, generate_loop


def test_compose_loop_csv_has_header_and_rows():
    seed = LoopSeed(motif="echo", fragments=["signal"], pulses=2, seed=7)
    csv_output = compose_loop(seed, format="csv")
    lines = [line for line in csv_output.strip().splitlines() if line]
    assert lines[0].split(",")[:3] == ["index", "voice", "fragment"]
    assert len(lines) == seed.pulses + 1


def test_summarise_loop_suite_counts_total_loops():
    seed = LoopSeed(motif="echo", fragments=["signal"], pulses=2, seed=3)
    loop = generate_loop(seed)
    summary = summarise_loop_suite([loop])
    assert summary["total_loops"] == 1
    assert summary["total_lines"] == len(loop.lines)
    assert isinstance(summary["top_voices"], list)
