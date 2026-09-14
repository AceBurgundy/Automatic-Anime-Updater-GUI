import { Component, css, html } from "../../../../../Component.js";

css(import.meta, ["../styles/diamond-list-block__item.css"]);

/**
 * Diamond List Block Item Component.
 * Legacy mapping: .diamond-item, .diamond-icon, .diamond-highlight.
 */
export class DiamondListBlockItem extends Component {
  /**
   * @param {Object} configuration
   * @param {string} [configuration.prefix=""] - Bold prefix headline text.
   * @param {string} [configuration.description=""] - Item descriptive body text.
   */
  constructor({ prefix = "", description = "" } = {}) {
    super();

    /** @type {string} */
    this.prefix = prefix;

    /** @type {string} */
    this.description = description;

    /** @type {TemplateResult|string} */
    const prefixTemplate = this.prefix
      ? html`<strong class="diamond-list-block__prefix">${this.prefix}</strong> `
      : "";

    this.template = html`
      <li class="diamond-list-block__item">
        <span class="diamond-list-block__icon" aria-hidden="true">✦</span>
        <span class="diamond-list-block__content">${prefixTemplate}${this.description}</span>
      </li>
    `;
  }
}

