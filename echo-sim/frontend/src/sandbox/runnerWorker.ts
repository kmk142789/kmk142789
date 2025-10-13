const forbiddenPatterns = [
  /fetch\s*\(/i,
  /XMLHttpRequest/i,
  /WebSocket/i,
  /importScripts/i,
  /self\s*\.\s*postMessage\s*\(/i,
  /navigator\./i,
];

self.addEventListener('message', (event) => {
  const { id, code, helpers } = event.data ?? {};
  if (!id || typeof code !== 'string') return;
  if (code.length > 4000) {
    postMessage({ type: 'sanitize-error', id, error: 'Code is too long for the sandbox.' });
    return;
  }
  if (forbiddenPatterns.some((pattern) => pattern.test(code))) {
    postMessage({ type: 'sanitize-error', id, error: 'Restricted APIs detected.' });
    return;
  }
  postMessage({ type: 'sanitized-code', id, code, helpers });
});
