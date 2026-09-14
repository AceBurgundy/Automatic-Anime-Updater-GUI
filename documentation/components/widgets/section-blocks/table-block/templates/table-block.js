import { Component, css, html } from "../../../../../Component.js";
import { attachTableCustomScrollbar } from "../scripts/table-block__custom-scrollbar.js";

css(import.meta, ["../styles/table-block.css"]);

/**
 * Table Block Component.
 * Renders an optional heading and a scrollable Material Design 3 data table.
 * Legacy mapping: .section-block, .m3-table-outer, .m3-table-wrapper, .m3-table.
 */
export class TableBlock extends Component {
  /**
   * @param {Object} configuration
   * @param {string} [configuration.headingTitle=""] - Optional heading text.
   * @param {number} [configuration.headingLevel=3] - Heading level (2 for H2, 3 for H3).
   * @param {Array<string>} [configuration.tableHeaders=[]] - Array of header label strings.
   * @param {Array<Array<string>>} [configuration.tableRows=[]] - 2D Array of table row cell strings.
   * @param {boolean} [configuration.forDashboard=false] - When true, heading uses large dashboard-scale typography.
   */
  constructor({
    headingTitle = "",
    headingLevel = 3,
    tableHeaders = [],
    tableRows = [],
    forDashboard = false
  } = {}) {
    super();

    /** @type {string} */
    this.headingTitle = headingTitle;

    /** @type {number} */
    this.headingLevel = headingLevel === 2 ? 2 : 3;

    /** @type {Array<string>} */
    this.tableHeaders = Array.isArray(tableHeaders) ? tableHeaders : [];

    /** @type {Array<Array<string>>} */
    this.tableRows = Array.isArray(tableRows) ? tableRows : [];

    /** @type {string} */
    const headingModifierClass = this.headingLevel === 2
      ? "table-block__heading--level-2"
      : "table-block__heading--level-3";

    /** @type {string} */
    const dashboardModifier = Boolean(forDashboard) ? " table-block__heading--for-dashboard" : "";

    /** @type {string} */
    const headingClassName = `table-block__heading ${headingModifierClass}${dashboardModifier}`;

    /** @type {TemplateResult|string} */
    let headingTemplate = "";
    if (this.headingTitle) {
      headingTemplate = this.headingLevel === 2
        ? html`<h2 class="${headingClassName}">${this.headingTitle}</h2>`
        : html`<h3 class="${headingClassName}">${this.headingTitle}</h3>`;
    }

    /** @type {TemplateResult|string} */
    let headersTemplate = "";
    if (this.tableHeaders.length > 0) {
      headersTemplate = html`
        <thead class="table-block__header-group">
          <tr class="table-block__header-row">
            ${this.tableHeaders.map((header) => html`<th class="table-block__header-cell">${header}</th>`)}
          </tr>
        </thead>
      `;
    }

    /** @type {Array<TemplateResult>} */
    const rowsTemplates = this.tableRows.map((rowData, rowIndex) => {
      const rowIndexString = String(rowIndex + 1);
      return html`
        <tr class="table-block__row" data-row-index="${rowIndexString}">
          ${rowData.map((cellText, cellIndex) => {
            const dataLabel = this.tableHeaders[cellIndex] || "";
            return html`<td class="table-block__cell" data-label="${dataLabel}"><span class="table-block__cell-content">${cellText}</span></td>`;
          })}
        </tr>
      `;
    });

    /** @type {string} */
    const tableBlockIdentifier = `table-block-${Math.random().toString(36).substring(2, 10)}`;

    this.template = html`
      <div class="table-block" id="${tableBlockIdentifier}">
        ${headingTemplate}
        <div class="table-block__outer">
          <div class="table-block__wrapper">
            <table class="table-block__table">
              ${headersTemplate}
              <tbody class="table-block__body">
                ${rowsTemplates}
              </tbody>
            </table>
          </div>
          <div class="table-block__scrollbar-track">
            <div class="table-block__scrollbar-thumb" role="scrollbar" aria-orientation="vertical"></div>
          </div>
        </div>
      </div>
    `;

    this.mounted = () => {
      /** @type {HTMLElement|null} */
      const rootElement = document.getElementById(tableBlockIdentifier);
      if (!rootElement) return;

      /** @type {HTMLElement|null} */
      const tableWrapper = rootElement.querySelector(".table-block__wrapper");
      /** @type {HTMLElement|null} */
      const scrollbarTrack = rootElement.querySelector(".table-block__scrollbar-track");
      /** @type {HTMLElement|null} */
      const scrollbarThumb = rootElement.querySelector(".table-block__scrollbar-thumb");

      if (tableWrapper && scrollbarTrack && scrollbarThumb) {
        attachTableCustomScrollbar(tableWrapper, scrollbarTrack, scrollbarThumb);
      }
    };
  }
}

