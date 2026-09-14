import { Component, css, html, signal } from "../../../../Component.js";
import { TableOfContentsItem } from "./table-of-contents__item.js";

css(import.meta, ["../styles/table-of-contents.css"]);

/**
 * @typedef {Object} TableOfContentsItemDescriptor
 * @property {string} displayLabel - Short heading label.
 * @property {string} targetIdentifier - Target heading element ID.
 * @property {string} [fullTitle] - Full heading title.
 */

/**
 * Legacy class reference: .content-toc-pane
 * Represents the sticky Table of Contents navigation rail with fixed "On this page" heading.
 */
export class TableOfContents extends Component {
  /**
   * @param {Object} configuration
   * @param {string} [configuration.pageTitle="Documentation"] - Active documentation page title.
   * @param {Array<TableOfContentsItemDescriptor>} [configuration.items=[]] - List of TOC heading targets.
   * @param {import("../../../../Component.js").Signal<string>} [configuration.activeHeadingSignal] - Reactive signal tracking active heading ID.
   * @param {function(string): void} [configuration.onItemSelect] - Selection callback.
   */
  constructor({
    pageTitle = "Documentation",
    items = [],
    activeHeadingSignal,
    onItemSelect
  } = {}) {
    super();

    /** @type {string} */
    this.pageTitle = pageTitle;

    /** @type {Array<TableOfContentsItemDescriptor>} */
    this.items = items;

    /** @type {import("../../../../Component.js").Signal<string>} */
    this.activeHeadingSignal = activeHeadingSignal || signal(this.items[0]?.targetIdentifier || "");

    /** @type {function(string): void|undefined} */
    this.onItemSelect = onItemSelect;

    /**
     * @param {string} targetIdentifier
     * @returns {void}
     */
    const handleItemSelect = (targetIdentifier) => {
      /** @type {HTMLElement|null} */
      const targetElement = document.getElementById(targetIdentifier);
      if (targetElement) {
        targetElement.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      if (typeof this.onItemSelect === "function") {
        this.onItemSelect(targetIdentifier);
      }
    };

    /** @type {Array<TableOfContentsItem>} */
    const itemComponents = this.items.map((itemDefinition) => {
      return new TableOfContentsItem({
        displayLabel: itemDefinition.displayLabel,
        targetIdentifier: itemDefinition.targetIdentifier,
        fullTitle: itemDefinition.fullTitle,
        activeHeadingSignal: this.activeHeadingSignal,
        onSelect: handleItemSelect
      });
    });

    this.template = html`
      <div class="table-of-contents" aria-label="Table of Contents">
        <div class="table-of-contents__heading">On this page</div>
        <div class="table-of-contents__page-title">${this.pageTitle}</div>
        <ul class="table-of-contents__list" role="list">
          ${itemComponents}
        </ul>
      </div>
    `;

    this.mounted = () => {
      /** @type {HTMLElement|null} */
      const containerElement = this.element || document.querySelector(".table-of-contents");
      if (!containerElement) return;

      containerElement.querySelectorAll(".table-of-contents__item-link").forEach((linkElement) => {
        linkElement.addEventListener("click", (clickEvent) => {
          clickEvent.preventDefault();
          const targetIdentifier = linkElement.getAttribute("data-target-identifier");
          if (targetIdentifier) {
            this.activeHeadingSignal.value = targetIdentifier;
            handleItemSelect(targetIdentifier);
          }
        });
      });
    };
  }
}

