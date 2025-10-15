# Manifest Dashboard

<div id="manifest-dashboard" data-manifest="/echo_manifest.json"></div>

<script>
(function () {
  const container = document.getElementById('manifest-dashboard');
  if (!container) {
    return;
  }
  const manifestUrl = container.getAttribute('data-manifest') || '/echo_manifest.json';
  function renderError(message) {
    container.innerHTML = `<div class="admonition warning"><p class="admonition-title">Manifest</p><p>${message}</p></div>`;
  }
  fetch(manifestUrl)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Unable to load manifest: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      const engines = Array.isArray(data.engines) ? data.engines : [];
      const rows = engines
        .map((engine) => {
          const tests = (engine.tests || []).join('<br>') || '—';
          return `<tr><td>${engine.name}</td><td>${engine.status}</td><td>${engine.path}</td><td>${tests}</td></tr>`;
        })
        .join('');
      const states = data.states || {};
      container.innerHTML = `
        <table>
          <thead>
            <tr><th>Engine</th><th>Status</th><th>Path</th><th>Tests</th></tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
        <p><strong>Cycle:</strong> ${states.cycle ?? 'n/a'} | <strong>Resonance:</strong> ${states.resonance ?? 'n/a'} | <strong>Amplification:</strong> ${states.amplification ?? 'n/a'}</p>
      `;
    })
    .catch((error) => {
      renderError(error.message);
    });
})();
</script>

<noscript>
This dashboard requires JavaScript to render the manifest table.
</noscript>
