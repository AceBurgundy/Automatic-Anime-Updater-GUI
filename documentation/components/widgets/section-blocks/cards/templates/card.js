import { Component, css, html } from "../../../../../Component.js";
import { ImageScale } from "../scripts/image-scale.js";
import { getCachedCardImageUrl } from "../scripts/abstract-image-service.js";

css(import.meta, ["../styles/card.css"]);

/**
 * Resolves any image source to a valid image URI.
 * - If given an inline SVG string (<svg... or <?xml...), encodes it as a data URI.
 * - If given a local file path, CDN URL, or data URI, returns it directly.
 * - If falsy, returns an empty string.
 *
 * @param {string} source - Raw image source (path, URL, data URI, or inline SVG string).
 * @returns {string} Fully resolved image URI.
 */
function resolveImageSourceUri(source) {
  if (!source || typeof source !== "string") {
    return "";
  }
  /** @type {string} */
  const trimmedSource = source.trimStart();
  if (trimmedSource.startsWith("<svg") || trimmedSource.startsWith("<?xml")) {
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(source)}`;
  }
  return source;
}

/**
 * Card Component.
 * Renders an M3-styled card featuring an art/image area, optional date badge,
 * headline title, and narrative description.
 *
 * Art / Image Source Agnostic:
 *   - Accepts local paths, CDN URLs, external SVGs, data URIs, or inline SVG strings.
 *   - When no image source is provided, automatically fetches a seeded abstract
 *     pattern image from the CDN.
 *
 * Loading Animation:
 *   - Displays an animated shimmer gradient skeleton while the image is loading.
 *   - Smoothly transitions from blurred to sharp upon image load completion.
 */
export class Card extends Component {
  /**
   * @param {Object} configuration
   * @param {string} [configuration.imageSource=""] - Image source (path, URL, data URI, or inline SVG).
   * @param {string} [configuration.imagePath=""] - Backward-compatible alias for imageSource.
   * @param {boolean} [configuration.shrink=false] - When true, shrinks image with object-fit contain.
   *   When false (default), image fills edge-to-edge with object-fit cover.
   * @param {string} [configuration.label=""] - Optional eyebrow badge or category label text.
   * @param {string} [configuration.date=""] - Backward-compatible alias for label.
   * @param {string} [configuration.title=""] - Headline title text.
   * @param {string} [configuration.description=""] - Narrative description text.
   * @param {string} [configuration.link=""] - Target documentation navigation path.
   * @param {boolean} [configuration.isRow=false] - Horizontal row orientation.
   * @param {import("../scripts/image-scale.js").ImageScale} [configuration.imageScale=ImageScale.MEDIUM]
   *   Image container height preset.
   * @param {function(string): void} [configuration.onNavigate] - Click navigation callback.
   */
  constructor({
    imageSource = "",
    imagePath = "",
    shrink = false,
    label = "",
    date = "",
    title = "",
    description = "",
    link = "",
    isRow = false,
    imageScale = ImageScale.MEDIUM,
    onNavigate
  } = {}) {
    super();

    /** @type {string} */
    this.imageSource = resolveImageSourceUri(imageSource || imagePath);

    /** @type {boolean} */
    this.shrink = Boolean(shrink);

    /** @type {string} */
    this.label = label || date;

    /** @type {string} */
    this.title = title;

    /** @type {string} */
    this.description = description;

    /** @type {string} */
    this.link = link;

    /** @type {boolean} */
    this.isRow = Boolean(isRow);

    /** @type {string} */
    this.imageScale = Object.values(ImageScale).includes(imageScale) ? imageScale : ImageScale.MEDIUM;

    /** @type {function(string): void|undefined} */
    this.onNavigate = onNavigate;

    /** @type {string} */
    const cardLookupKey = this.link || this.title || this.label || "default-card";

    /** @type {string} */
    const resolvedImagePath = getCachedCardImageUrl(cardLookupKey, this.imageSource);

    /** @type {string} */
    const cardElementId = `card-${Math.random().toString(36).slice(2, 9)}`;

    /** @type {string} */
    const rowModifierClass = this.isRow ? "card--row" : "";
    /** @type {string} */
    const rootClassName = `card ${rowModifierClass}`.trim();
    /** @type {string} */
    const hasLinkAttribute = this.link ? "true" : "false";

    /** @type {string} */
    const imageModifierClass = this.shrink ? "card__image--shrink" : "";
    /** @type {string} */
    const imageClassName = `card__image card__image--loading-state ${imageModifierClass}`.trim();

    /** @type {TemplateResult} */
    const imageTemplate = html`
      <div
        class="card__image-container"
        data-image-scale="${this.imageScale}"
        data-image-loading="true"
      >
        <img
          class="${imageClassName}"
          src="${resolvedImagePath}"
          alt="${this.title || "Card illustration"}"
          loading="lazy"
        />
      </div>
    `;

    /** @type {TemplateResult|string} */
    const labelTemplate = this.label
      ? html`<span class="card__label">${this.label}</span>`
      : "";

    /** @type {TemplateResult|string} */
    const titleTemplate = this.title
      ? html`<h3 class="card__title">${this.title}</h3>`
      : "";

    /** @type {TemplateResult|string} */
    const descriptionTemplate = this.description
      ? html`<p class="card__description">${this.description}</p>`
      : "";

    /**
     * Handles card click navigation.
     * @returns {void}
     */
    const handleClick = () => {
      if (this.link && typeof this.onNavigate === "function") {
        this.onNavigate(this.link);
      }
    };

    /**
     * Handles keyboard activation (Enter / Space) for accessibility.
     * @param {KeyboardEvent} keyboardEvent
     * @returns {void}
     */
    const handleKeyDown = (keyboardEvent) => {
      if (this.link && (keyboardEvent.key === "Enter" || keyboardEvent.key === " ")) {
        keyboardEvent.preventDefault();
        handleClick();
      }
    };

    this.template = html`
      <div
        id="${cardElementId}"
        class="${rootClassName}"
        data-has-link="${hasLinkAttribute}"
        role="${this.link ? "button" : "article"}"
        tabindex="${this.link ? "0" : "-1"}"
        aria-label="${this.title || "Documentation Card"}"
        onclick=${handleClick}
        onkeydown=${handleKeyDown}
      >
        ${imageTemplate}
        <div class="card__content">
          ${labelTemplate}
          ${titleTemplate}
          ${descriptionTemplate}
        </div>
      </div>
    `;

    this.mounted = () => {
      /** @type {HTMLElement|null} */
      const cardRoot = document.getElementById(cardElementId);
      if (!cardRoot) {
        return;
      }

      /** @type {HTMLElement|null} */
      const imageContainer = cardRoot.querySelector(".card__image-container");
      /** @type {HTMLImageElement|null} */
      const imageElement = imageContainer
        ? imageContainer.querySelector(".card__image--loading-state")
        : null;

      if (!imageContainer || !imageElement) {
        return;
      }

      /**
       * Called when the image finishes loading or encounters an error.
       * @returns {void}
       */
      const onImageSettled = () => {
        imageContainer.removeAttribute("data-image-loading");
        imageElement.classList.remove("card__image--loading-state");
        imageElement.classList.add("card__image--loaded");
      };

      if (imageElement.complete && imageElement.naturalWidth > 0) {
        onImageSettled();
      } else {
        imageElement.addEventListener("load", onImageSettled, { once: true });
        imageElement.addEventListener("error", onImageSettled, { once: true });
      }
    };
  }
}

/** Alias export for backward compatibility. */
export { Card as CardBlock };
