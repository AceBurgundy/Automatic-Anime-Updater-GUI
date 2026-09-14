import { Component, css, html } from "../../../../Component.js";
import { NavigationCategoryHeader } from "./navigation-category__header.js";
import { NavigationCategoryItem } from "./navigation-category__item.js";

css(import.meta, ["../styles/navigation-category.css"]);

/**
 * @typedef {Object} NavigationItemDescriptor
 * @property {string} itemTitle - Label of navigation item.
 * @property {string} itemIdentifier - Path or identifier.
 */

/**
 * Legacy class reference: .nav-category
 * Represents a Navigation Category Group containing a category header and child navigation items.
 */
export class NavigationCategory extends Component {
  /**
   * @param {Object} configuration
   * @param {string} configuration.categoryTitle - Title of the category group.
   * @param {Array<NavigationItemDescriptor>} [configuration.items=[]] - List of navigation items under this category.
   * @param {import("../../../../Component.js").Signal<string>} [configuration.activeItemSignal] - Reactive signal tracking currently selected item.
   * @param {function(): void} [configuration.onHeaderClick] - Callback invoked when the category header is clicked.
   */
  constructor({ categoryTitle, items = [], activeItemSignal, onItemSelect, onHeaderClick } = {}) {
    super();

    /** @type {string} */
    this.categoryTitle = categoryTitle || "";

    /** @type {Array<NavigationItemDescriptor>} */
    this.items = items;

    /** @type {import("../../../../Component.js").Signal<string>|undefined} */
    this.activeItemSignal = activeItemSignal;

    /** @type {function(string): void|undefined} */
    this.onItemSelect = onItemSelect;

    /** @type {function(): void|undefined} */
    this.onHeaderClick = onHeaderClick;

    /** @type {NavigationCategoryHeader} */
    const categoryHeaderComponent = new NavigationCategoryHeader({
      categoryTitle: this.categoryTitle,
      onToggle: () => {
        if (typeof this.onHeaderClick === "function") {
          this.onHeaderClick();
        }
      }
    });

    /** @type {Array<NavigationCategoryItem>} */
    const itemComponents = this.items.map((itemDefinition) => {
      return new NavigationCategoryItem({
        itemTitle: itemDefinition.itemTitle,
        itemIdentifier: itemDefinition.itemIdentifier,
        activeItemSignal: this.activeItemSignal,
        onSelect: this.onItemSelect
      });
    });

    this.template = html`
      <div class="navigation-category" role="group" aria-label=${this.categoryTitle}>
        ${categoryHeaderComponent}
        <ul class="navigation-category__list" role="list">
          ${itemComponents}
        </ul>
      </div>
    `;
  }
}
