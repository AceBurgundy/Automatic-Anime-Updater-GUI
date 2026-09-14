import { Component, html, css } from "../../../../Component.js";
import { SearchPill } from "../../../widgets/search-pill/templates/search-pill.js";
import { ThemeToggle } from "../../../widgets/theme-toggle/templates/theme-toggle.js";
import { NavigationCategory } from "../../../widgets/navigation-category/templates/navigation-category.js";
import { attachSmoothScroll } from "../scripts/sidebar__smooth-scroll.js";

css(import.meta, ["../styles/sidebar.css"]);

/**
 * Legacy class reference: .main-sidebar, .sidebar-content-viewport, .sidebar-main-view, .sidebar-sub-view, .nav-sub-back-btn, .nav-sub-items-container
 * Represents the primary navigation drawer containing the brand search bar, theme toggle, and category tree with mobile drill-down subviews.
 */
export class Sidebar extends Component {
  /**
   * @param {Object} configuration
   * @param {Array<Object>} [configuration.categoryGroups=[]] - Category groups array from DOCUMENTATION_DATA.
   * @param {import("../../../../Component.js").Signal<string>} configuration.activeItemSignal - Reactive signal tracking the active navigation path.
   * @param {function(string): void} [configuration.onItemSelect] - Callback when a navigation item is selected.
   * @param {function(): void} [configuration.onSearchTrigger] - Callback when the search bar is triggered.
   * @param {function(): void} [configuration.onBrandClick] - Callback when the header branding is clicked to navigate to Dashboard.
   */
  constructor({
    categoryGroups = [],
    activeItemSignal,
    onItemSelect,
    onSearchTrigger,
    onBrandClick
  }) {
    super();

    /** @type {Array<Object>} */
    this.categoryGroups = categoryGroups;

    /** @type {import("../../../../Component.js").Signal<string>} */
    this.activeItemSignal = activeItemSignal;

    /** @type {function(string): void|undefined} */
    this.onItemSelect = onItemSelect;

    /** @type {function(): void|undefined} */
    this.onSearchTrigger = onSearchTrigger;

    /** @type {function(): void|undefined} */
    this.onBrandClick = onBrandClick;

    /** @type {boolean} */
    this.isMenuAnimating = false;

    /** @type {SearchPill} */
    const searchPillComponent = new SearchPill({
      onTrigger: this.onSearchTrigger
    });

    /** @type {ThemeToggle} */
    const themeToggleComponent = new ThemeToggle();

    /** @type {Array<NavigationCategory>} */
    const categoryComponents = this.categoryGroups.map((group) => {
      /** @type {Array<import("../../widgets/navigation-category/templates/navigation-category.js").NavigationItemDescriptor>} */
      const items = (group.navigation_item_paths || []).map((path) => {
        /** @type {Object|undefined} */
        const itemSpecification = window.DOCUMENTATION_ITEMS?.[path];
        /** @type {string} */
        const itemTitle =
          itemSpecification?.item_title ||
          path.split("/").pop()?.replace(".js", "").replace(/[-_]/g, " ") ||
          "";

        return {
          itemTitle,
          itemIdentifier: path
        };
      });

      return new NavigationCategory({
        categoryTitle: group.category_name,
        items,
        activeItemSignal: this.activeItemSignal,
        onItemSelect: this.onItemSelect,
        onHeaderClick: () => {
          if (this.isMobileLayout()) {
            this.openCategorySubmenu(group);
          }
        }
      });
    });

    /**
     * Handles brand logo / title click.
     * @returns {void}
     */
    const handleBrandClick = () => {
      if (typeof this.onBrandClick === "function") {
        this.onBrandClick();
      } else if (typeof this.onItemSelect === "function") {
        this.onItemSelect("data/dashboard.js");
      }
    };

    /**
     * Handles keyboard activation on branding.
     * @param {KeyboardEvent} keyboardEvent
     * @returns {void}
     */
    const handleBrandKeyDown = (keyboardEvent) => {
      if (keyboardEvent.key === "Enter" || keyboardEvent.key === " ") {
        keyboardEvent.preventDefault();
        handleBrandClick();
      }
    };

    this.template = html`
      <nav id="sidebar" class="sidebar" aria-label="Main Documentation Navigation">
        <div
          class="sidebar__branding"
          role="button"
          tabindex="0"
          aria-label="Navigate to Dashboard"
          onclick=${handleBrandClick}
          onkeydown=${handleBrandKeyDown}
        >
          <img class="sidebar__branding-logo" src="./assets/icon.png" alt="Kyaa!! Icon" />
          <span class="sidebar__branding-title">${window.DOCUMENTATION_DATA?.brand_name || "Kyaa!!"}</span>
        </div>
        <div class="sidebar__header">
          ${searchPillComponent}
          ${themeToggleComponent}
        </div>
        <div class="sidebar__content-viewport" id="sidebarContentViewport">
          <div class="sidebar__main-view" id="sidebarMainView">
            <div class="sidebar__categories" id="sidebarCategoriesContainer">
              ${categoryComponents}
            </div>
          </div>
          <div class="sidebar__sub-view" id="sidebarSubView" style="display: none;">
            <button
              class="sidebar__sub-back-button"
              id="sidebarSubBackBtn"
              type="button"
              aria-label="Back to main menu"
              onclick=${() => this.backToMainMenu()}
            >
              <span class="google-symbols" aria-hidden="true">arrow_back</span>
              <span class="sidebar__sub-back-text" id="sidebarSubBackText">Main Menu</span>
            </button>
            <div class="sidebar__sub-items-container" id="sidebarSubItemsContainer"></div>
          </div>
        </div>
      </nav>
    `;

    /**
     * Initializes smooth momentum wheel scrolling on the viewport container.
     */
    const initSmoothScroll = () => {
      const viewport = document.getElementById("sidebarContentViewport");
      if (viewport && !viewport.__hasSmoothScroll) {
        viewport.__hasSmoothScroll = true;
        attachSmoothScroll(viewport);
      }
    };

    this.mounted = () => {
      initSmoothScroll();
    };

    if (typeof window !== "undefined") {
      requestAnimationFrame(initSmoothScroll);
      setTimeout(initSmoothScroll, 60);
      setTimeout(initSmoothScroll, 300);
    }
  }

  /**
   * Checks if mobile responsive layout is active.
   * @returns {boolean}
   */
  isMobileLayout() {
    if (typeof window === "undefined") return false;
    return (
      window.innerWidth <= 768 ||
      window.matchMedia("(orientation: portrait)").matches ||
      (window.matchMedia("(orientation: landscape)").matches && window.innerHeight <= 550)
    );
  }

  /**
   * Automatically opens the submenu corresponding to the current active navigation item.
   * If no item is active, it resets to the main categories view.
   * @param {boolean} [shouldAnimate=false] - Whether to animate transition.
   * @returns {void}
   */
  showSubmenuForActiveCategory(shouldAnimate = false) {
    const activeNavigationPath = this.activeItemSignal?.value || "";
    const activeCategoryGroup = this.categoryGroups.find((group) =>
      Array.isArray(group.navigation_item_paths) && group.navigation_item_paths.includes(activeNavigationPath)
    );

    if (activeCategoryGroup) {
      this.openCategorySubmenu(activeCategoryGroup, shouldAnimate);
    } else {
      this.resetToMainView();
    }
  }

  /**
   * Opens category submenu on mobile with drilldown animation or instant display.
   * @param {Object} categoryGroup - Category group specification.
   * @param {boolean} [shouldAnimate=true] - Whether to apply sliding CSS keyframes.
   * @returns {void}
   */
  openCategorySubmenu(categoryGroup, shouldAnimate = true) {
    if (!categoryGroup) return;
    if (shouldAnimate && this.isMenuAnimating) return;

    /** @type {HTMLElement|null} */
    const rootElement = document.getElementById("sidebar");
    /** @type {HTMLElement|null} */
    const mainView = rootElement?.querySelector("#sidebarMainView") || null;
    /** @type {HTMLElement|null} */
    const subView = rootElement?.querySelector("#sidebarSubView") || null;
    /** @type {HTMLElement|null} */
    const backText = rootElement?.querySelector("#sidebarSubBackText") || null;
    /** @type {HTMLElement|null} */
    const itemsContainer = rootElement?.querySelector("#sidebarSubItemsContainer") || null;

    if (!mainView || !subView || !backText || !itemsContainer) {
      return;
    }

    backText.textContent = `Main Menu \u2022 ${categoryGroup.category_name}`;
    itemsContainer.innerHTML = "";

    const activePath = this.activeItemSignal?.value || "";

    (categoryGroup.navigation_item_paths || []).forEach((navigationPath) => {
      /** @type {Object|undefined} */
      const itemSpecification = window.DOCUMENTATION_ITEMS?.[navigationPath];
      /** @type {string} */
      const fallbackTitle =
        itemSpecification?.item_title ||
        navigationPath.split("/").pop()?.replace(".js", "").replace(/[-_]/g, " ") ||
        "";

      /** @type {HTMLButtonElement} */
      const subItemButton = document.createElement("button");
      subItemButton.type = "button";
      subItemButton.className = "sidebar__sub-item-button";
      subItemButton.setAttribute("data-navigation-path", navigationPath);
      if (navigationPath === activePath) {
        subItemButton.classList.add("sidebar__sub-item-button--active");
      }

      /** @type {HTMLSpanElement} */
      const textSpan = document.createElement("span");
      textSpan.className = "sidebar__sub-item-text";
      textSpan.textContent = fallbackTitle;
      subItemButton.appendChild(textSpan);

      subItemButton.addEventListener("click", () => {
        if (typeof this.onItemSelect === "function") {
          this.onItemSelect(navigationPath);
        }
      });

      itemsContainer.appendChild(subItemButton);
    });

    mainView.classList.remove(
      "sidebar__view--slide-in-right",
      "sidebar__view--slide-out-right",
      "sidebar__view--slide-in-left",
      "sidebar__view--slide-out-left"
    );
    subView.classList.remove(
      "sidebar__view--slide-in-right",
      "sidebar__view--slide-out-right",
      "sidebar__view--slide-in-left",
      "sidebar__view--slide-out-left"
    );

    if (!shouldAnimate) {
      mainView.style.display = "none";
      subView.style.display = "flex";
      this.isMenuAnimating = false;
      return;
    }

    this.isMenuAnimating = true;
    mainView.classList.add("sidebar__view--slide-out-right");

    let isOutDone = false;
    /** @type {any} */
    let outTimeout = null;

    const handleMainSlideOut = () => {
      if (isOutDone) return;
      isOutDone = true;
      clearTimeout(outTimeout);
      mainView.removeEventListener("animationend", handleMainSlideOut);
      mainView.style.display = "none";
      mainView.classList.remove("sidebar__view--slide-out-right");

      subView.style.display = "flex";
      subView.classList.add("sidebar__view--slide-in-right");

      let isInDone = false;
      /** @type {any} */
      let inTimeout = null;

      const handleSubSlideIn = () => {
        if (isInDone) return;
        isInDone = true;
        clearTimeout(inTimeout);
        subView.removeEventListener("animationend", handleSubSlideIn);
        subView.classList.remove("sidebar__view--slide-in-right");
        this.isMenuAnimating = false;
      };

      subView.addEventListener("animationend", handleSubSlideIn);
      inTimeout = setTimeout(handleSubSlideIn, 300);
    };

    mainView.addEventListener("animationend", handleMainSlideOut);
    outTimeout = setTimeout(handleMainSlideOut, 280);
  }

  /**
   * Navigates back from category submenu to main menu.
   * @returns {void}
   */
  backToMainMenu() {
    if (this.isMenuAnimating) return;
    this.isMenuAnimating = true;

    /** @type {HTMLElement|null} */
    const rootElement = document.getElementById("sidebar");
    /** @type {HTMLElement|null} */
    const mainView = rootElement?.querySelector("#sidebarMainView") || null;
    /** @type {HTMLElement|null} */
    const subView = rootElement?.querySelector("#sidebarSubView") || null;

    if (!mainView || !subView) {
      this.isMenuAnimating = false;
      return;
    }

    subView.classList.remove(
      "sidebar__view--slide-in-right",
      "sidebar__view--slide-out-right",
      "sidebar__view--slide-in-left",
      "sidebar__view--slide-out-left"
    );
    mainView.classList.remove(
      "sidebar__view--slide-in-right",
      "sidebar__view--slide-out-right",
      "sidebar__view--slide-in-left",
      "sidebar__view--slide-out-left"
    );

    subView.classList.add("sidebar__view--slide-out-right");

    let isOutDone = false;
    /** @type {any} */
    let outTimeout = null;

    const handleSubSlideOut = () => {
      if (isOutDone) return;
      isOutDone = true;
      clearTimeout(outTimeout);
      subView.removeEventListener("animationend", handleSubSlideOut);
      subView.style.display = "none";
      subView.classList.remove("sidebar__view--slide-out-right");

      mainView.style.display = "flex";
      mainView.classList.add("sidebar__view--slide-in-right");

      let isInDone = false;
      /** @type {any} */
      let inTimeout = null;

      const handleMainSlideIn = () => {
        if (isInDone) return;
        isInDone = true;
        clearTimeout(inTimeout);
        mainView.removeEventListener("animationend", handleMainSlideIn);
        mainView.classList.remove("sidebar__view--slide-in-right");
        this.isMenuAnimating = false;
      };

      mainView.addEventListener("animationend", handleMainSlideIn);
      inTimeout = setTimeout(handleMainSlideIn, 300);
    };

    subView.addEventListener("animationend", handleSubSlideOut);
    outTimeout = setTimeout(handleSubSlideOut, 280);
  }

  /**
   * Resets the sidebar to the main categories view immediately.
   * @returns {void}
   */
  resetToMainView() {
    /** @type {HTMLElement|null} */
    const rootElement = document.getElementById("sidebar");
    /** @type {HTMLElement|null} */
    const mainView = rootElement?.querySelector("#sidebarMainView") || null;
    /** @type {HTMLElement|null} */
    const subView = rootElement?.querySelector("#sidebarSubView") || null;

    if (mainView && subView) {
      mainView.style.display = "flex";
      subView.style.display = "none";
      mainView.classList.remove(
        "sidebar__view--slide-in-right",
        "sidebar__view--slide-out-right",
        "sidebar__view--slide-in-left",
        "sidebar__view--slide-out-left"
      );
      subView.classList.remove(
        "sidebar__view--slide-in-right",
        "sidebar__view--slide-out-right",
        "sidebar__view--slide-in-left",
        "sidebar__view--slide-out-left"
      );
    }
    this.isMenuAnimating = false;
  }
}
