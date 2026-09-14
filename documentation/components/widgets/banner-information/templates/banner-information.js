import { Component, html, css } from "../../../../Component.js";
import { BadgeList } from "../../badge-list/templates/badge-list.js";

css(import.meta, ["../styles/banner-information.css"]);

/**
 * Legacy class reference: .split-asset .primary-container
 * Represents the primary hero banner information container including title, description, and badges.
 */
export class BannerInformation extends Component {
  /**
   * @param {Object} configuration
   * @param {string} configuration.title - Main headline title text.
   * @param {string} configuration.description - Narrative description text.
   * @param {Array<Object>|Map<string, string>} [configuration.badges=[]] - List or Map of badge specifications.
   * @param {boolean} [configuration.isCompact=false] - Whether to render a compact title.
   */
  constructor({ title, description, badges = [], isCompact = false }) {
    super();

    /** @type {string} */
    this.title = title;

    /** @type {string} */
    this.description = description;

    /** @type {Array<Object>|Map<string, string>} */
    this.badges = badges;

    /** @type {boolean} */
    this.isCompact = isCompact;

    /** @type {BadgeList} */
    const badgeListComponent = new BadgeList({
      badges: this.badges
    });

    /** @type {string} */
    const titleClassName = this.isCompact
      ? "banner-information__title banner-information__title--compact"
      : "banner-information__title";

    this.template = html`
      <div class="banner-information" aria-label="Hero Overview">
        <div class="banner-information__wrapper">
          <div class="banner-information__title-group">
            <h1 tabindex="-1" class="${titleClassName}">
              ${this.title}
            </h1>
            <div class="banner-information__description">
              ${this.description}
            </div>
          </div>
          <div class="banner-information__badges-container">
            ${badgeListComponent}
          </div>
        </div>
      </div>
    `;
  }
}
