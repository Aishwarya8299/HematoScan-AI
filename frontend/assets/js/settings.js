(() => {
  const preferencesKey = "hematoscan_preferences";
  const preferences = JSON.parse(localStorage.getItem(preferencesKey) || "{}");
  const nameInput = document.querySelector("[data-display-name]");
  const accountName = document.querySelector("[data-account-name]");
  const accountRole = document.querySelector("[data-account-role]");
  const profileMessage = document.querySelector("[data-profile-message]");
  const passwordForm = document.querySelector("[data-password-form]");
  const passwordMessage = document.querySelector("[data-password-message]");
  const focusMode = document.querySelector("[data-focus-mode]");

  document.querySelectorAll("[data-preference]").forEach((input) => {
    const key = input.dataset.preference;
    if (typeof preferences[key] === "boolean") input.checked = preferences[key];
    input.addEventListener("change", () => {
      preferences[key] = input.checked;
      localStorage.setItem(preferencesKey, JSON.stringify(preferences));
    });
  });

  if (preferences.focusMode) {
    focusMode.checked = true;
    document.body.classList.add("focus-mode");
  }
  focusMode?.addEventListener("change", () => {
    preferences.focusMode = focusMode.checked;
    document.body.classList.toggle("focus-mode", focusMode.checked);
    localStorage.setItem(preferencesKey, JSON.stringify(preferences));
  });

  document.querySelector("[data-save-profile]")?.addEventListener("click", () => {
    const name = nameInput.value.trim();
    if (name.length < 2) {
      profileMessage.textContent = "Enter a display name.";
      profileMessage.classList.remove("is-success");
      return;
    }
    accountName.textContent = name;
    profileMessage.textContent = "Profile preference saved in this browser.";
    profileMessage.classList.add("is-success");
  });

  passwordForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    const newPassword = document.querySelector("#new-password").value;
    const repeatPassword = document.querySelector("#repeat-password").value;
    passwordMessage.classList.remove("is-success");
    if (newPassword !== repeatPassword) {
      passwordMessage.textContent = "New passwords do not match.";
      return;
    }
    passwordMessage.textContent = "Password change will be connected to the account API.";
    passwordMessage.classList.add("is-success");
    passwordForm.reset();
  });

  document.querySelector("[data-sign-out]")?.addEventListener("click", () => {
    localStorage.clear();
    window.location.href = "index.html";
  });
})();
