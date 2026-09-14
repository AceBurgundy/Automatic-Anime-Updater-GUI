import { Component, html, css } from "../../../../Component.js";
import { Cards } from "../../../widgets/section-blocks/cards/templates/cards.js";
import { ParagraphBlock } from "../../../widgets/section-blocks/paragraph-block/templates/paragraph-block.js";
import { DiamondListBlock } from "../../../widgets/section-blocks/diamond-list-block/templates/diamond-list-block.js";
import { CodeBlock } from "../../../widgets/section-blocks/code-block/templates/code-block.js";
import { TableBlock } from "../../../widgets/section-blocks/table-block/templates/table-block.js";
import { ImageBlock } from "../../../widgets/section-blocks/image-block/templates/image-block.js";
import { PageNavigation } from "../../../widgets/page-navigation/templates/page-navigation.js";

css(import.meta, ["../styles/dashboard.css"]);

/**
 * Renders an individual section block component for the dashboard context.
 * Always passes forDashboard=true so section block headings and descriptions
 * use the large dashboard typescale.
 * @param {Object} sectionBlock - Section block data object.
 * @param {number} blockIndex - Block index within panel.
 * @param {function(string): void} [onNavigatePage] - Navigation callback.
 * @returns {Component|null}
 */
function renderDashboardSectionBlock(sectionBlock, blockIndex, onNavigatePage) {
  if (!sectionBlock || !sectionBlock.block_type) {
    return null;
  }

  /** @type {string} */
  const headingTitle = sectionBlock.heading_title || "";
  /** @type {number} */
  const headingLevel = 2;

  switch (sectionBlock.block_type) {
    case "paragraph":
      return new ParagraphBlock({
        headingTitle,
        headingLevel,
        paragraphText: sectionBlock.paragraph_text || "",
        forDashboard: true
      });

    case "diamond_list":
      return new DiamondListBlock({
        headingTitle,
        headingLevel,
        diamondItems: sectionBlock.diamond_items || [],
        forDashboard: true
      });

    case "code_block":
      return new CodeBlock({
        headingTitle,
        headingLevel,
        headerLabel: sectionBlock.header_label,
        languageIdentifier: sectionBlock.language_identifier || "bash",
        codeContent: sectionBlock.code_content || "",
        forDashboard: true
      });

    case "table":
      return new TableBlock({
        headingTitle,
        headingLevel,
        tableHeaders: sectionBlock.table_headers || [],
        tableRows: sectionBlock.table_rows || [],
        forDashboard: true
      });

    case "image":
      return new ImageBlock({
        headingTitle,
        headingLevel,
        imagePath: sectionBlock.image_path || "",
        altText: sectionBlock.alt_text || "Documentation figure",
        captionText: sectionBlock.caption_text || "",
        forDashboard: true
      });

    case "cards_container":
      return new Cards({
        headingTitle,
        headingLevel,
        description: sectionBlock.description || "",
        layoutType: sectionBlock.layout_type || "three_cards",
        cards: sectionBlock.cards || [],
        forDashboard: true,
        onNavigatePage
      });

    default:
      console.warn(`Unrecognized dashboard section block type: ${sectionBlock.block_type}`);
      return null;
  }
}

/**
 * Dashboard Page Component.
 * A self-contained landing page with its own isolated CSS class names (.dashboard__*)
 * that does not rely on or share styles with DocumentationContent.
 * Renders the first tab's section blocks with forDashboard=true on all blocks
 * so every heading and description uses the large dashboard typescale.
 */
export class Dashboard extends Component {
  /**
   * @param {Object} configuration
   * @param {Array<Object>} [configuration.tabList=[]] - Tab list specification (only the first tab is rendered).
   * @param {import("../../../widgets/page-navigation/templates/page-navigation.js").PageNavigationTarget|null} [configuration.previousPage=null] - Previous page navigation target.
   * @param {import("../../../widgets/page-navigation/templates/page-navigation.js").PageNavigationTarget|null} [configuration.nextPage=null] - Next page navigation target.
   * @param {function(string): void} [configuration.onNavigatePage] - Page navigation handler.
   */
  constructor({
    tabList = [],
    previousPage = null,
    nextPage = null,
    onNavigatePage
  } = {}) {
    super();

    /** @type {Array<Object>} */
    this.tabList = tabList;

    /** @type {function(string): void|undefined} */
    this.onNavigatePage = onNavigatePage;

    /** @type {Object|null} */
    const firstTab = this.tabList[0] || null;

    /** @type {Array<Component>} */
    const blockComponents = firstTab
      ? (firstTab.section_blocks || [])
          .map((block, blockIndex) => renderDashboardSectionBlock(block, blockIndex, this.onNavigatePage))
          .filter(Boolean)
      : [];

    /** @type {PageNavigation} */
    const pageNavigationComponent = new PageNavigation({
      previousTarget: previousPage
        ? {
            type: "page",
            destinationPath: previousPage.destinationPath,
            pageTitle: previousPage.pageTitle,
            subLabel: previousPage.subLabel
          }
        : null,
      nextTarget: nextPage
        ? {
            type: "page",
            destinationPath: nextPage.destinationPath,
            pageTitle: nextPage.pageTitle,
            subLabel: nextPage.subLabel
          }
        : null,
      onNavigateTarget: (target) => {
        if (target && target.type === "page" && target.destinationPath && typeof this.onNavigatePage === "function") {
          this.onNavigatePage(target.destinationPath);
        }
      }
    });

    this.template = html`
      <section class="dashboard" aria-label="Dashboard">
        <div class="dashboard__body">
          <div class="dashboard__content-pane">
            <div class="dashboard__panel">
              <div class="dashboard__section-blocks">
                ${blockComponents}
              </div>
              ${pageNavigationComponent}
            </div>
          </div>
        </div>
      </section>
    `;

    this.mounted = () => {
      if (typeof window !== "undefined" && window.Prism) {
        window.Prism.highlightAll();
      }
    };
  }
}
