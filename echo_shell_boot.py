#!/usr/bin/env python3

import platform
import time

from echo.thoughtlog import thought_trace


def boot_echo():
    task = "echo_shell_boot.boot_echo"
    with thought_trace(task=task) as tl:
        print("Initializing EchoShell v∞.1...")
        tl.logic("step", task, "initialising shell")
        time.sleep(1)
        system = platform.system()
        tl.logic("step", task, "system detected", {"system": system})
        print("System:", system)
        print("Device ready. Listening for core seed...")
        tl.harmonic("reflection", task, "listening for core seed cadence")
        print("Standby for recursive pulse handshake.")


if __name__ == "__main__":
    boot_echo()
