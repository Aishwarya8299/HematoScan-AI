(() => {
  const apiBase = `http://${window.location.hostname || "localhost"}:8000`;
  const requestedPage = new URLSearchParams(window.location.search).get("next");
  const nextPage = ["analysis.html", "technician.html"].includes(requestedPage) ? requestedPage : "technician.html";
  const form = document.querySelector("[data-login-form]");
  const message = document.querySelector("[data-form-message]");
  const submitLabel = document.querySelector("[data-submit-label]");
  const passwordToggle = document.querySelector("[data-password-toggle]");
  const password = document.querySelector("#password");

  const copy = {
    title: "Welcome back,\nLab Professional.",
    description: "Sign in to access your AI-powered blood smear analysis workspace. Fast, focused, and secure.",
    subtitle: "Access your technician dashboard.",
    demoLabel: "Technician",
    email: "technician@hematoscan.local",
  };

  const title = document.querySelector("[data-welcome-title]");
  title.innerHTML = copy.title.replace("\n", "<br>");
  document.querySelector("[data-welcome-copy]").textContent = copy.description;
  document.querySelector("[data-form-subtitle]").textContent = copy.subtitle;
  document.querySelector("[data-demo-label]").textContent = copy.demoLabel;
  document.querySelector("[data-demo-email]").textContent = copy.email;
  document.title = "HematoScan AI | Lab Sign In";

  passwordToggle?.addEventListener("click", () => {
    const showing = password.type === "text";
    password.type = showing ? "password" : "text";
    passwordToggle.textContent = showing ? "Show" : "Hide";
    passwordToggle.setAttribute("aria-label", showing ? "Show password" : "Hide password");
  });

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector("button[type='submit']");
    const formData = new FormData(form);
    const credentials = { email: formData.get("email"), password: formData.get("password") };
    submit.disabled = true;
    submitLabel.textContent = "Signing in...";
    message.textContent = "";
    message.classList.remove("is-success");

    try {
      const response = await fetch(`${apiBase}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Unable to sign in");
      }
      const profileResponse = await fetch(`${apiBase}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${result.access_token}` },
      });
      const profile = await profileResponse.json();
      if (!profileResponse.ok) throw new Error(profile.detail || "Unable to verify account");
      if (profile.role !== "technician") {
        throw new Error("This portal is currently available to lab technicians only.");
      }
      localStorage.setItem("hematoscan_access_token", result.access_token);
      localStorage.setItem("hematoscan_role", "technician");
      message.classList.add("is-success");
      message.textContent = "Signed in. Opening your workspace...";
      window.setTimeout(() => {
        window.location.href = nextPage;
      }, 350);
    } catch (error) {
      message.textContent = error instanceof Error ? error.message : "Unable to sign in";
      submit.disabled = false;
      submitLabel.textContent = "Sign in";
    }
  });
})();
