/**
 * Dynamically computes and updates root font scaling for ultra-wide screen resolutions.
 * @returns {void}
 */
export function updateRootScale() {
  if (typeof window === "undefined") {
    return;
  }

  if (window.innerWidth <= 768 || window.matchMedia("(orientation: portrait)").matches) {
    document.documentElement.style.fontSize = "";
    return;
  }

  /** @type {number} */
  const viewportWidth = window.innerWidth;

  if (viewportWidth > 1920) {
    /** @type {number} */
    const calculatedSize = 16 + (viewportWidth - 1920) / 60;
    /** @type {number} */
    const clampedSize = Math.min(Math.max(calculatedSize, 16), 72);
    document.documentElement.style.fontSize = `${clampedSize.toFixed(2)}px`;
  } else {
    document.documentElement.style.fontSize = "";
  }
}

/**
 * Initializes viewport scaling event listeners on window resize and DOM load.
 * @returns {function(): void} Cleanup listener remover function.
 */
export function initializeViewportScaling() {
  if (typeof window === "undefined") {
    return () => {};
  }

  window.addEventListener("resize", updateRootScale, { passive: true });
  updateRootScale();

  return () => {
    window.removeEventListener("resize", updateRootScale);
  };
}
