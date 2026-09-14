import { Component, css, html } from "../../../../../Component.js";
import { DiamondListBlockItem } from "./diamond-list-block__item.js";

css(import.meta, ["../styles/diamond-list-block.css"]);

/**
  * Diamond List Block Component.
  * Renders an optional heading and a bulleted list with diamond markers.
  * Legacy mapping: .section-block, .diamond-list.
  */
export class DiamondListBlock extends Component {
  /**
   * @param {Object} configuration
   * @param {string} [configuration.headingTitle=""] - Optional heading text.
   * @param {number} [configuration.headingLevel=3] - Heading level (2 for H2, 3 for H3).
   * @param {Array<Object>} [configuration.diamondItems=[]] - Array of diamond list items.
   * @param {boolean} [configuration.forDashboard=false] - When true, heading uses large dashboard-scale typography.
   */
  constructor({
    headingTitle = "",
    headingLevel = 3,
    diamondItems = [],
    forDashboard = false
  } = {}) {
    super();

    /** @type {string} */
    this.headingTitle = headingTitle;

    /** @type {number} */
    this.headingLevel = headingLevel === 2 ? 2 : 3;

    /** @type {Array<Object>} */
    this.diamondItems = Array.isArray(diamondItems) ? diamondItems : [];

    /** @type {string} */
    const headingModifierClass = this.headingLevel === 2
      ? "diamond-list-block__heading--level-2"
      : "diamond-list-block__heading--level-3";

    /** @type {string} */
    const dashboardModifier = Boolean(forDashboard) ? " diamond-list-block__heading--for-dashboard" : "";

    /** @type {string} */
    const headingClassName = `diamond-list-block__heading ${headingModifierClass}${dashboardModifier}`;

    /** @type {TemplateResult|string} */
    let headingTemplate = "";
    if (this.headingTitle) {
      headingTemplate = this.headingLevel === 2
        ? html`<h2 class="${headingClassName}">${this.headingTitle}</h2>`
        : html`<h3 class="${headingClassName}">${this.headingTitle}</h3>`;
    }

    /** @type {Array<DiamondListBlockItem>} */
    const itemComponents = this.diamondItems.map((item) => {
      return new DiamondListBlockItem({
        prefix: item.highlighted_prefix,
        description: item.item_description
      });
    });

    this.template = html`
      <div class="diamond-list-block">
        ${headingTemplate}
        <ul class="diamond-list-block__list">
          ${itemComponents}
        </ul>
      </div>
    `;
  }
}

