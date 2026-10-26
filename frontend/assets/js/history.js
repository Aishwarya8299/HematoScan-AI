(() => {
  const apiBase = `http://${window.location.hostname || "localhost"}:8000`;
  const token = localStorage.getItem("hematoscan_access_token");
  const body = document.querySelector("[data-history-body]");
  const total = document.querySelector("[data-case-total]");
  const search = document.querySelector("[data-search]");
  const statusFilter = document.querySelector("[data-status-filter]");
  const sort = document.querySelector("[data-sort]");
  const drawer = document.querySelector("[data-case-drawer]");
  const backdrop = document.querySelector("[data-drawer-backdrop]");
  const drawerBody = document.querySelector("[data-drawer-body]");
  let records = [];

  document.querySelector("[data-role-label]").textContent = "Technician portal";

  const formatDate = (value) => value ? new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) : "—";
  const statusLabel = (value) => ({ awaiting_review: "Awaiting review", reviewed: "Reviewed", rejected: "Rejected" }[value] || value.replaceAll("_", " "));
  const statusClass = (value) => value === "rejected" ? "status-badge--rejected" : value === "reviewed" ? "status-badge--done" : "status-badge--review";
  const caseId = (record) => record.case_id || record.id || record._id;

  const visibleRecords = () => {
    const query = search.value.trim().toLowerCase();
    const filtered = records.filter((record) => {
      const matchesQuery = !query || `${record.patient_id} ${record.filename} ${record.inference?.predicted_class || ""}`.toLowerCase().includes(query);
      return matchesQuery && (statusFilter.value === "all" || record.status === statusFilter.value);
    });
    return filtered.sort((a, b) => {
      if (sort.value === "result") return (a.inference?.predicted_class || "").localeCompare(b.inference?.predicted_class || "");
      const first = new Date(a.created_at).getTime();
      const second = new Date(b.created_at).getTime();
      return sort.value === "oldest" ? first - second : second - first;
    });
  };

  const openDrawer = async (record) => {
    drawerBody.innerHTML = '<p class="drawer-note">Loading case detail...</p>';
    drawer.hidden = false;
    backdrop.hidden = false;
    requestAnimationFrame(() => { drawer.classList.add("is-open"); drawer.setAttribute("aria-hidden", "false"); });
    let detail = record;
    const inference = detail.inference || {};
    const probabilities = inference.class_probabilities || [];
    drawerBody.innerHTML = `<section class="drawer-section"><h3>Case summary</h3><div class="drawer-grid"><div class="drawer-metric"><span>Patient ID</span><strong>${detail.patient_id}</strong></div><div class="drawer-metric"><span>Uploaded</span><strong>${formatDate(detail.created_at)}</strong></div><div class="drawer-metric"><span>Result</span><strong>${inference.predicted_class || "Not classified"}</strong></div><div class="drawer-metric"><span>Status</span><strong>${statusLabel(detail.status)}</strong></div></div></section><section class="drawer-section"><h3>Original uploaded image</h3><img class="drawer-image" data-drawer-image alt="Original uploaded blood smear"></section><section class="drawer-section"><h3>Classification confidence</h3>${probabilities.length ? probabilities.map((item) => `<div class="drawer-probability"><div class="drawer-probability__head"><span>${item.label}</span><span>${Math.round(item.probability * 100)}%</span></div><div class="drawer-probability__bar"><span style="width:${item.probability * 100}%"></span></div></div>`).join("") : '<p class="drawer-note">Detailed probabilities are not available for this case.</p>'}</section><button class="button drawer-download" type="button" data-drawer-download>Download PDF Report</button>`;
    if (detail.image_url && token) {
      try {
        const imageResponse = await fetch(`${apiBase}${detail.image_url}`, { headers: { Authorization: `Bearer ${token}` } });
        if (imageResponse.ok) drawerBody.querySelector("[data-drawer-image]").src = URL.createObjectURL(await imageResponse.blob());
      } catch (_) { }
    }
    drawerBody.querySelector("[data-drawer-download]").addEventListener("click", () => window.print());
  };

  const closeDrawer = () => { drawer.classList.remove("is-open"); drawer.setAttribute("aria-hidden", "true"); window.setTimeout(() => { drawer.hidden = true; backdrop.hidden = true; }, 220); };
  document.querySelector("[data-drawer-close]").addEventListener("click", closeDrawer);
  backdrop.addEventListener("click", closeDrawer);

  const render = () => {
    const visible = visibleRecords();
    total.textContent = `${visible.length} case${visible.length === 1 ? "" : "s"}`;
    if (!visible.length) {
      body.innerHTML = '<tr class="history-empty"><td colspan="6"><span class="empty-icon" aria-hidden="true">▤</span><strong>No matching cases</strong><span>Try changing your search or filter.</span></td></tr>';
      return;
    }
    body.innerHTML = visible.map((record) => {
      const result = record.inference?.predicted_class || "Not classified";
      const resultClass = result === "HEALTHY" ? "is-healthy" : result === "Not classified" ? "is-muted" : "";
      return `<tr><td><strong>${record.patient_id}</strong><small>Case ${caseId(record)}</small></td><td>${record.filename}</td><td><span class="result-text ${resultClass}">${result}</span></td><td><span class="status-badge ${statusClass(record.status)}">${statusLabel(record.status)}</span></td><td>${formatDate(record.created_at)}</td><td><button class="row-action" type="button" data-open-case="${caseId(record)}">View</button></td></tr>`;
    }).join("");
    body.querySelectorAll("[data-open-case]").forEach((button) => button.addEventListener("click", () => openDrawer(records.find((record) => caseId(record) === button.dataset.openCase))));
  };

  const loadRecords = async () => {
    if (!token) { render(); return; }
    try {
      const response = await fetch(`${apiBase}/api/v1/technician/cases`, { headers: { Authorization: `Bearer ${token}` }, signal: AbortSignal.timeout(4000) });
      if (response.ok) records = await response.json();
    } catch (_) { /* Empty state remains useful when the API is unavailable. */ }
    render();
  };

  [search, statusFilter, sort].forEach((control) => control.addEventListener("input", render));
  document.querySelector("[data-sign-out]").addEventListener("click", () => { localStorage.clear(); window.location.href = "index.html"; });
  loadRecords();
})();
