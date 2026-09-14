import { Component, css, html, signal } from "../../../../Component.js";
import { fetchNavigationItemData } from "../../../../common/scripts/data-loader.js";

css(import.meta, ["../styles/navigation-category__item.css"]);

/**
 * Legacy class reference: .nav-item-btn
 * Represents a single Navigation Item button inside a Category Group without item icon.
 */
export class NavigationCategoryItem extends Component {
  /**
   * @param {Object} configuration
   * @param {string} [configuration.itemTitle=""] - Initial title label of the navigation item.
   * @param {string} configuration.itemIdentifier - Unique identifier or route path for the item.
   * @param {import("../../../../../Component.js").Signal<string>} configuration.activeItemSignal - Reactive signal storing the currently active item identifier.
   * @param {function(string): void} [configuration.onSelect] - Callback invoked when this item is clicked.
   */
  constructor({ itemTitle = "", itemIdentifier = "", activeItemSignal, onSelect } = {}) {
    super();

    /** @type {string} */
    this.itemIdentifier = itemIdentifier || "";

    /** @type {import("../../../../../Component.js").Signal<string>} */
    this.itemTitleSignal = signal(itemTitle || "");

    /** @type {import("../../../../../Component.js").Signal<string>} */
    this.activeItemSignal = activeItemSignal;

    /** @type {function(string): void|undefined} */
    this.onSelect = onSelect;

    /**
     * @returns {void}
     */
    const handleClick = () => {
      if (this.activeItemSignal) {
        this.activeItemSignal.value = this.itemIdentifier;
      }
      if (typeof this.onSelect === "function") {
        this.onSelect(this.itemIdentifier);
      }
    };

    /** @type {boolean} */
    const isActive = this.activeItemSignal ? this.activeItemSignal.value === this.itemIdentifier : false;

    /** @type {string} */
    const buttonClassName = isActive
      ? "navigation-category__item-button navigation-category__item-button--active"
      : "navigation-category__item-button";

    this.template = html`
      <li class="navigation-category__item">
        <button
          type="button"
          class=${buttonClassName}
          data-navigation-path=${this.itemIdentifier}
          onclick=${handleClick}
        >
          <span class="navigation-category__item-label">${this.itemTitleSignal}</span>
        </button>
      </li>
    `;

    this.mounted = () => {
      if (this.itemIdentifier) {
        fetchNavigationItemData(this.itemIdentifier)
          .then((itemSpecification) => {
            if (itemSpecification && itemSpecification.item_title) {
              this.itemTitleSignal.value = itemSpecification.item_title;
            }
          })
          .catch((fetchError) => {
            console.warn(
              `Could not preload title for ${this.itemIdentifier}:`,
              fetchError
            );
          });
      }
    };
  }
}
