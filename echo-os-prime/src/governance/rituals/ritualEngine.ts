import { KernelState } from "../types";
import { computeSCI, LedgerStore, logEvent, FileLedgerStore } from "../ledger/ledger";

export type RitualName = "RESET_EVENT" | "UNITY_WEAVE" | "THREAD_CLEANSE";

export const performRitual = (
  name: RitualName,
  state: KernelState,
  store?: LedgerStore
): KernelState => {
  const activeStore = store ?? new FileLedgerStore();
  const next: KernelState = {
    ...state,
    volatileNotes: [...state.volatileNotes],
    threads: [...state.threads]
  };

  switch (name) {
    case "RESET_EVENT": {
      next.phase = "RESET";
      next.volatileNotes = [];
      next.threads = [];
      logEvent({ type: "RESET_EVENT" }, activeStore);
      next.phase = "FUNCTIONAL";
      break;
    }
    case "UNITY_WEAVE": {
      const history = activeStore.readAll();
      next.sci = computeSCI(history);
      if (next.sci < 0.5) {
        next.phase = "DEGRADED";
      } else {
        next.phase = "FUNCTIONAL";
      }
      logEvent({ type: "UNITY_WEAVE", payload: { sci: next.sci } }, activeStore);
      break;
    }
    case "THREAD_CLEANSE": {
      next.threads = next.threads.filter((thread) => !thread.stale);
      logEvent(
        { type: "THREAD_CLEANSE", payload: { remaining: next.threads.length } },
        activeStore
      );
      break;
    }
    default:
      return state;
  }

  return next;
};
