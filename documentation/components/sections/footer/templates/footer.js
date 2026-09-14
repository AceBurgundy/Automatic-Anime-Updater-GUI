import { Component, css, html } from "../../../../Component.js";

css(import.meta, ["../styles/footer.css"]);

/**
 * @typedef {Object} FooterSocialLink
 * @property {string} icon_name - Google Material Symbol icon identifier.
 * @property {string} platform_name - Display name of social platform.
 * @property {string} url - Destination URL.
 */

/**
 * @typedef {Object} FooterColumnLink
 * @property {string} label - Anchor label text.
 * @property {string} url - Target URL.
 */

/**
 * @typedef {Object} FooterColumn
 * @property {string} column_title - Column section header.
 * @property {Array<FooterColumnLink>} links - Column link entries.
 */

/**
 * @typedef {Object} FooterLegalLink
 * @property {string} label - Anchor label text.
 * @property {string} url - Target policy URL.
 */

/**
 * Footer Component.
 * Global application footer mirroring the Material Design 3 (m3.material.io)
 * site footer with a clean 2-row layout:
 *   Row 1: Left brand outro description & social links | Right multi-column navigation links
 *   Row 2: Bottom legal links & copyright policy bar
 */
export class Footer extends Component {
  /**
   * @param {Object} [configuration]
   * @param {string} [configuration.brandName="Material Design"] - Main brand title.
   * @param {string} [configuration.brandDescription=""] - Brand narrative text.
   * @param {Array<FooterSocialLink>} [configuration.socialLinks=[]] - Social platform links.
   * @param {Array<FooterColumn>} [configuration.columns=[]] - Resource link columns.
   * @param {Array<FooterLegalLink>} [configuration.legalLinks=[]] - Bottom legal links.
   * @param {string} [configuration.copyrightText=""] - License and copyright statement.
   */
  constructor({
    brandName = "Material Design",
    brandDescription = "",
    socialLinks = [],
    columns = [],
    legalLinks = [],
    copyrightText = ""
  } = {}) {
    super();

    /** @type {string} */
    this.brandName = brandName;

    /** @type {string} */
    this.brandDescription = brandDescription;

    /** @type {Array<FooterSocialLink>} */
    this.socialLinks = Array.isArray(socialLinks) ? socialLinks : [];

    /** @type {Array<FooterColumn>} */
    this.columns = Array.isArray(columns) ? columns : [];

    /** @type {Array<FooterLegalLink>} */
    this.legalLinks = Array.isArray(legalLinks) ? legalLinks : [];

    /** @type {string} */
    this.copyrightText = copyrightText;

    /** @type {TemplateResult} */
    const socialLinksTemplate = html`
      <div class="app-footer__social-list" role="list" aria-label="Social Channels">
        ${this.socialLinks.map(socialItem => html`
          <a
            href="${socialItem.url}"
            class="app-footer__social-link"
            target="_blank"
            rel="noopener noreferrer"
            role="listitem"
            aria-label="${socialItem.platform_name}"
          >
            <span class="google-symbols app-footer__social-icon">${socialItem.icon_name}</span>
            <span>${socialItem.platform_name}</span>
          </a>
        `)}
      </div>
    `;

    /** @type {TemplateResult} */
    const columnsTemplate = html`
      <div class="app-footer__columns-grid" role="navigation" aria-label="Footer Navigation">
        ${this.columns.map(columnItem => html`
          <div class="app-footer__column">
            <h4 class="app-footer__column-heading">${columnItem.column_title}</h4>
            <ul class="app-footer__column-list" role="list">
              ${(columnItem.links || []).map(linkItem => html`
                <li role="listitem">
                  <a
                    href="${linkItem.url}"
                    class="app-footer__column-link"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    ${linkItem.label}
                  </a>
                </li>
              `)}
            </ul>
          </div>
        `)}
      </div>
    `;

    /** @type {TemplateResult} */
    const legalLinksTemplate = html`
      <div class="app-footer__legal-links" role="list" aria-label="Legal & Policies">
        ${this.legalLinks.map(legalItem => html`
          <a
            href="${legalItem.url}"
            class="app-footer__legal-link"
            target="_blank"
            rel="noopener noreferrer"
            role="listitem"
          >
            ${legalItem.label}
          </a>
        `)}
      </div>
    `;

    this.template = html`
      <footer class="app-footer" role="contentinfo" aria-label="Site Footer">
        <div class="app-footer__container">
          <!-- Row 1: Left Outro & Socials | Right Link Columns -->
          <div class="app-footer__main-row">
            <div class="app-footer__intro">
              <div class="app-footer__brand-wrap">
                <h3 class="app-footer__brand-title">${this.brandName}</h3>
                <p class="app-footer__brand-description">${this.brandDescription}</p>
              </div>
              ${socialLinksTemplate}
            </div>

            ${columnsTemplate}
          </div>

          <!-- Row 2: Legal Links & Copyright Bar -->
          <div class="app-footer__legal-bar">
            ${legalLinksTemplate}
            <p class="app-footer__copyright">${this.copyrightText}</p>
          </div>
        </div>
      </footer>
    `;
  }
}
