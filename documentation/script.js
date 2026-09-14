import { Root } from "./Component.js";
import { App } from "./components/pages/app/templates/app.js";
import { initializeTheme } from "./common/scripts/theme-manager.js";
import { initializeViewportScaling } from "./common/scripts/viewport-scaler.js";
import documentationData from "./data/data.js";

initializeTheme();
initializeViewportScaling();

new Root({
  destination: class extends App {
    constructor() {
      super({ documentationData });
    }
  },
  path: "/"
}).render();
