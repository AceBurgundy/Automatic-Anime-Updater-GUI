/**
 * @file Component.js
 * @description Zero-dependency, ultra-secure, single-file JavaScript SPA reactive engine.
 */

/** @type {Record<string, typeof Component>} */
const routes = {};

/** @type {Array<Promise<string>>} */
const pendingCssLoads = [];

/** @type {Array<Component>} */
const pendingMounts = [];

/** @type {Array<Component>} */
let activeComponents = [];

/** @type {boolean} */
let shouldQueueMounts = false;

/** @type {number} */
let renderVersion = 0;

/** @type {string} */
let applicationBasePath = "";

/**
 * Sets the base path for client-side routing.
 * @param {string} basePath - The base path prefix (e.g. "/sub-app").
 * @returns {void}
 */
export function setBasePath(basePath) {
  applicationBasePath = basePath.endsWith("/") ? basePath.slice(0, -1) : basePath;
}

/**
 * Generates a random alphanumeric unique identifier string.
 * @returns {string} The generated unique identifier.
 */
const uniqueIdentifier = () => Math.random().toString(36).substring(2, 10);

/**
 * Marker class for explicitly trusted HTML markup.
 */
export class TrustedHTMLString {
  /**
   * @param {string} value - The trusted HTML string content.
   */
  constructor(value) {
    /** @type {string} */
    this.value = value;
  }

  /**
   * Returns the trusted HTML string.
   * @returns {string}
   */
  toString() {
    return this.value;
  }
}

/**
 * Marks a string as explicitly trusted HTML markup.
 * @param {string} markup - Raw HTML markup string.
 * @returns {TrustedHTMLString}
 */
export const raw = markup => new TrustedHTMLString(markup);

/**
 * CSP nonce captured at module evaluation time.
 * @type {string}
 */
const CSP_NONCE = document.currentScript?.nonce
  ?? document.querySelector("script[nonce]")?.nonce
  ?? "";

/**
 * Idempotent and compatibility-verified TrustedTypes policy.
 * @type {TrustedTypePolicy|null}
 */
const trustedTypesPolicy = (() => {
  if (!window.trustedTypes?.createPolicy) {
    return null;
  }
  try {
    return window.trustedTypes.createPolicy("lite-spa-policy", {
      /**
       * @param {string} htmlString - Raw HTML string to pass through.
       * @returns {string}
       */
      createHTML: htmlString => htmlString
    });
  } catch {
    /** @type {TrustedTypePolicy|undefined} */
    const existingPolicy = window.trustedTypes.getPolicy?.("lite-spa-policy");
    if (existingPolicy) {
      try {
        existingPolicy.createHTML("<b>test</b>");
        return existingPolicy;
      } catch {
        console.error("[lite-spa] Existing 'lite-spa-policy' is incompatible with pass-through.");
        return null;
      }
    }
    return null;
  }
})();

/**
 * Escapes unsafe characters in a string for safe HTML interpolation.
 * @param {string} unsafeString - The raw string to escape.
 * @returns {string} The escaped HTML string.
 */
function escapeHtml(unsafeString) {
  return String(unsafeString)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * Deep-sanitizes and freezes an object against prototype pollution.
 * @template T
 * @param {T} targetObject - The object to sanitize and freeze.
 * @returns {T} The sanitized, frozen object.
 */
export function sanitizeAndFreeze(targetObject) {
  if (targetObject === null || typeof targetObject !== "object") {
    return targetObject;
  }
  Object.getOwnPropertyNames(targetObject).forEach(propertyKey => {
    if (propertyKey === "__proto__" || propertyKey === "constructor" || propertyKey === "prototype") {
      delete targetObject[propertyKey];
    } else {
      sanitizeAndFreeze(targetObject[propertyKey]);
    }
  });
  return Object.freeze(targetObject);
}

/**
 * Calls Document.prototype.getElementById directly to prevent DOM clobbering.
 * @param {string} elementIdentifier - The element ID to look up.
 * @returns {HTMLElement|null} The matching element or null.
 */
export function safeGetElementById(elementIdentifier) {
  return Document.prototype.getElementById.call(document, elementIdentifier);
}

/**
 * Normalizes and sanitizes a URL path against open redirects.
 * @param {string} rawPath - The raw URL path string.
 * @returns {string} The safe, normalized path string.
 */
export function sanitizeRoutePath(rawPath) {
  if (typeof rawPath !== "string") {
    return "/";
  }
  /** @type {string} */
  let cleanPath = rawPath.trim();
  if (cleanPath.startsWith("javascript:") || cleanPath.startsWith("data:") || cleanPath.startsWith("vbscript:")) {
    return "/";
  }
  if (cleanPath.startsWith("//") || cleanPath.startsWith("\\/")) {
    return "/";
  }
  if (applicationBasePath && cleanPath.startsWith(applicationBasePath)) {
    cleanPath = cleanPath.slice(applicationBasePath.length);
  }
  if (!cleanPath.startsWith("/")) {
    cleanPath = "/" + cleanPath;
  }
  return cleanPath;
}

/**
 * @typedef {Object} CompiledTemplateSlot
 * @property {number} index - Index of interpolated value.
 * @property {string} type - "attribute" or "content" or "rcdata".
 * @property {string} [attributeName] - Name of attribute if slot is in an attribute.
 * @property {string} [elementTag] - Tag name of element if slot is in RCDATA element.
 */

/**
 * @typedef {Object} CompiledTemplate
 * @property {string} htmlMarkup - Pre-processed HTML markup containing anchor markers.
 * @property {Array<CompiledTemplateSlot>} slots - Metadata for interpolated slots.
 */

/** @type {WeakMap<TemplateStringsArray, CompiledTemplate>} */
const templateCache = new WeakMap();

/**
 * Compiles a static template strings array into markup with slot anchor markers.
 * @param {TemplateStringsArray} templateStrings - The raw template strings.
 * @returns {CompiledTemplate}
 */
function compileTemplate(templateStrings) {
  /** @type {Array<CompiledTemplateSlot>} */
  const slots = [];
  /** @type {string} */
  let combinedMarkup = "";

  for (let index = 0; index < templateStrings.length; index++) {
    combinedMarkup += templateStrings[index];
    if (index < templateStrings.length - 1) {
      /** @type {string} */
      const precedingChunk = combinedMarkup;
      /** @type {RegExpMatchArray|null} */
      const attrMatch = precedingChunk.match(/<[^>]*\b([a-zA-Z0-9_-]+)\s*=\s*['"]?$/s);
      /** @type {boolean} */
      const isInRcdata = /<(textarea|style|script|title)[^>]*>[^<]*$/i.test(precedingChunk);

      if (isInRcdata) {
        slots.push({ index, type: "rcdata" });
        combinedMarkup += `__LITE_SLOT_RCDATA_${index}__`;
      } else if (attrMatch) {
        /** @type {string} */
        const attributeName = attrMatch[1];
        slots.push({ index, type: "attribute", attributeName });
        combinedMarkup += `__LITE_SLOT_ATTR_${index}__`;
      } else {
        slots.push({ index, type: "content" });
        combinedMarkup += `<!--lite-slot-start-${index}--><!--lite-slot-end-${index}-->`;
      }
    }
  }

  return { htmlMarkup: combinedMarkup, slots };
}

/**
 * Sanitizes an interpolated value according to strict type-gate rules.
 * @param {unknown} value - The value to sanitize.
 * @returns {string} Safe HTML string for template insertion.
 */
/** @type {Map<string, Signal<unknown>>} */
const activeSignalBindings = new Map();

/** @type {Map<string, { eventName: string, handler: EventListener }>} */
const activeEventBindings = new Map();

/**
 * Sanitizes an interpolated value according to strict type-gate rules.
 * @param {unknown} value - The value to sanitize.
 * @returns {string} Safe HTML string for template insertion.
 */
function sanitizeTemplateValue(value) {
  if (value instanceof TrustedHTMLString) {
    return value.value;
  }
  if (value instanceof TemplateResult) {
    return renderTemplateResultToString(value);
  }
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "string") {
    return escapeHtml(value);
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.map(sanitizeTemplateValue).join("");
  }
  if (isSignal(value)) {
    return createDomBindingMarker(value);
  }
  if (value instanceof Redirect || value instanceof Component) {
    return String(value);
  }
  if (typeof value === "object" && typeof value.toString === "function" && value.toString !== Object.prototype.toString) {
    return String(value);
  }
  return escapeHtml(Object.prototype.toString.call(value));
}

/**
 * Result object produced by the html tagged template literal.
 */
export class TemplateResult {
  /**
   * @param {CompiledTemplate} compiled - The compiled template metadata.
   * @param {Array<unknown>} values - The interpolated dynamic values.
   */
  constructor(compiled, values) {
    /** @type {CompiledTemplate} */
    this.compiled = compiled;
    /** @type {Array<unknown>} */
    this.values = values;
  }

  /**
   * Converts the template result to an HTML string.
   * @returns {string}
   */
  toString() {
    return renderTemplateResultToString(this);
  }
}

/**
 * Renders a TemplateResult instance to a fully sanitized HTML string.
 * @param {TemplateResult} templateResult - The template result to render.
 * @returns {string}
 */
function renderTemplateResultToString(templateResult) {
  /** @type {string} */
  let renderedOutput = templateResult.compiled.htmlMarkup;

  templateResult.compiled.slots.forEach(slot => {
    /** @type {unknown} */
    const dynamicValue = templateResult.values[slot.index];

    if (slot.type === "attribute") {
      /** @type {string} */
      const attrName = slot.attributeName ?? "";
      /** @type {boolean} */
      const isEventHandler = attrName.startsWith("on") && typeof dynamicValue === "function";

      if (isEventHandler) {
        /** @type {string} */
        const eventName = attrName.slice(2).toLowerCase();
        /** @type {string} */
        const eventToken = uniqueIdentifier();
        activeEventBindings.set(eventToken, { eventName, handler: /** @type {EventListener} */ (dynamicValue) });

        /** @type {RegExp} */
        const attrPattern = new RegExp(`\\b${attrName}\\s*=\\s*['"]?__LITE_SLOT_ATTR_${slot.index}__['"]?`);
        renderedOutput = renderedOutput.replace(attrPattern, `data-lite-evt="${eventToken}"`);
      } else {
        /** @type {string} */
        const sanitizedReplacement = sanitizeTemplateValue(dynamicValue);
        renderedOutput = renderedOutput.replace(`__LITE_SLOT_ATTR_${slot.index}__`, sanitizedReplacement);
      }
    } else if (slot.type === "rcdata") {
      /** @type {string} */
      const sanitizedReplacement = sanitizeTemplateValue(dynamicValue);
      renderedOutput = renderedOutput.replace(`__LITE_SLOT_RCDATA_${slot.index}__`, sanitizedReplacement);
    } else {
      /** @type {string} */
      const sanitizedReplacement = sanitizeTemplateValue(dynamicValue);
      /** @type {string} */
      const startMarker = `<!--lite-slot-start-${slot.index}-->`;
      /** @type {string} */
      const endMarker = `<!--lite-slot-end-${slot.index}-->`;
      renderedOutput = renderedOutput.replace(
        startMarker + endMarker,
        `${startMarker}${sanitizedReplacement}${endMarker}`
      );
    }
  });

  return renderedOutput;
}

/**
 * Tagged template function for constructing secure HTML markup.
 * @param {TemplateStringsArray} strings - Static template string chunks.
 * @param {...unknown} values - Dynamic interpolated values.
 * @returns {TemplateResult}
 */
export function html(strings, ...values) {
  /** @type {CompiledTemplate|undefined} */
  let compiled = templateCache.get(strings);
  if (!compiled) {
    compiled = compileTemplate(strings);
    templateCache.set(strings, compiled);
  }
  return new TemplateResult(compiled, values);
}

/**
 * Bridges a Promise to a reactive signal with a fallback placeholder.
 * @template T
 * @param {Promise<T>} promise - The promise to resolve.
 * @param {unknown} [placeholder=""] - Placeholder content shown while pending.
 * @returns {Signal<T|typeof placeholder>}
 */
export function until(promise, placeholder = "") {
  /** @type {Signal<T|typeof placeholder>} */
  const resultSignal = signal(placeholder);
  promise.then(
    resolvedValue => {
      resultSignal.value = resolvedValue;
    },
    rejectionError => {
      console.error("[lite-spa] until() promise rejected:", rejectionError);
    }
  );
  return resultSignal;
}

/** @type {WeakMap<Comment, WeakRef<Signal<unknown>>>} */
const domBindingRegistry = new WeakMap();

/**
 * Creates a comment marker in the DOM for reactive signal binding without memory cycles.
 * @param {Signal<unknown>} targetSignal - The signal to bind.
 * @returns {string}
 */
/**
 * Creates a comment marker in the DOM for reactive signal binding without memory cycles.
 * @param {Signal<unknown>} targetSignal - The signal to bind.
 * @returns {string}
 */
function createDomBindingMarker(targetSignal) {
  /** @type {string} */
  const slotIdentifier = uniqueIdentifier();
  activeSignalBindings.set(slotIdentifier, targetSignal);
  return `<!--lite-signal-slot-${slotIdentifier}-->${targetSignal.value}<!--lite-signal-slot-end-${slotIdentifier}-->`;
}

/**
 * Hydrates and binds comment markers to active signals within a container element.
 * @param {HTMLElement|Document} containerElement - Root DOM container.
 * @returns {Array<function(): void>} Array of unsubscribe cleanup functions.
 */
function hydrateSignalBindings(containerElement) {
  if (!containerElement || typeof document === "undefined") {
    return [];
  }
  /** @type {Array<function(): void>} */
  const cleanupFunctions = [];

  // 1. Hydrate Signal Comment Bindings
  /** @type {TreeWalker} */
  const walker = document.createTreeWalker(containerElement, NodeFilter.SHOW_COMMENT);
  /** @type {Array<Comment>} */
  const commentsToProcess = [];
  while (walker.nextNode()) {
    commentsToProcess.push(/** @type {Comment} */ (walker.currentNode));
  }

  commentsToProcess.forEach(commentNode => {
    /** @type {RegExpMatchArray|null} */
    const match = commentNode.nodeValue?.match(/^lite-signal-slot-([a-zA-Z0-9_-]+)$/) ?? null;
    if (!match) {
      return;
    }
    /** @type {string} */
    const slotId = match[1];
    /** @type {Signal<unknown>|undefined} */
    const boundSignal = activeSignalBindings.get(slotId);
    if (!boundSignal) {
      return;
    }

    /** @type {ChildNode|null} */
    const textNode = commentNode.nextSibling;
    if (textNode && textNode.nodeType === Node.TEXT_NODE) {
      const updateTextNode = () => {
        textNode.nodeValue = String(boundSignal.value);
      };
      const unsubscribe = boundSignal.subscribe(updateTextNode);
      cleanupFunctions.push(unsubscribe);
    }
  });

  // 2. Hydrate Direct Event Listeners (onclick=${fn}, @click=${fn})
  /** @type {NodeListOf<HTMLElement>} */
  const eventElements = containerElement.querySelectorAll("[data-lite-evt]");
  eventElements.forEach(elementNode => {
    /** @type {string|null} */
    const eventToken = elementNode.getAttribute("data-lite-evt");
    if (!eventToken) {
      return;
    }
    const binding = activeEventBindings.get(eventToken);
    if (!binding) {
      return;
    }

    elementNode.addEventListener(binding.eventName, binding.handler);
    cleanupFunctions.push(() => {
      elementNode.removeEventListener(binding.eventName, binding.handler);
      activeEventBindings.delete(eventToken);
    });
  });

  return cleanupFunctions;
}

/**
 * Checks if a value is a reactive signal object.
 * @param {unknown} value - Value to test.
 * @returns {boolean}
 */
function isSignal(value) {
  return value !== null && typeof value === "object" && typeof value.subscribe === "function" && "value" in value;
}

/** @type {Set<Function>} */
const pendingEffects = new Set();
/** @type {boolean} */
let flushScheduled = false;

/**
 * Schedules an effect callback for execution in the next microtask checkpoint.
 * @param {Function} effectFunction - The effect to schedule.
 * @returns {void}
 */
function scheduleEffect(effectFunction) {
  pendingEffects.add(effectFunction);
  if (!flushScheduled) {
    flushScheduled = true;
    Promise.resolve().then(flushEffects);
  }
}

/**
 * Flushes and executes all scheduled effects in the queue.
 * @returns {void}
 */
function flushEffects() {
  flushScheduled = false;
  /** @type {Array<Function>} */
  const effectsToExecute = [...pendingEffects];
  pendingEffects.clear();
  effectsToExecute.forEach(effectFunction => runEffect(effectFunction));
}

/** @type {Set<Function>} */
const runningEffects = new Set();
/** @type {Function|null} */
let activeEffect = null;

/**
 * Executes an effect with circular dependency protection and strict activeEffect restoration.
 * @param {Function} effectFunction - The effect function to execute.
 * @returns {void}
 */
function runEffect(effectFunction) {
  if (runningEffects.has(effectFunction)) {
    console.error("[lite-spa] Circular dependency detected. Aborting re-entrant effect execution:", effectFunction);
    return;
  }

  // Phase 1: Isolated cleanup of prior subscriptions
  try {
    effectFunction.registeredInSets?.forEach(subscriberSet => subscriberSet.delete(effectFunction));
    effectFunction.registeredInSets?.clear();
    if (typeof effectFunction._cleanup === "function") {
      effectFunction._cleanup();
      effectFunction._cleanup = null;
    }
  } catch (cleanupError) {
    console.error("[lite-spa] Effect cleanup error:", cleanupError);
  }

  // Phase 2: Execution with activeEffect stack restoration
  runningEffects.add(effectFunction);
  /** @type {Function|null} */
  const previousEffect = activeEffect;
  try {
    activeEffect = effectFunction;
    /** @type {unknown} */
    const cleanupReturn = effectFunction();
    if (typeof cleanupReturn === "function") {
      effectFunction._cleanup = cleanupReturn;
    }
  } finally {
    activeEffect = previousEffect;
    runningEffects.delete(effectFunction);
  }
}

/**
 * @template T
 * @typedef {Object} Signal
 * @property {T} value - Current value getter and setter.
 * @property {function(function(T): void): function(): void} subscribe - Subscription method.
 * @property {function(): string} toString - Marker string representation.
 */

/**
 * Creates a fine-grained reactive signal container with microtask update coalescing.
 * @template T
 * @param {T} initialValue - Initial state value.
 * @returns {Signal<T>}
 */
export function signal(initialValue) {
  /** @type {T} */
  let currentValue = initialValue;
  /** @type {Set<Function>} */
  const subscribers = new Set();

  return {
    get value() {
      if (activeEffect) {
        subscribers.add(activeEffect);
        if (!activeEffect.registeredInSets) {
          activeEffect.registeredInSets = new Set();
        }
        activeEffect.registeredInSets.add(subscribers);
      }
      return currentValue;
    },
    set value(newValue) {
      if (currentValue !== newValue) {
        currentValue = newValue;
        subscribers.forEach(subscriberFunction => scheduleEffect(subscriberFunction));
      }
    },
    subscribe(callback) {
      subscribers.add(callback);
      return () => subscribers.delete(callback);
    },
    toString() {
      return String(currentValue);
    }
  };
}

/**
 * Creates a memoized pull-based computed signal with glitch-free evaluation.
 * @template T
 * @param {function(): T} computationFunction - Pure computation function.
 * @returns {Signal<T>}
 */
export function computed(computationFunction) {
  /** @type {T} */
  let cachedValue;
  /** @type {boolean} */
  let isDirty = true;
  /** @type {Set<Function>} */
  const subscribers = new Set();
  /** @type {Set<Set<Function>>} */
  const registeredInSets = new Set();

  /**
   * Invalidation callback invoked when dependencies mutate.
   * @returns {void}
   */
  function invalidate() {
    if (!isDirty) {
      isDirty = true;
      subscribers.forEach(subscriberFunction => scheduleEffect(subscriberFunction));
    }
  }

  return {
    get value() {
      if (activeEffect) {
        subscribers.add(activeEffect);
        if (!activeEffect.registeredInSets) {
          activeEffect.registeredInSets = new Set();
        }
        activeEffect.registeredInSets.add(subscribers);
      }
      if (isDirty) {
        isDirty = false;
        registeredInSets.forEach(dependencySet => dependencySet.delete(invalidate));
        registeredInSets.clear();

        /** @type {Function|null} */
        const previousEffect = activeEffect;
        activeEffect = invalidate;
        activeEffect.registeredInSets = registeredInSets;
        try {
          cachedValue = computationFunction();
        } finally {
          activeEffect = previousEffect;
        }
      }
      return cachedValue;
    },
    subscribe(callback) {
      subscribers.add(callback);
      return () => subscribers.delete(callback);
    },
    toString() {
      return String(this.value);
    }
  };
}

/**
 * Registers a side-effect callback that automatically re-executes on dependency mutations.
 * @param {function(): (void|function(): void)} effectFunction - The effect logic.
 * @returns {function(): void} Cleanup unsubscription function.
 */
export function effect(effectFunction) {
  /** @type {Function} */
  const runner = () => effectFunction();
  runner.registeredInSets = new Set();
  runner._cleanup = null;
  runEffect(runner);
  return () => {
    runner.registeredInSets?.forEach(set => set.delete(runner));
    runner.registeredInSets?.clear();
    if (typeof runner._cleanup === "function") {
      runner._cleanup();
    }
  };
}

/** @type {boolean} */
const IS_SECURE_CONTEXT = (
  window.isSecureContext ??
  (location.protocol === "https:" || location.hostname === "localhost" || location.hostname === "127.0.0.1")
);

/** @type {string} */
const TAB_ID = typeof crypto.randomUUID === "function" ? crypto.randomUUID() : uniqueIdentifier();

/** @type {string} */
let RELAY_NAMESPACE = "__lite_spa__";

/**
 * Sets the global storage namespace prefix for cross-tab relay state.
 * @param {string} prefix - Custom namespace prefix.
 * @returns {void}
 */
export function setRelayNamespace(prefix) {
  RELAY_NAMESPACE = prefix.replace(/[^a-z0-9_-]/gi, "_");
}

/**
 * Safe sessionStorage wrapper that falls back to memory storage in private browsing.
 */
const safeSessionStorage = {
  /** @type {Map<string, string>} */
  memoryStore: new Map(),

  /**
   * @param {string} storageKeyName
   * @returns {string|null}
   */
  getItem(storageKeyName) {
    try {
      return sessionStorage.getItem(storageKeyName);
    } catch {
      return this.memoryStore.get(storageKeyName) ?? null;
    }
  },

  /**
   * @param {string} storageKeyName
   * @param {string} storageValue
   * @returns {void}
   */
  setItem(storageKeyName, storageValue) {
    try {
      sessionStorage.setItem(storageKeyName, storageValue);
    } catch {
      this.memoryStore.set(storageKeyName, storageValue);
    }
  }
};

/**
 * Safe localStorage wrapper that falls back to memory storage in file:/// and private browsing.
 */
const safeLocalStorage = {
  /** @type {Map<string, string>} */
  memoryStore: new Map(),

  /**
   * @param {string} storageKeyName
   * @returns {string|null}
   */
  getItem(storageKeyName) {
    try {
      return typeof window !== "undefined" && window.localStorage ? window.localStorage.getItem(storageKeyName) : (this.memoryStore.get(storageKeyName) ?? null);
    } catch {
      return this.memoryStore.get(storageKeyName) ?? null;
    }
  },

  /**
   * @param {string} storageKeyName
   * @param {string} storageValue
   * @returns {void}
   */
  setItem(storageKeyName, storageValue) {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        window.localStorage.setItem(storageKeyName, storageValue);
      } else {
        this.memoryStore.set(storageKeyName, storageValue);
      }
    } catch {
      this.memoryStore.set(storageKeyName, storageValue);
    }
  },

  /**
   * @param {string} storageKeyName
   * @returns {void}
   */
  removeItem(storageKeyName) {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        window.localStorage.removeItem(storageKeyName);
      }
    } catch {
      // Ignore
    }
    this.memoryStore.delete(storageKeyName);
  }
};

/**
 * Safe localStorage writer handling quota exhaustion exceptions and file:/// environments.
 * @param {string} storageKeyName - Storage key.
 * @param {string} serializedValue - JSON string to write.
 * @returns {boolean} True if write succeeded, false on quota exhaustion.
 */
function safeLocalStorageSet(storageKeyName, serializedValue) {
  try {
    if (typeof window !== "undefined" && window.localStorage) {
      window.localStorage.setItem(storageKeyName, serializedValue);
      return true;
    }
  } catch (storageError) {
    if (storageError instanceof DOMException && storageError.name === "QuotaExceededError") {
      console.warn(`[lite-spa] localStorage quota exceeded. Key "${storageKeyName}" could not be saved.`);
      if (typeof document !== "undefined") {
        document.dispatchEvent(new CustomEvent("lite-spa-storage-quota-exceeded", {
          detail: { key: storageKeyName }
        }));
      }
      return false;
    }
  }
  safeLocalStorage.setItem(storageKeyName, serializedValue);
  return true;
}

/**
 * Ephemeral session HMAC key promise. Resolves to null on non-secure contexts.
 * @type {Promise<CryptoKey|null>}
 */
const hmacKeyPromise = IS_SECURE_CONTEXT
  ? (async () => {
      try {
        /** @type {string} */
        const sessionSalt = safeSessionStorage.getItem("__lite_spa_hmac_salt__") || TAB_ID;
        safeSessionStorage.setItem("__lite_spa_hmac_salt__", sessionSalt);
        return await crypto.subtle.importKey(
          "raw",
          new TextEncoder().encode(sessionSalt),
          { name: "HMAC", hash: "SHA-256" },
          false,
          ["sign", "verify"]
        );
      } catch (keyImportError) {
        console.warn("[lite-spa] Crypto key import failed:", keyImportError);
        return null;
      }
    })()
  : (() => {
      console.warn("[lite-spa] Non-secure context (http://): HMAC relay signing disabled.");
      return Promise.resolve(null);
    })();

/** @type {boolean} */
let hmacKeyReady = false;
/** @type {CryptoKey|null} */
let activeHmacKey = null;

hmacKeyPromise.then(resolvedKey => {
  activeHmacKey = resolvedKey;
  hmacKeyReady = true;
});

/**
 * Signs a payload string with HMAC-SHA256.
 * @param {string} payloadString - String to sign.
 * @returns {Promise<string>} Hex signature.
 */
async function computeHmacSignature(payloadString) {
  if (!activeHmacKey) {
    return "";
  }
  /** @type {ArrayBuffer} */
  const signatureBuffer = await crypto.subtle.sign(
    "HMAC",
    activeHmacKey,
    new TextEncoder().encode(payloadString)
  );
  return Array.from(new Uint8Array(signatureBuffer))
    .map(byte => byte.toString(16).padStart(2, "0"))
    .join("");
}

/**
 * Verifies an HMAC signature against payload string.
 * @param {string} payloadString - String to verify.
 * @param {string} hexSignature - Hex signature.
 * @returns {Promise<boolean>}
 */
async function verifyHmacSignature(payloadString, hexSignature) {
  if (!activeHmacKey || !hexSignature) {
    return false;
  }
  /** @type {Uint8Array} */
  const signatureBytes = new Uint8Array(
    hexSignature.match(/.{1,2}/g)?.map(byte => parseInt(byte, 16)) ?? []
  );
  return await crypto.subtle.verify(
    "HMAC",
    activeHmacKey,
    signatureBytes,
    new TextEncoder().encode(payloadString)
  );
}

/** @type {Map<string, EventListener>} */
const storageListeners = new Map();

/**
 * Registers a deduplicated storage event listener for a given storage key.
 * @param {string} storageKeyName - Key to listen for.
 * @param {EventListener} listenerFunction - Event handler.
 * @returns {void}
 */
function registerStorageListener(storageKeyName, listenerFunction) {
  /** @type {EventListener|undefined} */
  const existingListener = storageListeners.get(storageKeyName);
  if (existingListener) {
    window.removeEventListener("storage", existingListener);
  }
  storageListeners.set(storageKeyName, listenerFunction);
  window.addEventListener("storage", listenerFunction);
}

/**
 * Removes all registered storage listeners.
 * @returns {void}
 */
function unregisterAllStorageListeners() {
  storageListeners.forEach(listenerFunction => window.removeEventListener("storage", listenerFunction));
}

/**
 * Re-attaches all registered storage listeners after BFCache restoration.
 * @returns {void}
 */
function reregisterAllStorageListeners() {
  storageListeners.forEach(listenerFunction => window.addEventListener("storage", listenerFunction));
}

/**
 * @typedef {Object} RelaySignalExtension
 * @property {string} securityMode - "hmac" or "plain" depending on context security.
 */

/**
 * Creates a singleton cross-tab synchronized reactive signal backed by storage.
 * @template T
 * @param {string} keyName - Unique state key.
 * @param {T} defaultValue - Default state value.
 * @returns {Signal<T> & RelaySignalExtension}
 */
export function relay(keyName, defaultValue) {
  /** @type {string} */
  const fullStorageKey = `${RELAY_NAMESPACE}${keyName}`;
  /** @type {number} */
  let writeSequence = 0;
  /** @type {unknown} */
  let pendingWriteValue = undefined;
  /** @type {boolean} */
  let hasPendingWrite = false;

  /**
   * Loads initial value safely from storage with corrupted JSON protection.
   * @returns {T}
   */
  function loadStoredValue() {
    /** @type {string|null} */
    const rawStored = safeLocalStorage.getItem(fullStorageKey);
    if (!rawStored) {
      return defaultValue;
    }
    try {
      /** @type {any} */
      const parsedPayload = JSON.parse(rawStored);
      if (parsedPayload && typeof parsedPayload === "object" && "value" in parsedPayload) {
        return parsedPayload.value;
      }
      return parsedPayload;
    } catch {
      console.warn(`[lite-spa] Corrupted relay storage for key "${keyName}". Resetting to default.`);
      safeLocalStorage.removeItem(fullStorageKey);
      return defaultValue;
    }
  }

  /** @type {Signal<T>} */
  const innerSignal = signal(loadStoredValue());

  /**
   * Persists value to storage with HMAC signing.
   * @param {T} valueToStore - Value to persist.
   * @returns {void}
   */
  async function persistValue(valueToStore) {
    if (!hmacKeyReady) {
      pendingWriteValue = valueToStore;
      hasPendingWrite = true;
      return;
    }
    writeSequence++;
    /** @type {string} */
    const serializedData = JSON.stringify(valueToStore);
    /** @type {string} */
    const payloadToSign = `${TAB_ID}:${writeSequence}:${serializedData}`;
    /** @type {string} */
    const signature = await computeHmacSignature(payloadToSign);

    /** @type {string} */
    const storagePayload = JSON.stringify({
      value: valueToStore,
      tabId: TAB_ID,
      sequence: writeSequence,
      signature
    });

    safeLocalStorageSet(fullStorageKey, storagePayload);
  }

  hmacKeyPromise.then(() => {
    if (hasPendingWrite) {
      persistValue(pendingWriteValue);
      hasPendingWrite = false;
      pendingWriteValue = undefined;
    }
  });

  // Cross-tab storage event receiver
  registerStorageListener(fullStorageKey, async (storageEvent) => {
    if (storageEvent.key !== fullStorageKey || !storageEvent.newValue) {
      return;
    }
    try {
      /** @type {any} */
      const payload = JSON.parse(storageEvent.newValue);
      if (payload.tabId === TAB_ID) {
        return; // Echo suppression
      }

      if (activeHmacKey && payload.signature) {
        /** @type {string} */
        const payloadToVerify = `${payload.tabId}:${payload.sequence}:${JSON.stringify(payload.value)}`;
        /** @type {boolean} */
        const isValid = await verifyHmacSignature(payloadToVerify, payload.signature);
        if (!isValid) {
          console.warn(`[lite-spa] HMAC verification failed for relay key "${keyName}". Rejecting forged payload.`);
          document.dispatchEvent(new CustomEvent("lite-spa-security-violation", {
            detail: { key: keyName, rogueTabId: payload.tabId }
          }));
          return; // Reject without resetting
        }
      }

      innerSignal.value = payload.value;
    } catch (parseError) {
      console.warn(`[lite-spa] Failed to parse cross-tab storage payload for "${keyName}":`, parseError);
    }
  });

  return {
    get value() {
      return innerSignal.value;
    },
    set value(newValue) {
      innerSignal.value = newValue;
      persistValue(newValue);
    },
    subscribe(callback) {
      return innerSignal.subscribe(callback);
    },
    toString() {
      return String(innerSignal.value);
    },
    get securityMode() {
      return IS_SECURE_CONTEXT ? "hmac" : "plain";
    }
  };
}

/** @type {boolean} */
const SUPPORTS_ADOPTED_STYLESHEETS = (
  "adoptedStyleSheets" in Document.prototype &&
  (() => {
    try {
      new CSSStyleSheet();
      return true;
    } catch {
      return false;
    }
  })()
);

/** @type {WeakMap<Function, string>} */
const classBaseUrlCache = new WeakMap();

/** @type {WeakMap<Function, CSSStyleSheet>} */
const classStyleSheetCache = new WeakMap();

/**
 * Sanitizes a scope identifier to prevent CSS selector injection attacks.
 * @param {string} rawScopeId - Raw scope identifier.
 * @returns {string} Clean, safe CSS attribute selector value.
 */
function sanitizeScopeId(rawScopeId) {
  return rawScopeId
    .toLowerCase()
    .replace(/[^a-z0-9-_]/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
}

/**
 * Extracts the calling module URL from a stack trace string cross-browser.
 * @param {string|undefined} stackTrace - Captured stack trace.
 * @returns {string|null} The resolved caller module URL or null.
 */
function extractCallerUrl(stackTrace) {
  if (!stackTrace) {
    return null;
  }
  /** @type {RegExp} */
  const urlPattern = /(https?:\/\/[^\s):]+|file:\/\/\/[^\s):]+)/g;
  /** @type {Array<RegExpMatchArray>} */
  const matchedUrls = [...stackTrace.matchAll(urlPattern)];
  
  for (const match of matchedUrls) {
    /** @type {string} */
    const candidateUrl = match[1];
    if (!candidateUrl.includes("Component.js")) {
      return candidateUrl;
    }
  }
  return matchedUrls[1]?.[1] ?? matchedUrls[0]?.[1] ?? null;
}

/**
 * Recursively prefixes CSS selectors inside style rules, including nested grouping rules.
 * @param {CSSRule} cssRule - Rule to scope.
 * @param {string} scopeAttributeSelector - The scope attribute selector (e.g. [data-scope="..."]).
 * @returns {void}
 */
function scopeCssRule(cssRule, scopeAttributeSelector) {
  if (cssRule instanceof CSSStyleRule) {
    cssRule.selectorText = cssRule.selectorText
      .split(",")
      .map(selectorChunk => `${scopeAttributeSelector} ${selectorChunk.trim()}`)
      .join(", ");
  } else if ("cssRules" in cssRule && cssRule.cssRules) {
    Array.from(cssRule.cssRules).forEach(innerRule => scopeCssRule(innerRule, scopeAttributeSelector));
  }
}

/**
 * Adopts a stylesheet using full array reassignment for Safari <= 16 compatibility.
 * @param {CSSStyleSheet} sheetToAdopt - Stylesheet to add.
 * @param {Document|ShadowRoot} [targetRoot=document] - Target DOM root.
 * @returns {void}
 */
export function adoptStyleSheet(sheetToAdopt, targetRoot = document) {
  targetRoot.adoptedStyleSheets = [...targetRoot.adoptedStyleSheets, sheetToAdopt];
}

/**
 * Removes a stylesheet using full array reassignment for Safari <= 16 compatibility.
 * @param {CSSStyleSheet} sheetToRemove - Stylesheet to remove.
 * @param {Document|ShadowRoot} [targetRoot=document] - Target DOM root.
 * @returns {void}
 */
export function unadoptStyleSheet(sheetToRemove, targetRoot = document) {
  targetRoot.adoptedStyleSheets = targetRoot.adoptedStyleSheets.filter(sheet => sheet !== sheetToRemove);
}

/**
 * Applies scoped styles to the document with feature-detection fallback.
 * @param {string} scopedCssContent - Scoped CSS text.
 * @param {string} scopeIdentifier - Unique scope ID for deduplication.
 * @returns {function(): void} Cleanup remover function.
 */
function applyComponentStyles(scopedCssContent, scopeIdentifier) {
  if (SUPPORTS_ADOPTED_STYLESHEETS) {
    /** @type {CSSStyleSheet} */
    const styleSheet = new CSSStyleSheet();
    styleSheet.replaceSync(scopedCssContent);
    adoptStyleSheet(styleSheet);
    return () => unadoptStyleSheet(styleSheet);
  } else {
    /** @type {Element|null} */
    const existingTag = document.head.querySelector(`style[data-lite-scope="${scopeIdentifier}"]`);
    if (existingTag) {
      return () => {};
    }
    /** @type {HTMLStyleElement} */
    const styleElement = document.createElement("style");
    styleElement.setAttribute("data-lite-scope", scopeIdentifier);
    styleElement.textContent = scopedCssContent;
    document.head.appendChild(styleElement);
    return () => styleElement.remove();
  }
}

/** @type {IntersectionObserver|null} */
let globalPhantomObserver = null;

/**
 * Gets or initializes the shared IntersectionObserver for phantom hydration.
 * @returns {IntersectionObserver}
 */
function getPhantomObserver() {
  if (!globalPhantomObserver) {
    globalPhantomObserver = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            /** @type {HTMLElement} */
            const placeholderElement = entry.target;
            if (typeof placeholderElement.__phantomHydrate === "function") {
              placeholderElement.__phantomHydrate();
            }
          }
        });
      },
      { rootMargin: "200px" }
    );
  }
  return globalPhantomObserver;
}

/**
 * Creates a lazy phantom component placeholder with viewport auto-hydration.
 * @param {function(): Promise<{default: typeof Component}|typeof Component>} importFunction - Dynamic import loader.
 * @returns {{ toString: function(): string, load: function(): Promise<Component> }}
 */
export function phantom(importFunction) {
  /** @type {string} */
  const placeholderId = `phantom-${uniqueIdentifier()}`;

  /**
   * Programmatically loads and mounts the real component.
   * @returns {Promise<Component>}
   */
  const loadComponent = async () => {
    /** @type {HTMLElement|null} */
    const placeholder = safeGetElementById(placeholderId);
    try {
      /** @type {any} */
      const importedModule = await importFunction();
      /** @type {typeof Component} */
      const ComponentClass = importedModule.default || importedModule;
      /** @type {Component} */
      const instance = new ComponentClass();

      if (placeholder) {
        getPhantomObserver().unobserve(placeholder);
        /** @type {HTMLTemplateElement} */
        const templateTag = document.createElement("template");
        templateTag.innerHTML = instance.toString();
        /** @type {DocumentFragment} */
        const fragment = templateTag.content;
        placeholder.replaceWith(fragment);
        instance.__mount();
      }
      return instance;
    } catch (importError) {
      console.error(`[lite-spa] phantom component failed to import (${placeholderId}):`, importError);
      if (placeholder) {
        getPhantomObserver().unobserve(placeholder);
        placeholder.setAttribute("data-phantom-error", "true");
        placeholder.setAttribute("aria-label", "Component failed to load");
      }
      throw importError;
    }
  };

  /**
   * Renders the placeholder tag and attaches observer listener.
   * @returns {string}
   */
  const renderPlaceholder = () => {
    setTimeout(() => {
      /** @type {HTMLElement|null} */
      const placeholder = safeGetElementById(placeholderId);
      if (placeholder) {
        placeholder.__phantomHydrate = loadComponent;
        getPhantomObserver().observe(placeholder);
      }
    }, 0);
    return `<div id="${placeholderId}" data-phantom="true"></div>`;
  };

  return {
    toString: renderPlaceholder,
    load: loadComponent
  };
}

/** @type {number} */
let navigationSequenceNumber = 0;

/**
 * Restores scroll position after the next browser paint cycle with cancellation token.
 * @param {number} targetScrollY - Target Y coordinate.
 * @returns {void}
 */
function deferredScrollRestore(targetScrollY) {
  /** @type {number} */
  const currentSequence = ++navigationSequenceNumber;
  requestAnimationFrame(() => {
    if (currentSequence !== navigationSequenceNumber) {
      return;
    }
    requestAnimationFrame(() => {
      if (currentSequence !== navigationSequenceNumber) {
        return;
      }
      window.scrollTo({ top: targetScrollY, behavior: "instant" });
    });
  });
}

/**
 * State-driven router path signal.
 * @type {Signal<string> & RelaySignalExtension}
 */
export const route = relay("router-path", window.location.pathname);

/**
 * Intercepts client-side navigation clicks with Shadow DOM pierce-through.
 * @param {MouseEvent} clickEvent
 * @returns {void}
 */
document.addEventListener("click", clickEvent => {
  /** @type {Array<EventTarget>} */
  const eventPath = clickEvent.composedPath ? clickEvent.composedPath() : [clickEvent.target];
  /** @type {HTMLAnchorElement|null} */
  let routeAnchor = null;

  for (const targetNode of eventPath) {
    if (targetNode instanceof HTMLElement && targetNode.hasAttribute("data-lite-spa-route")) {
      routeAnchor = targetNode;
      break;
    }
  }

  if (!routeAnchor) {
    return;
  }

  /** @type {string|null} */
  const destinationPath = routeAnchor.getAttribute("href");
  if (!destinationPath) {
    return;
  }

  /** @type {any} */
  let matchedComponent = routes[destinationPath];
  if (typeof matchedComponent === "function") {
    if (!(matchedComponent.prototype instanceof Component) && matchedComponent !== Component) {
      try {
        matchedComponent = matchedComponent();
      } catch {
        // Fallback
      }
    }
  }
  if (!matchedComponent) {
    return;
  }

  clickEvent.preventDefault();
  renderRoute(matchedComponent, destinationPath);
});

/**
 * Resolves a registered component class by route path, evaluating lazy getters if present.
 * @param {string} targetPath - Route URL path.
 * @returns {typeof Component|undefined}
 */
function resolveRouteComponent(targetPath) {
  /** @type {any} */
  let matched = routes[targetPath];
  if (typeof matched === "function") {
    if (matched.prototype && matched.prototype instanceof Component) {
      return matched;
    }
    try {
      /** @type {any} */
      const evaluated = matched();
      if (evaluated && evaluated.prototype && evaluated.prototype instanceof Component) {
        return evaluated;
      }
    } catch {
      // Fallback
    }
  }
  return undefined;
}

// BFCache and popstate event management for browser back/forward buttons
window.addEventListener("popstate", popstateEvent => {
  /** @type {string} */
  const currentPath = sanitizeRoutePath(window.location.pathname);
  /** @type {typeof Component|undefined} */
  const destinationPage = resolveRouteComponent(currentPath);
  /** @type {number} */
  const savedScrollPosition = popstateEvent.state?.__liteScrollY ?? 0;

  if (destinationPage) {
    if (route.value !== currentPath) {
      route.value = currentPath;
    }
    renderRoute(destinationPage, currentPath, { updateHistory: false, state: popstateEvent.state });
    deferredScrollRestore(savedScrollPosition);
  }
});

window.addEventListener("pageshow", pageshowEvent => {
  if (pageshowEvent.persisted) {
    reregisterAllStorageListeners();
    /** @type {HTMLElement|null} */
    const routeContainer = document.querySelector("[data-lite-route-container]") ?? document.body;
    if (routeContainer) {
      unmountActiveComponents();
    }
    /** @type {string} */
    const currentPath = sanitizeRoutePath(window.location.pathname);
    /** @type {typeof Component|undefined} */
    const targetPage = routes[currentPath];
    if (targetPage) {
      renderRoute(targetPage, currentPath, { updateHistory: false });
    }
  }
});

window.addEventListener("pagehide", pagehideEvent => {
  if (pagehideEvent.persisted) {
    unregisterAllStorageListeners();
  }
});

/**
 * Creates a route state object with scroll snapshot and stack index.
 * @param {string} pathString - The route path.
 * @returns {{ path: string, __liteSpaIndex: number, __liteScrollY: number }}
 */
const routeState = pathString => ({
  path: pathString,
  __liteSpaIndex: history.length,
  __liteScrollY: window.scrollY
});

/**
 * Waits for pending stylesheet loads with non-blocking race timeout for instant rendering.
 * @returns {Promise<void|any>}
 */
const waitForStyles = () => {
  /** @type {Array<Promise<string>>} */
  const activeCssLoads = pendingCssLoads.splice(0);
  if (activeCssLoads.length === 0) {
    return Promise.resolve();
  }
  return Promise.race([
    Promise.allSettled(activeCssLoads),
    new Promise(resolve => setTimeout(resolve, 100))
  ]);
};

/**
 * Mounts all components currently queued in pendingMounts.
 * @returns {Array<Component>}
 */
const mountQueuedComponents = () => {
  /** @type {Array<Component>} */
  const queued = pendingMounts.splice(0);
  queued.forEach(componentInstance => componentInstance.__mount());
  return queued;
};

/**
 * Unmounts all active components in reverse instantiation order.
 * @returns {void}
 */
const unmountActiveComponents = () => {
  if (activeComponents.length === 0) {
    return;
  }
  activeComponents.slice().reverse().forEach(componentInstance => componentInstance.__unmount());
  activeComponents = [];
};

/**
 * Renders a component for a specific URL path with non-destructive history.
 * @param {typeof Component} destinationComponent - The component class to render.
 * @param {string} pathString - The URL path.
 * @param {Object} [renderOptions] - Settings.
 * @param {boolean} [renderOptions.replace=false] - Whether to replace history state.
 * @param {boolean} [renderOptions.updateHistory=true] - Whether to push history state.
 * @returns {Promise<void>}
 */
const renderRoute = async (destinationComponent, pathString, { replace = false, updateHistory = true } = {}) => {
  /** @type {number} */
  const currentRenderVersion = ++renderVersion;
  routes[pathString] = destinationComponent;

  /** @type {string} */
  let renderedTemplateString = "";

  try {
    pendingMounts.splice(0);
    shouldQueueMounts = true;

    /** @type {Component} */
    const componentInstance = new destinationComponent();
    renderedTemplateString = componentInstance.toString();
  } finally {
    shouldQueueMounts = false;
  }

  await waitForStyles();

  if (currentRenderVersion !== renderVersion) {
    return;
  }

  if (updateHistory && window.location.pathname !== pathString) {
    try {
      /** @type {string} */
      const historyMethod = replace ? "replaceState" : "pushState";
      window.history[historyMethod](routeState(pathString), "", pathString);
    } catch {
      // In file:/// protocol, history.pushState with absolute path throws SecurityError
    }
  }

  if (route.value !== pathString) {
    route.value = pathString;
  }

  unmountActiveComponents();
  /** @type {HTMLElement|null} */
  const routeContainer = document.querySelector("[data-lite-route-container]") ?? document.body;

  /**
   * Applies the rendered template markup and mounts active components.
   * @returns {void}
   */
  const applyRender = () => {
    routeContainer.innerHTML = renderedTemplateString;
    routeContainer.classList.remove("lite-page-enter");
    void routeContainer.offsetWidth; // Trigger reflow for CSS animation restart
    routeContainer.classList.add("lite-page-enter");
    activeComponents = mountQueuedComponents();
  };

  if (typeof document.startViewTransition === "function") {
    document.startViewTransition(() => applyRender());
  } else {
    applyRender();
  }
};

export class Redirect {
  /**
   * Constructs a Redirect navigation anchor component.
   * @param {Object} redirectOptions
   * @param {string} redirectOptions.id - Unique element ID.
   * @param {typeof Component|function(): typeof Component|string} redirectOptions.destination - Target component class or lazy getter.
   * @param {string} redirectOptions.path - Target URL path.
   * @param {Record<string, string>} [redirectOptions.attributes={}] - Additional HTML attributes.
   * @param {string} [redirectOptions.innerHTML=""] - Anchor inner content.
   */
  constructor({ id, destination, path, attributes = {}, innerHTML = "" } = {}) {
    if (!id || typeof id !== "string") {
      throw new Error("Redirect element ID must be a non-empty string");
    }
    if (!destination) {
      throw new Error("Redirect destination class cannot be null");
    }
    if (typeof path !== "string") {
      throw new Error("Redirect path must be of type string");
    }

    /** @type {string} */
    const cleanAttributes = Object.entries(attributes)
      .map(([attrKey, attrVal]) => `${attrKey}="${escapeHtml(attrVal)}"`)
      .join(" ");

    /**
     * Resolves the destination component class dynamically.
     * @returns {typeof Component}
     */
    const resolveDestination = () => {
      if (typeof destination === "function") {
        if (destination.prototype && destination.prototype instanceof Component) {
          return destination;
        }
        try {
          const evaluated = destination();
          if (evaluated) {
            return evaluated;
          }
        } catch {
          return destination;
        }
        return destination;
      }
      if (typeof destination === "string" && typeof window !== "undefined") {
        return window[destination] || window.LiteSpa?.[destination];
      }
      return destination;
    };

    /**
     * @returns {string}
     */
    const renderAnchor = () => {
      /** @type {string} */
      const uniqueAnchorId = `${id}-${uniqueIdentifier()}`;
      routes[path] = resolveDestination;
      return `<a href="${path}" id="${uniqueAnchorId}" data-lite-spa-route="${path}" ${cleanAttributes}>${innerHTML}</a>`;
    };

    /** @type {function(): string} */
    this.toString = () => renderAnchor();
  }
}

export class Root {
  /**
   * Constructs and boots the Root component for the application entry point.
   * @param {Object} rootOptions
   * @param {typeof Component} rootOptions.destination - Initial component class.
   * @param {string} [rootOptions.path="/"] - Root route path.
   */
  constructor({ destination, path = "/" } = {}) {
    if (!destination) {
      throw new Error("Root destination component class cannot be null");
    }
    if (typeof path !== "string") {
      throw new Error("Root path must be of type string");
    }

    /**
     * Boots the root route into the DOM.
     * @returns {void}
     */
    this.render = () => {
      routes[path] = destination;
      try {
        window.history.replaceState(routeState(path), "", path);
      } catch {
        // In file:/// protocol, history.replaceState with absolute path throws SecurityError
      }
      renderRoute(destination, path, { replace: true, updateHistory: false });
    };
  }
}

/**
 * Resolves the calling script path from import.meta or URL object.
 * @param {ImportMeta|{url: string}} importMeta - Module metadata or URL descriptor.
 * @returns {string} Clean script path.
 */
export const getFullPath = (importMeta) => {
  if (!importMeta || !importMeta.url) {
    if (typeof window !== "undefined" && window.location) {
      const windowPath = window.location.pathname;
      return windowPath.startsWith("/") ? windowPath.slice(1) : windowPath;
    }
    throw new Error("Missing import.meta. Pass `import.meta` as the argument.");
  }
  /** @type {string} */
  const scriptSource = new URL(importMeta.url, document.baseURI).pathname;
  return scriptSource.startsWith("/") ? scriptSource.slice(1) : scriptSource;
};

/**
 * Dynamically loads CSS stylesheets relative to the caller module without requiring manual import.meta.
 * @param {ImportMeta|Array<string>|string} metaOrPaths - Optional import.meta, or directly stylesheet path(s).
 * @param {Array<string>|string} [optionalPaths] - Stylesheet path(s) if import.meta was passed as first argument.
 * @returns {Promise<Array<string>>}
 */
export const css = (metaOrPaths, optionalPaths) => {
  /** @type {string|null} */
  let callerUrl = null;
  /** @type {Array<string>} */
  let cssPaths = [];

  if (Array.isArray(metaOrPaths) || typeof metaOrPaths === "string") {
    cssPaths = Array.isArray(metaOrPaths) ? metaOrPaths : [metaOrPaths];
    /** @type {string|undefined} */
    const stackTrace = new Error().stack;
    callerUrl = extractCallerUrl(stackTrace) || (typeof window !== "undefined" ? window.location.href : "");
  } else if (metaOrPaths && typeof metaOrPaths.url === "string") {
    callerUrl = metaOrPaths.url;
    cssPaths = Array.isArray(optionalPaths) ? optionalPaths : (optionalPaths ? [optionalPaths] : []);
  } else {
    /** @type {string|undefined} */
    const stackTrace = new Error().stack;
    callerUrl = extractCallerUrl(stackTrace) || (typeof window !== "undefined" ? window.location.href : "");
    cssPaths = Array.isArray(optionalPaths) ? optionalPaths : (optionalPaths ? [optionalPaths] : []);
  }

  /** @type {string} */
  const callerBaseUrl = callerUrl ? new URL(".", callerUrl).href : (typeof document !== "undefined" ? document.baseURI : "");

  return Promise.all(cssPaths.map(rawCssPath => {
    /** @type {string} */
    const resolvedUrl = new URL(rawCssPath, callerBaseUrl).href;
    /** @type {HTMLLinkElement|null} */
    const cssAlreadyLinked = typeof document !== "undefined" ? document.querySelector(`link[href='${resolvedUrl}']`) : null;
    if (cssAlreadyLinked) {
      /** @type {boolean} */
      const isLoaded = cssAlreadyLinked.dataset.loaded === "true" || !!cssAlreadyLinked.sheet;
      /** @type {Promise<string>} */
      const existingLoad = isLoaded
        ? Promise.resolve(resolvedUrl)
        : new Promise(resolve => {
            cssAlreadyLinked.addEventListener("load", () => resolve(resolvedUrl), { once: true });
            cssAlreadyLinked.addEventListener("error", () => resolve(resolvedUrl), { once: true });
          });
      pendingCssLoads.push(existingLoad);
      return existingLoad;
    }

    /** @type {HTMLLinkElement} */
    const styleLink = document.createElement("link");
    styleLink.rel = "stylesheet";
    styleLink.href = resolvedUrl;

    /** @type {Promise<string>} */
    const cssLoad = new Promise(resolve => {
      styleLink.onload = () => {
        styleLink.dataset.loaded = "true";
        resolve(resolvedUrl);
      };
      styleLink.onerror = () => resolve(resolvedUrl);
    });

    pendingCssLoads.push(cssLoad);
    document.head.appendChild(styleLink);
    return cssLoad;
  }));
};

/**
 * @typedef {Object} CdnDescriptor
 * @property {string} src - Script URL.
 * @property {string} [integrity] - Subresource Integrity hash.
 * @property {string} [crossOrigin="anonymous"] - CORS mode for SRI.
 */

/**
 * Injects a CDN script tag with CSP nonce propagation and optional SRI enforcement.
 * @param {string|CdnDescriptor} input - URL string, script tag string, or descriptor object.
 * @returns {Promise<void>}
 */
export const cdn = input =>
  new Promise((resolve, reject) => {
    if (!input) {
      reject(new Error("cdn() requires a URL string, script tag, or descriptor object."));
      return;
    }

    /** @type {string} */
    let scriptSourceUrl = "";
    /** @type {boolean} */
    let isModuleScript = false;
    /** @type {string|undefined} */
    let integrityHash = undefined;
    /** @type {string} */
    let crossOriginMode = "anonymous";

    if (typeof input === "object") {
      scriptSourceUrl = input.src;
      integrityHash = input.integrity;
      crossOriginMode = input.crossOrigin ?? "anonymous";
    } else if (typeof input === "string") {
      /** @type {string} */
      const trimmedInput = input.trim();
      if (trimmedInput.startsWith("<script")) {
        /** @type {HTMLTemplateElement} */
        const templateElement = document.createElement("template");
        templateElement.innerHTML = trimmedInput;
        /** @type {ChildNode|null} */
        const parsedNode = templateElement.content.firstChild;
        if (!(parsedNode instanceof HTMLScriptElement)) {
          reject(new Error("cdn() string must contain a valid <script> tag."));
          return;
        }
        scriptSourceUrl = parsedNode.src;
        isModuleScript = parsedNode.type === "module";
        integrityHash = parsedNode.integrity || undefined;
        crossOriginMode = parsedNode.crossOrigin || "anonymous";
      } else {
        scriptSourceUrl = trimmedInput;
      }
    }

    /** @type {HTMLScriptElement|null} */
    const existingScriptElement = document.querySelector(`script[src="${scriptSourceUrl}"]`);
    if (existingScriptElement) {
      if (existingScriptElement.dataset.loaded === "true") {
        resolve();
      } else {
        existingScriptElement.addEventListener("load", () => resolve(), { once: true });
        existingScriptElement.addEventListener("error", () => reject(new Error(`Failed to load ${scriptSourceUrl}`)), { once: true });
      }
      return;
    }

    /** @type {HTMLScriptElement} */
    const scriptElement = document.createElement("script");
    scriptElement.src = scriptSourceUrl;
    if (CSP_NONCE) {
      scriptElement.nonce = CSP_NONCE;
    }
    if (integrityHash) {
      scriptElement.integrity = integrityHash;
      scriptElement.crossOrigin = crossOriginMode;
    }
    if (isModuleScript) {
      scriptElement.type = "module";
    }
    scriptElement.setAttribute("data-cdn", scriptSourceUrl);

    scriptElement.onload = () => {
      scriptElement.dataset.loaded = "true";
      resolve();
    };
    scriptElement.onerror = () => reject(new Error(`[lite-spa] Failed to load CDN script: ${scriptSourceUrl}`));

    document.head.appendChild(scriptElement);
  });

/**
 * Base Component class with fine-grained reactivity, lifecycle abort controllers, and error boundaries.
 */
export class Component {


  /** @type {boolean} */
  #isMounted = false;

  /** @type {function()|null} */
  #cleanup = null;

  /** @type {AbortController} */
  #abortController = new AbortController();

  /** @type {string|null} */
  #scopeId = null;

  /** @type {function()|null} */
  #stylesCleanup = null;

  /**
   * Resets the AbortController at the beginning of each render cycle.
   * @private
   * @returns {void}
   */
  #beginRender() {
    this.#abortController.abort("re-render");
    this.#abortController = new AbortController();
  }

  constructor() {
    /** @type {string|TemplateResult} */
    this.template = "";

    /** @type {function()|null} */
    this.logic = null;

    /** @type {function()|null} */
    this.beforeMount = null;

    /** @type {function()|null} */
    this.mounted = null;

    /** @type {function()|null} */
    this.beforeUnmount = null;

    /** @type {function()|null} */
    this.unmounted = null;

    /** @type {function(Error): void|null} */
    this.onError = null;

    /**
     * Sets component-scoped stylesheets using caller stack introspection.
     * @param {Array<string>} relativeStylePaths - Array of relative CSS file paths.
     */
    this.styles = (relativeStylePaths) => {
      if (!Array.isArray(relativeStylePaths) || relativeStylePaths.length === 0) {
        return;
      }
      /** @type {Function} */
      const componentClass = this.constructor;
      /** @type {string} */
      const scopeIdentifier = sanitizeScopeId(`scope-${componentClass.name}-${uniqueIdentifier()}`);
      this.#scopeId = scopeIdentifier;

      /** @type {string} */
      let baseUrl = classBaseUrlCache.get(componentClass) ?? "";
      if (!baseUrl) {
        baseUrl = extractCallerUrl(new Error().stack) ?? document.baseURI;
        classBaseUrlCache.set(componentClass, baseUrl);
      }

      relativeStylePaths.forEach(async relativePath => {
        /** @type {string} */
        const resolvedCssUrl = new URL(relativePath, baseUrl).href;
        try {
          /** @type {Response} */
          const cssResponse = await fetch(resolvedCssUrl);
          /** @type {string} */
          const rawCssContent = await cssResponse.text();

          /** @type {CSSStyleSheet} */
          const styleSheet = new CSSStyleSheet();
          styleSheet.replaceSync(rawCssContent);
          Array.from(styleSheet.cssRules).forEach(rule => scopeCssRule(rule, `[data-scope="${scopeIdentifier}"]`));

          /** @type {string} */
          let scopedText = "";
          Array.from(styleSheet.cssRules).forEach(rule => {
            scopedText += rule.cssText + "\n";
          });

          this.#stylesCleanup = applyComponentStyles(scopedText, scopeIdentifier);
        } catch (cssFetchError) {
          console.warn(`[lite-spa] Scoped CSS fetch blocked (CORS/file://) for ${resolvedCssUrl}. Falling back to <link> tag:`, cssFetchError);
          /** @type {HTMLLinkElement} */
          const fallbackLink = document.createElement("link");
          fallbackLink.rel = "stylesheet";
          fallbackLink.href = resolvedCssUrl;
          document.head.appendChild(fallbackLink);
          this.#stylesCleanup = () => fallbackLink.remove();
        }
      });
    };

    /**
     * Returns the current render cycle AbortSignal.
     * @type {AbortSignal}
     */
    Object.defineProperty(this, "signal", {
      get: () => this.#abortController.signal,
      enumerable: true,
      configurable: true
    });

    /**
     * Component-scoped fetch automatically cancelled on unmount or re-render.
     * @param {RequestInfo|URL} input - Fetch input.
     * @param {RequestInit} [init] - Fetch init options.
     * @returns {Promise<Response>}
     */
    this.fetch = (input, init = {}) => {
      return fetch(input, { ...init, signal: this.#abortController.signal });
    };

    /**
     * Attaches an event listener automatically detached on unmount or re-render.
     * @param {EventTarget} target - Target element.
     * @param {string} eventType - Event type name.
     * @param {EventListenerOrEventListenerObject} listener - Callback.
     * @param {AddEventListenerOptions|boolean} [options] - Options.
     * @returns {void}
     */
    this.listen = (target, eventType, listener, options) => {
      target.addEventListener(eventType, listener, {
        ...(typeof options === "object" ? options : {}),
        signal: this.#abortController.signal
      });
    };



    /**
     * Renders template markup and attaches scope attributes.
     * @returns {string}
     */
    const render = () => {
      this.#beginRender();

      /** @type {string} */
      let templateOutput = "";
      if (this.template instanceof TemplateResult) {
        templateOutput = this.template.toString();
      } else if (typeof this.template === "string") {
        templateOutput = this.template;
      }

      if (this.#scopeId && templateOutput) {
        templateOutput = templateOutput.replace(/^(\s*<[a-zA-Z0-9_-]+)/, `$1 data-scope="${this.#scopeId}"`);
      }

      if (!shouldQueueMounts) {
        setTimeout(() => this.__mount(), 0);
      }

      return templateOutput;
    };

    /**
     * Mounts the component, executing lifecycle hooks with error boundary protection.
     * @returns {void}
     */
    this.__mount = () => {
      if (this.#isMounted) {
        return;
      }

      try {
        /** @type {Array<function(): void>} */
        const signalCleanups = hydrateSignalBindings(document.body);

        if (typeof this.beforeMount === "function") {
          this.beforeMount();
        }

        if (typeof this.logic === "function") {
          /** @type {any} */
          const cleanupReturn = this.logic();
          if (typeof cleanupReturn === "function") {
            this.#cleanup = () => {
              cleanupReturn();
              signalCleanups.forEach(fn => fn());
            };
          } else {
            this.#cleanup = () => {
              signalCleanups.forEach(fn => fn());
            };
          }
        } else {
          this.#cleanup = () => {
            signalCleanups.forEach(fn => fn());
          };
        }

        if (typeof this.mounted === "function") {
          this.mounted();
        }

        this.#isMounted = true;
      } catch (mountError) {
        console.error("[lite-spa] Component __mount() failed:", mountError, this);
        if (typeof this.onError === "function") {
          this.onError(mountError);
        }
      }
    };

    /**
     * Unmounts the component and releases all resources and event listeners.
     * @returns {void}
     */
    this.__unmount = () => {
      if (!this.#isMounted) {
        return;
      }

      try {
        if (typeof this.beforeUnmount === "function") {
          this.beforeUnmount();
        }

        if (typeof this.#cleanup === "function") {
          this.#cleanup();
        }

        this.#abortController.abort("unmount");

        if (typeof this.#stylesCleanup === "function") {
          this.#stylesCleanup();
        }

        if (typeof this.unmounted === "function") {
          this.unmounted();
        }
      } catch (unmountError) {
        console.error("[lite-spa] Component __unmount() error:", unmountError);
      } finally {
        this.#cleanup = null;
        this.#stylesCleanup = null;
        this.#isMounted = false;
      }
    };

    /**
     * Returns rendered HTML template string.
     * @returns {string}
     */
    this.toString = () => {
      /** @type {string} */
      const renderedMarkup = render();
      if (shouldQueueMounts) {
        pendingMounts.push(this);
      }
      return renderedMarkup;
    };
  }
}
