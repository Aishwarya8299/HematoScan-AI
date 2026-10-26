(() => {
  const sidebar = document.querySelector("[data-sidebar]");
  const scrim = document.querySelector("[data-sidebar-close]");
  const openButton = document.querySelector("[data-sidebar-open]");

  if (!sidebar || !scrim || !openButton) {
    return;
  }

  const setOpen = (isOpen) => {
    sidebar.classList.toggle("is-open", isOpen);
    scrim.classList.toggle("is-visible", isOpen);
    openButton.setAttribute("aria-expanded", String(isOpen));
    document.body.style.overflow = isOpen ? "hidden" : "";
  };

  openButton.addEventListener("click", () => setOpen(true));
  scrim.addEventListener("click", () => setOpen(false));

  sidebar.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", () => setOpen(false));
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 760) {
      setOpen(false);
    }
  });
})();
