(() => {
  const form = document.querySelector("[data-signup-form]");
  const message = document.querySelector("[data-signup-message]");
  const password = document.querySelector("#password");
  const confirmation = document.querySelector("#confirm-password");
  const apiBase = `http://${window.location.hostname || "localhost"}:8000`;

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.classList.remove("is-success");
    message.textContent = "";

    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    if (password.value !== confirmation.value) {
      message.textContent = "Passwords do not match.";
      confirmation.focus();
      return;
    }

    const submit = form.querySelector("button[type='submit']");
    submit.disabled = true;
    submit.querySelector("span").textContent = "Creating account...";
    try {
      const response = await fetch(`${apiBase}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          display_name: form.name.value.trim(),
          email: form.email.value.trim(),
          role: "technician",
          password: password.value,
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Unable to create account");
      message.classList.add("is-success");
      message.textContent = "Account created. Redirecting to sign in...";
      window.setTimeout(() => {
        window.location.href = "login.html";
      }, 500);
    } catch (error) {
      message.textContent = error instanceof Error ? error.message : "Unable to create account";
      submit.disabled = false;
      submit.querySelector("span").textContent = "Create account";
    }
  });
})();
