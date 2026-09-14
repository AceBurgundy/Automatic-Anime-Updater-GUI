import { Component, html, css } from "../../../../Component.js";
import { BannerInformation } from "../../../widgets/banner-information/templates/banner-information.js";
import { BannerImage } from "../../../widgets/banner-image/templates/banner-image.js";

css(import.meta, ["../styles/banner.css"]);

/**
 * Legacy class reference: .split-asset
 * Represents the composite hero banner combining information text/badges and the visual banner image.
 */
export class Banner extends Component {
  /**
   * @param {Object} configuration
   * @param {string} configuration.title - Main headline title text.
   * @param {string} configuration.description - Narrative description text.
   * @param {Array<Object>|Map<string, string>} [configuration.badges=[]] - List or Map of badge specifications.
   * @param {boolean} [configuration.isCompact=false] - Whether to render a compact title.
   * @param {import("../../widgets/banner-image/templates/banner-image.js").BannerImageSpecification} [configuration.bannerImage={}] - Banner image specification.
   * @param {import("../../widgets/banner-image/templates/banner-image.js").BannerImageSpecification} [configuration.mockupCard={}] - Legacy alias for bannerImage.
   */
  constructor({
    title,
    description,
    badges = [],
    isCompact = false,
    bannerImage = {},
    mockupCard = {}
  }) {
    super();

    /** @type {BannerInformation} */
    const bannerInformationComponent = new BannerInformation({
      title,
      description,
      badges,
      isCompact
    });

    /** @type {BannerImage} */
    const bannerImageComponent = new BannerImage({
      bannerImage: Object.keys(bannerImage).length > 0 ? bannerImage : mockupCard
    });

    this.template = html`
      <header id="banner" class="banner" aria-label="Hero Banner">
        ${bannerInformationComponent}
        ${bannerImageComponent}
      </header>
    `;
  }
}
