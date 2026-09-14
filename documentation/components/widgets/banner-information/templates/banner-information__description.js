import { Component, html, css } from "../../../../Component.js";

css(import.meta, ["../styles/banner-information__description.css"]);

/**
 * Old class reference: .primary-container .description / .split-asset .title .description
 * Represents the hero banner narrative description text.
 */
export class BannerInformationDescription extends Component {
  /**
   * @param {Object} configuration
   * @param {string} configuration.descriptionText - Narrative body content for the lead description.
   */
  constructor({ descriptionText }) {
    super();

    /** @type {string} */
    this.descriptionText = descriptionText;

    this.template = html`
      <p class="banner-information__description">
        ${this.descriptionText}
      </p>
    `;
  }
}
