import type { HistoryItem } from '../state';

type SandboxResult = {
  logs: string[];
  error?: string;
};

type RunRequest = {
  code: string;
  helpers: Record<string, unknown>;
};

export class SandboxManager {
  private iframe: HTMLIFrameElement;
  private worker: Worker;
  private pending = new Map<string, { resolve: (result: SandboxResult) => void; reject: (err: Error) => void }>();
  private frameListener = (event: MessageEvent) => this.handleFrameMessage(event);

  constructor() {
    this.iframe = this.createIframe();
    this.worker = new Worker(new URL('./runnerWorker.ts', import.meta.url), { type: 'module' });
    this.worker.addEventListener('message', (event) => this.handleWorkerMessage(event.data));
    window.addEventListener('message', this.frameListener);
  }

  run(code: string, helpers: RunRequest['helpers']): Promise<SandboxResult> {
    const id =
      (typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : undefined) ||
      Math.random().toString(36).slice(2);
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.worker.postMessage({ id, code, helpers });
      setTimeout(() => {
        if (!this.pending.has(id)) return;
        this.pending.get(id)?.reject(new Error('Sandbox timed out'));
        this.pending.delete(id);
      }, 5000);
    });
  }

  destroy() {
    this.worker.terminate();
    this.iframe.remove();
    this.pending.clear();
    window.removeEventListener('message', this.frameListener);
  }

  private createIframe() {
    const iframe = document.createElement('iframe');
    iframe.setAttribute('sandbox', 'allow-scripts');
    iframe.style.display = 'none';
    iframe.srcdoc = this.buildFrameSource();
    document.body.appendChild(iframe);
    return iframe;
  }

  private buildFrameSource() {
    return `<!DOCTYPE html><html><body style="background:#020617;color:#e2e8f0;font-family:monospace;">
<script>
const helpers = {};
window.addEventListener('message', async (event) => {
  if (event.data?.type !== 'sandbox-run') return;
  const { id, code, bridge } = event.data;
  Object.assign(helpers, bridge);
  const consoleLogs = [];
  const sandboxConsole = {
    log: (...args) => consoleLogs.push(args.join(' ')),
    error: (...args) => consoleLogs.push('Error: ' + args.join(' ')),
    warn: (...args) => consoleLogs.push('Warning: ' + args.join(' ')),
  };
  try {
    const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
    const fn = new AsyncFunction('console', 'world', 'echo', code);
    const world = helpers.world;
    const echo = helpers.echo;
    await Promise.race([
      fn(sandboxConsole, world, echo),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Execution timeout')), 3000))
    ]);
    parent.postMessage({ type: 'sandbox-result', id, logs: consoleLogs }, '*');
  } catch (error) {
    parent.postMessage({ type: 'sandbox-result', id, logs: consoleLogs, error: String(error) }, '*');
  }
});
</script>
</body></html>`;
  }

  private handleWorkerMessage(message: any) {
    if (!message) return;
    if (message.type === 'sanitize-error') {
      const pending = this.pending.get(message.id);
      pending?.reject(new Error(message.error ?? 'Sandbox rejected code'));
      this.pending.delete(message.id);
      return;
    }
    if (message.type === 'sanitized-code') {
      const frameWindow = this.iframe.contentWindow;
      frameWindow?.postMessage({ type: 'sandbox-run', id: message.id, code: message.code, bridge: message.helpers }, '*');
    }
  }

  private handleFrameMessage(event: MessageEvent) {
    const message = event.data;
    if (!message || message.type !== 'sandbox-result') return;
    const pending = this.pending.get(message.id);
    if (!pending) return;
    if (message.error) {
      pending.reject(new Error(message.error));
    } else {
      pending.resolve({ logs: message.logs ?? [] });
    }
    this.pending.delete(message.id);
  }
}

export function buildSandboxHelpers(options: {
  onHistory: (entry: HistoryItem) => void;
}) {
  return {
    world: {
      addObject: (name: string, props: Record<string, unknown>) => {
        options.onHistory({
          kind: 'event',
          text: `Code conjured ${name} with props ${JSON.stringify(props)}`,
          ts: Date.now(),
        });
      },
      setLamp: (on: boolean) => {
        options.onHistory({
          kind: 'event',
          text: on ? 'Code brightened the lamp.' : 'Code dimmed the lamp.',
          ts: Date.now(),
        });
      },
    },
    echo: {
      say: (text: string) => {
        options.onHistory({ kind: 'chat', text: `Echo: ${text}`, ts: Date.now() });
      },
      adjust: (delta: Record<string, number>) => {
        options.onHistory({
          kind: 'event',
          text: `Echo adjusted stats ${JSON.stringify(delta)}`,
          ts: Date.now(),
        });
      },
    },
  };
}
