import { Component, html, signal, css } from "../../../../Component.js";
import { toggleThemeMode } from "../../../../common/scripts/theme-manager.js";
import { showToast } from "../../toast/scripts/toast__service.js";

css(import.meta, ["../styles/theme-toggle.css"]);

/**
 * Legacy class reference: .theme-btn / #themeToggleBtn
 * Represents a circular icon button for switching between Light and Dark color themes.
 */
export class ThemeToggle extends Component {
  /**
   * @param {Object} [configuration]
   * @param {function("light"|"dark"): void} [configuration.onToggle] - Callback invoked when theme mode changes.
   */
  constructor({ onToggle } = {}) {
    super();

    /** @type {function("light"|"dark"): void|undefined} */
    this.onToggle = onToggle;

    /** @type {string|null} */
    const currentThemeAttribute = typeof document !== "undefined"
      ? document.documentElement.getAttribute("data-theme")
      : "dark";

    /** @type {import("../../../../Component.js").Signal<"light"|"dark">} */
    this.themeModeSignal = signal(currentThemeAttribute === "light" ? "light" : "dark");

    /**
     * @returns {void}
     */
    const handleToggleClick = () => {
      /** @type {"light"|"dark"} */
      const updatedThemeMode = toggleThemeMode();
      this.themeModeSignal.value = updatedThemeMode;

      const nextIconName = updatedThemeMode === "light" ? "dark_mode" : "light_mode";
      /** @type {NodeListOf<HTMLElement>} */
      const iconElements = document.querySelectorAll(".theme-toggle__icon, [data-theme-icon]");
      iconElements.forEach((iconElement) => {
        iconElement.textContent = nextIconName;
      });

      showToast(`Theme switched to ${updatedThemeMode} mode`);

      if (typeof this.onToggle === "function") {
        this.onToggle(updatedThemeMode);
      }
    };

    /** @type {string} */
    const initialIconName = this.themeModeSignal.value === "light" ? "dark_mode" : "light_mode";

    /** @type {string} */
    const ariaLabel = this.themeModeSignal.value === "light" ? "Switch to dark theme" : "Switch to light theme";

    this.template = html`
      <button
        type="button"
        class="theme-toggle"
        aria-label=${ariaLabel}
        title=${ariaLabel}
        onclick=${handleToggleClick}
      >
        <span class="google-symbols theme-toggle__icon" data-theme-icon>${initialIconName}</span>
      </button>
    `;
  }
}
