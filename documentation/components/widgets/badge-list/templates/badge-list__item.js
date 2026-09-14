import { Component, css, html } from "../../../../Component.js";

css(import.meta, ["../styles/badge-list__item.css"]);

/**
 * Legacy class reference: .badge-list__item
 * Represents an individual pill badge displaying an icon and label.
 */
export class BadgeListItem extends Component {
  /**
   * @param {Object} [configuration={}]
   * @param {string} [configuration.badgeLabel=""] - Text displayed on the badge.
   * @param {string} [configuration.iconName=""] - Material Symbol icon name.
   */
  constructor({ badgeLabel = "", iconName = "" } = {}) {
    super();

    /** @type {string} */
    this.badgeLabel = badgeLabel;

    /** @type {string} */
    this.iconName = iconName;

    this.template = html`
      <div class="badge-list__item" role="listitem">
        <span class="google-symbols notranslate badge-list__item-icon">${this.iconName}</span>
        <span class="badge-list__item-label">${this.badgeLabel}</span>
      </div>
    `;
  }
}
