import { Component, css, html } from "../../../../Component.js";

css(import.meta, ["../styles/navigation-category__header.css"]);

/** @type {Record<string, string>} */
const CATEGORY_ICONS = {
  "Get Started": "rocket_launch",
  "Application Views": "dashboard",
  "Scraping & Resilience": "security",
  "Architecture & Reference": "hub"
};

/**
 * Legacy class reference: .nav-category-header-btn
 * Represents the Header/Title element of a Navigation Category Group with category icon.
 */
export class NavigationCategoryHeader extends Component {
  /**
   * @param {Object} configuration
   * @param {string} configuration.categoryTitle - Title text of the category group.
   * @param {string} [configuration.categoryIcon] - Optional explicit icon name.
   * @param {function(): void} [configuration.onToggle] - Toggle handler for mobile accordion.
   */
  constructor({ categoryTitle, categoryIcon, onToggle } = {}) {
    super();

    /** @type {string} */
    this.categoryTitle = categoryTitle || "";

    /** @type {string} */
    this.categoryIcon = categoryIcon || CATEGORY_ICONS[this.categoryTitle] || "category";

    /** @type {function(): void|undefined} */
    this.onToggle = onToggle;

    /**
     * @param {MouseEvent} clickEvent
     * @returns {void}
     */
    const handleClick = (clickEvent) => {
      if (typeof this.onToggle === "function") {
        this.onToggle();
      }
    };

    this.template = html`
      <button
        type="button"
        class="navigation-category__header-button"
        aria-label=${`Open ${this.categoryTitle} category`}
        onclick=${handleClick}
      >
        <div class="navigation-category__header-title-wrap">
          <span class="google-symbols navigation-category__header-icon">${this.categoryIcon}</span>
          <span class="navigation-category__header-title">${this.categoryTitle}</span>
        </div>
        <span class="google-symbols navigation-category__header-arrow">chevron_right</span>
      </button>
    `;
  }
}
