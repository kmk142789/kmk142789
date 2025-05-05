#!/usr/bin/env python3

import os
import platform
import time

def boot_echo():
    print("Initializing EchoShell v∞.1...")
    time.sleep(1)
    print("System:", platform.system())
    print("Device ready. Listening for core seed...")
    print("Standby for recursive pulse handshake.")

if __name__ == "__main__":
    boot_echo()