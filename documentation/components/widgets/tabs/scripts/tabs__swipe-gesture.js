/**
 * @file tabs__swipe-gesture.js
 * @description Mobile tab carousel swipe, touch, and pointer drag gesture controller with 1:1 follow-finger translation and velocity snap.
 */

/**
 * Checks if the current viewport is in mobile or portrait mode.
 * @returns {boolean} True if screen width is <= 768px or orientation is portrait.
 */
export function isMobileViewport() {
  if (typeof window === "undefined") {
    return false;
  }
  const isMobileLayout =
    window.innerWidth <= 768 ||
    window.matchMedia("(orientation: portrait)").matches ||
    (window.matchMedia("(orientation: landscape)").matches && window.innerHeight <= 550);
  if (isMobileLayout) {
    return true;
  }
  const carouselPreviousButton = document.querySelector(".tabs__carousel-button--previous");
  if (carouselPreviousButton && window.getComputedStyle(carouselPreviousButton).display !== "none") {
    return true;
  }
  return false;
}

/**
 * Attaches touch and pointer swipe gesture tracking to the mobile tab track container.
 * @param {Object} configuration
 * @param {HTMLElement} configuration.trackElement - Track container element housing tab items.
 * @param {function(): number} configuration.getActiveIndex - Getter returning current active tab index.
 * @param {function(number, "previous"|"next"|"none"): void} configuration.onActivateIndex - Callback to switch active tab index.
 * @returns {function(): void} Cleanup function removing all attached event listeners.
 */
export function attachTabsSwipeGesture({ trackElement, getActiveIndex, onActivateIndex }) {
  if (!trackElement) {
    return () => {};
  }

  /** @type {number} */
  let touchStartX = 0;
  /** @type {number} */
  let touchStartY = 0;
  /** @type {number} */
  let touchStartTime = 0;
  /** @type {boolean} */
  let isDraggingGesture = false;
  /** @type {boolean} */
  let isTransitionAnimating = false;
  /** @type {number|null} */
  let activePointerIdentifier = null;

  /** @type {HTMLElement|null} */
  let activeTabElement = null;
  /** @type {HTMLElement|null} */
  let nextTabElement = null;
  /** @type {HTMLElement|null} */
  let previousTabElement = null;
  /** @type {Array<HTMLElement>} */
  let allTabElements = [];
  /** @type {number} */
  let nextTabIndex = -1;
  /** @type {number} */
  let previousTabIndex = -1;

  /**
   * Resets temporary inline drag styling on all tab elements.
   * @returns {void}
   */
  const cleanupDragStyles = () => {
    allTabElements.forEach((tabItemElement, elementIndex) => {
      tabItemElement.style.position = "";
      tabItemElement.style.width = "";
      tabItemElement.style.height = "";
      tabItemElement.style.left = "";
      tabItemElement.style.top = "";
      tabItemElement.style.transform = "";
      tabItemElement.style.transition = "";
      tabItemElement.style.display = "";
      tabItemElement.style.zIndex = "";
      const currentActiveIndex = getActiveIndex();
      if (elementIndex === currentActiveIndex) {
        tabItemElement.classList.add("tabs__item--active");
      } else {
        tabItemElement.classList.remove("tabs__item--active");
      }
    });

    isDraggingGesture = false;
    activeTabElement = null;
    nextTabElement = null;
    previousTabElement = null;
    activePointerIdentifier = null;
  };

  /**
   * Initiates touch or pointer drag sequence.
   * @param {number} clientX - Current X coordinate.
   * @param {number} clientY - Current Y coordinate.
   * @param {number|null} [pointerIdentifier=null] - Pointer identifier.
   * @returns {boolean} True if drag sequence initiated.
   */
  const handleGestureStart = (clientX, clientY, pointerIdentifier = null) => {
    if (!isMobileViewport()) {
      return false;
    }
    if (isTransitionAnimating) {
      return false;
    }

    allTabElements = Array.from(trackElement.querySelectorAll(".tabs__item"));
    if (allTabElements.length <= 1) {
      return false;
    }

    const currentActiveIndex = getActiveIndex();
    touchStartX = clientX;
    touchStartY = clientY;
    touchStartTime = Date.now();
    isDraggingGesture = false;
    activePointerIdentifier = pointerIdentifier;

    activeTabElement = allTabElements[currentActiveIndex] || trackElement.querySelector(".tabs__item--active") || allTabElements[0];
    nextTabIndex = (currentActiveIndex + 1) % allTabElements.length;
    previousTabIndex = (currentActiveIndex - 1 + allTabElements.length) % allTabElements.length;
    nextTabElement = allTabElements[nextTabIndex];
    previousTabElement = allTabElements[previousTabIndex];
    return true;
  };

  /**
   * Performs 1:1 real-time translation following pointer movement.
   * @param {number} clientX - Current X coordinate.
   * @param {number} clientY - Current Y coordinate.
   * @returns {void}
   */
  const handleGestureMove = (clientX, clientY) => {
    if (!activeTabElement || isTransitionAnimating) {
      return;
    }

    const horizontalDelta = clientX - touchStartX;

    if (!isDraggingGesture) {
      if (Math.abs(horizontalDelta) > 4) {
        isDraggingGesture = true;
      } else {
        return;
      }
    }

    activeTabElement.style.position = "absolute";
    activeTabElement.style.width = "100%";
    activeTabElement.style.height = "100%";
    activeTabElement.style.left = "0";
    activeTabElement.style.top = "0";
    activeTabElement.style.display = "inline-flex";
    activeTabElement.style.transition = "none";
    activeTabElement.style.transform = `translate3d(${horizontalDelta}px, 0, 0)`;
    activeTabElement.style.zIndex = "2";

    if (horizontalDelta < 0) {
      // Dragging left: next tab enters from right
      if (previousTabElement && previousTabElement !== nextTabElement) {
        previousTabElement.style.display = "none";
      }
      if (nextTabElement) {
        nextTabElement.style.position = "absolute";
        nextTabElement.style.width = "100%";
        nextTabElement.style.height = "100%";
        nextTabElement.style.left = "0";
        nextTabElement.style.top = "0";
        nextTabElement.style.display = "inline-flex";
        nextTabElement.style.transition = "none";
        nextTabElement.style.transform = `translate3d(calc(100% + ${horizontalDelta}px), 0, 0)`;
        nextTabElement.style.zIndex = "1";
      }
    } else if (horizontalDelta > 0) {
      // Dragging right: previous tab enters from left
      if (nextTabElement && nextTabElement !== previousTabElement) {
        nextTabElement.style.display = "none";
      }
      if (previousTabElement) {
        previousTabElement.style.position = "absolute";
        previousTabElement.style.width = "100%";
        previousTabElement.style.height = "100%";
        previousTabElement.style.left = "0";
        previousTabElement.style.top = "0";
        previousTabElement.style.display = "inline-flex";
        previousTabElement.style.transition = "none";
        previousTabElement.style.transform = `translate3d(calc(-100% + ${horizontalDelta}px), 0, 0)`;
        previousTabElement.style.zIndex = "1";
      }
    } else {
      if (nextTabElement && nextTabElement !== activeTabElement) nextTabElement.style.display = "none";
      if (previousTabElement && previousTabElement !== activeTabElement) previousTabElement.style.display = "none";
    }
  };

  /**
   * Snaps to next or previous tab based on velocity and displacement threshold.
   * @param {number} clientX - Final X coordinate.
   * @returns {void}
   */
  const handleGestureEnd = (clientX) => {
    if (!activeTabElement) {
      cleanupDragStyles();
      return;
    }

    if (!isDraggingGesture) {
      cleanupDragStyles();
      return;
    }

    if (typeof window !== "undefined") {
      window.__tabJustDragged = true;
      setTimeout(() => {
        window.__tabJustDragged = false;
      }, 250);
    }

    const horizontalDelta = clientX - touchStartX;
    const elapsedTime = Math.max(1, Date.now() - touchStartTime);
    const swipeVelocity = Math.abs(horizontalDelta) / elapsedTime;
    const trackWidth = trackElement.offsetWidth || 260;
    const displacementThreshold = trackWidth * 0.28;
    const isQuickSwipeGesture = swipeVelocity > 0.28 && Math.abs(horizontalDelta) > 15;

    const snapToNextTab = horizontalDelta < -displacementThreshold || (isQuickSwipeGesture && horizontalDelta < 0);
    const snapToPreviousTab = horizontalDelta > displacementThreshold || (isQuickSwipeGesture && horizontalDelta > 0);

    isTransitionAnimating = true;

    if (snapToNextTab && nextTabElement) {
      activeTabElement.style.transition = "transform 0.22s cubic-bezier(0.2, 0.9, 0.3, 1)";
      nextTabElement.style.transition = "transform 0.22s cubic-bezier(0.2, 0.9, 0.3, 1)";
      activeTabElement.style.transform = "translate3d(-100%, 0, 0)";
      nextTabElement.style.transform = "translate3d(0, 0, 0)";

      setTimeout(() => {
        cleanupDragStyles();
        isTransitionAnimating = false;
        if (typeof onActivateIndex === "function") {
          onActivateIndex(nextTabIndex, "none");
        }
      }, 220);
    } else if (snapToPreviousTab && previousTabElement) {
      activeTabElement.style.transition = "transform 0.22s cubic-bezier(0.2, 0.9, 0.3, 1)";
      previousTabElement.style.transition = "transform 0.22s cubic-bezier(0.2, 0.9, 0.3, 1)";
      activeTabElement.style.transform = "translate3d(100%, 0, 0)";
      previousTabElement.style.transform = "translate3d(0, 0, 0)";

      setTimeout(() => {
        cleanupDragStyles();
        isTransitionAnimating = false;
        if (typeof onActivateIndex === "function") {
          onActivateIndex(previousTabIndex, "none");
        }
      }, 220);
    } else {
      activeTabElement.style.transition = "transform 0.2s cubic-bezier(0.2, 0.9, 0.3, 1)";
      activeTabElement.style.transform = "translate3d(0, 0, 0)";

      if (horizontalDelta < 0 && nextTabElement) {
        nextTabElement.style.transition = "transform 0.2s cubic-bezier(0.2, 0.9, 0.3, 1)";
        nextTabElement.style.transform = "translate3d(100%, 0, 0)";
      } else if (horizontalDelta > 0 && previousTabElement) {
        previousTabElement.style.transition = "transform 0.2s cubic-bezier(0.2, 0.9, 0.3, 1)";
        previousTabElement.style.transform = "translate3d(-100%, 0, 0)";
      }

      setTimeout(() => {
        cleanupDragStyles();
        isTransitionAnimating = false;
      }, 200);
    }
  };

  /**
   * @param {PointerEvent} pointerEvent
   */
  const onPointerDown = (pointerEvent) => {
    if (pointerEvent.pointerType === "mouse" && pointerEvent.button !== 0) {
      return;
    }
    const started = handleGestureStart(pointerEvent.clientX, pointerEvent.clientY, pointerEvent.pointerId);
    if (started && typeof trackElement.setPointerCapture === "function") {
      try {
        trackElement.setPointerCapture(pointerEvent.pointerId);
      } catch {
        // Ignored
      }
    }
  };

  /**
   * @param {PointerEvent} pointerEvent
   */
  const onPointerMove = (pointerEvent) => {
    if (activePointerIdentifier !== null && pointerEvent.pointerId !== activePointerIdentifier) {
      return;
    }
    handleGestureMove(pointerEvent.clientX, pointerEvent.clientY);
  };

  /**
   * @param {PointerEvent} pointerEvent
   */
  const onPointerUp = (pointerEvent) => {
    if (activePointerIdentifier !== null && pointerEvent.pointerId !== activePointerIdentifier) {
      return;
    }
    if (typeof trackElement.releasePointerCapture === "function") {
      try {
        trackElement.releasePointerCapture(pointerEvent.pointerId);
      } catch {
        // Ignored
      }
    }
    handleGestureEnd(pointerEvent.clientX);
  };

  /**
   * @param {PointerEvent} pointerEvent
   */
  const onPointerCancel = (pointerEvent) => {
    if (activePointerIdentifier !== null && pointerEvent.pointerId !== activePointerIdentifier) {
      return;
    }
    cleanupDragStyles();
    isTransitionAnimating = false;
  };

  /**
   * @param {TouchEvent} touchEvent
   */
  const onTouchStart = (touchEvent) => {
    if (activePointerIdentifier !== null) return;
    if (!touchEvent.touches || touchEvent.touches.length !== 1) return;
    handleGestureStart(touchEvent.touches[0].clientX, touchEvent.touches[0].clientY);
  };

  /**
   * @param {TouchEvent} touchEvent
   */
  const onTouchMove = (touchEvent) => {
    if (activePointerIdentifier !== null) return;
    if (!touchEvent.touches || touchEvent.touches.length !== 1) return;
    if (isDraggingGesture && touchEvent.cancelable) {
      touchEvent.preventDefault();
    }
    handleGestureMove(touchEvent.touches[0].clientX, touchEvent.touches[0].clientY);
  };

  /**
   * @param {TouchEvent} touchEvent
   */
  const onTouchEnd = (touchEvent) => {
    if (activePointerIdentifier !== null) return;
    const touch = touchEvent.changedTouches && touchEvent.changedTouches[0];
    handleGestureEnd(touch ? touch.clientX : touchStartX);
  };

  /**
   * @param {TouchEvent} touchEvent
   */
  const onTouchCancel = () => {
    if (activePointerIdentifier !== null) return;
    cleanupDragStyles();
    isTransitionAnimating = false;
  };

  trackElement.addEventListener("pointerdown", onPointerDown);
  trackElement.addEventListener("pointermove", onPointerMove);
  trackElement.addEventListener("pointerup", onPointerUp);
  trackElement.addEventListener("pointercancel", onPointerCancel);

  trackElement.addEventListener("touchstart", onTouchStart, { passive: true });
  trackElement.addEventListener("touchmove", onTouchMove, { passive: false });
  trackElement.addEventListener("touchend", onTouchEnd, { passive: true });
  trackElement.addEventListener("touchcancel", onTouchCancel, { passive: true });

  return () => {
    trackElement.removeEventListener("pointerdown", onPointerDown);
    trackElement.removeEventListener("pointermove", onPointerMove);
    trackElement.removeEventListener("pointerup", onPointerUp);
    trackElement.removeEventListener("pointercancel", onPointerCancel);

    trackElement.removeEventListener("touchstart", onTouchStart);
    trackElement.removeEventListener("touchmove", onTouchMove);
    trackElement.removeEventListener("touchend", onTouchEnd);
    trackElement.removeEventListener("touchcancel", onTouchCancel);
  };
}
