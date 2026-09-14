/**
 * ImageScale — Enumeration of supported card image container height presets.
 * Used by Card to control the aspect ratio and vertical weight of the image area.
 *
 * @enum {string}
 */
export const ImageScale = Object.freeze({
  /** 200px image container height — compact card format. */
  SMALL: "small",
  /** 300px image container height — standard card format (default). */
  MEDIUM: "medium"
});
