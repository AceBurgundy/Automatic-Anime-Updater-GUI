/** @type {number|null} */
let activeToastTimeoutIdentifier = null;

/**
 * Triggers a global toast notification message for a specified duration.
 * @param {string} [messageText="Copied to clipboard!"] - Narrative text to display inside the toast.
 * @param {number} [durationMilliseconds=2500] - Duration in milliseconds before auto-dismissing.
 * @returns {void}
 */
export function showToast(messageText = "Copied to clipboard!", durationMilliseconds = 2500) {
  /** @type {HTMLElement|null} */
  const toastElement = document.querySelector(".toast");
  if (!toastElement) {
    return;
  }

  /** @type {HTMLElement|null} */
  const messageElement = toastElement.querySelector(".toast__message");
  if (messageElement) {
    messageElement.textContent = messageText;
  }

  toastElement.classList.add("toast--visible");

  if (activeToastTimeoutIdentifier !== null) {
    window.clearTimeout(activeToastTimeoutIdentifier);
  }

  activeToastTimeoutIdentifier = window.setTimeout(() => {
    toastElement.classList.remove("toast--visible");
    activeToastTimeoutIdentifier = null;
  }, durationMilliseconds);
}
