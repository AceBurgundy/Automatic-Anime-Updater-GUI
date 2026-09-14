import { Component, html, signal, css } from "../../../../Component.js";
import { TopBar } from "../../../widgets/top-bar/templates/top-bar.js";
import { Sidebar } from "../../../sections/sidebar/templates/sidebar.js";
import { Banner } from "../../../sections/banner/templates/banner.js";
import { DocumentationContent } from "../../../sections/documentation-content/templates/documentation-content.js";
import { Footer } from "../../../sections/footer/templates/footer.js";
import { Dashboard } from "../../dashboard/templates/dashboard.js";
import { SearchModal } from "../../../widgets/search-modal/templates/search-modal.js";
import { Toast } from "../../../widgets/toast/templates/toast.js";
import { LoadingScreen } from "../../../widgets/loading-screen/templates/loading-screen.js";
import { openSearchModal } from "../../../widgets/search-modal/scripts/search-modal__service.js";
import { fetchNavigationItemData } from "../../../../common/scripts/data-loader.js";

css(import.meta, ["../styles/app.css"]);

/**
 * Formats a navigation path into a human-readable title fallback.
 * @param {string} navigationPath - Target navigation item file path.
 * @returns {string} Formatted title string.
 */
function formatFallbackTitle(navigationPath) {
  if (!navigationPath || typeof navigationPath !== "string") {
    return "";
  }
  const filename = navigationPath.split("/").pop() || "";
  return filename.replace(".js", "").replace(/[-_]/g, " ");
}

/**
 * Legacy class reference: .app-root, .main-viewport, .sidebar-backdrop
 * Main Single Page Application component orchestrating navigation state, dynamic script loading, and viewport rendering.
 */
export class App extends Component {
  /**
   * @param {Object} [configuration={}]
   * @param {Array<Object>} [configuration.categoryGroups=[]] - Category groups specification array.
   */
  /**
   * @param {Object} [configuration]
   * @param {Object|Array<Object>} [configuration.documentationData={}] - Master documentation registry from data.js.
   * @param {Array<Object>} [configuration.categoryGroups=[]] - Category groups list (backward-compatible alias).
   */
  constructor({
    documentationData = {},
    categoryGroups = []
  } = {}) {
    super();

    /** @type {Object} */
    const masterData = documentationData && typeof documentationData === "object" && !Array.isArray(documentationData)
      ? documentationData
      : {
          dashboard_path: "data/dashboard.js",
          category_groups: Array.isArray(categoryGroups) && categoryGroups.length > 0
            ? categoryGroups
            : Array.isArray(documentationData)
              ? documentationData
              : []
        };

    /** @type {string} */
    this.dashboardPath = masterData.dashboard_path || "data/dashboard.js";

    /** @type {string} */
    this.footerPath = masterData.footer_path || "data/footer.js";

    /** @type {Array<Object>} */
    this.categoryGroups = Array.isArray(masterData.category_groups)
      ? masterData.category_groups
      : [];

    // Expose documentation registry globally for search service and backward compatibility
    window.DOCUMENTATION_DATA = masterData;
    window.DOCUMENTATION_ITEMS = window.DOCUMENTATION_ITEMS || {};

    /** @type {string} */
    const initialPath = this.dashboardPath;

    /** @type {import("../../../../Component.js").Signal<string>} */
    this.activePathSignal = signal(initialPath);

    /** @type {LoadingScreen} */
    this.loadingScreenComponent = new LoadingScreen();

    /** @type {TopBar} */
    this.topBarComponent = new TopBar({
      title: masterData.brand_name || "Kyaa!!",
      onMenuToggle: () => {
        this.toggleMobileDrawer();
      },
      onBrandClick: () => {
        this.navigateTo(this.dashboardPath);
        this.closeMobileDrawer();
      }
    });

    /** @type {Sidebar} */
    this.sidebarComponent = new Sidebar({
      categoryGroups: this.categoryGroups,
      activeItemSignal: this.activePathSignal,
      onItemSelect: (selectedPath) => {
        this.navigateTo(selectedPath);
        this.closeMobileDrawer();
      },
      onSearchTrigger: () => {
        openSearchModal();
      },
      onBrandClick: () => {
        this.navigateTo(this.dashboardPath);
        this.closeMobileDrawer();
      }
    });

    /** @type {SearchModal} */
    const searchModalComponent = new SearchModal({
      onSelect: (selectedPath) => {
        this.navigateTo(selectedPath);
        this.closeMobileDrawer();
      }
    });

    /** @type {Toast} */
    const toastComponent = new Toast();

    this.template = html`
      <div class="app-root" id="appRoot">
        ${this.loadingScreenComponent}
        ${this.topBarComponent}
        ${this.sidebarComponent}
        <main
          id="mainViewport"
          class="app-root__viewport"
          data-main-viewport
          tabindex="-1"
          aria-label="Documentation Viewport"
        >
          <!-- Dynamic Banner and DocumentationContent will be injected here on mount -->
        </main>
        <div
          class="app-root__backdrop"
          data-app-backdrop
          aria-hidden="true"
        ></div>
        ${searchModalComponent}
        ${toastComponent}
      </div>
    `;

    this.mounted = () => {
      this.attachBackdropListener();
      this.attachWindowResizeListener();
      if (initialPath) {
        this.loadInitialPage(initialPath);
      } else {
        setTimeout(() => {
          this.loadingScreenComponent.dismiss(() => {
            this.preloadAllNavigationItems();
          });
        }, 800);
      }
    };
  }

  /**
   * Performs the initial page load with cinematic loading screen dismissal and deferred background preloading.
   * @param {string} initialPath - Path to the initial documentation item.
   * @returns {Promise<void>}
   */
  async loadInitialPage(initialPath) {
    try {
      await this.loadNavigationItem(initialPath);
      setTimeout(() => {
        this.loadingScreenComponent.dismiss(() => {
          this.preloadAllNavigationItems();
        });
      }, 800);
    } catch (initialLoadError) {
      console.error("Initial documentation load error:", initialLoadError);
      setTimeout(() => {
        this.loadingScreenComponent.dismiss(() => {
          this.preloadAllNavigationItems();
        });
      }, 800);
    }
  }

  /**
   * Attaches window resize and orientation listeners to reset drawer on desktop viewport transition.
   * @returns {void}
   */
  attachWindowResizeListener() {
    const handleLayoutChange = () => {
      if (!this.sidebarComponent?.isMobileLayout()) {
        this.closeMobileDrawer();
        this.sidebarComponent?.resetToMainView();
      }
    };

    window.addEventListener("resize", handleLayoutChange, { passive: true });
    window.addEventListener("orientationchange", handleLayoutChange, { passive: true });
    if (typeof window.screen !== "undefined" && window.screen.orientation) {
      window.screen.orientation.addEventListener("change", handleLayoutChange);
    }
  }

  /**
   * Attaches click listener to the mobile backdrop overlay to dismiss the navigation drawer.
   * @returns {void}
   */
  attachBackdropListener() {
    /** @type {HTMLElement|null} */
    const backdropElement = document.querySelector("[data-app-backdrop]");
    if (backdropElement) {
      backdropElement.addEventListener("click", () => {
        this.closeMobileDrawer();
      });
    }
  }

  /**
   * Toggles the mobile navigation drawer and backdrop visibility.
   * Automatically opens the submenu if an active category item exists, otherwise shows the main menu.
   * @returns {void}
   */
  toggleMobileDrawer() {
    /** @type {HTMLElement|null} */
    const sidebarElement = document.getElementById("sidebar");
    /** @type {HTMLElement|null} */
    const backdropElement = document.querySelector("[data-app-backdrop]");

    if (sidebarElement) {
      const isOpen = sidebarElement.classList.toggle("sidebar--open");
      if (this.topBarComponent) {
        this.topBarComponent.setMenuOpen(isOpen);
      }

      if (isOpen) {
        const activeNavigationPath = this.activePathSignal.value;
        const activeCategoryGroup = this.categoryGroups.find((group) =>
          Array.isArray(group.navigation_item_paths) && group.navigation_item_paths.includes(activeNavigationPath)
        );

        if (activeCategoryGroup && this.sidebarComponent) {
          this.sidebarComponent.showSubmenuForActiveCategory(false);
        } else if (this.sidebarComponent) {
          this.sidebarComponent.resetToMainView();
        }

        if (activeNavigationPath) {
          document.querySelectorAll("[data-navigation-path]").forEach((buttonElement) => {
            if (buttonElement.getAttribute("data-navigation-path") === activeNavigationPath) {
              buttonElement.classList.add("navigation-category__item-button--active");
              if (buttonElement.classList.contains("sidebar__sub-item-button")) {
                buttonElement.classList.add("sidebar__sub-item-button--active");
              }
            } else {
              buttonElement.classList.remove("navigation-category__item-button--active");
              if (buttonElement.classList.contains("sidebar__sub-item-button")) {
                buttonElement.classList.remove("sidebar__sub-item-button--active");
              }
            }
          });
        }
      }
    }
    if (backdropElement) {
      const isSidebarOpen = sidebarElement?.classList.contains("sidebar--open") || false;
      backdropElement.classList.toggle("app-root__backdrop--visible", isSidebarOpen);
    }
  }

  /**
   * Closes the mobile navigation drawer and hides the backdrop overlay.
   * @returns {void}
   */
  closeMobileDrawer() {
    /** @type {HTMLElement|null} */
    const sidebarElement = document.getElementById("sidebar");
    /** @type {HTMLElement|null} */
    const backdropElement = document.querySelector("[data-app-backdrop]");

    if (sidebarElement) {
      sidebarElement.classList.remove("sidebar--open");
    }
    if (this.topBarComponent) {
      this.topBarComponent.setMenuOpen(false);
    }
    if (backdropElement) {
      backdropElement.classList.remove("app-root__backdrop--visible");
    }
  }

  /**
   * Navigates to a specific documentation page path.
   * @param {string} targetNavigationPath - Path of the target documentation item.
   * @returns {void}
   */
  navigateTo(targetNavigationPath) {
    if (!targetNavigationPath) {
      return;
    }
    this.activePathSignal.value = targetNavigationPath;
    this.loadNavigationItem(targetNavigationPath);
  }

  /**
   * Asynchronously preloads all navigation item scripts in the background.
   * @returns {void}
   */
  preloadAllNavigationItems() {
    this.fetchNavigationItemData(this.dashboardPath).catch(() => {});
    this.fetchNavigationItemData(this.footerPath).catch(() => {});
    this.categoryGroups.forEach((group) => {
      const itemPaths = group.navigation_item_paths || [];
      itemPaths.forEach((path) => {
        this.fetchNavigationItemData(path).catch((error) => {
          console.warn(`Could not preload documentation item (${path}):`, error);
        });
      });
    });
  }

  /**
   * Loads a navigation item specification script dynamically using the data loader.
   * @param {string} navigationPath - Target item script path.
   * @returns {Promise<Object>} Resolved navigation item specification object.
   */
  async fetchNavigationItemData(navigationPath) {
    return fetchNavigationItemData(navigationPath);
  }

  /**
   * Loads and mounts the active navigation item page into the main viewport.
   * @param {string} navigationPath - Target navigation item path.
   * @returns {Promise<void>}
   */
  async loadNavigationItem(navigationPath) {
    /** @type {HTMLElement|null} */
    const viewportElement = document.getElementById("mainViewport");
    if (!viewportElement || !navigationPath) {
      return;
    }

    this.activePathSignal.value = navigationPath;

    // Highlight active sidebar item across the entire DOM
    document.querySelectorAll("[data-navigation-path]").forEach((buttonElement) => {
      if (buttonElement.getAttribute("data-navigation-path") === navigationPath) {
        buttonElement.classList.add("navigation-category__item-button--active");
        if (buttonElement.classList.contains("sidebar__sub-item-button")) {
          buttonElement.classList.add("sidebar__sub-item-button--active");
        }
      } else {
        buttonElement.classList.remove("navigation-category__item-button--active");
        if (buttonElement.classList.contains("sidebar__sub-item-button")) {
          buttonElement.classList.remove("sidebar__sub-item-button--active");
        }
      }
    });

    // Highlight active category toggle on mobile
    document.querySelectorAll(".navigation-category").forEach((categoryElement, categoryIndex) => {
      const categoryGroup = this.categoryGroups[categoryIndex];
      const categoryHeaderButton = categoryElement.querySelector(".navigation-category__header-button");
      if (categoryHeaderButton && categoryGroup && Array.isArray(categoryGroup.navigation_item_paths)) {
        if (categoryGroup.navigation_item_paths.includes(navigationPath)) {
          categoryHeaderButton.classList.add("navigation-category__header-button--has-active");
        } else {
          categoryHeaderButton.classList.remove("navigation-category__header-button--has-active");
        }
      }
    });

    try {
      /** @type {Object} */
      const itemData = await this.fetchNavigationItemData(navigationPath);
      /** @type {Object} */
      const headerContainer = itemData.header_container || {};
      /** @type {Array<Object>} */
      const tabList = itemData.tab_list || [];

      /** @type {Array<string>} */
      const allNavigationPaths = [];
      this.categoryGroups.forEach((group) => {
        if (Array.isArray(group.navigation_item_paths)) {
          allNavigationPaths.push(...group.navigation_item_paths);
        }
      });

      const currentIndex = allNavigationPaths.indexOf(navigationPath);

      /** @type {import("../../../widgets/page-navigation/templates/page-navigation.js").PageNavigationTarget|null} */
      let previousPage = null;
      /** @type {import("../../../widgets/page-navigation/templates/page-navigation.js").PageNavigationTarget|null} */
      let nextPage = null;

      if (navigationPath === this.dashboardPath) {
        previousPage = null;
        if (allNavigationPaths.length > 0) {
          const firstPath = allNavigationPaths[0];
          const firstCached = window.DOCUMENTATION_ITEMS[firstPath];
          nextPage = {
            pageTitle: firstCached?.item_title || formatFallbackTitle(firstPath),
            destinationPath: firstPath,
            subLabel: "Up Next"
          };
        }
      } else if (currentIndex === 0) {
        const dashboardCached = window.DOCUMENTATION_ITEMS[this.dashboardPath];
        previousPage = {
          pageTitle: dashboardCached?.item_title || "Dashboard",
          destinationPath: this.dashboardPath,
          subLabel: "Previous"
        };
        if (allNavigationPaths.length > 1) {
          const nextPath = allNavigationPaths[1];
          const nextCached = window.DOCUMENTATION_ITEMS[nextPath];
          nextPage = {
            pageTitle: nextCached?.item_title || formatFallbackTitle(nextPath),
            destinationPath: nextPath,
            subLabel: "Up Next"
          };
        }
      } else if (currentIndex > 0) {
        const previousPath = allNavigationPaths[currentIndex - 1];
        const previousCached = window.DOCUMENTATION_ITEMS[previousPath];
        previousPage = {
          pageTitle: previousCached?.item_title || formatFallbackTitle(previousPath),
          destinationPath: previousPath,
          subLabel: "Previous"
        };

        if (currentIndex < allNavigationPaths.length - 1) {
          const nextPath = allNavigationPaths[currentIndex + 1];
          const nextCached = window.DOCUMENTATION_ITEMS[nextPath];
          nextPage = {
            pageTitle: nextCached?.item_title || formatFallbackTitle(nextPath),
            destinationPath: nextPath,
            subLabel: "Up Next"
          };
        }
      }

      /** @type {Banner} */
      const bannerComponent = new Banner({
        title: headerContainer.title || "",
        description: headerContainer.description || "",
        badges: headerContainer.badge_list || [],
        isCompact: (headerContainer.title || "").length >= 20,
        bannerImage: headerContainer.banner_image || headerContainer.mockup_card || {}
      });

      /** @type {string} */
      let contentHtml;
      /** @type {function(): void} */
      let mountContent;

      if (navigationPath === this.dashboardPath) {
        /** @type {Dashboard} */
        const dashboardComponent = new Dashboard({
          tabList,
          previousPage,
          nextPage,
          onNavigatePage: (destinationPath) => {
            this.navigateTo(destinationPath);
          }
        });
        contentHtml = dashboardComponent.toString();
        mountContent = () => { dashboardComponent.__mount?.(); };
      } else {
        /** @type {DocumentationContent} */
        const documentationContentComponent = new DocumentationContent({
          itemTitle: itemData.item_title || "Documentation",
          tabList,
          previousPage,
          nextPage,
          hideTabs: Boolean(itemData.hide_tabs),
          hideTableOfContents: Boolean(itemData.hide_toc),
          onNavigatePage: (destinationPath) => {
            this.navigateTo(destinationPath);
          }
        });
        contentHtml = documentationContentComponent.toString();
        mountContent = () => { documentationContentComponent.__mount?.(); };
      }

      // Fetch or use cached footer specification
      /** @type {Object} */
      const footerData = await this.fetchNavigationItemData(this.footerPath).catch(() => ({}));
      /** @type {Footer} */
      const footerComponent = new Footer({
        brandName: footerData.brand_name || "Material Design",
        brandDescription: footerData.brand_description || "",
        socialLinks: footerData.social_links || [],
        columns: footerData.columns || [],
        legalLinks: footerData.legal_links || [],
        copyrightText: footerData.copyright_text || ""
      });

      viewportElement.innerHTML = bannerComponent.toString() + contentHtml + footerComponent.toString();
      bannerComponent.__mount?.();
      mountContent();
      footerComponent.__mount?.();

      viewportElement.scrollTo({ top: 0, behavior: "smooth" });
    } catch (loadingError) {
      console.error("Failed to load documentation item:", loadingError);
      viewportElement.innerHTML = `
        <div style="padding: 3rem; color: var(--md-sys-color-error);">
          <h2>Error Loading Documentation</h2>
          <p>Failed to load <code>${navigationPath}</code>. Please check network connection and file paths.</p>
        </div>
      `;
    }
  }
}
