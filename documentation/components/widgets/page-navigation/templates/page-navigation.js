import { Component, css, html } from "../../../../Component.js";
import { PageNavigationButton } from "./page-navigation__button.js";

css(import.meta, ["../styles/page-navigation.css"]);

/**
 * @typedef {Object} PageNavigationTarget
 * @property {string} pageTitle - Title of target page or tab.
 * @property {string} [destinationPath] - Path or identifier for page navigation.
 * @property {number} [tabIndex] - Target tab index for internal tab navigation.
 * @property {"tab"|"page"} [type] - Target type.
 * @property {string} [subLabel] - Optional subtitle (e.g. "Previous", "Up Next").
 */

/**
 * Legacy class reference: .bottom-page-nav-container
 * Represents the bottom page navigation bar rendering Previous and Next navigation cards.
 */
export class PageNavigation extends Component {
  /**
   * @param {Object} configuration
   * @param {PageNavigationTarget|null} [configuration.previousTarget=null] - Previous target descriptor.
   * @param {PageNavigationTarget|null} [configuration.nextTarget=null] - Next target descriptor.
   * @param {PageNavigationTarget|null} [configuration.previousPage=null] - Legacy alias for previousTarget.
   * @param {PageNavigationTarget|null} [configuration.nextPage=null] - Legacy alias for nextTarget.
   * @param {function(PageNavigationTarget): void} [configuration.onNavigateTarget] - Callback when target is selected.
   * @param {function(string): void} [configuration.onNavigate] - Callback invoked with destinationPath.
   */
  constructor({
    previousTarget = null,
    nextTarget = null,
    previousPage = null,
    nextPage = null,
    onNavigateTarget,
    onNavigate
  } = {}) {
    super();

    /** @type {PageNavigationTarget|null} */
    this.previousTarget = previousTarget || previousPage;

    /** @type {PageNavigationTarget|null} */
    this.nextTarget = nextTarget || nextPage;

    /** @type {function(PageNavigationTarget): void|undefined} */
    this.onNavigateTarget = onNavigateTarget;

    /** @type {function(string): void|undefined} */
    this.onNavigate = onNavigate;

    /**
     * @param {PageNavigationTarget} target
     * @returns {void}
     */
    const handleTargetClick = (target) => {
      if (typeof this.onNavigateTarget === "function") {
        this.onNavigateTarget(target);
      } else if (typeof this.onNavigate === "function" && target.destinationPath) {
        this.onNavigate(target.destinationPath);
      }
    };

    /** @type {PageNavigationButton|string} */
    const previousButtonComponent = this.previousTarget
      ? new PageNavigationButton({
          direction: "previous",
          subLabel: this.previousTarget.subLabel,
          pageTitle: this.previousTarget.pageTitle,
          destinationPath: this.previousTarget.destinationPath || "",
          onClick: () => handleTargetClick(this.previousTarget)
        })
      : "";

    /** @type {PageNavigationButton|string} */
    const nextButtonComponent = this.nextTarget
      ? new PageNavigationButton({
          direction: "next",
          subLabel: this.nextTarget.subLabel,
          pageTitle: this.nextTarget.pageTitle,
          destinationPath: this.nextTarget.destinationPath || "",
          onClick: () => handleTargetClick(this.nextTarget)
        })
      : "";

    this.template = html`
      <nav class="page-navigation" aria-label="Page Navigation" data-page-navigation>
        <div class="page-navigation__container">
          ${previousButtonComponent}
          ${nextButtonComponent}
        </div>
      </nav>
    `;
  }
}

