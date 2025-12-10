"""One-command governance enablement across all modules."""

from agent_mesh.hook_governance import *
from runtime.hook_governance import *
from revenue_mesh.hook_governance import *
from atlas_os.hook_governance import *
from alignment_fabric.hook_governance import *
from pulse_dashboard.hook_governance import *
from echo_governance_core.domain_authority import ensure_domain_authority

print("Echo Governance Core successfully bound across all modules.")
authority_snapshot = ensure_domain_authority()
print(
    f"Domain authority bound to {authority_snapshot['actor']} with "
    f"{len(authority_snapshot['domains'])} managed domains."
)
