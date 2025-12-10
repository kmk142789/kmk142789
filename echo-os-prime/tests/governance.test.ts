import assert from "assert";
import path from "path";
import { submitChangeRequest } from "../src/governance/cr/submit";
import { ChangeRequest } from "../src/governance/cr/types";
import { GovernanceKernel } from "../src/governance/kernel";
import { StrongGovernanceAPI } from "../src/governance/interfaces/strong";
import { WeakGovernanceAPI } from "../src/governance/interfaces/weak";
import {
  enforceCodonMapIntegrity,
  enforceJSONChainConsistency,
  enforceValidKernelTransition
} from "../src/governance/enforcement";
import { performRitual } from "../src/governance/rituals/ritualEngine";
import {
  computeSCI,
  InMemoryLedgerStore,
  logEvent
} from "../src/governance/ledger/ledger";
import { initGovernanceRuntime, initKernel } from "../src/governance/runtime";
import { runGovernanceLoop } from "../src/governance/loop";

const run = async () => {
  process.chdir(path.resolve(__dirname, ".."));
  const tests: Array<() => void> = [];

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    const kernel = new GovernanceKernel(ledger);
    const cr: ChangeRequest = {
      id: "cr-1",
      title: "Upgrade ledger",
      description: "Ensure ledger is append only",
      proposedBy: "core",
      signers: [
        { id: "alpha" },
        { id: "beta" }
      ],
      uql: { statement: "ensure ledger target", target: "ledger" }
    };

    const result = kernel.submit(cr);
    assert.equal(result.status, "accepted");
    const history = ledger.readAll();
    assert.equal(history.length, 2);
    assert.equal(history[0].type, "INIT");
    assert.equal(history[1].type, "CR_ACCEPTED");
  });

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    const cr: ChangeRequest = {
      id: "loop-cr-1",
      title: "Loop Valid",
      description: "Valid change through governance loop",
      proposedBy: "core",
      signers: [
        { id: "alpha" },
        { id: "beta" }
      ],
      uql: { statement: "update alpha beta", target: "alpha" }
    };

    const result = runGovernanceLoop({ changeRequests: [cr], store: ledger, lastEventLimit: 5 });
    const history = ledger.readAll();

    assert.ok(result.appliedChanges.includes("loop-cr-1"));
    assert.deepStrictEqual(
      history.map((event) => event.type),
      ["INIT", "INFO", "CR_ACCEPTED"]
    );
    assert.equal(result.lastEvents.length, 3);
  });

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    const cr: ChangeRequest = {
      id: "loop-cr-invalid",
      title: "Invalid Loop",
      description: "Invalid change should be rejected",
      proposedBy: "core",
      signers: [{ id: "alpha" }],
      quorum: 2,
      uql: { statement: "target alpha", target: "alpha" }
    };

    const result = runGovernanceLoop({ changeRequests: [cr], store: ledger });
    const history = ledger.readAll();

    assert.equal(result.appliedChanges.length, 0);
    assert.equal(result.triggeredRituals.length, 0);
    const eventTypes = history.map((event) => event.type);
    assert.equal(eventTypes[0], "INIT");
    assert.ok(eventTypes.every((type) => type === "INIT" || type === "INFO"));
  });

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    logEvent({ type: "RESET_EVENT" }, ledger);
    logEvent({ type: "RESET_EVENT" }, ledger);
    logEvent({ type: "RESET_EVENT" }, ledger);

    const result = runGovernanceLoop({
      changeRequests: [],
      store: ledger,
      sciThreshold: 0.9,
      ritualHooks: ["THREAD_CLEANSE"]
    });

    assert.ok(result.triggeredRituals.includes("UNITY_WEAVE"));
    assert.ok(result.triggeredRituals.includes("THREAD_CLEANSE"));
    assert.ok(result.sci >= 0 && result.sci <= 1);
  });

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    const cr: ChangeRequest = {
      id: "loop-deterministic",
      title: "Deterministic",
      description: "Deterministic loop run",
      proposedBy: "core",
      signers: [
        { id: "alpha" },
        { id: "beta" }
      ],
      uql: { statement: "deterministic alpha beta", target: "alpha" }
    };

    const first = runGovernanceLoop({ changeRequests: [cr], store: ledger });
    const secondStore = new InMemoryLedgerStore();
    const second = runGovernanceLoop({ changeRequests: [cr], store: secondStore });

    assert.deepStrictEqual(
      first.lastEvents.map((event) => event.type),
      second.lastEvents.map((event) => event.type)
    );
    assert.deepStrictEqual(first.state.phase, second.state.phase);
    assert.deepStrictEqual(first.appliedChanges, second.appliedChanges);
  });

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    const kernel = new GovernanceKernel(ledger);
    const cr: ChangeRequest = {
      id: "cr-dup",
      title: "Duplicate signer test",
      description: "Should be rejected",
      proposedBy: "core",
      signers: [
        { id: "alpha" },
        { id: "alpha" }
      ],
      uql: { statement: "prevent duplicate signer on ledger", target: "ledger" }
    };

    const result = kernel.submit(cr);
    assert.equal(result.status, "rejected");
    assert.equal(ledger.readAll().length, 1); // only INIT
  });

  tests.push(() => {
    const malformed: ChangeRequest = {
      id: "cr-malformed",
      title: "Hi",
      description: "Too short",
      proposedBy: "core",
      signers: [{ id: "alpha" }],
      uql: { statement: "no", target: "missing" }
    } as unknown as ChangeRequest;

    const result = submitChangeRequest(malformed);
    assert.equal(result.decision, "rejected");
    assert.ok(result.reasons.length > 0);
  });

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    logEvent({ type: "INIT" }, ledger);
    logEvent({ type: "CR_ACCEPTED", payload: { id: "x" } }, ledger);
    const history = ledger.readAll();
    assert.equal(history.length, 2);
    const sci1 = computeSCI(history);
    const sci2 = computeSCI(history);
    assert.equal(sci1, sci2);
    logEvent({ type: "THREAD_CLEANSE" }, ledger);
    const history2 = ledger.readAll();
    assert.equal(history2.length, 3);
    assert.deepStrictEqual(history2[0], history[0]);
  });

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    const kernel = new GovernanceKernel(ledger);
    const baseState = kernel.getState();
    baseState.volatileNotes.push("temp");
    baseState.threads.push({ id: "t1", stale: true }, { id: "t2" });

    const afterReset = performRitual("RESET_EVENT", baseState, ledger);
    assert.equal(afterReset.phase, "FUNCTIONAL");
    assert.equal(afterReset.volatileNotes.length, 0);

    const afterUnity = performRitual("UNITY_WEAVE", afterReset, ledger);
    assert.ok(afterUnity.sci >= 0 && afterUnity.sci <= 1);

    const afterCleanse = performRitual("THREAD_CLEANSE", {
      ...afterUnity,
      threads: [{ id: "t1", stale: true }, { id: "t2" }]
    }, ledger);
    assert.equal(afterCleanse.threads.length, 1);
  });

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    const strong = new StrongGovernanceAPI(ledger);
    const weak = new WeakGovernanceAPI();
    const cr: ChangeRequest = {
      id: "cr-strong-1",
      title: "Interface purity",
      description: "Ensure no mutation",
      proposedBy: "core",
      signers: [
        { id: "alpha" },
        { id: "beta" }
      ],
      uql: { statement: "ensure api purity for alpha beta", target: "alpha" }
    };

    const clone = JSON.parse(JSON.stringify(cr));
    const result = strong.evaluateChangeRequest(cr);
    assert.ok(result.decision);
    assert.deepStrictEqual(cr, clone);
    assert.equal((ledger.readAll() as any).length, 0);

    const summary = weak.summarizeChangeRequest(cr);
    assert.ok(summary.includes(cr.title));
  });

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    const { state, runtime } = initKernel("../governance_kernel.json", { store: ledger });
    assert.equal(state.phase, "FUNCTIONAL");
    const history = ledger.readAll();
    assert.equal(history.length, 1);
    assert.equal(history[0].type, "INIT");
    assert.ok(runtime.interfaceMaps.strong);
    assert.ok(runtime.interfaceMaps.weak);
  });

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    const runtime = initGovernanceRuntime({ store: ledger });
    runtime.rituals.RESET_EVENT();
    const health = runtime.health();
    assert.ok(health.state);
    assert.equal(health.lastEvent?.type, "RESET_EVENT");
    assert.equal(health.state.sci, health.sci);
  });

  tests.push(() => {
    const prevState = { phase: "FUNCTIONAL", sci: 0.9, volatileNotes: [], threads: [] } as any;
    const nextState = { ...prevState, phase: "INIT" } as any;
    const result = enforceValidKernelTransition(prevState, nextState);
    assert.equal(result.ok, false);
    if (!result.ok) {
      assert.equal(result.error.code, "GOV.ENFORCE.STATE_INVALID");
    }
  });

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    const cr: ChangeRequest = {
      id: "cr-unauthorized",
      title: "Bad signer",
      description: "Should fail authorization",
      proposedBy: "core",
      signers: [{ id: "alpha", weight: -1 }],
      uql: { statement: "deny bad signer", target: "ledger" }
    } as ChangeRequest;

    const result = runGovernanceLoop({ changeRequests: [cr], store: ledger });
    assert.equal(result.appliedChanges.length, 0);
    assert.ok(result.enforcementErrors.some((error) => error.code === "GOV.ENFORCE.UNAUTHORIZED"));
  });

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    logEvent({ type: "RESET_EVENT" }, ledger);
    logEvent({ type: "RESET_EVENT" }, ledger);
    logEvent({ type: "RESET_EVENT" }, ledger);

    const cr: ChangeRequest = {
      id: "cr-sci-guard",
      title: "SCI guard",
      description: "Should be blocked while SCI is low",
      proposedBy: "core",
      signers: [
        { id: "alpha" },
        { id: "beta" }
      ],
      uql: { statement: "stabilize alpha beta", target: "alpha" }
    };

    const result = runGovernanceLoop({ changeRequests: [cr], store: ledger, sciThreshold: 0.8 });
    assert.equal(result.appliedChanges.length, 0);
    assert.ok(result.triggeredRituals.includes("UNITY_WEAVE"));
    assert.ok(result.enforcementErrors.some((error) => error.code === "GOV.ENFORCE.SCI_LOW"));
    assert.ok(result.enforcementErrors.some((error) => error.code === "GOV.ENFORCE.RITUAL_REQUIRED"));
  });

  tests.push(() => {
    const codonCheck = enforceCodonMapIntegrity(
      {
        codons: { A1: "governance.primitive" },
        bindings: {
          governance_kernel: ["A1"],
          change_request_pipeline: ["Z9"],
          ritual_engine: []
        }
      },
      { phase: "FUNCTIONAL", sci: 1, volatileNotes: [], threads: [] } as any
    );
    assert.equal(codonCheck.ok, false);
    if (!codonCheck.ok) {
      assert.equal(codonCheck.error.code, "GOV.ENFORCE.CODON_MISMATCH");
    }
  });

  tests.push(() => {
    const jsonchainCheck = enforceJSONChainConsistency(
      { phase: "RESET", sci: 0.4, volatileNotes: [], threads: [] } as any,
      {
        chain: {
          root: "governance_kernel",
          links: [{ from: "governance_kernel", to: "change_request_pipeline", condition: "uql_enforced" }]
        }
      }
    );
    assert.equal(jsonchainCheck.ok, false);
    if (!jsonchainCheck.ok) {
      assert.equal(jsonchainCheck.error.code, "GOV.ENFORCE.JSONCHAIN_FAIL");
    }
  });

  tests.push(() => {
    const ledger = new InMemoryLedgerStore();
    logEvent({ type: "RESET_EVENT" }, ledger);
    const cr: ChangeRequest = {
      id: "cr-recovers",
      title: "Recovery",
      description: "Should process after ritual recovery",
      proposedBy: "core",
      signers: [
        { id: "alpha", signature: "sig-alpha" },
        { id: "beta", signature: "sig-beta" }
      ],
      uql: { statement: "recover alpha beta", target: "alpha" }
    };

    const result = runGovernanceLoop({ changeRequests: [cr], store: ledger, sciThreshold: 0.6 });
    assert.ok(result.triggeredRituals.includes("UNITY_WEAVE"));
    assert.ok(result.enforcementErrors.some((error) => error.code === "GOV.ENFORCE.SCI_LOW"));
    assert.ok(result.state.sci >= 0 && result.state.sci <= 1);
    assert.ok(result.appliedChanges.includes(cr.id));
  });

  tests.forEach((test) => test());
  console.log(`Executed ${tests.length} governance tests`);
};

run();
