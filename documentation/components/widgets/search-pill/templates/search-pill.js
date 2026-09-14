import { Component, html, css } from "../../../../Component.js";
import { openSearchModal } from "../../search-modal/scripts/search-modal__service.js";

css(import.meta, ["../styles/search-pill.css"]);

/**
 * Search Pill Component.
 * Renders an interactive search bar trigger button with an icon and shortcut badge.
 * Legacy mapping: .sidebar-search-pill, .search-placeholder, .search-shortcut.
 */
export class SearchPill extends Component {
  /**
   * @param {Object} [configuration={}]
   * @param {string} [configuration.placeholder="Search docs..."] - Placeholder text.
   * @param {string} [configuration.shortcutText="Ctrl+K"] - Keyboard shortcut hint text.
   * @param {function(): void} [configuration.onTrigger] - Callback invoked when the search pill is activated.
   */
  constructor({
    placeholder = "Search docs...",
    shortcutText = "Ctrl+K",
    onTrigger
  } = {}) {
    super();

    /** @type {string} */
    this.placeholder = placeholder;

    /** @type {string} */
    this.shortcutText = shortcutText;

    /** @type {function(): void|undefined} */
    this.onTrigger = onTrigger;

    /**
     * Handles search pill activation click or keydown.
     * @returns {void}
     */
    const handleTrigger = () => {
      if (typeof this.onTrigger === "function") {
        this.onTrigger();
      } else {
        openSearchModal();
      }
    };

    /**
     * @param {KeyboardEvent} keyboardEvent
     * @returns {void}
     */
    const handleKeyDown = (keyboardEvent) => {
      if (keyboardEvent.key === "Enter" || keyboardEvent.key === " ") {
        keyboardEvent.preventDefault();
        handleTrigger();
      }
    };

    /** @type {string} */
    const ariaLabel = `Search documentation (${this.shortcutText})`;

    this.template = html`
      <div
        class="search-pill"
        role="button"
        tabindex="0"
        aria-label=${ariaLabel}
        onclick=${handleTrigger}
        onkeydown=${handleKeyDown}
      >
        <span class="google-symbols search-pill__icon" aria-hidden="true">search</span>
        <span class="search-pill__placeholder">${this.placeholder}</span>
        <span class="search-pill__shortcut">${this.shortcutText}</span>
      </div>
    `;
  }
}

