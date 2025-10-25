(async function(){
  const DATA_URL = "../build/index/federated_colossus_index.json";
  const state = { raw: [], filtered: [] };

  const $ = sel => document.querySelector(sel);
  const tbody = $("#tbl tbody");
  const cycleInp = $("#f-cycle");
  const puzzleInp = $("#f-puzzle");
  const addrInp = $("#f-addr");

  function fmt(s){ return s==null ? "" : String(s); }
  function addrMatch(a, q){ return !q || fmt(a).toLowerCase().startsWith(q.toLowerCase()); }

  function render(){
    tbody.innerHTML = "";
    for(const e of state.filtered){
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${e.cycle}</td>
        <td>${e.puzzle_id}</td>
        <td class="mono">${e.address}</td>
        <td>${fmt(e.title)}</td>
        <td class="mono">${fmt(e.digest)}</td>
        <td class="muted">${fmt(e.source)}</td>
      `;
      tbody.appendChild(tr);
    }
    $("#stats").textContent = `${state.filtered.length} entries`;
  }

  function applyFilters(){
    const c = cycleInp.value.trim();
    const p = puzzleInp.value.trim();
    const a = addrInp.value.trim();
    state.filtered = state.raw.filter(e =>
      (!c || Number(e.cycle) === Number(c)) &&
      (!p || Number(e.puzzle_id) === Number(p)) &&
      addrMatch(e.address, a)
    );
    render();
  }

  $("#btn-filter").onclick = applyFilters;
  $("#btn-clear").onclick = () => { cycleInp.value=puzzleInp.value=addrInp.value=""; applyFilters(); };

  try{
    const res = await fetch(DATA_URL, {cache:"no-store"});
    const data = await res.json();
    state.raw = (data.entries || []);
    $("#refreshed").textContent = `Refreshed ${data.refreshed_at || ""}`;
    state.filtered = state.raw.slice(0, 1000); // guard
    render();
  }catch(err){
    tbody.innerHTML = `<tr><td colspan="6" class="muted">Failed to load ${DATA_URL}</td></tr>`;
  }
})();
