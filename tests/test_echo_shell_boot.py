import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from echo_shell_boot import boot_echo


def test_boot_echo_output(capsys):
    boot_echo()
    captured = capsys.readouterr()
    out_lines = captured.out.strip().splitlines()
    assert out_lines[0].startswith("Initializing EchoShell")
    assert any("Device ready" in line for line in out_lines)
