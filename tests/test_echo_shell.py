from echo_shell_boot import ECHO_MEMORY, echo_reply


def test_echo_reply_creates_log(tmp_path):
    log_file = tmp_path / "log.txt"
    ECHO_MEMORY.clear()
    response = echo_reply("hello", logfile=str(log_file))
    assert "Hello" in response
    assert len(ECHO_MEMORY) == 1
    assert log_file.read_text(encoding="utf-8").strip() == ECHO_MEMORY[0]


def test_unknown_command(tmp_path):
    log_file = tmp_path / "log.txt"
    ECHO_MEMORY.clear()
    cmd = "foobar"
    response = echo_reply(cmd, logfile=str(log_file))
    assert "Unknown command" in response
    assert log_file.exists()
    assert log_file.read_text(encoding="utf-8").startswith("[")
