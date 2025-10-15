# Echo Manifest Dashboard

<div id="echo-manifest-dashboard" class="manifest-dashboard">
  <p>Loading manifest snapshot…</p>
</div>

<script>
(function () {
  const container = document.getElementById('echo-manifest-dashboard');
  if (!container) {
    return;
  }

  function renderTable(manifest) {
    const table = document.createElement('table');
    table.innerHTML = `
      <thead>
        <tr>
          <th>Engine</th>
          <th>Kind</th>
          <th>Entrypoints</th>
          <th>Tests</th>
        </tr>
      </thead>
      <tbody>
        ${manifest.engines
          .map(
            (engine) => `
              <tr>
                <td>${engine.name}</td>
                <td>${engine.kind}</td>
                <td>${engine.entrypoints.length}</td>
                <td>${engine.tests.length}</td>
              </tr>
            `,
          )
          .join('')}
      </tbody>
    `;

    const states = document.createElement('p');
    states.textContent = `Cycle: ${manifest.states.cycle} · Resonance: ${manifest.states.resonance} · Amplification: ${manifest.states.amplification}`;

    container.innerHTML = '';
    container.appendChild(states);
    container.appendChild(table);
  }

  fetch('../echo_manifest.json')
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Failed to fetch manifest: ${response.status}`);
      }
      return response.json();
    })
    .then(renderTable)
    .catch((error) => {
      container.innerHTML = `<p class="error">Unable to load manifest dashboard: ${error.message}</p>`;
    });
})();
</script>

<style>
.manifest-dashboard table {
  border-collapse: collapse;
  width: 100%;
  margin-top: 0.75rem;
}

.manifest-dashboard th,
.manifest-dashboard td {
  border: 1px solid #ccc;
  padding: 0.5rem;
  text-align: left;
}

.manifest-dashboard thead {
  background-color: rgba(0, 0, 0, 0.05);
}

.manifest-dashboard .error {
  color: #d73a49;
  font-weight: 600;
}
</style>
