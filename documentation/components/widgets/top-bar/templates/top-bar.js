import { Component, html, signal, css } from "../../../../Component.js";
import { toggleThemeMode } from "../../../../common/scripts/theme-manager.js";
import { openSearchModal } from "../../search-modal/scripts/search-modal__service.js";

import { showToast } from "../../toast/scripts/toast__service.js";

css(import.meta, ["../styles/top-bar.css"]);

/**
 * Top Bar Component.
 * Fixed header for mobile and portrait viewports hosting the drawer menu trigger, title, theme toggle, and search button.
 * Legacy mapping: .mobile-topbar, .mobile-topbar-left, .mobile-topbar-right, .mobile-topbar-btn, .mobile-topbar-title.
 */
export class TopBar extends Component {
  /**
   * @param {Object} [configuration={}]
   * @param {string} [configuration.title="Material Dialogs"] - Title displayed in the top bar.
   * @param {function(): void} [configuration.onMenuToggle] - Callback invoked when the burger menu button is clicked.
   * @param {function(): void} [configuration.onBrandClick] - Callback invoked when the brand title is clicked.
   */
  constructor({ title = "Material Dialogs", onMenuToggle, onBrandClick } = {}) {
    super();

    /** @type {string} */
    this.title = title;

    /** @type {function(): void|undefined} */
    this.onMenuToggle = onMenuToggle;

    /** @type {function(): void|undefined} */
    this.onBrandClick = onBrandClick;

    /** @type {string|null} */
    const currentThemeAttribute = typeof document !== "undefined"
      ? document.documentElement.getAttribute("data-theme")
      : "dark";

    /** @type {import("../../../../Component.js").Signal<string>} */
    this.themeIconSignal = signal(currentThemeAttribute === "light" ? "dark_mode" : "light_mode");

    /** @type {import("../../../../Component.js").Signal<string>} */
    this.burgerIconSignal = signal("menu");

    /**
     * Updates burger icon state.
     * @param {boolean} isOpen
     * @returns {void}
     */
    this.setMenuOpen = (isOpen) => {
      this.burgerIconSignal.value = isOpen ? "close" : "menu";
    };

    /**
     * Handles theme toggle click.
     * @returns {void}
     */
    const handleThemeToggleClick = () => {
      /** @type {"light"|"dark"} */
      const updatedThemeMode = toggleThemeMode();
      const nextIconName = updatedThemeMode === "light" ? "dark_mode" : "light_mode";
      this.themeIconSignal.value = nextIconName;

      /** @type {NodeListOf<HTMLElement>} */
      const iconElements = document.querySelectorAll(".theme-toggle__icon, [data-theme-icon]");
      iconElements.forEach((iconElement) => {
        iconElement.textContent = nextIconName;
      });

      showToast(`Theme switched to ${updatedThemeMode} mode`);
    };

    /**
     * Handles search button click.
     * @returns {void}
     */
    const handleSearchClick = () => {
      openSearchModal();
    };

    /**
     * Handles mobile menu toggle click.
     * @returns {void}
     */
    const handleMenuClick = () => {
      if (typeof this.onMenuToggle === "function") {
        this.onMenuToggle();
      }
    };

    /**
     * Handles brand title click.
     * @returns {void}
     */
    const handleBrandClick = () => {
      if (typeof this.onBrandClick === "function") {
        this.onBrandClick();
      }
    };

    /**
     * Handles brand title keyboard activation.
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
      <header id="topBar" class="top-bar" aria-label="Mobile Navigation Header">
        <div class="top-bar__left">
          <button
            type="button"
            class="top-bar__button"
            aria-label="Toggle Navigation Drawer"
            onclick=${handleMenuClick}
          >
            <span class="google-symbols top-bar__icon" aria-hidden="true">${this.burgerIconSignal}</span>
          </button>
          <div
            class="top-bar__title"
            role="button"
            tabindex="0"
            aria-label="Navigate to Material Dialogs Dashboard"
            onclick=${handleBrandClick}
            onkeydown=${handleBrandKeyDown}
          >${this.title}</div>
        </div>
        <div class="top-bar__right">
          <button
            type="button"
            class="top-bar__button"
            aria-label="Toggle Light / Dark Theme"
            onclick=${handleThemeToggleClick}
          >
            <span class="google-symbols top-bar__icon" aria-hidden="true">${this.themeIconSignal}</span>
          </button>
          <button
            type="button"
            class="top-bar__button"
            aria-label="Open Search Documentation"
            onclick=${handleSearchClick}
          >
            <span class="google-symbols top-bar__icon" aria-hidden="true">search</span>
          </button>
        </div>
      </header>
    `;
  }
}

