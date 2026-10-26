(() => {
  const apiBase = `http://${window.location.hostname || "localhost"}:8000`;
  const token = localStorage.getItem("hematoscan_access_token");
  if (!token) {
    window.location.replace("login.html?next=analysis.html");
    return;
  }
  const form = document.querySelector("[data-analysis-form]");
  const fileInput = document.querySelector("#image-file");
  const dropZone = document.querySelector("[data-drop-zone]");
  const preview = document.querySelector("[data-image-preview]");
  const previewImage = document.querySelector("[data-preview-image]");
  const fileName = document.querySelector("[data-file-name]");
  const previewName = document.querySelector("[data-preview-name]");
  const previewSize = document.querySelector("[data-preview-size]");
  const message = document.querySelector("[data-analysis-message]");
  const submit = form?.querySelector("[type='submit']");
  const submitLabel = document.querySelector("[data-submit-label]");
  const recentBody = document.querySelector("[data-recent-body]");
  const resultPanel = document.querySelector("[data-analysis-result]");
  const resultStatus = document.querySelector("[data-result-status]");
  const resultReason = document.querySelector("[data-result-reason]");
  const resultSummary = document.querySelector("[data-result-summary]");
  const resultProbabilities = document.querySelector("[data-result-probabilities]");
  let selectedFile = null;

  const showMessage = (text, type = "") => {
    message.textContent = text;
    message.className = `form-message ${type}`.trim();
  };

  const setFile = (file) => {
    if (!file) return;
    const validTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!validTypes.includes(file.type)) {
      showMessage("Choose a JPEG, PNG, or WebP image.", "is-error");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      showMessage("Image must be smaller than 10 MB.", "is-error");
      return;
    }
    selectedFile = file;
    fileName.textContent = file.name;
    previewName.textContent = file.name;
    previewSize.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;
    previewImage.src = URL.createObjectURL(file);
    preview.hidden = false;
    dropZone.classList.add("has-file");
    showMessage("");
  };

  fileInput?.addEventListener("change", () => setFile(fileInput.files[0]));
  document.querySelector("[data-remove-image]")?.addEventListener("click", () => {
    selectedFile = null;
    fileInput.value = "";
    preview.hidden = true;
    fileName.textContent = "No image selected";
    dropZone.classList.remove("has-file");
  });

  ["dragenter", "dragover"].forEach((eventName) => dropZone?.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("is-dragging");
  }));
  ["dragleave", "drop"].forEach((eventName) => dropZone?.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("is-dragging");
  }));
  dropZone?.addEventListener("drop", (event) => setFile(event.dataTransfer.files[0]));

  const showResult = (inference) => {
    const rejected = inference.status === "rejected";
    resultPanel.hidden = false;
    resultStatus.textContent = rejected ? "Rejected" : "Analysis complete";
    resultStatus.className = `status-badge ${rejected ? "status-badge--rejected" : "status-badge--review"}`;
    resultReason.hidden = !inference.rejection_reason;
    resultReason.textContent = inference.rejection_reason || "";
    resultSummary.replaceChildren();

    const metrics = [
      ["Predicted class", inference.predicted_class || (rejected ? "Not classified" : "Unavailable")],
      ["Classifier confidence", inference.classifier_confidence == null ? "Not available" : `${Math.round(inference.classifier_confidence * 100)}%`],
      ["Gatekeeper confidence", inference.gatekeeper?.confidence == null ? "Not available" : `${Math.round(inference.gatekeeper.confidence * 100)}%`],
    ];
    metrics.forEach(([label, value]) => {
      const metric = document.createElement("div");
      metric.className = "result-metric";
      const title = document.createElement("span");
      title.textContent = label;
      const content = document.createElement("strong");
      content.textContent = value;
      metric.append(title, content);
      resultSummary.append(metric);
    });

    resultProbabilities.replaceChildren();
    (inference.class_probabilities || []).forEach(({ label, probability }) => {
      const row = document.createElement("div");
      const heading = document.createElement("div");
      heading.className = "result-probability__heading";
      const name = document.createElement("span");
      name.textContent = label;
      const percentage = document.createElement("span");
      percentage.textContent = `${Math.round(probability * 100)}%`;
      heading.append(name, percentage);
      const track = document.createElement("div");
      track.className = "result-probability__track";
      const fill = document.createElement("span");
      fill.style.width = `${Math.max(0, Math.min(100, probability * 100))}%`;
      track.append(fill);
      row.append(heading, track);
      resultProbabilities.append(row);
    });
    resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const addRecentRow = (response) => {
    recentBody.querySelector(".empty-row")?.remove();
    const row = document.createElement("tr");
    const values = [
      response.patient_id,
      response.filename,
      response.status === "rejected" ? "Rejected" : "Awaiting review",
      response.inference.predicted_class || "Not classified",
      "Just now",
    ];
    values.forEach((value, index) => {
      const cell = document.createElement("td");
      if (index === 0) {
        const patient = document.createElement("strong");
        patient.textContent = value;
        cell.append(patient);
      } else if (index === 2) {
        const badge = document.createElement("span");
        badge.className = `status-badge ${response.status === "rejected" ? "status-badge--rejected" : "status-badge--review"}`;
        badge.textContent = value;
        cell.append(badge);
      } else {
        cell.textContent = value;
      }
      row.append(cell);
    });
    recentBody.prepend(row);
  };

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!token) {
      showMessage("Sign in as a technician before uploading a case.", "is-error");
      return;
    }
    if (!selectedFile) {
      showMessage("Choose a JPEG, PNG, or WebP image.", "is-error");
      return;
    }
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    const patientId = document.querySelector("#patient-id").value.trim();
    const body = new FormData();
    body.append("patient_id", patientId);
    body.append("image", selectedFile);
    resultPanel.hidden = true;
    submit.disabled = true;
    submitLabel.textContent = "Processing...";
    showMessage("Gatekeeper screening is running. You can keep this page open.");

    try {
      const response = await fetch(`${apiBase}/api/v1/technician/upload`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Upload failed");
      showResult(result.inference);
      addRecentRow(result);
      showMessage(result.inference.status === "rejected" ? "Image rejected by gatekeeper." : "Analysis complete.", "is-success");
      form.reset();
      selectedFile = null;
      preview.hidden = true;
      fileName.textContent = "No image selected";
      dropZone.classList.remove("has-file");
    } catch (error) {
      showMessage(error instanceof Error ? error.message : "Upload failed", "is-error");
    } finally {
      submit.disabled = false;
      submitLabel.textContent = "Run Analysis";
    }
  });
})();
