(() => {
  const apiBase = `http://${window.location.hostname || "localhost"}:8000`;
  const token = localStorage.getItem("hematoscan_access_token");
  const healthLabel = document.querySelector("[data-health-label]");
  const healthPill = document.querySelector("[data-health-pill]");
  const gatekeeperStatus = document.querySelector("[data-gatekeeper-status]");
  const signOut = document.querySelector("[data-sign-out]");
  const statTotal = document.querySelector("[data-stat-total]");
  const statCancer = document.querySelector("[data-stat-cancer]");
  const statNormal = document.querySelector("[data-stat-normal]");

  const setHealth = (label, online) => {
    if (healthLabel) healthLabel.textContent = label;
    healthPill?.classList.toggle("is-offline", !online);
    if (gatekeeperStatus) gatekeeperStatus.textContent = online ? "Ready" : "Offline";
  };

  if (!token) {
    setHealth("Session required", false);
  } else {
    fetch(`${apiBase}/api/v1/system/health`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(2500),
    })
      .then((response) => {
        if (!response.ok) throw new Error("Health request failed");
        return response.json();
      })
      .then((health) => setHealth(health.ml_models_loaded ? "AI Model Online" : "Models warming up", health.ml_models_loaded))
      .catch(() => setHealth("System unavailable", false));

    fetch(`${apiBase}/api/v1/technician/cases`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(4000),
    })
      .then((response) => response.ok ? response.json() : [])
      .then((cases) => {
        const cancer = cases.filter((item) => item.inference?.predicted_class && item.inference.predicted_class !== "HEALTHY").length;
        const normal = cases.filter((item) => item.inference?.predicted_class === "HEALTHY").length;
        if (statTotal) statTotal.textContent = cases.length;
        if (statCancer) statCancer.textContent = cancer;
        if (statNormal) statNormal.textContent = normal;
      })
      .catch(() => {});
  }

  signOut?.addEventListener("click", () => {
    localStorage.removeItem("hematoscan_access_token");
    localStorage.removeItem("hematoscan_role");
    window.location.href = "index.html";
  });
})();
