(() => {
  const menu = document.querySelector("[data-landing-menu]");
  const nav = document.querySelector(".public-nav");
  const statusTargets = document.querySelectorAll("[data-system-status]");
  const apiBase = `http://${window.location.hostname || "localhost"}:8000`;

  if (menu && nav) {
    menu.addEventListener("click", () => {
      const isOpen = nav.classList.toggle("is-open");
      menu.setAttribute("aria-expanded", String(isOpen));
    });

    nav.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        nav.classList.remove("is-open");
        menu.setAttribute("aria-expanded", "false");
      });
    });
  }

  const updateStatus = (label, online) => {
    statusTargets.forEach((target) => {
      target.textContent = label;
      target.closest(".status-pill, .trust-strip__status")?.classList.toggle("is-offline", !online);
    });
  };

  fetch(`${apiBase}/api/v1/system/health`, { signal: AbortSignal.timeout(2500) })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Health check failed");
      }
      return response.json();
    })
    .then((health) => {
      const online = health.status === "operational" && health.ml_models_loaded;
      updateStatus(online ? "AI model online" : "AI model warming up", online);
    })
    .catch(() => updateStatus("System check unavailable", false));
})();
