import { Component, html, signal, css } from "../../../../Component.js";
import { Tabs } from "../../../widgets/tabs/templates/tabs.js";
import { PageNavigation } from "../../../widgets/page-navigation/templates/page-navigation.js";
import { TableOfContents } from "../../../widgets/table-of-contents/templates/table-of-contents.js";
import { ParagraphBlock } from "../../../widgets/section-blocks/paragraph-block/templates/paragraph-block.js";
import { DiamondListBlock } from "../../../widgets/section-blocks/diamond-list-block/templates/diamond-list-block.js";
import { CodeBlock } from "../../../widgets/section-blocks/code-block/templates/code-block.js";
import { TableBlock } from "../../../widgets/section-blocks/table-block/templates/table-block.js";
import { ImageBlock } from "../../../widgets/section-blocks/image-block/templates/image-block.js";
import { Cards } from "../../../widgets/section-blocks/cards/templates/cards.js";

css(import.meta, ["../styles/documentation-content.css"]);

/**
 * Extracts Table of Contents item descriptors from a tab's section blocks.
 * @param {Array<Object>} [sectionBlocks=[]] - Array of section block specifications.
 * @returns {Array<import("../../widgets/table-of-contents/templates/table-of-contents.js").TableOfContentsItemDescriptor>} Extracted TOC items.
 */
function extractTableOfContentsItems(sectionBlocks = []) {
  if (!Array.isArray(sectionBlocks)) {
    return [];
  }

  /** @type {Array<import("../../widgets/table-of-contents/templates/table-of-contents.js").TableOfContentsItemDescriptor>} */
  const tableOfContentsItems = [];
  let headingIndex = 0;

  sectionBlocks.forEach((block) => {
    if (block.heading_title) {
      /** @type {string} */
      const headingIdentifier = `section-heading-${headingIndex}`;
      /** @type {string} */
      const fullText = block.heading_title.replace(/[✦•#]/g, " ").replace(/\s+/g, " ").trim();

      if (fullText) {
        tableOfContentsItems.push({
          displayLabel: fullText,
          targetIdentifier: headingIdentifier,
          fullTitle: fullText
        });
      }
      headingIndex++;
    }
  });

  return tableOfContentsItems;
}

/**
 * Factory creating an individual section block Component from data specification.
 * @param {Object} sectionBlock - Section block data object.
 * @param {number} blockIndex - Index of block within section.
 * @param {function(string): void} [onNavigatePage] - Page navigation callback for clickable blocks.
 * @returns {Component|null} Rendered section block Component.
 */
function renderSectionBlockComponent(sectionBlock, blockIndex, onNavigatePage) {
  if (!sectionBlock || !sectionBlock.block_type) {
    return null;
  }

  /** @type {string} */
  const headingTitle = sectionBlock.heading_title || "";
  /** @type {number} */
  const headingLevel = blockIndex === 0 ? 2 : 3;

  switch (sectionBlock.block_type) {
    case "paragraph":
      return new ParagraphBlock({
        headingTitle,
        headingLevel,
        paragraphText: sectionBlock.paragraph_text || ""
      });

    case "diamond_list":
      return new DiamondListBlock({
        headingTitle,
        headingLevel,
        diamondItems: sectionBlock.diamond_items || []
      });

    case "code_block":
      return new CodeBlock({
        headingTitle,
        headingLevel,
        headerLabel: sectionBlock.header_label,
        languageIdentifier: sectionBlock.language_identifier || "bash",
        codeContent: sectionBlock.code_content || ""
      });

    case "table":
      return new TableBlock({
        headingTitle,
        headingLevel,
        tableHeaders: sectionBlock.table_headers || [],
        tableRows: sectionBlock.table_rows || []
      });

    case "image":
      return new ImageBlock({
        headingTitle,
        headingLevel,
        imagePath: sectionBlock.image_path || "",
        altText: sectionBlock.alt_text || "Documentation figure",
        captionText: sectionBlock.caption_text || ""
      });

    case "cards_container":
      return new Cards({
        headingTitle,
        headingLevel,
        description: sectionBlock.description || "",
        layoutType: sectionBlock.layout_type || "three_cards",
        cards: sectionBlock.cards || [],
        onNavigatePage
      });

    default:
      console.warn(`Unrecognized section block type: ${sectionBlock.block_type}`);
      return null;
  }
}

/**
 * Represents a single tab content panel hosting section block components.
 */
class DocumentationTabPanel extends Component {
  /**
   * @param {Object} configuration
   * @param {number} configuration.tabIndex - Numerical tab index.
   * @param {boolean} configuration.isActive - Whether this panel is initially active.
   * @param {Array<Component>} configuration.blockComponents - Section block components to render.
   */
  constructor({ tabIndex, isActive, blockComponents }) {
    super();

    /** @type {number} */
    this.tabIndex = tabIndex;

    /** @type {boolean} */
    this.isActive = isActive;

    /** @type {Array<Component>} */
    this.blockComponents = blockComponents;

    /** @type {string} */
    const activeClass = this.isActive ? "documentation-content__panel--active" : "";
    /** @type {string} */
    const panelClassName = `documentation-content__panel ${activeClass}`.trim();
    /** @type {string} */
    const panelId = `tab-panel-${this.tabIndex}`;
    /** @type {string} */
    const tabPanelAttribute = String(this.tabIndex);

    this.template = html`
      <div
        class="${panelClassName}"
        id="${panelId}"
        data-tab-panel="${tabPanelAttribute}"
      >
        <div class="documentation-content__subsection">
          ${this.blockComponents}
        </div>
      </div>
    `;
  }
}

/**
 * Legacy class reference: .content-body-layout, .content-main-pane, .tab-content-panel, .article-tab-list
 * Represents the main documentation article content section hosting tabs, block panels, bottom navigation, and right-rail TOC.
 */
export class DocumentationContent extends Component {
  /**
   * @param {Object} configuration
   * @param {string} [configuration.itemTitle="Documentation"] - Active documentation page title.
   * @param {Array<Object>} [configuration.tabList=[]] - Tab list specification.
   * @param {import("../../widgets/page-navigation/templates/page-navigation.js").PageNavigationTarget|null} [configuration.previousPage=null] - Previous page.
   * @param {import("../../widgets/page-navigation/templates/page-navigation.js").PageNavigationTarget|null} [configuration.nextPage=null] - Next page.
   * @param {boolean} [configuration.hideTabs=false] - Whether to omit rendering tabs header.
   * @param {boolean} [configuration.hideTableOfContents=false] - Whether to omit rendering table of contents pane.
   * @param {function(string): void} [configuration.onNavigatePage] - Page navigation handler.
   */
  constructor({
    itemTitle = "Documentation",
    tabList = [],
    previousPage = null,
    nextPage = null,
    hideTabs = false,
    hideTableOfContents = false,
    onNavigatePage
  } = {}) {
    super();

    /** @type {string} */
    this.itemTitle = itemTitle;

    /** @type {Array<Object>} */
    this.tabList = tabList;

    /** @type {import("../../widgets/page-navigation/templates/page-navigation.js").PageNavigationTarget|null} */
    this.previousPage = previousPage;

    /** @type {import("../../widgets/page-navigation/templates/page-navigation.js").PageNavigationTarget|null} */
    this.nextPage = nextPage;

    /** @type {boolean} */
    this.hideTabs = Boolean(hideTabs);

    /** @type {boolean} */
    this.hideTableOfContents = Boolean(hideTableOfContents);

    /** @type {function(string): void|undefined} */
    this.onNavigatePage = onNavigatePage;

    /** @type {import("../../../../Component.js").Signal<number>} */
    this.activeTabIndexSignal = signal(0);

    /** @type {import("../../../../Component.js").Signal<string>} */
    this.activeHeadingSignal = signal("");

    /** @type {Array<import("../../widgets/tabs/templates/tabs.js").TabDescriptor>} */
    const tabDescriptors = this.tabList.map((tabItem) => ({
      tabTitle: tabItem.tab_title,
      iconName: tabItem.icon_name || "article"
    }));

    /** @type {Tabs} */
    this.tabsComponent = new Tabs({
      tabList: tabDescriptors,
      initialIndex: 0,
      onTabChange: (newIndex, direction) => {
        this.updateActivePanel(newIndex, direction, false);
      }
    });

    const initialTargets = this.computeNavigationTargets(0);

    /** @type {PageNavigation} */
    const pageNavigationComponent = new PageNavigation({
      previousTarget: initialTargets.previousTarget,
      nextTarget: initialTargets.nextTarget,
      onNavigateTarget: (target) => {
        this.handleNavigationTarget(target);
      }
    });

    /** @type {Array<TableOfContents>} */
    this.tableOfContentsComponentsByTab = this.tabList.map((tabItem) => {
      /** @type {Array<import("../../widgets/table-of-contents/templates/table-of-contents.js").TableOfContentsItemDescriptor>} */
      const tableOfContentsItems = extractTableOfContentsItems(tabItem.section_blocks);
      return new TableOfContents({
        pageTitle: this.itemTitle,
        items: tableOfContentsItems,
        activeHeadingSignal: this.activeHeadingSignal,
        onItemSelect: (headingId) => {
          /** @type {HTMLElement|null} */
          const targetHeading = document.getElementById(headingId);
          if (targetHeading) {
            targetHeading.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        }
      });
    });

    /** @type {Array<DocumentationTabPanel>} */
    const panelComponents = this.tabList.map((tabItem, tabIndex) => {
      /** @type {Array<Component>} */
      const blockComponents = (tabItem.section_blocks || [])
        .map((block, blockIndex) => renderSectionBlockComponent(block, blockIndex, this.onNavigatePage))
        .filter(Boolean);

      return new DocumentationTabPanel({
        tabIndex,
        isActive: tabIndex === 0,
        blockComponents
      });
    });

    const shouldHideTabsHeader = this.hideTabs || this.tabList.length <= 1;

    /** @type {TemplateResult|string} */
    const tabsHeaderTemplate = shouldHideTabsHeader
      ? ""
      : html`
        <div class="documentation-content__tabs-header" data-tabs-sticky-container>
          ${this.tabsComponent}
        </div>
      `;

    /** @type {TemplateResult|string} */
    const tableOfContentsPaneTemplate = this.hideTableOfContents
      ? ""
      : html`
        <aside class="documentation-content__table-of-contents-pane" data-table-of-contents-container>
          ${this.tableOfContentsComponentsByTab[0] || ""}
        </aside>
      `;

    const noTabsClass = shouldHideTabsHeader ? "documentation-content--no-tabs" : "";
    const noTocClass = this.hideTableOfContents ? "documentation-content--no-toc" : "";
    const rootClassName = `documentation-content ${noTabsClass} ${noTocClass}`.trim();

    this.template = html`
      <article class="${rootClassName}" aria-label="Documentation Body">
        ${tabsHeaderTemplate}

        <div class="documentation-content__body">
          <div class="documentation-content__main-pane">
            ${panelComponents}
            <div data-page-navigation-container>
              ${pageNavigationComponent}
            </div>
          </div>

          ${tableOfContentsPaneTemplate}
        </div>
      </article>
    `;

    this.mounted = () => {
      this.attachHeadingIdentifiers();
      this.setupStickyAndScrollSpy();
      if (typeof window !== "undefined" && window.Prism) {
        window.Prism.highlightAll();
      }
    };
  }

  /**
   * Computes previous and next navigation targets for a specific tab index.
   * @param {number} tabIndex - Active tab index.
   * @returns {{ previousTarget: import("../../widgets/page-navigation/templates/page-navigation.js").PageNavigationTarget|null, nextTarget: import("../../widgets/page-navigation/templates/page-navigation.js").PageNavigationTarget|null }}
   */
  computeNavigationTargets(tabIndex) {
    /** @type {import("../../widgets/page-navigation/templates/page-navigation.js").PageNavigationTarget|null} */
    let previousTarget = null;
    if (tabIndex > 0) {
      previousTarget = {
        type: "tab",
        tabIndex: tabIndex - 1,
        pageTitle: this.tabList[tabIndex - 1]?.tab_title || "Previous Tab",
        subLabel: "Previous"
      };
    } else if (this.previousPage) {
      previousTarget = {
        type: "page",
        destinationPath: this.previousPage.destinationPath,
        pageTitle: this.previousPage.pageTitle,
        subLabel: "Previous"
      };
    }

    /** @type {import("../../widgets/page-navigation/templates/page-navigation.js").PageNavigationTarget|null} */
    let nextTarget = null;
    if (tabIndex < this.tabList.length - 1) {
      nextTarget = {
        type: "tab",
        tabIndex: tabIndex + 1,
        pageTitle: this.tabList[tabIndex + 1]?.tab_title || "Next Tab",
        subLabel: "Up Next"
      };
    } else if (this.nextPage) {
      nextTarget = {
        type: "page",
        destinationPath: this.nextPage.destinationPath,
        pageTitle: this.nextPage.pageTitle,
        subLabel: "Up Next"
      };
    }

    return { previousTarget, nextTarget };
  }

  /**
   * Handles navigation action (switching tabs or navigating to a new page).
   * @param {import("../../widgets/page-navigation/templates/page-navigation.js").PageNavigationTarget} target - Target descriptor.
   * @returns {void}
   */
  handleNavigationTarget(target) {
    if (!target) return;
    if (target.type === "tab" && typeof target.tabIndex === "number") {
      /** @type {"previous"|"next"} */
      const direction = target.subLabel === "Previous" ? "previous" : "next";
      this.updateActivePanel(target.tabIndex, direction, true);
      /** @type {HTMLElement|null} */
      const scrollContainer = document.getElementById("mainViewport") || window;
      if (scrollContainer === window) {
        window.scrollTo({ top: 0, behavior: "smooth" });
      } else {
        scrollContainer.scrollTo({ top: 0, behavior: "smooth" });
      }
    } else if (target.type === "page" && target.destinationPath) {
      if (typeof this.onNavigatePage === "function") {
        this.onNavigatePage(target.destinationPath);
      }
    }
  }

  /**
   * Assigns sequential ID attributes to rendered headings for Table of Contents link navigation.
   * @returns {void}
   */
  attachHeadingIdentifiers() {
    /** @type {HTMLElement|null} */
    const rootElement = this.element || document.querySelector(".documentation-content");
    if (!rootElement) return;

    this.tabList.forEach((tabItem, tabIndex) => {
      /** @type {HTMLElement|null} */
      const panel = rootElement.querySelector(`[data-tab-panel="${tabIndex}"]`);
      if (!panel) return;

      /** @type {NodeListOf<HTMLElement>} */
      const headings = panel.querySelectorAll("h2, h3");
      headings.forEach((heading, headingIndex) => {
        heading.id = `section-heading-${headingIndex}`;
      });
    });
  }

  /**
   * Switches the active tab panel, swaps the active Table of Contents component, and updates bottom navigation.
   * @param {number} newIndex - Newly selected tab index.
   * @param {"previous"|"next"|"none"|null} [direction=null] - Direction of tab animation.
   * @param {boolean} [synchronizeTabs=true] - Whether to synchronize tabs animation.
   * @returns {void}
   */
  updateActivePanel(newIndex, direction = null, synchronizeTabs = true) {
    this.activeTabIndexSignal.value = newIndex;
    if (this.tabsComponent && this.tabsComponent.activeTabSignal) {
      this.tabsComponent.activeTabSignal.value = newIndex;
    }

    if (synchronizeTabs && this.tabsComponent && typeof this.tabsComponent.activateTabWithAnimation === "function") {
      this.tabsComponent.activateTabWithAnimation(newIndex, direction, false);
    } else {
      /** @type {HTMLElement|null} */
      const rootElement = this.element || document.querySelector(".documentation-content");
      if (rootElement) {
        rootElement.querySelectorAll(".tabs__item").forEach((tabButton, index) => {
          if (index === newIndex) {
            tabButton.classList.add("tabs__item--active");
            tabButton.setAttribute("aria-selected", "true");
          } else {
            tabButton.classList.remove("tabs__item--active");
            tabButton.setAttribute("aria-selected", "false");
          }
        });
      }
    }

    /** @type {HTMLElement|null} */
    const rootElement = this.element || document.querySelector(".documentation-content");
    if (!rootElement) return;

    // Update active content panels
    rootElement.querySelectorAll("[data-tab-panel]").forEach((panel, index) => {
      if (index === newIndex) {
        panel.classList.add("documentation-content__panel--active");
      } else {
        panel.classList.remove("documentation-content__panel--active");
      }
    });

    // Update Table of Contents
    /** @type {HTMLElement|null} */
    const tableOfContentsContainer = rootElement.querySelector("[data-table-of-contents-container]");
    if (tableOfContentsContainer && this.tableOfContentsComponentsByTab[newIndex]) {
      tableOfContentsContainer.innerHTML = this.tableOfContentsComponentsByTab[newIndex].toString();
      this.tableOfContentsComponentsByTab[newIndex].__mount?.();
    }

    // Update Bottom Page Navigation
    /** @type {HTMLElement|null} */
    const bottomNavContainer = rootElement.querySelector("[data-page-navigation-container]");
    if (bottomNavContainer) {
      const { previousTarget, nextTarget } = this.computeNavigationTargets(newIndex);
      const updatedPageNavigation = new PageNavigation({
        previousTarget,
        nextTarget,
        onNavigateTarget: (target) => {
          this.handleNavigationTarget(target);
        }
      });
      bottomNavContainer.innerHTML = updatedPageNavigation.toString();
      updatedPageNavigation.__mount?.();
    }

    // Re-sync table custom scrollbars on newly active panel
    requestAnimationFrame(() => {
      const activePanel = rootElement.querySelector(`[data-tab-panel="${newIndex}"]`);
      if (activePanel) {
        activePanel.querySelectorAll(".table-block__wrapper").forEach((wrapper) => {
          wrapper.dispatchEvent(new Event("scroll"));
        });
      }
    });
  }

  /**
   * Sets up scroll listeners for sticky header background padding and TOC scroll-spy.
   * @returns {void}
   */
  setupStickyAndScrollSpy() {
    /** @type {HTMLElement|null} */
    const scrollContainer = document.getElementById("mainViewport") || window;
    /** @type {HTMLElement|null} */
    const rootElement = this.element || document.querySelector(".documentation-content");
    /** @type {HTMLElement|null} */
    const tabsStickyHeader = rootElement?.querySelector("[data-tabs-sticky-container]");

    const handleScroll = () => {
      /** @type {number} */
      const scrollTop = scrollContainer === window
        ? window.scrollY
        : (scrollContainer).scrollTop;

      /** @type {HTMLElement|null} */
      const bannerElement = document.getElementById("banner");
      /** @type {number} */
      const bannerHeight = bannerElement ? bannerElement.offsetHeight : 380;
      /** @type {number} */
      const stickThreshold = Math.max(200, bannerHeight - 100);

      if (tabsStickyHeader) {
        if (scrollTop > stickThreshold) {
          tabsStickyHeader.classList.add("is-stuck");
        } else {
          tabsStickyHeader.classList.remove("is-stuck");
        }
      }

      /** @type {HTMLElement|null} */
      const currentRoot = this.element || document.querySelector(".documentation-content");
      /** @type {HTMLElement|null} */
      const activePanel = currentRoot?.querySelector(".documentation-content__panel--active");
      if (!activePanel) return;

      /** @type {Array<HTMLElement>} */
      const headings = Array.from(activePanel.querySelectorAll("h2, h3"));
      if (headings.length === 0) return;

      const viewportTop = scrollContainer === window ? 0 : (scrollContainer).getBoundingClientRect().top;
      const scrollThreshold = viewportTop + 160;

      let currentHeadingId = headings[0].getAttribute("id") || "";

      if (scrollContainer !== window && scrollContainer.scrollTop + scrollContainer.clientHeight >= scrollContainer.scrollHeight - 30) {
        currentHeadingId = headings[headings.length - 1].getAttribute("id") || "";
      } else {
        for (let i = 0; i < headings.length; i++) {
          const headingRect = headings[i].getBoundingClientRect();
          if (headingRect.top <= scrollThreshold) {
            currentHeadingId = headings[i].getAttribute("id") || "";
          } else {
            break;
          }
        }
      }

      this.activeHeadingSignal.value = currentHeadingId;

      // Ensure active class is synchronized directly in DOM
      if (currentRoot && currentHeadingId) {
        currentRoot.querySelectorAll(".table-of-contents__item-link").forEach((link) => {
          if (link.getAttribute("data-target-identifier") === currentHeadingId) {
            link.classList.add("table-of-contents__item-link--active");
          } else {
            link.classList.remove("table-of-contents__item-link--active");
          }
        });
      }
    };

    if (scrollContainer === window) {
      window.addEventListener("scroll", handleScroll, { passive: true });
    } else {
      scrollContainer.addEventListener("scroll", handleScroll, { passive: true });
    }
  }
}
