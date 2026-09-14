import { Component, css, html } from "../../../../Component.js";

css(import.meta, ["../styles/search-modal__item.css"]);

/**
 * Search Modal Result Item Component.
 * Legacy mapping: .search-result-item.
 */
export class SearchModalItem extends Component {
  /**
   * @param {Object} configuration
   * @param {string} [configuration.title=""] - Title headline of the documentation item.
   * @param {string} [configuration.description=""] - Description snippet of the item.
   * @param {string} [configuration.iconName="article"] - Google Symbol icon name.
   * @param {string} [configuration.path=""] - Target path to load.
   * @param {function(string): void} [configuration.onSelect] - Callback when item is clicked or selected.
   */
  constructor({
    title = "",
    description = "",
    iconName = "article",
    path = "",
    onSelect
  } = {}) {
    super();

    /** @type {string} */
    this.title = title;

    /** @type {string} */
    this.description = description;

    /** @type {string} */
    this.iconName = iconName;

    /** @type {string} */
    this.path = path;

    /** @type {function(string): void|undefined} */
    this.onSelect = onSelect;

    /**
     * @returns {void}
     */
    const handleClick = () => {
      if (typeof this.onSelect === "function") {
        this.onSelect(this.path);
      }
    };

    /**
     * @param {KeyboardEvent} keyboardEvent
     * @returns {void}
     */
    const handleKeyDown = (keyboardEvent) => {
      if (keyboardEvent.key === "Enter" || keyboardEvent.key === " ") {
        keyboardEvent.preventDefault();
        handleClick();
      }
    };

    this.template = html`
      <div
        class="search-modal-item"
        role="button"
        tabindex="0"
        onclick=${handleClick}
        onkeydown=${handleKeyDown}
      >
        <span class="google-symbols search-modal-item__icon" aria-hidden="true">${this.iconName}</span>
        <div class="search-modal-item__content">
          <div class="search-modal-item__title">${this.title}</div>
          <div class="search-modal-item__description">${this.description}</div>
        </div>
      </div>
    `;
  }
}

