import { Component, css, html } from "../../../../Component.js";

css(import.meta, ["../styles/tabs__item.css"]);

/**
 * Legacy class reference: .tab-btn / [role="tab"]
 * Represents a single selectable Tab Item widget.
 */
export class TabItem extends Component {
  /**
   * @param {Object} configuration
   * @param {string} configuration.tabTitle - Label displayed on the tab.
   * @param {string} configuration.iconName - Material Symbol icon name.
   * @param {number} configuration.tabIndex - Numerical index of this tab.
   * @param {import("../../../../../Component.js").Signal<number>} configuration.activeTabSignal - Reactive signal tracking active tab index.
   * @param {function(number): void} configuration.onSelect - Selection callback invoked with tabIndex.
   */
  constructor({ tabTitle, iconName, tabIndex, activeTabSignal, onSelect }) {
    super();

    /** @type {string} */
    this.tabTitle = tabTitle;

    /** @type {string} */
    this.iconName = iconName;

    /** @type {number} */
    this.tabIndex = tabIndex;

    /** @type {import("../../../../../Component.js").Signal<number>} */
    this.activeTabSignal = activeTabSignal;

    /** @type {function(number): void} */
    this.onSelect = onSelect;

    /**
     * @returns {void}
     */
    const handleTabClick = () => {
      if (typeof window !== "undefined" && window.__tabJustDragged) {
        return;
      }
      if (typeof this.onSelect === "function") {
        this.onSelect(this.tabIndex);
      }
    };

    /** @type {boolean} */
    const isSelected = this.activeTabSignal.value === this.tabIndex;

    /** @type {string} */
    const buttonClassName = isSelected
      ? "tabs__item tabs__item--active"
      : "tabs__item";

    this.template = html`
      <button
        type="button"
        role="tab"
        class="${buttonClassName}"
        aria-selected="${isSelected ? "true" : "false"}"
        data-tab-index="${String(this.tabIndex)}"
        onclick=${handleTabClick}
      >
        <span class="google-symbols notranslate tabs__item-icon">${this.iconName}</span>
        <span class="tabs__item-label">${this.tabTitle}</span>
      </button>
    `;
  }
}
