/**
 * Kyaa!! Anime Refresher - Documentation Master Data Registry.
 * Central registry connecting the landing dashboard, footer, and all category groups.
 * @type {Object}
 */
const documentationData = {
  brand_name: "Kyaa!!",
  dashboard_path: "data/dashboard.js",
  footer_path: "data/footer.js",
  category_groups: [
    {
      category_name: "Get Started",
      navigation_item_paths: [
        "data/navigation-items/overview-and-architecture.js",
        "data/navigation-items/installation-and-setup.js",
        "data/navigation-items/quickstart-and-usage.js"
      ]
    },
    {
      category_name: "Application Views",
      navigation_item_paths: [
        "data/navigation-items/tasks-and-live-streaming.js",
        "data/navigation-items/library-and-settings.js",
        "data/navigation-items/scheduling-and-automation.js",
        "data/navigation-items/theming-and-design-system.js"
      ]
    },
    {
      category_name: "Scraping & Resilience",
      navigation_item_paths: [
        "data/navigation-items/anti-detect-and-camoufox.js",
        "data/navigation-items/circuit-breaker-and-mirrors.js"
      ]
    },
    {
      category_name: "Architecture & Reference",
      navigation_item_paths: [
        "data/navigation-items/cli-commands-reference.js",
        "data/navigation-items/ai-episode-parser-model.js",
        "data/navigation-items/database-and-safetyguard.js"
      ]
    }
  ]
};

export default documentationData;
