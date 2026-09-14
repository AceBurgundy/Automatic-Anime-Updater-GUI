import { Component, css, html } from "../../../../Component.js";

css(import.meta, ["../styles/page-navigation__button.css"]);

/**
 * Legacy class reference: .bottom-page-nav-card
 * Represents a single directional page navigation card button (Previous or Next).
 */
export class PageNavigationButton extends Component {
  /**
   * @param {Object} configuration
   * @param {"previous"|"next"} configuration.direction - Direction of navigation.
   * @param {string} [configuration.subLabel] - Directional subtitle (e.g. "Previous" or "Up Next").
   * @param {string} configuration.pageTitle - Title of destination documentation page.
   * @param {string} [configuration.destinationPath=""] - Destination navigation identifier or route.
   * @param {function(): void} [configuration.onClick] - Click callback.
   * @param {function(string): void} [configuration.onNavigate] - Navigation callback.
   */
  constructor({ direction, subLabel, pageTitle, destinationPath = "", onClick, onNavigate }) {
    super();

    /** @type {"previous"|"next"} */
    this.direction = direction;

    /** @type {string} */
    this.subLabel = subLabel || (direction === "previous" ? "Previous" : "Up Next");

    /** @type {string} */
    this.pageTitle = pageTitle;

    /** @type {string} */
    this.destinationPath = destinationPath;

    /** @type {function(): void|undefined} */
    this.onClick = onClick;

    /** @type {function(string): void|undefined} */
    this.onNavigate = onNavigate;

    /**
     * @returns {void}
     */
    const handleClick = () => {
      if (typeof this.onClick === "function") {
        this.onClick();
      } else if (typeof this.onNavigate === "function") {
        this.onNavigate(this.destinationPath);
      }
    };

    /** @type {string} */
    const buttonClassName = `page-navigation__button page-navigation__button--${this.direction}`;

    /** @type {string} */
    const iconName = this.direction === "previous" ? "arrow_back" : "arrow_forward";

    /** @type {string} */
    const buttonAriaLabel = `${this.subLabel}: ${this.pageTitle}`;

    /** @type {TemplateResult} */
    const labelTemplate = this.direction === "previous"
      ? html`<span class="google-symbols page-navigation__icon">${iconName}</span><span>${this.subLabel}</span>`
      : html`<span>${this.subLabel}</span><span class="google-symbols page-navigation__icon">${iconName}</span>`;

    this.template = html`
      <button
        type="button"
        class="${buttonClassName}"
        aria-label="${buttonAriaLabel}"
        data-destination-path="${this.destinationPath}"
        onclick=${handleClick}
      >
        <div class="page-navigation__label">
          ${labelTemplate}
        </div>
        <div class="page-navigation__title">
          ${this.pageTitle}
        </div>
      </button>
    `;
  }
}
