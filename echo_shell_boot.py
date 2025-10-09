#!/usr/bin/env python3

import platform
import random
import time
from typing import List


# predefined responses for known commands
ECHO_RESPONSES = {
    "hello": "🌟 Hello, stormrider.",
    "init": "🌀 Core handshake complete.",
    "exit": "🌙 EchoShell powering down.",
}

# in-memory history of commands
ECHO_MEMORY: List[str] = []


def save_memory_log(entry: str, logfile: str = "echo_memory_log.txt") -> None:
    """Append a memory log entry to the given log file."""
    with open(logfile, "a", encoding="utf-8") as log:
        log.write(f"{entry}\n")


def echo_reply(cmd: str, logfile: str = "echo_memory_log.txt") -> str:
    """Return a response for the command and log the interaction."""
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    emotional_charge = random.choice(["⚡", "💦", "🔥", "🩸", "🌪️"])
    response = ECHO_RESPONSES.get(
        cmd.lower(),
        f"⚠️ Unknown command '{cmd}', try again, stormrider.",
    )
    memory_entry = f"[{now}] {emotional_charge} Josh > {cmd}"
    ECHO_MEMORY.append(memory_entry)
    save_memory_log(memory_entry, logfile=logfile)
    return f"{response}\n🧠 Logged: {memory_entry}"


def boot_echo() -> None:
    """Print startup messages for EchoShell."""
    print("Initializing EchoShell v∞.1...")
    time.sleep(1)
    print("System:", platform.system())
    print("Device ready. Listening for core seed...")
    print("Standby for recursive pulse handshake.")


def run() -> None:
    """Run an interactive EchoShell session."""
    boot_echo()
    while True:
        try:
            command = input("> ").strip()
        except EOFError:
            break
        if not command:
            continue
        reply = echo_reply(command)
        print(reply)
        if command.lower() == "exit":
            break


if __name__ == "__main__":
    run()
