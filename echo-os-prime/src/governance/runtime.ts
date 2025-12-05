import fs from "fs";
import path from "path";
import { GovernanceKernel } from "./kernel";
import { StrongGovernanceAPI } from "./interfaces/strong";
import { WeakGovernanceAPI } from "./interfaces/weak";
import {
  FileLedgerStore,
  IntegrityEvent,
  LedgerStore
} from "./ledger/ledger";
import { ChangeRequest } from "./cr/types";
import { RitualName } from "./rituals/ritualEngine";
import { KernelState, ManifestDocument } from "./types";

export type GovernanceHealth = {
  state: KernelState;
  sci: number;
  lastEvent?: IntegrityEvent;
  ledgerPath?: string;
};

export type GovernanceRuntime = {
  kernelConfig: unknown;
  interfaceMaps: { strong: unknown; weak: unknown };
  kernel: GovernanceKernel;
  bindings: {
    strong: Record<string, unknown>;
    weak: Record<string, unknown>;
  };
  rituals: Record<RitualName, () => KernelState>;
  health: () => GovernanceHealth;
};

type InitOptions = {
  kernelPath?: string;
  strongInterfacePath?: string;
  weakInterfacePath?: string;
  store?: LedgerStore;
};

const loadJson = (relativePath: string) => {
  const filePath = path.resolve(process.cwd(), relativePath);
  const contents = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(contents);
};

export const initGovernanceRuntime = (options: InitOptions = {}): GovernanceRuntime => {
  const kernelConfig = loadJson(options.kernelPath ?? "../governance_kernel.json");
  const strongInterfaceMap = loadJson(options.strongInterfacePath ?? "../interface_map_strong.json");
  const weakInterfaceMap = loadJson(options.weakInterfacePath ?? "../interface_map_weak.json");

  const ledgerStore = options.store ?? new FileLedgerStore();
  const kernel = new GovernanceKernel(ledgerStore);
  const strongApi: StrongGovernanceAPI = kernel.getStrongInterface();
  const weakApi = new WeakGovernanceAPI();

  const deterministicBindings = {
    governance_kernel: (manifest: ManifestDocument) => kernel.evaluateManifest(manifest),
    change_request_pipeline: (cr: ChangeRequest) => kernel.submit(cr),
    ritual_engine: (name: RitualName) => kernel.runRitual(name),
    ledger: (limit = 10) => kernel.recentEvents(limit)
  };

  const advisoryBindings = {
    governance_kernel: (manifest: ManifestDocument) => strongApi.validateManifest(manifest),
    change_request_pipeline: (cr: ChangeRequest) => weakApi.summarizeChangeRequest(cr),
    ritual_engine: () => weakApi.narrativeFromLedger(ledgerStore.readAll())
  };

  const rituals: Record<RitualName, () => KernelState> = {
    RESET_EVENT: () => kernel.runRitual("RESET_EVENT"),
    UNITY_WEAVE: () => kernel.runRitual("UNITY_WEAVE"),
    THREAD_CLEANSE: () => kernel.runRitual("THREAD_CLEANSE")
  };

  const health = (): GovernanceHealth => {
    const history = ledgerStore.readAll();
    const lastEvent = history[history.length - 1];
    const state = kernel.getState();
    const ledgerPath =
      typeof (ledgerStore as FileLedgerStore).getLocation === "function"
        ? (ledgerStore as FileLedgerStore).getLocation()
        : undefined;

    return { state, sci: state.sci, lastEvent, ledgerPath };
  };

  return {
    kernelConfig,
    interfaceMaps: { strong: strongInterfaceMap, weak: weakInterfaceMap },
    kernel,
    bindings: { strong: deterministicBindings, weak: advisoryBindings },
    rituals,
    health
  };
};

export const initKernel = (
  kernelPath = "../governance_kernel.json",
  options: Omit<InitOptions, "kernelPath"> = {}
): { state: KernelState; runtime: GovernanceRuntime } => {
  const runtime = initGovernanceRuntime({ ...options, kernelPath });
  return { state: runtime.kernel.getState(), runtime };
};
