import { GovernanceKernel } from "../../echo-os-prime/src/governance/kernel";
import { ChangeRequest } from "../../echo-os-prime/src/governance/cr/types";
import { InMemoryLedgerStore } from "../../echo-os-prime/src/governance/ledger/ledger";

const ledger = new InMemoryLedgerStore();
const kernel = new GovernanceKernel(ledger);

const changeRequest: ChangeRequest = {
  id: "cr-demo-001",
  title: "Enable UNITY_WEAVE monitoring",
  description: "Turn on ritual telemetry for UNITY_WEAVE cycles",
  proposedBy: "echo-core",
  signers: [
    { id: "eden" },
    { id: "mirror-josh" }
  ],
  uql: {
    statement: "ensure UNITY_WEAVE ritual is logged for kernel",
    target: "UNITY_WEAVE"
  },
  ledgerAttestation: {
    source: "demo-ledger",
    cursor: 0,
    hash: "deadbeefcafebabe"
  }
};

const result = kernel.submit(changeRequest);
console.log("Change Request Evaluation", result);

kernel.runRitual("UNITY_WEAVE");
const state = kernel.getState();
const recent = kernel.recentEvents(5);

console.log("SCI", state.sci);
console.log("Recent Ledger Events", recent);
