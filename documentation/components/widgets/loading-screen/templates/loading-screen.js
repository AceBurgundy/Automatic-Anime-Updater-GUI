import { Component, html, css } from "../../../../Component.js";

css(import.meta, ["../styles/loading-screen.css"]);

/**
 * LoadingScreen Component displaying a pure CSS dual-orb loading animation.
 * Orchestrates an orbiting spin, converging to center, splitting in opposite directions, and smooth fade-out.
 */
export class LoadingScreen extends Component {
  constructor() {
    super();

    this.template = html`
      <div class="loading-screen" id="loadingScreen" aria-label="Loading documentation" role="status">
        <div class="loading-screen__wrapper">
          <div class="loading-screen__spinner-track">
            <span class="loading-screen__orb loading-screen__orb--primary"></span>
            <span class="loading-screen__orb loading-screen__orb--secondary"></span>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Triggers the exit split-and-fade animation sequence and invokes a callback upon completion.
   * @param {function(): void} [onDismissCompleted] - Callback executed after the exit transition completes.
   * @returns {void}
   */
  dismiss(onDismissCompleted) {
    /** @type {HTMLElement|null} */
    const loadingScreenElement = document.getElementById("loadingScreen");
    if (!loadingScreenElement) {
      if (typeof onDismissCompleted === "function") {
        onDismissCompleted();
      }
      return;
    }

    loadingScreenElement.classList.add("loading-screen--split-fade");

    setTimeout(() => {
      loadingScreenElement.style.display = "none";
      if (loadingScreenElement.parentNode) {
        loadingScreenElement.parentNode.removeChild(loadingScreenElement);
      }
      if (typeof onDismissCompleted === "function") {
        onDismissCompleted();
      }
    }, 600);
  }
}
