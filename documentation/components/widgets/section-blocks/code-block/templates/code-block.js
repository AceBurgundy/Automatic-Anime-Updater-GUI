import { Component, css, html } from "../../../../../Component.js";
import { copyCodeToClipboard } from "../scripts/code-block__clipboard.js";

css(import.meta, ["../styles/code-block.css"]);

/**
 * Escapes HTML entities to ensure safe rendering inside <code> blocks.
 * @param {string} sourceText - Raw text to escape.
 * @returns {string} Escaped HTML string.
 */
function escapeHtml(sourceText) {
  if (!sourceText) {
    return "";
  }
  return sourceText
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Code Block Component.
 * Renders an optional heading, a header bar with language label and copy button, and a preformatted code container.
 * Legacy mapping: .section-block, .code-container, .code-header, .copy-btn, .code-content.
 */
export class CodeBlock extends Component {
  /**
   * @param {Object} configuration
   * @param {string} [configuration.headingTitle=""] - Optional heading text.
   * @param {number} [configuration.headingLevel=3] - Heading level (2 for H2, 3 for H3).
   * @param {string} [configuration.headerLabel=""] - Display label in the code header bar.
   * @param {string} [configuration.languageIdentifier="bash"] - Language identifier for syntax highlighting.
   * @param {string} [configuration.codeContent=""] - Code text content.
   * @param {boolean} [configuration.forDashboard=false] - When true, heading uses large dashboard-scale typography.
   */
  constructor({
    headingTitle = "",
    headingLevel = 3,
    headerLabel = "",
    languageIdentifier = "bash",
    codeContent = "",
    forDashboard = false
  } = {}) {
    super();

    /** @type {string} */
    this.headingTitle = headingTitle;

    /** @type {number} */
    this.headingLevel = headingLevel === 2 ? 2 : 3;

    /** @type {string} */
    this.languageIdentifier = languageIdentifier || "bash";

    /** @type {string} */
    this.headerLabel = headerLabel || this.languageIdentifier || "Code";

    /** @type {string} */
    this.codeContent = codeContent;

    /** @type {string} */
    const headingModifierClass = this.headingLevel === 2
      ? "code-block__heading--level-2"
      : "code-block__heading--level-3";

    /** @type {string} */
    const dashboardModifier = Boolean(forDashboard) ? " code-block__heading--for-dashboard" : "";

    /** @type {string} */
    const headingClassName = `code-block__heading ${headingModifierClass}${dashboardModifier}`;

    /** @type {TemplateResult|string} */
    let headingTemplate = "";
    if (this.headingTitle) {
      headingTemplate = this.headingLevel === 2
        ? html`<h2 class="${headingClassName}">${this.headingTitle}</h2>`
        : html`<h3 class="${headingClassName}">${this.headingTitle}</h3>`;
    }

    /**
     * Handles copying code snippet to clipboard.
     * @returns {void}
     */
    const handleCopy = () => {
      copyCodeToClipboard(this.codeContent);
    };

    /** @type {string} */
    const codeClassName = `code-block__code language-${this.languageIdentifier}`;

    this.template = html`
      <div class="code-block">
        ${headingTemplate}
        <div class="code-block__container">
          <div class="code-block__header">
            <span class="code-block__label">${this.headerLabel}</span>
            <button
              type="button"
              class="code-block__copy-button"
              aria-label="Copy code to clipboard"
              onclick=${handleCopy}
            >
              <span class="google-symbols notranslate code-block__copy-icon" aria-hidden="true">content_copy</span>
              <span>Copy</span>
            </button>
          </div>
          <pre class="code-block__pre"><code class="${codeClassName}">${this.codeContent}</code></pre>
        </div>
      </div>
    `;

    this.mounted = () => {
      if (typeof window !== "undefined" && window.Prism) {
        window.Prism.highlightAll();
      }
    };
  }
}

