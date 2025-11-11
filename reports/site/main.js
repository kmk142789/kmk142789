import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";

async function loadMatrix() {
  const response = await fetch("../matrix.json", { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Unable to load matrix.json: ${response.status}`);
  }
  return response.json();
}

async function loadMermaid() {
  const response = await fetch("../authority_flow.mmd", { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Unable to load authority_flow.mmd: ${response.status}`);
  }
  return response.text();
}

function renderMatrix(matrix) {
  const tbody = document.querySelector("#matrix-table tbody");
  tbody.innerHTML = "";
  ["Pass", "Soft", "Fail"].forEach((key) => {
    const row = document.createElement("tr");
    const outcome = document.createElement("td");
    outcome.textContent = key;
    const count = document.createElement("td");
    count.textContent = matrix.matrix[key] ?? 0;
    row.appendChild(outcome);
    row.appendChild(count);
    tbody.appendChild(row);
  });

  const findingsContainer = document.querySelector("#findings");
  findingsContainer.innerHTML = "";
  matrix.findings.forEach((finding) => {
    const card = document.createElement("article");
    card.classList.add("finding", finding.severity.toLowerCase());
    const title = document.createElement("h3");
    title.textContent = `${finding.severity.toUpperCase()}: ${finding.title}`;
    const description = document.createElement("p");
    description.textContent = finding.description;
    const references = document.createElement("ul");
    finding.references.forEach((ref) => {
      const li = document.createElement("li");
      li.textContent = `${ref.artifact}:${ref.clause} (${ref.line_start}-${ref.line_end})`;
      references.appendChild(li);
    });
    card.append(title, description, references);
    findingsContainer.appendChild(card);
  });
}

async function bootstrap() {
  try {
    const [matrix, mermaidDefinition] = await Promise.all([loadMatrix(), loadMermaid()]);
    renderMatrix(matrix);
    const container = document.getElementById("mermaid-diagram");
    container.textContent = mermaidDefinition;
    await mermaid.run({ querySelector: "#mermaid-diagram" });
  } catch (error) {
    console.error(error);
    const findingsContainer = document.querySelector("#findings");
    findingsContainer.innerHTML = `<p class="error">${error.message}</p>`;
  }
}

mermaid.initialize({ startOnLoad: false, theme: "neutral" });
bootstrap();
