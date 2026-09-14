import { Component, css, html } from "../../../../../Component.js";

css(import.meta, ["../styles/image-block.css"]);

/**
 * Image Block Component.
 * Renders an optional heading, a framed preview image container, and a caption.
 * Legacy mapping: .section-block, .doc-image-figure, .doc-image-container, .doc-image-element, .doc-image-caption-container, .doc-image-caption.
 */
export class ImageBlock extends Component {
  /**
   * @param {Object} configuration
   * @param {string} [configuration.headingTitle=""] - Optional heading text.
   * @param {number} [configuration.headingLevel=3] - Heading level (2 for H2, 3 for H3).
   * @param {string} [configuration.imagePath=""] - Path to the image asset.
   * @param {string} [configuration.altText="Documentation figure"] - Alternative text description for accessibility.
   * @param {string} [configuration.captionText=""] - Optional caption text displayed beneath the image.
   * @param {boolean} [configuration.forDashboard=false] - When true, heading uses large dashboard-scale typography.
   */
  constructor({
    headingTitle = "",
    headingLevel = 3,
    imagePath = "",
    altText = "Documentation figure",
    captionText = "",
    forDashboard = false
  } = {}) {
    super();

    /** @type {string} */
    this.headingTitle = headingTitle;

    /** @type {number} */
    this.headingLevel = headingLevel === 2 ? 2 : 3;

    /** @type {string} */
    this.imagePath = imagePath;

    /** @type {string} */
    this.altText = altText || "Documentation figure";

    /** @type {string} */
    this.captionText = captionText;

    /** @type {string} */
    const headingModifierClass = this.headingLevel === 2
      ? "image-block__heading--level-2"
      : "image-block__heading--level-3";

    /** @type {string} */
    const dashboardModifier = Boolean(forDashboard) ? " image-block__heading--for-dashboard" : "";

    /** @type {string} */
    const headingClassName = `image-block__heading ${headingModifierClass}${dashboardModifier}`;

    /** @type {TemplateResult|string} */
    let headingTemplate = "";
    if (this.headingTitle) {
      headingTemplate = this.headingLevel === 2
        ? html`<h2 class="${headingClassName}">${this.headingTitle}</h2>`
        : html`<h3 class="${headingClassName}">${this.headingTitle}</h3>`;
    }

    /** @type {TemplateResult|string} */
    const captionTemplate = this.captionText
      ? html`
        <div class="image-block__caption-container">
          <figcaption class="image-block__caption">${this.captionText}</figcaption>
        </div>
      `
      : "";

    this.template = html`
      <div class="image-block">
        ${headingTemplate}
        <figure class="image-block__figure">
          <div class="image-block__container">
            <img class="image-block__image" src="${this.imagePath}" alt="${this.altText}" loading="lazy" />
          </div>
          ${captionTemplate}
        </figure>
      </div>
    `;
  }
}

