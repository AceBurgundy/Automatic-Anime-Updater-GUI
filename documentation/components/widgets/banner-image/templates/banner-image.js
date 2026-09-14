import { Component, css, html, signal } from "../../../../Component.js";
import { BannerImageOption } from "./banner-image__option.js";

css(import.meta, ["../styles/banner-image.css"]);

/**
 * @typedef {Object} BannerImageSpecification
 * @property {string} [imagePath] - Image URL.
 * @property {string} [image_path] - Alias for imagePath.
 * @property {boolean} [shrink=false] - Whether to shrink image to 90% width with surrounding space.
 * @property {string} [mockupTitle="Overview"] - Legacy title for dialog card preview.
 * @property {Array<string>} [mockupOptions=[]] - Legacy selectable options.
 * @property {Array<string>} [mockupActionButtons=[]] - Legacy action buttons.
 */

/**
 * Legacy class reference: .split-asset-image, BannerMockup
 * Represents the hero banner graphic visual container hosting images (with shrink support) or interactive previews.
 */
export class BannerImage extends Component {
  /**
   * @param {Object} [configuration]
   * @param {string} [configuration.imagePath] - Direct image source path.
   * @param {boolean} [configuration.shrink=false] - Whether to restrict image to 90% width.
   * @param {BannerImageSpecification} [configuration.bannerImage] - Banner image specification object.
   * @param {BannerImageSpecification} [configuration.mockupCard] - Legacy fallback specification object.
   */
  constructor({
    imagePath,
    shrink = false,
    bannerImage = {},
    mockupCard = {}
  } = {}) {
    super();

    /** @type {string|undefined} */
    this.imagePath =
      imagePath ||
      bannerImage.image_path ||
      bannerImage.imagePath ||
      mockupCard.mockup_image_path ||
      mockupCard.imagePath;

    /** @type {boolean} */
    this.shrink =
      typeof shrink === "boolean"
        ? shrink
        : Boolean(bannerImage.shrink ?? mockupCard.shrink ?? false);

    /** @type {string} */
    this.mockupTitle =
      bannerImage.mockup_title ||
      bannerImage.mockupTitle ||
      mockupCard.mockup_title ||
      mockupCard.mockupTitle ||
      "Overview";

    /** @type {Array<string>} */
    this.mockupOptions =
      bannerImage.mockup_options ||
      bannerImage.mockupOptions ||
      mockupCard.mockup_options ||
      mockupCard.mockupOptions ||
      [];

    /** @type {Array<string>} */
    this.mockupActionButtons =
      bannerImage.mockup_action_buttons ||
      bannerImage.mockupActionButtons ||
      mockupCard.mockup_action_buttons ||
      mockupCard.mockupActionButtons ||
      [];

    /** @type {import("../../../../Component.js").Signal<number>} */
    this.selectedOptionSignal = signal(0);

    /** @type {TemplateResult|string} */
    let previewContentTemplate;

    if (this.imagePath) {
      /** @type {string} */
      const imageClassName = this.shrink
        ? "banner-image__image banner-image__image--shrink"
        : "banner-image__image";

      previewContentTemplate = html`
        <img class="${imageClassName}" src="${this.imagePath}" alt="Hero Banner Visual" />
      `;
    } else {
      /** @type {Array<BannerImageOption>} */
      const optionComponents = this.mockupOptions.map((optionString, index) => {
        return new BannerImageOption({
          optionLabel: optionString,
          optionIndex: index,
          selectedOptionSignal: this.selectedOptionSignal
        });
      });

      /** @type {Array<TemplateResult>} */
      const actionButtonTemplates = this.mockupActionButtons.map((buttonLabel) => {
        return html`<span class="banner-image__action-button">${buttonLabel}</span>`;
      });

      previewContentTemplate = html`
        <div class="banner-image__dialog-card" role="dialog" aria-modal="false">
          <div class="banner-image__title">${this.mockupTitle}</div>
          <div class="banner-image__options-list" role="radiogroup">
            ${optionComponents}
          </div>
          <div class="banner-image__footer-actions">
            ${actionButtonTemplates}
          </div>
        </div>
      `;
    }

    this.template = html`
      <div class="banner-image" aria-label="Visual Preview">
        ${previewContentTemplate}
      </div>
    `;
  }
}
