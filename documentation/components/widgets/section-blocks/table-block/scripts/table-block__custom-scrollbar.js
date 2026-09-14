/**
 * @file table-block__custom-scrollbar.js
 * @description Synchronized custom scrollbar controller for mobile card list tables.
 */

/**
 * Attaches synchronized custom scrollbar thumb dragging, track clicking, and wrapper drag-to-scroll to a mobile table.
 * @param {HTMLElement} tableWrapper - Scrollable table wrapper element.
 * @param {HTMLElement} scrollbarTrack - Scrollbar track container element.
 * @param {HTMLElement} scrollbarThumb - Standing pill thumb element.
 * @returns {function(): void} Cleanup function removing attached event listeners and observers.
 */
export function attachTableCustomScrollbar(tableWrapper, scrollbarTrack, scrollbarThumb) {
  if (!tableWrapper || !scrollbarTrack || !scrollbarThumb) {
    return () => {};
  }

  /** @type {boolean} */
  let isThumbDragging = false;
  /** @type {number} */
  let thumbStartY = 0;
  /** @type {number} */
  let thumbStartScrollTop = 0;

  /** @type {boolean} */
  let isContentDragging = false;
  /** @type {number} */
  let contentStartY = 0;
  /** @type {number} */
  let contentStartScrollTop = 0;

  /**
   * Recalculates and positions the scrollbar thumb based on table scroll progress.
   * @returns {void}
   */
  const updateThumbPosition = () => {
    const scrollHeight = tableWrapper.scrollHeight;
    const clientHeight = tableWrapper.clientHeight;
    const maxScroll = scrollHeight - clientHeight;
    const trackHeight = scrollbarTrack.clientHeight || 380;
    const thumbHeight = scrollbarThumb.offsetHeight || 80;
    const maxThumbTravel = Math.max(0, trackHeight - thumbHeight);

    if (maxScroll <= 5) {
      scrollbarThumb.style.transform = "translate3d(0, 0px, 0)";
      scrollbarThumb.style.opacity = "0.35";
      scrollbarThumb.style.pointerEvents = "none";
      return;
    }

    scrollbarThumb.style.opacity = "1";
    scrollbarThumb.style.pointerEvents = "auto";
    const scrollRatio = Math.min(1, Math.max(0, tableWrapper.scrollTop / maxScroll));
    const thumbY = scrollRatio * maxThumbTravel;
    scrollbarThumb.style.transform = `translate3d(0, ${thumbY}px, 0)`;
  };

  /**
   * Handles table wrapper scroll event.
   * @returns {void}
   */
  const handleScroll = () => {
    if (!isThumbDragging) {
      requestAnimationFrame(updateThumbPosition);
    }
  };

  /**
   * @param {PointerEvent} pointerEvent
   * @returns {void}
   */
  const handleThumbPointerDown = (pointerEvent) => {
    if (pointerEvent.pointerType === "mouse" && pointerEvent.button !== 0) return;
    isThumbDragging = true;
    thumbStartY = pointerEvent.clientY;
    thumbStartScrollTop = tableWrapper.scrollTop;
    if (typeof scrollbarThumb.setPointerCapture === "function") {
      try {
        scrollbarThumb.setPointerCapture(pointerEvent.pointerId);
      } catch {
        // Fallback
      }
    }
    scrollbarThumb.classList.add("is-dragging");
    pointerEvent.preventDefault();
  };

  /**
   * @param {PointerEvent} pointerEvent
   * @returns {void}
   */
  const handleThumbPointerMove = (pointerEvent) => {
    if (!isThumbDragging) return;
    const deltaY = pointerEvent.clientY - thumbStartY;
    const scrollHeight = tableWrapper.scrollHeight;
    const clientHeight = tableWrapper.clientHeight;
    const maxScroll = scrollHeight - clientHeight;
    const trackHeight = scrollbarTrack.clientHeight || 380;
    const thumbHeight = scrollbarThumb.offsetHeight || 80;
    const maxThumbTravel = Math.max(1, trackHeight - thumbHeight);

    const scrollDelta = (deltaY / maxThumbTravel) * maxScroll;
    tableWrapper.scrollTop = Math.min(maxScroll, Math.max(0, thumbStartScrollTop + scrollDelta));
    updateThumbPosition();
  };

  /**
   * @param {PointerEvent} pointerEvent
   * @returns {void}
   */
  const handleThumbPointerUp = (pointerEvent) => {
    if (isThumbDragging) {
      isThumbDragging = false;
      scrollbarThumb.classList.remove("is-dragging");
      if (typeof scrollbarThumb.releasePointerCapture === "function") {
        try {
          scrollbarThumb.releasePointerCapture(pointerEvent.pointerId);
        } catch {
          // Fallback
        }
      }
    }
  };

  /**
   * @param {PointerEvent} pointerEvent
   * @returns {void}
   */
  const handleContentPointerDown = (pointerEvent) => {
    if (pointerEvent.pointerType === "mouse" && pointerEvent.button === 0) {
      isContentDragging = true;
      contentStartY = pointerEvent.clientY;
      contentStartScrollTop = tableWrapper.scrollTop;
    }
  };

  /**
   * @param {PointerEvent} pointerEvent
   * @returns {void}
   */
  const handleContentPointerMove = (pointerEvent) => {
    if (!isContentDragging) return;
    const deltaY = pointerEvent.clientY - contentStartY;
    if (Math.abs(deltaY) > 2) {
      tableWrapper.scrollTop = contentStartScrollTop - deltaY;
      updateThumbPosition();
    }
  };

  /**
   * @returns {void}
   */
  const handleContentPointerEnd = () => {
    if (isContentDragging) {
      isContentDragging = false;
    }
  };

  /**
   * @param {PointerEvent} pointerEvent
   * @returns {void}
   */
  const handleTrackClick = (pointerEvent) => {
    if (pointerEvent.target === scrollbarThumb) return;
    const rect = scrollbarTrack.getBoundingClientRect();
    const clickY = pointerEvent.clientY - rect.top;
    const thumbHeight = scrollbarThumb.offsetHeight || 80;
    const targetThumbY = clickY - (thumbHeight / 2);
    const trackHeight = scrollbarTrack.clientHeight || 380;
    const maxThumbTravel = Math.max(1, trackHeight - thumbHeight);
    const ratio = Math.min(1, Math.max(0, targetThumbY / maxThumbTravel));

    const maxScroll = tableWrapper.scrollHeight - tableWrapper.clientHeight;
    tableWrapper.scrollTo({ top: ratio * maxScroll, behavior: "smooth" });
  };

  tableWrapper.addEventListener("scroll", handleScroll, { passive: true });
  tableWrapper.addEventListener("pointerdown", handleContentPointerDown);
  window.addEventListener("pointermove", handleContentPointerMove);
  window.addEventListener("pointerup", handleContentPointerEnd);
  window.addEventListener("pointercancel", handleContentPointerEnd);

  scrollbarThumb.addEventListener("pointerdown", handleThumbPointerDown);
  scrollbarThumb.addEventListener("pointermove", handleThumbPointerMove);
  scrollbarThumb.addEventListener("pointerup", handleThumbPointerUp);
  scrollbarThumb.addEventListener("pointercancel", handleThumbPointerUp);
  scrollbarTrack.addEventListener("pointerdown", handleTrackClick);

  // ResizeObserver for dynamic container adjustments (tabs switching, font load, orientation change)
  /** @type {ResizeObserver|null} */
  let resizeObserver = null;
  if (typeof ResizeObserver !== "undefined") {
    resizeObserver = new ResizeObserver(() => {
      requestAnimationFrame(updateThumbPosition);
    });
    resizeObserver.observe(tableWrapper);
  }

  // Initial and deferred checks
  requestAnimationFrame(updateThumbPosition);
  setTimeout(updateThumbPosition, 100);
  setTimeout(updateThumbPosition, 400);

  return () => {
    tableWrapper.removeEventListener("scroll", handleScroll);
    tableWrapper.removeEventListener("pointerdown", handleContentPointerDown);
    window.removeEventListener("pointermove", handleContentPointerMove);
    window.removeEventListener("pointerup", handleContentPointerEnd);
    window.removeEventListener("pointercancel", handleContentPointerEnd);

    scrollbarThumb.removeEventListener("pointerdown", handleThumbPointerDown);
    scrollbarThumb.removeEventListener("pointermove", handleThumbPointerMove);
    scrollbarThumb.removeEventListener("pointerup", handleThumbPointerUp);
    scrollbarThumb.removeEventListener("pointercancel", handleThumbPointerUp);
    scrollbarTrack.removeEventListener("pointerdown", handleTrackClick);

    if (resizeObserver) {
      resizeObserver.disconnect();
    }
  };
}
