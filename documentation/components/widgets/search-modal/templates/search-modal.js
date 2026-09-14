import { Component, html, css } from "../../../../Component.js";
import { SearchModalItem } from "./search-modal__item.js";
import {
  subscribeToModalState,
  subscribeToQueryResults,
  closeSearchModal,
  searchDocumentation,
  selectSearchResult,
  setItemSelectionHandler
} from "../scripts/search-modal__service.js";

css(import.meta, ["../styles/search-modal.css"]);

/**
 * Search Modal Dialog Component.
 * Legacy mapping: .search-modal-backdrop, .search-modal-container, .search-modal-input-wrap, .search-results-list.
 */
export class SearchModal extends Component {
  /**
   * @param {Object} [configuration={}]
   * @param {function(string): void} [configuration.onSelect] - Callback when an item is selected from search results.
   */
  constructor({ onSelect } = {}) {
    super();

    if (typeof onSelect === "function") {
      setItemSelectionHandler(onSelect);
    }

    this.template = html`
      <div class="search-modal search-modal--hidden" id="searchModalBackdrop" data-search-modal-backdrop>
        <div class="search-modal__container" role="dialog" aria-modal="true" data-search-modal-dialog>
          <div class="search-modal__input-wrapper">
            <span class="google-symbols search-modal__input-icon" aria-hidden="true">search</span>
            <input
              type="text"
              class="search-modal__input"
              placeholder="Search documentation..."
              id="searchModalInput"
            />
          </div>
          <div class="search-modal__results" id="searchResultsContainer"></div>
        </div>
      </div>
    `;

    this.mounted = () => {
      /** @type {HTMLElement|null} */
      const backdropElement = document.getElementById("searchModalBackdrop");
      /** @type {HTMLInputElement|null} */
      const inputElement = /** @type {HTMLInputElement|null} */ (document.getElementById("searchModalInput"));
      /** @type {HTMLElement|null} */
      const resultsContainer = document.getElementById("searchResultsContainer");

      if (backdropElement) {
        backdropElement.addEventListener("click", (clickEvent) => {
          if (clickEvent.target === backdropElement) {
            closeSearchModal();
          }
        });
      }

      if (inputElement) {
        inputElement.addEventListener("input", (inputEvent) => {
          /** @type {HTMLInputElement} */
          const target = /** @type {HTMLInputElement} */ (inputEvent.target);
          searchDocumentation(target.value);
        });
      }

      /**
       * @param {Array<import("../scripts/search-modal__service.js").SearchIndexEntry>} results
       * @returns {void}
       */
      const renderResults = (results) => {
        if (!resultsContainer) {
          return;
        }
        if (results.length === 0) {
          resultsContainer.innerHTML = '<div class="search-modal__empty">No documentation results found</div>';
          return;
        }
        /** @type {Array<SearchModalItem>} */
        const itemComponents = results.map((entry) => {
          return new SearchModalItem({
            title: entry.title,
            description: entry.description,
            iconName: entry.iconName,
            path: entry.path,
            onSelect: (selectedPath) => {
              selectSearchResult(selectedPath);
            }
          });
        });
        resultsContainer.innerHTML = itemComponents.map(item => item.toString()).join("");
      };

      subscribeToModalState((isOpen) => {
        if (!backdropElement) {
          return;
        }
        if (isOpen) {
          backdropElement.classList.remove("search-modal--hidden");
          if (inputElement) {
            inputElement.value = "";
            searchDocumentation("");
            setTimeout(() => inputElement.focus(), 50);
          }
        } else {
          backdropElement.classList.add("search-modal--hidden");
        }
      });

      subscribeToQueryResults((results) => {
        renderResults(results);
      });
    };
  }
}

