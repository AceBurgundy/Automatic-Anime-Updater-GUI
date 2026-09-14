import { Component, css, html } from "../../../../Component.js";

css(import.meta, ["../styles/banner-image__option.css"]);

/**
 * Legacy class reference: .mockup-option
 * Represents a single selectable radio option inside the hero dialog preview card.
 */
export class BannerImageOption extends Component {
  /**
   * @param {Object} configuration
   * @param {string} configuration.optionLabel - Descriptive text of the option.
   * @param {number} configuration.optionIndex - Numerical index of this option.
   * @param {import("../../../../Component.js").Signal<number>} configuration.selectedOptionSignal - Reactive signal for selected index.
   * @param {function(number): void} [configuration.onSelect] - Selection callback.
   */
  constructor({ optionLabel, optionIndex, selectedOptionSignal, onSelect }) {
    super();

    /** @type {string} */
    this.optionLabel = optionLabel;

    /** @type {number} */
    this.optionIndex = optionIndex;

    /** @type {import("../../../../Component.js").Signal<number>} */
    this.selectedOptionSignal = selectedOptionSignal;

    /** @type {function(number): void|undefined} */
    this.onSelect = onSelect;

    /**
     * @returns {void}
     */
    const handleClick = () => {
      this.selectedOptionSignal.value = this.optionIndex;
      if (typeof this.onSelect === "function") {
        this.onSelect(this.optionIndex);
      }
    };

    /** @type {boolean} */
    const isSelected = this.selectedOptionSignal.value === this.optionIndex;

    /** @type {string} */
    const optionClassName = isSelected
      ? "banner-image__option banner-image__option--selected"
      : "banner-image__option";

    /** @type {string} */
    const ariaCheckedValue = isSelected ? "true" : "false";

    this.template = html`
      <div
        class="${optionClassName}"
        role="radio"
        aria-checked="${ariaCheckedValue}"
        tabindex="0"
        onclick=${handleClick}
      >
        <span class="banner-image__radio"></span>
        <span class="banner-image__option-label">${this.optionLabel}</span>
      </div>
    `;
  }
}
