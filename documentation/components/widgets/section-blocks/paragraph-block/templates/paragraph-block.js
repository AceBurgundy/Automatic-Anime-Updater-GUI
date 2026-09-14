import { Component, css, html, raw } from "../../../../../Component.js";

css(import.meta, ["../styles/paragraph-block.css"]);

/**
 * Splits raw paragraph text into chunks containing at most a specified number of sentences.
 * @param {string} rawText - Raw paragraph text.
 * @param {number} [sentencesPerParagraph=2] - Number of sentences per chunk.
 * @returns {Array<string>} Array of chunked sentence strings.
 */
function splitParagraphIntoSentenceChunks(rawText, sentencesPerParagraph = 2) {
  if (!rawText || typeof rawText !== "string") {
    return [];
  }
  /** @type {string} */
  const trimmedText = rawText.trim();
  if (!trimmedText) {
    return [];
  }

  /** @type {RegExp} */
  const sentenceRegularExpression = /[^.!?]+(?:[.!?]+['")\]]?(?=\s+[A-Z0-9]|$)|$)/g;
  /** @type {Array<string>} */
  const matchedSentences = (trimmedText.match(sentenceRegularExpression) || [trimmedText])
    .map((sentence) => sentence.trim())
    .filter(Boolean);

  if (matchedSentences.length <= sentencesPerParagraph) {
    return [trimmedText];
  }

  /** @type {Array<string>} */
  const chunkedParagraphs = [];
  for (let index = 0; index < matchedSentences.length; index += sentencesPerParagraph) {
    /** @type {Array<string>} */
    const sentenceGroup = matchedSentences.slice(index, index + sentencesPerParagraph);
    chunkedParagraphs.push(sentenceGroup.join(" "));
  }
  return chunkedParagraphs;
}

/**
 * Paragraph Block Component.
 * Renders an optional H2/H3 section heading and responsive body text.
 * Legacy mapping: .section-block, .section-h2, .section-h3, .section-p, .desktop-only-p, .mobile-only-p-group.
 */
export class ParagraphBlock extends Component {
  /**
   * @param {Object} configuration
   * @param {string} [configuration.headingTitle=""] - Optional heading text.
   * @param {number} [configuration.headingLevel=2] - Heading level (2 for H2, 3 for H3).
   * @param {string} [configuration.paragraphText=""] - Body text for the paragraph.
   * @param {boolean} [configuration.forDashboard=false] - When true, heading uses large dashboard-scale typography.
   */
  constructor({
    headingTitle = "",
    headingLevel = 2,
    paragraphText = "",
    forDashboard = false
  } = {}) {
    super();

    /** @type {string} */
    this.headingTitle = headingTitle;

    /** @type {number} */
    this.headingLevel = headingLevel === 3 ? 3 : 2;

    /** @type {string} */
    this.paragraphText = paragraphText;

    /** @type {string} */
    const headingModifierClass = this.headingLevel === 3
      ? "paragraph-block__heading--level-3"
      : "paragraph-block__heading--level-2";

    /** @type {string} */
    const dashboardModifier = Boolean(forDashboard) ? " paragraph-block__heading--for-dashboard" : "";

    /** @type {string} */
    const headingClassName = `paragraph-block__heading ${headingModifierClass}${dashboardModifier}`;

    /** @type {Array<string>} */
    const sentenceChunks = splitParagraphIntoSentenceChunks(this.paragraphText, 2);

    /** @type {TemplateResult|string} */
    let headingTemplate = "";
    if (this.headingTitle) {
      headingTemplate = this.headingLevel === 3
        ? html`<h3 class="${headingClassName}">${this.headingTitle}</h3>`
        : html`<h2 class="${headingClassName}">${this.headingTitle}</h2>`;
    }

    /** @type {TemplateResult} */
    let bodyTemplate;
    if (sentenceChunks.length <= 1) {
      bodyTemplate = html`<p class="paragraph-block__text">${this.paragraphText}</p>`;
    } else {
      bodyTemplate = html`
        <p class="paragraph-block__text paragraph-block__text--desktop">${this.paragraphText}</p>
        <div class="paragraph-block__mobile-group">
          ${sentenceChunks.map((chunk) => html`<p class="paragraph-block__text">${chunk}</p>`)}
        </div>
      `;
    }

    this.template = html`
      <div class="paragraph-block">
        ${headingTemplate}
        ${bodyTemplate}
      </div>
    `;
  }
}

