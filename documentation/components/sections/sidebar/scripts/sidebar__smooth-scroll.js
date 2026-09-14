/**
 * @file sidebar__smooth-scroll.js
 * @description Ultra-smooth inertial 60fps/120fps momentum scroll engine for the sidebar viewport.
 */

/**
 * Attaches fluid momentum lerp (linear interpolation) smooth wheel scrolling to the sidebar viewport.
 * @param {HTMLElement} viewportElement - The scrollable sidebar content container.
 * @returns {function(): void} Cleanup function to remove event listeners.
 */
export function attachSmoothScroll(viewportElement) {
  if (!viewportElement) {
    return () => {};
  }

  let targetY = viewportElement.scrollTop;
  let currentY = viewportElement.scrollTop;
  let isAnimating = false;
  let animationFrameId = null;

  // 0.09 provides an ultra-silky, luxurious deceleration curve with zero stutter
  const EASING = 0.09;

  /**
   * Animation frame loop with sub-pixel interpolation.
   */
  const step = () => {
    const diff = targetY - currentY;

    if (Math.abs(diff) < 0.25) {
      currentY = targetY;
      viewportElement.scrollTop = Math.round(currentY);
      isAnimating = false;
      return;
    }

    currentY += diff * EASING;
    viewportElement.scrollTop = currentY;
    animationFrameId = requestAnimationFrame(step);
  };

  /**
   * Intercepts mouse wheel ticks and converts them into continuous momentum easing.
   * @param {WheelEvent} wheelEvent
   */
  const handleWheel = (wheelEvent) => {
    // Allow standard browser zoom with Ctrl + Wheel
    if (wheelEvent.ctrlKey || wheelEvent.metaKey) {
      return;
    }

    // Ignore horizontal scrolling (Shift + Wheel)
    if (wheelEvent.shiftKey || Math.abs(wheelEvent.deltaX) > Math.abs(wheelEvent.deltaY)) {
      return;
    }

    const maxScroll = viewportElement.scrollHeight - viewportElement.clientHeight;
    if (maxScroll <= 0) {
      return;
    }

    // Normalize wheel delta across delta modes
    let delta = wheelEvent.deltaY;
    if (wheelEvent.deltaMode === 1) {
      // Lines mode (Firefox default for stepped wheels)
      delta *= 35;
    } else if (wheelEvent.deltaMode === 2) {
      // Pages mode
      delta *= viewportElement.clientHeight;
    }

    // Accumulate target scroll with clamping
    const nextTarget = Math.max(0, Math.min(maxScroll, targetY + delta));

    // If already at scroll bounds, do not prevent default to allow natural boundary feel
    if (nextTarget === targetY && (targetY === 0 || targetY === maxScroll)) {
      return;
    }

    wheelEvent.preventDefault();
    targetY = nextTarget;

    if (!isAnimating) {
      currentY = viewportElement.scrollTop;
      isAnimating = true;
      animationFrameId = requestAnimationFrame(step);
    }
  };

  /**
   * Resyncs coordinates when element scrolls natively (e.g. keyboard navigation or drag).
   */
  const handleNativeScroll = () => {
    if (!isAnimating) {
      currentY = viewportElement.scrollTop;
      targetY = viewportElement.scrollTop;
    }
  };

  viewportElement.addEventListener("wheel", handleWheel, { passive: false });
  viewportElement.addEventListener("scroll", handleNativeScroll, { passive: true });

  return () => {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
    }
    viewportElement.removeEventListener("wheel", handleWheel);
    viewportElement.removeEventListener("scroll", handleNativeScroll);
  };
}
