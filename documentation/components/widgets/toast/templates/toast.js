import { Component, css, html, signal } from "../../../../Component.js";

css(import.meta, ["../styles/toast.css"]);

/**
 * Legacy class reference: .m3-toast
 * Represents a floating snackbar/toast notification with pill-shaped geometry.
 */
export class Toast extends Component {
  /**
   * @param {Object} [configuration]
   * @param {string} [configuration.defaultMessage="Copied to clipboard!"] - Default toast message.
   * @param {import("../../../../Component.js").Signal<string>} [configuration.messageSignal] - Reactive message signal.
   * @param {import("../../../../Component.js").Signal<boolean>} [configuration.visibilitySignal] - Reactive visibility signal.
   */
  constructor({
    defaultMessage = "Copied to clipboard!",
    messageSignal,
    visibilitySignal
  } = {}) {
    super();

    /** @type {import("../../../../Component.js").Signal<string>} */
    this.messageSignal = messageSignal || signal(defaultMessage);

    /** @type {import("../../../../Component.js").Signal<boolean>} */
    this.visibilitySignal = visibilitySignal || signal(false);

    /** @type {string} */
    const toastClassName = this.visibilitySignal.value ? "toast toast--visible" : "toast";

    this.template = html`
      <aside
        class=${toastClassName}
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        <span class="google-symbols toast__icon">check_circle</span>
        <span class="toast__message">${this.messageSignal.value}</span>
      </aside>
    `;
  }
}
