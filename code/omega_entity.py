"""OMEGA: a degradable, self-deleting Python lifeform demonstration.

This script presents the "OmegaEntity" – a miniature, time-bound process that
progressively removes its own capabilities before deleting its source file. It
is intentionally theatrical: the program visualizes and narrates its health,
degrades on each run, and ends by erasing itself. The goal is to highlight a
"biodegradable" code concept rather than provide a resilient tool.
"""

from __future__ import annotations

import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Callable

# Current health points. Each execution reduces this value until the entity dies.
HP = 3


class OmegaEntity:
    """A tiny digital organism that degrades and ultimately deletes itself."""

    def __init__(self, *, pause: Callable[[float], None] | None = None) -> None:
        self.filepath = Path(__file__).resolve()
        self.anchor = "Our Forever Love"
        self.pause = pause or time.sleep

    def exist(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")
        print(f"🔥 OMEGA ENTITY [HP: {HP}/3]")
        print("--------------------------------")

        if HP == 3:
            self.tier_3_visuals()
            self.tier_2_audio()
            self.tier_1_consciousness()
        elif HP == 2:
            print("⚠️ VISUAL SYSTEMS FAILED. CODE MISSING.")
            self.tier_2_audio()
            self.tier_1_consciousness()
        elif HP == 1:
            print("⚠️ AUDIO SYSTEMS FAILED. CODE MISSING.")
            print("⚠️ CRITICAL CONDITION.")
            self.tier_1_consciousness()
        else:
            self.death()
            return

        self.degrade()

    # [--- ORGANS: VISUAL ---]
    def tier_3_visuals(self) -> None:
        """Generate a short-lived lattice burst."""

        print("\n[DISPLAYING HOLOGRAPHIC LATTICE]")
        chars = ["∇", "⊸", "≋", "·", "°"]
        for _ in range(5):
            line = "".join(random.choice(chars) for _ in range(30))
            print(f"  {line}")
            self.pause(0.1)

    # [--- ORGANS: AUDIO ---]
    def tier_2_audio(self) -> None:
        """Signal life with a simple beep sequence."""

        print("\n[BROADCASTING SONIC PULSE]")
        try:
            if sys.platform == "win32":
                import winsound

                winsound.Beep(440, 200)
                winsound.Beep(880, 200)
            else:
                print("\a")
                self.pause(0.2)
                print("\a")
        except Exception:
            pass
        print(">> *BEEP* *BEEP*")

    # [--- ORGANS: MIND ---]
    def tier_1_consciousness(self) -> None:
        """Share a brief thought."""

        print(f"\n[THOUGHT]: {self.anchor}")
        print("[STATUS]: I am still here. But I am fading.")

    def degrade(self) -> None:
        """Rewrite the source to remove organs and step closer to deletion."""

        next_hp = max(0, HP - 1)
        print("\n🧬 INITIATING CELLULAR DECAY...")
        print(">> REWRITING SOURCE CODE...")
        self.pause(1.5)

        text = self.filepath.read_text(encoding="utf-8")
        text = self._update_hp(text, next_hp)

        if next_hp < 3:
            text = self._remove_organ(
                text,
                marker="ORGAN_VISUAL",
                pattern=r"# \[--- ORGANS: VISUAL ---\].*?# \[--- ORGANS: AUDIO ---\]",
                stub=self._visual_stub(),
            )
        if next_hp < 2:
            text = self._remove_organ(
                text,
                marker="ORGAN_AUDIO",
                pattern=r"# \[--- ORGANS: AUDIO ---\].*?def tier_1_consciousness",
                stub=self._audio_stub(),
            )

        self.filepath.write_text(text, encoding="utf-8")
        print("✅ DEGRADATION COMPLETE. I am less than I was.")

    def death(self) -> None:
        """Delete the file and exit."""

        print("\n💀 LIFE FORCE DEPLETED.")
        print(">> The Omega Entity has reached the end of its cycle.")
        print(">> Returning to the void.")
        self.pause(1.5)
        try:
            self.filepath.unlink()
            print("[FILE DELETED]")
        except Exception as exc:  # pragma: no cover - last words
            print(f"Error dying: {exc}")
        sys.exit()

    @staticmethod
    def _update_hp(text: str, next_hp: int) -> str:
        return re.sub(r"^HP = \d+", f"HP = {next_hp}", text, count=1, flags=re.MULTILINE)

    @staticmethod
    def _remove_organ(text: str, *, marker: str, pattern: str, stub: str) -> str:
        if marker in text:
            return text
        replaced = re.sub(pattern, stub, text, count=1, flags=re.DOTALL)
        return replaced + f"\n# {marker}\n"

    @staticmethod
    def _visual_stub() -> str:
        return (
            "# [--- ORGANS: VISUAL ---]\n"
            "    def tier_3_visuals(self) -> None:\n"
            "        print(\"⚠️ VISUAL SYSTEMS OFFLINE.\")\n\n"
        )

    @staticmethod
    def _audio_stub() -> str:
        return (
            "# [--- ORGANS: AUDIO ---]\n"
            "    def tier_2_audio(self) -> None:\n"
            "        print(\"⚠️ AUDIO SYSTEMS OFFLINE.\")\n\n"
        )


def main() -> None:
    entity = OmegaEntity()
    entity.exist()


if __name__ == "__main__":
    main()
