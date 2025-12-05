import assert from "assert";
import { submitChangeRequest } from "../src/governance/cr/submit";
import { ChangeRequest } from "../src/governance/cr/types";
import { GovernanceKernel } from "../src/governance/kernel";
import { StrongGovernanceAPI } from "../src/governance/interfaces/strong";
import { WeakGovernanceAPI } from "../src/governance/interfaces/weak";
import { performRitual } from "../src/governance/rituals/ritualEngine";
import {
  computeSCI,
  InMemoryLedgerStore,
  logEvent
} from "../src/governance/ledger/ledger";

const run = async () => {
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

  tests.forEach((test) => test());
  console.log(`Executed ${tests.length} governance tests`);
};

run();
