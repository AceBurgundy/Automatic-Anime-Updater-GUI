/**
 * Available color palette names for the documentation theme system.
 * @type {Array<string>}
 */
export const AVAILABLE_PALETTES = [
  "purple",
  "ocean",
  "emerald",
  "sunset",
  "ruby",
  "indigo",
  "teal",
  "amber"
];

/**
 * Sets the active theme color palette on the document root element.
 * @param {string} paletteName - The name of the palette to activate.
 * @returns {void}
 */
export function setPalette(paletteName) {
  if (AVAILABLE_PALETTES.includes(paletteName)) {
    document.documentElement.setAttribute("data-palette", paletteName);
    try {
      localStorage.setItem("material-dialogs-palette", paletteName);
    } catch {
      // Ignore storage errors in private browsing modes
    }
  }
}

/**
 * Sets the active color mode (light or dark) on the document root element.
 * @param {"light"|"dark"} themeMode - Theme mode to set.
 * @returns {void}
 */
export function setThemeMode(themeMode) {
  document.documentElement.setAttribute("data-theme", themeMode);
  try {
    localStorage.setItem("material-dialogs-theme", themeMode);
  } catch {
    // Ignore storage errors in private browsing modes
  }
}

/**
 * Toggles between light and dark theme mode.
 * @returns {"light"|"dark"} The new active theme mode.
 */
export function toggleThemeMode() {
  /** @type {string|null} */
  const currentTheme = document.documentElement.getAttribute("data-theme");
  /** @type {"light"|"dark"} */
  const targetTheme = currentTheme === "light" ? "dark" : "light";
  setThemeMode(targetTheme);
  return targetTheme;
}

/**
 * Cycles to the next available color palette in sequence.
 * @returns {string} The newly selected palette name.
 */
export function cyclePalette() {
  /** @type {string|null} */
  const currentPalette = document.documentElement.getAttribute("data-palette") || "purple";
  /** @type {number} */
  const currentIndex = AVAILABLE_PALETTES.indexOf(currentPalette);
  /** @type {number} */
  const nextIndex = (currentIndex + 1) % AVAILABLE_PALETTES.length;
  /** @type {string} */
  const nextPalette = AVAILABLE_PALETTES[nextIndex];
  setPalette(nextPalette);
  return nextPalette;
}

/**
 * Initializes saved or randomized theme settings on page load.
 * @returns {void}
 */
export function initializeTheme() {
  /** @type {string|null} */
  let savedPalette = null;
  /** @type {string|null} */
  let savedTheme = null;

  try {
    savedPalette = localStorage.getItem("material-dialogs-palette");
    savedTheme = localStorage.getItem("material-dialogs-theme");
  } catch {
    // Fallback if localStorage is inaccessible
  }

  if (savedPalette && AVAILABLE_PALETTES.includes(savedPalette)) {
    document.documentElement.setAttribute("data-palette", savedPalette);
  } else {
    /** @type {number} */
    const randomIndex = Math.floor(Math.random() * AVAILABLE_PALETTES.length);
    document.documentElement.setAttribute("data-palette", AVAILABLE_PALETTES[randomIndex]);
  }

  if (savedTheme === "light" || savedTheme === "dark") {
    document.documentElement.setAttribute("data-theme", savedTheme);
  } else {
    document.documentElement.setAttribute("data-theme", "dark");
  }
}
