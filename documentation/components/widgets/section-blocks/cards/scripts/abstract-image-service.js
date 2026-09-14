/**
 * Storage key for persistent card image cache in localStorage.
 * @type {string}
 */
const CARD_IMAGE_CACHE_STORAGE_KEY = "material_dialogs_card_image_cache";

/**
 * In-memory image cache map for fast sub-millisecond retrieval.
 * @type {Map<string, string>}
 */
const inMemoryImageCache = new Map();

/**
 * Loads persistent cache from localStorage into in-memory cache on startup.
 * @returns {void}
 */
function initializePersistentCache() {
  if (typeof window === "undefined" || !window.localStorage) {
    return;
  }
  try {
    const rawStoredCache = window.localStorage.getItem(CARD_IMAGE_CACHE_STORAGE_KEY);
    if (rawStoredCache) {
      /** @type {Record<string, string>} */
      const parsedStoredCache = JSON.parse(rawStoredCache);
      if (parsedStoredCache && typeof parsedStoredCache === "object") {
        Object.entries(parsedStoredCache).forEach(([cacheKey, imageUrl]) => {
          if (typeof cacheKey === "string" && typeof imageUrl === "string") {
            inMemoryImageCache.set(cacheKey, imageUrl);
          }
        });
      }
    }
  } catch (storageError) {
    console.warn("Could not initialize card image persistent cache from localStorage:", storageError);
  }
}

/**
 * Saves in-memory cache entries back to localStorage.
 * @returns {void}
 */
function persistCacheToStorage() {
  if (typeof window === "undefined" || !window.localStorage) {
    return;
  }
  try {
    /** @type {Record<string, string>} */
    const cacheObject = {};
    inMemoryImageCache.forEach((imageUrl, cacheKey) => {
      cacheObject[cacheKey] = imageUrl;
    });
    window.localStorage.setItem(CARD_IMAGE_CACHE_STORAGE_KEY, JSON.stringify(cacheObject));
  } catch (storageError) {
    console.warn("Could not persist card image cache to localStorage:", storageError);
  }
}

// Initialize cache from localStorage
initializePersistentCache();

/**
 * Computes a deterministic integer hash from a string identifier.
 * @param {string} inputString - Identifier string (title, link, label).
 * @returns {number} Positive integer hash.
 */
function computeDeterministicHash(inputString) {
  if (!inputString || typeof inputString !== "string") {
    return 1;
  }
  let hashAccumulator = 0;
  for (let characterIndex = 0; characterIndex < inputString.length; characterIndex += 1) {
    const characterCode = inputString.charCodeAt(characterIndex);
    hashAccumulator = ((hashAccumulator << 5) - hashAccumulator) + characterCode;
    hashAccumulator |= 0;
  }
  return Math.abs(hashAccumulator);
}

/**
 * Fetches seeded placeholder images from Lorem Picsum (Fastly CDN).
 * URL format: https://picsum.photos/seed/{seed}/{width}/{height}
 *
 * @param {number|string|null} [seed=null] - Seed value for deterministic images.
 * @returns {string} Absolute image URL.
 */
export function getAbstractImageUrl(seed = null) {
  /** @type {number} */
  const resolvedSeed = seed !== null && seed !== undefined && !Number.isNaN(Number(seed))
    ? Number(seed)
    : Math.floor(Math.random() * 1000) + 1;

  return `https://picsum.photos/seed/${resolvedSeed}/800/400`;
}

/**
 * Retrieves a cached image URL for a card, ensuring identical images across page reloads.
 * If an explicit image source is provided, it is returned directly.
 * Otherwise, resolves and caches a deterministic abstract image URL keyed by the card's identifier.
 *
 * @param {string} cardIdentifier - Unique card key (e.g. title, link, or label).
 * @param {string} [explicitSource=""] - Optional explicit image source path or URL.
 * @returns {string} Cached or resolved image URL.
 */
export function getCachedCardImageUrl(cardIdentifier, explicitSource = "") {
  if (explicitSource && typeof explicitSource === "string") {
    return explicitSource;
  }

  const lookupKey = (cardIdentifier || "").trim();
  if (!lookupKey) {
    return getAbstractImageUrl(1);
  }

  // Check in-memory cache first
  if (inMemoryImageCache.has(lookupKey)) {
    return /** @type {string} */ (inMemoryImageCache.get(lookupKey));
  }

  // Compute deterministic seed based on string hash
  const hashValue = computeDeterministicHash(lookupKey);
  const deterministicSeed = (hashValue % 1000) + 1;
  const generatedImageUrl = getAbstractImageUrl(deterministicSeed);

  // Store in cache and persist
  inMemoryImageCache.set(lookupKey, generatedImageUrl);
  persistCacheToStorage();

  // Pre-warm browser image cache
  if (typeof window !== "undefined" && typeof Image !== "undefined") {
    const preloaderImage = new Image();
    preloaderImage.src = generatedImageUrl;
  }

  return generatedImageUrl;
}

