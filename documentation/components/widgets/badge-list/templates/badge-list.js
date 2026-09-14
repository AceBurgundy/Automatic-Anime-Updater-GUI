import { Component, css, html } from "../../../../Component.js";
import { BadgeListItem } from "./badge-list__item.js";

css(import.meta, ["../styles/badge-list.css"]);

/**
 * @typedef {Object} BadgeDescriptor
 * @property {string} [badge_label] - Text label from specification.
 * @property {string} [badgeLabel] - Text label camelCase variant.
 * @property {string} [icon_name] - Material Symbol icon name from specification.
 * @property {string} [iconName] - Material Symbol icon name camelCase variant.
 */

/**
 * Legacy class reference: .resource-badges
 * Represents a container grouping multiple BadgeListItem components, accepting an Array or Map.
 */
export class BadgeList extends Component {
  /**
   * @param {Object} [configuration={}]
   * @param {Array<BadgeDescriptor>|Map<string, string>} [configuration.badges=[]] - Array or Map of badge definitions.
   */
  constructor({ badges = [] } = {}) {
    super();

    /** @type {Array<{ badgeLabel: string, iconName: string }>} */
    const normalizedBadgeList = [];

    // Always include the lead Resources badge pill matching old/index.html
    normalizedBadgeList.push({
      badgeLabel: "Resources",
      iconName: "apps"
    });

    if (badges instanceof Map) {
      badges.forEach((iconName, badgeLabel) => {
        normalizedBadgeList.push({ badgeLabel, iconName });
      });
    } else if (Array.isArray(badges)) {
      // Limit to 5 badges from the specification, matching old/index.html
      const limitedBadges = badges.slice(0, 5);
      limitedBadges.forEach((badge) => {
        /** @type {string} */
        const badgeLabel = badge.badge_label || badge.badgeLabel || "";
        /** @type {string} */
        const iconName = badge.icon_name || badge.iconName || "";
        if (badgeLabel || iconName) {
          normalizedBadgeList.push({ badgeLabel, iconName });
        }
      });
    }

    /** @type {Array<BadgeListItem>} */
    const badgeComponents = normalizedBadgeList.map((badgeDefinition) => {
      return new BadgeListItem({
        badgeLabel: badgeDefinition.badgeLabel,
        iconName: badgeDefinition.iconName
      });
    });

    this.template = html`
      <div class="badge-list" role="list" aria-label="Resource Badges">
        ${badgeComponents}
      </div>
    `;
  }
}
