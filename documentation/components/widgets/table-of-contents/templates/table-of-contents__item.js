import { Component, css, html } from "../../../../Component.js";

css(import.meta, ["../styles/table-of-contents__item.css"]);

/**
 * Legacy class reference: .toc-item-link
 * Represents a single link item within the Table of Contents rail.
 */
export class TableOfContentsItem extends Component {
  /**
   * @param {Object} configuration
   * @param {string} configuration.displayLabel - Short label for the heading.
   * @param {string} configuration.targetIdentifier - Heading element ID target.
   * @param {string} [configuration.fullTitle] - Full heading text for title tooltip.
   * @param {import("../../../../../Component.js").Signal<string>} configuration.activeHeadingSignal - Reactive signal tracking active heading ID.
   * @param {function(string): void} [configuration.onSelect] - Selection callback.
   */
  constructor({ displayLabel, targetIdentifier, fullTitle, activeHeadingSignal, onSelect }) {
    super();

    /** @type {string} */
    this.displayLabel = displayLabel;

    /** @type {string} */
    this.targetIdentifier = targetIdentifier;

    /** @type {string} */
    this.fullTitle = fullTitle || displayLabel;

    /** @type {import("../../../../../Component.js").Signal<string>} */
    this.activeHeadingSignal = activeHeadingSignal;

    /** @type {function(string): void|undefined} */
    this.onSelect = onSelect;

    /**
     * @param {MouseEvent} clickEvent
     * @returns {void}
     */
    const handleClick = (clickEvent) => {
      clickEvent.preventDefault();
      this.activeHeadingSignal.value = this.targetIdentifier;
      if (typeof this.onSelect === "function") {
        this.onSelect(this.targetIdentifier);
      }
    };

    /** @type {boolean} */
    const isActive = this.activeHeadingSignal.value === this.targetIdentifier;

    /** @type {string} */
    const linkClassName = isActive
      ? "table-of-contents__item-link table-of-contents__item-link--active"
      : "table-of-contents__item-link";

    /** @type {string} */
    const hrefValue = `#${this.targetIdentifier}`;

    this.template = html`
      <li class="table-of-contents__item">
        <a
          href="${hrefValue}"
          class="${linkClassName}"
          data-target-identifier="${this.targetIdentifier}"
          title="${this.fullTitle}"
          onclick=${handleClick}
        >
          ${this.displayLabel}
        </a>
      </li>
    `;
  }
}
