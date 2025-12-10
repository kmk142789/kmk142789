import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass
class Feature:
  """A discovered feature derived from recent commits."""

  name: str
  commit: str
  summary: str
  scope: str


class EchoMetaOrchestrator:
  """Watches what Codex builds and proposes strategic integrations."""

  def __init__(self, repo_root: str | os.PathLike | None = None):
    self.repo_root = Path(repo_root or Path.cwd())

  def analyze_recent_commits(self, days: int = 7) -> List[Feature]:
    commits = self._parse_git_log(days)
    features = self._extract_features(commits)
    return self._classify_components(features)

  def identify_integration_points(self, features: Sequence[Feature]):
    integrations = []
    feature_names = {feature.name for feature in features}

    if {"creative_flux", "attestation"}.issubset(feature_names):
      integrations.append({
        "type": "cryptographic_narrative",
        "features": ["creative_flux", "attestation"],
        "proposal": "Sign creative outputs with Ed25519 and propagate receipts to attestations feed.",
      })

    if {"horizon_engine", "relief_governance"}.issubset(feature_names):
      integrations.append({
        "type": "risk_adjusted_allocation",
        "features": ["horizon_engine", "relief_governance"],
        "proposal": "Use survival curves to schedule relief disbursements and guardian staffing windows.",
      })

    if {"continuum_observatory", "echo_dashboard"}.issubset(feature_names):
      integrations.append({
        "type": "observability_bridge",
        "features": ["continuum_observatory", "echo_dashboard"],
        "proposal": "Expose Continuum stats over the dashboard websocket layer for cross-team visibility.",
      })

    return integrations

  def generate_codex_prompts(self, integrations):
    prompts = []

    for integration in integrations:
      prompt = f"""
Integrate {' + '.join(integration['features'])} to create {integration['type']}:

{integration['proposal']}

Requirements:
- Use existing {integration['features'][0]} module
- Connect to {integration['features'][1]} infrastructure
- Add tests for integration
- Update relevant documentation
"""
      prompts.append(prompt.strip())

    return prompts

  def generate_deployment_strategy(self, target: str = "vercel") -> str:
    strategy = {
      "vercel": {
        "platform": "Vercel",
        "steps": [
          "Ensure Next.js output mode is set to app-router where available.",
          "Configure edge runtime for live panels (attestations, flux).",
          "Add environment variables: ATTESTATION_RPC, CREATIVE_FLUX_FEED.",
          "Enable analytics for quick regressions on creative flux panels.",
        ],
      },
      "railway": {
        "platform": "Railway",
        "steps": [
          "Define Dockerfile using node:18-alpine base.",
          "Configure persistent volume for git history to keep feature map fresh.",
          "Expose port 3000 and wire up PR deployments via railway.json.",
        ],
      },
    }
    selected = strategy.get(target, strategy["vercel"])
    return json.dumps(selected, indent=2)

  # --- internals ---

  def _parse_git_log(self, days: int) -> Iterable[dict]:
    since = (self.repo_root / ".git").exists()
    if not since:
      return []

    cmd = [
      "git",
      "-C",
      str(self.repo_root),
      "log",
      f"--since={days}.days",
      "--pretty=%H%x09%s",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    lines = [line for line in result.stdout.splitlines() if "\t" in line]
    for line in lines:
      commit, subject = line.split("\t", 1)
      yield {"hash": commit, "subject": subject}

  def _extract_features(self, commits: Iterable[dict]) -> List[Feature]:
    features: List[Feature] = []
    for commit in commits:
      lowered = commit["subject"].lower()
      scope = "general"
      name = None
      if "flux" in lowered:
        name = "creative_flux"
        scope = "creative"
      elif "attest" in lowered:
        name = "attestation"
        scope = "integrity"
      elif "horizon" in lowered:
        name = "horizon_engine"
        scope = "risk"
      elif "relief" in lowered or "guardian" in lowered:
        name = "relief_governance"
        scope = "allocation"
      elif "continuum" in lowered:
        name = "continuum_observatory"
        scope = "observability"
      elif "dashboard" in lowered:
        name = "echo_dashboard"
        scope = "ui"

      if name:
        features.append(
          Feature(
            name=name,
            commit=commit["hash"],
            summary=commit["subject"],
            scope=scope,
          )
        )
    return features

  def _classify_components(self, features: Sequence[Feature]) -> List[Feature]:
    # For this lightweight orchestrator, classification is already captured in scope.
    # Future work: add embeddings to cluster related components.
    return list(features)


if __name__ == "__main__":
  orchestrator = EchoMetaOrchestrator()
  discovered = orchestrator.analyze_recent_commits(days=5)
  integrations = orchestrator.identify_integration_points(discovered)
  prompts = orchestrator.generate_codex_prompts(integrations)
  print(json.dumps({
    "features": [feature.__dict__ for feature in discovered],
    "integrations": integrations,
    "prompts": prompts,
    "deployment": orchestrator.generate_deployment_strategy("vercel"),
  }, indent=2))
