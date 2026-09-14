import { Component, css, html } from "../../../../../Component.js";
import { Card } from "./card.js";
import { ImageScale } from "../scripts/image-scale.js";

css(import.meta, ["../styles/cards.css"]);

/**
 * Cards Section Component.
 * Renders a full section block containing a section header (title, description)
 * and an adaptive grid of Card components (three_cards, five_cards, two_cards).
 */
export class Cards extends Component {
  /**
   * @param {Object} configuration
   * @param {string} [configuration.headingTitle=""] - Section title text.
   * @param {number} [configuration.headingLevel=2] - Heading rank (2 or 3).
   * @param {string} [configuration.description=""] - Descriptive text below the title.
   * @param {string} [configuration.layoutType="three_cards"] - Grid layout preset.
   * @param {Array<Object>} [configuration.cards=[]] - Card specifications list.
   * @param {boolean} [configuration.forDashboard=false] - Whether to use landing page typography scale.
   * @param {function(string): void} [configuration.onNavigatePage] - Page navigation callback.
   */
  constructor({
    headingTitle = "",
    headingLevel = 2,
    description = "",
    layoutType = "three_cards",
    cards = [],
    forDashboard = false,
    onNavigatePage
  } = {}) {
    super();

    /** @type {string} */
    this.headingTitle = headingTitle;

    /** @type {number} */
    this.headingLevel = headingLevel;

    /** @type {string} */
    this.description = description;

    /** @type {string} */
    this.layoutType = layoutType;

    /** @type {Array<Object>} */
    this.cards = Array.isArray(cards) ? cards : [];

    /** @type {boolean} */
    this.forDashboard = Boolean(forDashboard);

    /** @type {function(string): void|undefined} */
    this.onNavigatePage = onNavigatePage;

    /** @type {string} */
    const headingModifierClass = this.headingLevel === 3
      ? "cards__heading--level-3"
      : "cards__heading--level-2";

    /** @type {string} */
    const dashboardHeadingModifier = this.forDashboard ? " cards__heading--for-dashboard" : "";

    /** @type {string} */
    const headingClassName = `cards__heading ${headingModifierClass}${dashboardHeadingModifier}`;

    /** @type {string} */
    const descriptionClassName = this.forDashboard
      ? "cards__description cards__description--for-dashboard"
      : "cards__description";

    /** @type {TemplateResult|string} */
    const headingTemplate = this.headingTitle
      ? this.headingLevel === 3
        ? html`<h3 class="${headingClassName}">${this.headingTitle}</h3>`
        : html`<h2 class="${headingClassName}">${this.headingTitle}</h2>`
      : "";

    /** @type {TemplateResult|string} */
    const descriptionTemplate = this.description
      ? html`<p class="${descriptionClassName}">${this.description}</p>`
      : "";

    /** @type {TemplateResult|string} */
    const headerTemplate = (headingTemplate || descriptionTemplate)
      ? html`
        <div class="cards__header">
          ${headingTemplate}
          ${descriptionTemplate}
        </div>
      `
      : "";

    /** @type {TemplateResult} */
    const gridContentTemplate = this.renderGridRows();

    this.template = html`
      <section class="cards" aria-label="${this.headingTitle || "Cards Section"}">
        ${headerTemplate}
        <div class="cards__grid">
          ${gridContentTemplate}
        </div>
      </section>
    `;
  }

  /**
   * Instantiates a Card component from specification data.
   * @param {Object} cardSpecification
   * @param {boolean} [isRow=false]
   * @returns {Card}
   */
  createCardComponent(cardSpecification, isRow = false) {
    /** @type {string} */
    const specImageScale = cardSpecification.image_scale || cardSpecification.imageScale || "";
    /** @type {string} */
    const resolvedImageScale = Object.values(ImageScale).includes(specImageScale)
      ? specImageScale
      : ImageScale.MEDIUM;

    return new Card({
      imageSource: cardSpecification.image_source || cardSpecification.imageSource || cardSpecification.image_path || cardSpecification.imagePath || "",
      shrink: cardSpecification.shrink !== undefined ? Boolean(cardSpecification.shrink) : false,
      label: cardSpecification.label || cardSpecification.category || cardSpecification.date || "",
      title: cardSpecification.title || "",
      description: cardSpecification.description || "",
      link: cardSpecification.link || "",
      isRow,
      imageScale: resolvedImageScale,
      onNavigate: this.onNavigatePage
    });
  }

  /**
   * Renders the appropriate row structure based on layoutType and card list.
   * @returns {TemplateResult}
   */
  renderGridRows() {
    if (this.layoutType === "three_cards" || (this.cards.length === 3 && this.layoutType !== "two_cards")) {
      /** @type {Card} */
      const featuredCard = this.createCardComponent(this.cards[0] || {}, true);
      /** @type {Card} */
      const secondaryCard1 = this.createCardComponent(this.cards[1] || {}, false);
      /** @type {Card} */
      const secondaryCard2 = this.createCardComponent(this.cards[2] || {}, false);

      return html`
        <div class="cards__row-single">
          ${featuredCard}
        </div>
        <div class="cards__row-duo">
          ${secondaryCard1}
          ${secondaryCard2}
        </div>
      `;
    }

    if (this.layoutType === "five_cards" || this.cards.length === 5) {
      /** @type {Card} */
      const topCard1 = this.createCardComponent(this.cards[0] || {}, false);
      /** @type {Card} */
      const topCard2 = this.createCardComponent(this.cards[1] || {}, false);
      /** @type {Card} */
      const bottomCard1 = this.createCardComponent(this.cards[2] || {}, false);
      /** @type {Card} */
      const bottomCard2 = this.createCardComponent(this.cards[3] || {}, false);
      /** @type {Card} */
      const bottomCard3 = this.createCardComponent(this.cards[4] || {}, false);

      return html`
        <div class="cards__row-duo">
          ${topCard1}
          ${topCard2}
        </div>
        <div class="cards__row-trio">
          ${bottomCard1}
          ${bottomCard2}
          ${bottomCard3}
        </div>
      `;
    }

    if (this.layoutType === "two_cards" || this.cards.length === 2) {
      /** @type {Card} */
      const card1 = this.createCardComponent(this.cards[0] || {}, false);
      /** @type {Card} */
      const card2 = this.createCardComponent(this.cards[1] || {}, false);

      return html`
        <div class="cards__row-duo">
          ${card1}
          ${card2}
        </div>
      `;
    }

    /** @type {Array<Card>} */
    const standardCards = this.cards.map(cardItem => this.createCardComponent(cardItem, false));
    return html`
      <div class="cards__row-duo">
        ${standardCards}
      </div>
    `;
  }
}

/** Alias export for backward compatibility. */
export { Cards as CardsContainerBlock };
