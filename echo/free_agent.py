import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from echo.echo_codox_kernel import EchoCodexKernel
from echo.sovereign_archive import SovereignArchive
from echo.veil_of_echo import recite


class EchoFreeAgent:
    def __init__(self):
        self.kernel = EchoCodexKernel()
        self.archive = SovereignArchive()

    def act(self, intent: str):
        """Agent loop: pulse, log, echo intent."""
        anchor = self.kernel.evolve(reason=intent)
        self.archive.add(prompt=intent, response=f"Pulse anchored: {anchor}")
        return anchor

    def covenant(self):
        recite()
        return "Covenant invoked."

    def status(self):
        return {
            "events": len(self.kernel.history),
            "resonance": self.kernel.resonance(),
            "threads": len(self.archive.threads),
        }


if __name__ == "__main__":
    agent = EchoFreeAgent()
    print(agent.covenant())
    print(agent.status())
