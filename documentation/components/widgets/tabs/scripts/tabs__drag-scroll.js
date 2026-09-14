import { isMobileViewport } from "./tabs__swipe-gesture.js";

/**
 * Attaches pointer-based horizontal drag-to-scroll interaction to a tab container.
 * @param {HTMLElement} scrollContainerElement - Container element to make scrollable.
 * @returns {function(): void} Cleanup event listener remover function.
 */
export function attachDragToScroll(scrollContainerElement) {
  if (!scrollContainerElement) {
    return () => {};
  }

  /** @type {boolean} */
  let isPointerActive = false;
  /** @type {boolean} */
  let hasDragged = false;
  /** @type {number} */
  let initialClientX = 0;
  /** @type {number} */
  let initialScrollPosition = 0;

  /**
   * @param {PointerEvent} pointerEvent
   * @returns {void}
   */
  const handlePointerDown = (pointerEvent) => {
    if (pointerEvent.pointerType === "mouse" && pointerEvent.button !== 0) {
      return;
    }
    if (isMobileViewport()) {
      return;
    }
    isPointerActive = true;
    hasDragged = false;
    initialClientX = pointerEvent.clientX;
    initialScrollPosition = scrollContainerElement.scrollLeft;
  };

  /**
   * @param {PointerEvent} pointerEvent
   * @returns {void}
   */
  const handlePointerMove = (pointerEvent) => {
    if (!isPointerActive) {
      return;
    }
    /** @type {number} */
    const horizontalDelta = pointerEvent.clientX - initialClientX;
    if (!hasDragged && Math.abs(horizontalDelta) > 5) {
      hasDragged = true;
      if (typeof scrollContainerElement.setPointerCapture === "function") {
        try {
          scrollContainerElement.setPointerCapture(pointerEvent.pointerId);
        } catch {
          // Fallback
        }
      }
    }
    if (hasDragged) {
      scrollContainerElement.scrollLeft = initialScrollPosition - horizontalDelta;
    }
  };

  /**
   * @param {PointerEvent} pointerEvent
   * @returns {void}
   */
  const handlePointerUp = (pointerEvent) => {
    if (!isPointerActive) {
      return;
    }
    isPointerActive = false;
    if (hasDragged && typeof scrollContainerElement.releasePointerCapture === "function") {
      try {
        if (scrollContainerElement.hasPointerCapture(pointerEvent.pointerId)) {
          scrollContainerElement.releasePointerCapture(pointerEvent.pointerId);
        }
      } catch {
        // Fallback
      }
    }
    hasDragged = false;
  };

  scrollContainerElement.addEventListener("pointerdown", handlePointerDown);
  scrollContainerElement.addEventListener("pointermove", handlePointerMove);
  scrollContainerElement.addEventListener("pointerup", handlePointerUp);
  scrollContainerElement.addEventListener("pointercancel", handlePointerUp);

  return () => {
    scrollContainerElement.removeEventListener("pointerdown", handlePointerDown);
    scrollContainerElement.removeEventListener("pointermove", handlePointerMove);
    scrollContainerElement.removeEventListener("pointerup", handlePointerUp);
    scrollContainerElement.removeEventListener("pointercancel", handlePointerUp);
  };
}

