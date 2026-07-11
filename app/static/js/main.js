"use strict";

const form = document.querySelector("#upload-form");
const input = document.querySelector("#pdf-file");
const dropZone = document.querySelector("#drop-zone");
const fileName = document.querySelector("#file-name");
const submitButton = document.querySelector("#submit-button");
const statusPanel = document.querySelector("#status-panel");
const statusMessage = document.querySelector("#status-message");
const errorMessage = document.querySelector("#error-message");
const summaryCard = document.querySelector("#summary-card");
const summaryText = document.querySelector("#summary-text");
const wordCount = document.querySelector("#word-count");
const processingTime = document.querySelector("#processing-time");
const maxFileSize = 20 * 1024 * 1024;

function showError(message) { errorMessage.textContent = message; errorMessage.hidden = false; }
function clearError() { errorMessage.hidden = true; errorMessage.textContent = ""; }
function createFileList(file) { const transfer = new DataTransfer(); if (file) transfer.items.add(file); return transfer.files; }
function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  statusPanel.hidden = !isLoading;
  if (isLoading) statusMessage.textContent = "Extracting text and generating your summary…";
}
function setFile(file) {
  input.files = createFileList(file);
  fileName.textContent = file ? file.name : "";
  setLoading(false);
}
function validFile(file) {
  if (!file) { showError("Choose a PDF file to continue."); return false; }
  if (!file.name.toLowerCase().endsWith(".pdf")) { showError("Please choose a PDF file."); return false; }
  if (file.size > maxFileSize) { showError("PDF files must be 20 MB or smaller."); return false; }
  return true;
}

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.cssText = "position:fixed;opacity:0;pointer-events:none;";
  document.body.appendChild(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  textarea.remove();
  if (!copied) throw new Error("Copy is unavailable in this browser.");
}

setLoading(false);
input.addEventListener("change", () => { clearError(); setFile(input.files[0]); });
["dragenter", "dragover"].forEach((name) => dropZone.addEventListener(name, (event) => { event.preventDefault(); dropZone.classList.add("is-dragging"); }));
["dragleave", "drop"].forEach((name) => dropZone.addEventListener(name, (event) => { event.preventDefault(); dropZone.classList.remove("is-dragging"); }));
dropZone.addEventListener("drop", (event) => { clearError(); setFile(event.dataTransfer.files[0]); });

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  summaryCard.hidden = true;
  const file = input.files[0];
  if (!validFile(file)) return;
  setLoading(true);
  try {
    const body = new FormData();
    body.append("file", file);
    const response = await fetch("/api/summarize", { method: "POST", body });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || "Unable to summarize this document.");
    summaryText.textContent = payload.summary;
    wordCount.textContent = `${payload.word_count} words`;
    processingTime.textContent = `${payload.processing_time_seconds.toFixed(2)} seconds`;
    summaryCard.hidden = false;
    summaryCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (error) {
    showError(error instanceof Error ? error.message : "Unable to summarize this document.");
  } finally {
    setLoading(false);
  }
});

document.querySelector("#copy-button").addEventListener("click", async (event) => {
  try {
    await copyText(summaryText.textContent);
    event.currentTarget.textContent = "Copied!";
    window.setTimeout(() => { event.currentTarget.textContent = "Copy summary"; }, 1500);
  } catch (_) {
    showError("Could not copy the summary. Please select and copy it manually.");
  }
});
document.querySelector("#reset-button").addEventListener("click", () => {
  form.reset(); fileName.textContent = ""; summaryText.textContent = ""; wordCount.textContent = "";
  processingTime.textContent = ""; clearError(); setLoading(false); summaryCard.hidden = true; input.focus();
});
