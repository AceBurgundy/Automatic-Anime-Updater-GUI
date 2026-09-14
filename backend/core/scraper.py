import asyncio
import io
import json
import logging
import random
import re
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Callable
from urllib.parse import urljoin
import httpx


from thefuzz import fuzz
from playwright.async_api import async_playwright, Page, BrowserContext, Browser, TimeoutError as PlaywrightTimeoutError

try:
    from camoufox.async_api import AsyncCamoufox
    CAMOUFOX_AVAILABLE = True
except ImportError:
    CAMOUFOX_AVAILABLE = False

try:
    from playwright_stealth import Stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

from config import (
    BASE_URLS,
    HEADLESS,
    FALLBACK_MAX_RETRIES,
    PROJECT_DIR,
    BROWSER_TYPE,
    AUDIO_PREFERENCE,
    PREFERRED_RESOLUTION,
)
from constants import (
    DEFAULT_PREFERRED_RESOLUTION,
    VALID_RESOLUTIONS,
    RESOLUTION_PRIORITY_MAP,
)
from core.ai_helper import AIHelper
from core.state_manager import StateManager


logger = logging.getLogger("anime_refresher.scraper")

@dataclass
class AnimepaheItem:
    title: str
    episode_num: int
    play_url: str
    anime_session: str = ""

class AnimepaheScraper:
    def __init__(
        self,
        state_manager: StateManager,
        base_urls: List[str] = None,
        headless: bool = HEADLESS,
        browser_type: str = BROWSER_TYPE,
        audio_preference: str = AUDIO_PREFERENCE,
        preferred_resolution: str = PREFERRED_RESOLUTION
    ):
        self.state_manager = state_manager
        self.base_urls = base_urls or BASE_URLS
        self.headless = headless
        self.browser_type = browser_type.lower()
        self.audio_preference = audio_preference.lower()
        self.preferred_resolution = preferred_resolution.lower().rstrip("p")
        self.active_base_url = self.base_urls[0]
        self.ai_helper = AIHelper()
        self.profile_dir = PROJECT_DIR / ".browser_profile"
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.debug_dir = PROJECT_DIR / "debug_screenshots"
        self.debug_dir.mkdir(parents=True, exist_ok=True)

        self.camoufox_cm = None
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        logger.debug(f"Initializing scraper browser (Engine: {self.browser_type}, Headless: {self.headless})...")
        
        if self.browser_type in ("firefox", "camoufox") and CAMOUFOX_AVAILABLE:
            logger.info("Launching Camoufox stealth anti-detect engine (humanize=True)...")
            self.camoufox_cm = AsyncCamoufox(headless=self.headless, humanize=True)
            self.browser = await self.camoufox_cm.__aenter__()
            self.page = await self.browser.new_page()
            self.context = self.page.context
        else:
            self.playwright = await async_playwright().start()
            if self.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(
                    headless=self.headless,
                    firefox_user_prefs={
                        "dom.webdriver.enabled": False,
                        "useAutomationExtension": False,
                        "general.useragent.override": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0"
                    }
                )
                self.context = await self.browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
                    locale="en-US"
                )
                self.page = await self.context.new_page()
            else:
                chrome_args = [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars",
                    "--disable-dev-shm-usage",
                    "--window-size=1920,1080"
                ]
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                try:
                    self.context = await self.playwright.chromium.launch_persistent_context(
                        str(self.profile_dir.resolve()),
                        headless=self.headless,
                        channel="chrome",
                        ignore_default_args=["--enable-automation"],
                        args=chrome_args,
                        viewport={"width": 1920, "height": 1080},
                        user_agent=user_agent,
                        locale="en-US"
                    )
                except Exception as e:
                    logger.debug(f"Could not launch Chrome channel ({e}). Using bundled chromium...")
                    self.context = await self.playwright.chromium.launch_persistent_context(
                        str(self.profile_dir.resolve()),
                        headless=self.headless,
                        ignore_default_args=["--enable-automation"],
                        args=chrome_args,
                        viewport={"width": 1920, "height": 1080},
                        user_agent=user_agent,
                        locale="en-US"
                    )
                if STEALTH_AVAILABLE:
                    try:
                        await Stealth().apply_stealth_async(self.context)
                    except Exception:
                        pass
                self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
                if STEALTH_AVAILABLE:
                    try:
                        await Stealth().apply_stealth_async(self.page)
                    except Exception:
                        pass

        logger.info(f"Browser started successfully (Engine: {self.browser_type.capitalize()}, Headless: {self.headless})")

    async def close(self):
        logger.debug("Closing browser session...")
        if hasattr(self, "page") and self.page:
            try:
                await self.page.close()
            except Exception:
                pass
        if self.context:
            try:
                await self.context.close()
            except Exception:
                pass
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
        if self.camoufox_cm:
            try:
                await self.camoufox_cm.__aexit__(None, None, None)
            except Exception:
                pass
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass

    async def _create_page(self) -> Page:
        if hasattr(self, "page") and self.page and not self.page.is_closed():
            return self.page
        if self.browser:
            try:
                if hasattr(self.browser, "new_page"):
                    self.page = await self.browser.new_page()
                    self.context = getattr(self.page, "context", None)
                elif self.context and not self.context.is_closed():
                    self.page = await self.context.new_page()
                else:
                    self.page = await self.browser.new_page()
                    self.context = getattr(self.page, "context", None)
            except Exception:
                if self.context and not self.context.is_closed():
                    self.page = await self.context.new_page()
                elif hasattr(self.browser, "new_page"):
                    self.page = await self.browser.new_page()
            return self.page
        elif self.context and not self.context.is_closed():
            self.page = await self.context.new_page()
            return self.page
        raise RuntimeError("Browser context is not initialized")

    async def _reset_page(self) -> Page:
        """Safely resets the active page to clear in-flight navigation states."""
        if hasattr(self, "page") and self.page:
            try:
                if not self.page.is_closed():
                    await self.page.close()
            except Exception:
                pass
        self.page = None
        return await self._create_page()

    async def _reset_browser_context(self) -> Page:
        """
        Clears all cookies, storage, and in-flight tabs to completely purge
        corrupted Cloudflare challenge tokens (__cf_chl_rt_tk, etc.).
        """
        logger.warning("Purging browser context cookies and resetting active session...")
        if hasattr(self, "page") and self.page:
            try:
                if not self.page.is_closed():
                    await self.page.close()
            except Exception:
                pass
        self.page = None

        if self.context and not self.context.is_closed():
            try:
                await self.context.clear_cookies()
            except Exception as e:
                logger.debug(f"Failed to clear cookies: {e}")

        return await self._create_page()

    async def _safe_goto(self, url: str, wait_until: str = "domcontentloaded", timeout: float = 30000) -> Tuple[Page, Optional[Any]]:
        """Safely navigates to a URL, retrying once if connection drop occurs."""
        page = await self._create_page()
        try:
            response = await page.goto(url, wait_until=wait_until, timeout=timeout)
            return page, response
        except Exception as e:
            logger.debug(f"Navigation to {url} encountered error ({e}). Resetting page and retrying...")
            page = await self._reset_page()
            response = await page.goto(url, wait_until=wait_until, timeout=timeout)
            return page, response

    async def jitter(self, min_sec: float = 1.0, max_sec: float = 2.5):
        """Variable delay with realistic jitter."""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def _human_mouse_move(self, page: Page, target_x: float, target_y: float, steps: int = 15):
        """Simulates smooth mouse movement."""
        try:
            if self.browser_type in ("firefox", "camoufox") and CAMOUFOX_AVAILABLE:
                await page.mouse.move(target_x, target_y)
            else:
                vp = page.viewport_size or {"width": 1920, "height": 1080}
                cur_x = random.uniform(vp["width"] * 0.3, vp["width"] * 0.7)
                cur_y = random.uniform(vp["height"] * 0.3, vp["height"] * 0.7)
                for i in range(1, steps + 1):
                    t = i / steps
                    factor = t * t * (3 - 2 * t)
                    x = cur_x + (target_x - cur_x) * factor + random.uniform(-2, 2)
                    y = cur_y + (target_y - cur_y) * factor + random.uniform(-2, 2)
                    await page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.015, 0.035))
                await page.mouse.move(target_x, target_y)
        except Exception:
            pass

    async def _human_scroll(self, page: Page):
        """Simulates realistic browsing scroll behavior."""
        try:
            delta = random.randint(180, 420)
            await page.mouse.wheel(0, delta)
            await asyncio.sleep(random.uniform(0.2, 0.5))
            if random.random() < 0.35:
                await page.mouse.wheel(0, -random.randint(60, 150))
                await asyncio.sleep(random.uniform(0.1, 0.3))
        except Exception:
            pass

    async def _handle_cloudflare_if_present(self, page: Page, max_wait: int = 30) -> bool:
        """Detects and waits for Cloudflare Turnstile / Managed challenge clearance."""
        for sec in range(0, max_wait, 2):
            try:
                title = await page.title()
                current_url = page.url
            except Exception:
                title = ""
                current_url = ""

            title_clean = title.strip()

            # Check DOM for challenge markers
            has_challenge_dom = False
            try:
                has_challenge_dom = await page.evaluate('''() => {
                    return Boolean(
                        document.querySelector('#challenge-stage, #cf-stage, #turnstile-wrapper, .cf-turnstile, iframe[src*="challenges.cloudflare.com"], iframe[src*="cloudflare"], #challenge-running, #challenge-error-title')
                    );
                }''')
            except Exception:
                pass

            is_cf_challenge = (
                not title_clean
                or "Just a moment" in title
                or "Performing security" in title
                or "__cf_chl" in current_url
                or "Attention Required" in title
                or "Turnstile" in title
                or "Cloudflare" in title
                or "Verify you are human" in title
                or "Security Check" in title
                or "502" in title
                or "503" in title
                or "520" in title
                or "403" in title
                or "429" in title
                or has_challenge_dom
            )

            # If not visibly in a challenge and URL has settled
            if not is_cf_challenge and not title.startswith("Loading"):
                try:
                    content_check = await page.evaluate('''() => {
                        const hasAnimeContent = Boolean(document.querySelector('nav, .navbar, .theatre, .episode, #search, .theatre-info, .episode-wrap, #downloadMenu, #pickDownload'));
                        const hasKwikContent = Boolean(document.querySelector('form button, button[type="submit"], .button.is-success, .button.is-primary, a.button, .box, input[type="submit"]'));
                        return hasAnimeContent || hasKwikContent;
                    }''')
                    if content_check:
                        logger.debug(f"Cloudflare verification cleared (Title: '{title}')")
                        return True
                except Exception:
                    pass

            logger.debug(f"Cloudflare wait ({sec+2}s/{max_wait}s): Title = '{title}', URL = '{current_url[:60]}...'")

            # Try finding Turnstile iframe on page and clicking coordinates
            try:
                cf_iframes = page.locator("iframe[src*='cloudflare'], iframe[src*='turnstile'], iframe[src*='challenges'], iframe[title*='Cloudflare'], iframe[title*='Turnstile']")
                count = await cf_iframes.count()
                if count > 0:
                    for idx in range(count):
                        iframe_el = cf_iframes.nth(idx)
                        box = await iframe_el.bounding_box(timeout=1500)
                        if box:
                            click_x = box["x"] + min(30, box["width"] / 4)
                            click_y = box["y"] + box["height"] / 2
                            await page.mouse.click(click_x, click_y)
            except Exception:
                pass

            # Check inner frame elements for Turnstile checkbox
            try:
                for frame in page.frames:
                    if "cloudflare" in frame.url or "turnstile" in frame.url or "challenge" in frame.url:
                        box = await frame.query_selector("input[type='checkbox'], span.mark, .ctp-checkbox-label, #cf-stage, #challenge-stage")
                        if box:
                            logger.debug("Found Cloudflare Turnstile checkbox inside frame. Clicking...")
                            await box.click(timeout=2000)
            except Exception:
                pass

            await asyncio.sleep(2.0)

        try:
            title = await page.title()
            title_clean = title.strip()
            current_url = page.url
            is_valid = (
                title_clean != ""
                and "Just a moment" not in title
                and "Performing security" not in title
                and "__cf_chl" not in current_url
                and "Attention Required" not in title
                and "Turnstile" not in title
                and "Cloudflare" not in title
                and "Verify you are human" not in title
            )
            return is_valid
        except Exception:
            return False

    async def find_active_mirror(self) -> str:
        """Tests base URLs and selects the first responsive Animepahe mirror with fast failover."""
        page = await self._create_page()
        for url in self.base_urls:
            try:
                logger.info(f"Testing mirror connection: {url}...")
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=6000)
                passed = await self._handle_cloudflare_if_present(page, max_wait=8)
                if passed:
                    self.active_base_url = url
                    logger.info(f"Selected active Animepahe mirror: {self.active_base_url}")
                    return url
                else:
                    logger.debug(f"Mirror {url} did not clear challenge in 8s. Probing next mirror...")
            except Exception as e:
                logger.debug(f"Mirror {url} probe timed out or failed: {e}")

        # If all mirrors are currently challenged, default immediately to the first mirror without blocking
        logger.info(f"Selected active Animepahe mirror: {self.base_urls[0]}")
        self.active_base_url = self.base_urls[0]
        return self.base_urls[0]

    async def rotate_mirror(self) -> str:
        """
        Rotates to the next available mirror in base_urls, purges corrupted challenge
        state/cookies via _reset_browser_context, and probes connectivity on the new mirror.
        """
        if not self.base_urls:
            return self.active_base_url

        try:
            cur_idx = self.base_urls.index(self.active_base_url)
        except ValueError:
            cur_idx = 0

        next_idx = (cur_idx + 1) % len(self.base_urls)
        old_mirror = self.active_base_url
        self.active_base_url = self.base_urls[next_idx]
        logger.warning(f"Mirror rotation triggered: {old_mirror} -> {self.active_base_url}")

        # Purge cookies & page context to prevent cross-mirror challenge poisoning
        page = await self._reset_browser_context()
        try:
            logger.info(f"Probing rotated mirror {self.active_base_url}...")
            page, _ = await self._safe_goto(self.active_base_url, wait_until="domcontentloaded", timeout=15000)
            await self._handle_cloudflare_if_present(page, max_wait=15)
        except Exception as e:
            logger.warning(f"Error during mirror switch probe to {self.active_base_url}: {e}")

        return self.active_base_url

    async def scrape_recent_releases(self, max_pages: int = 3) -> List[Dict[str, Any]]:
        """Scrapes recent episode release cards across pages 1 to max_pages."""
        page = await self._create_page()
        releases: List[Dict[str, Any]] = []

        try:
            for page_num in range(1, max_pages + 1):
                url = f"{self.active_base_url}/?page={page_num}" if page_num > 1 else self.active_base_url
                logger.info(f"Scraping recent releases (Page {page_num}/{max_pages}): {url}")
                await page.goto(url, wait_until="commit", timeout=30000)
                await self._handle_cloudflare_if_present(page, max_wait=35)
                await self.jitter(1.0, 2.0)

                # Strategy 1: Fetch internal airing API
                api_items = await page.evaluate(f'''async () => {{
                    try {{
                        const res = await fetch('/api?m=airing&page={page_num}');
                        if (res.ok) {{
                            const json = await res.json();
                            return json.data || [];
                        }}
                    }} catch (e) {{}}
                    return [];
                }}''')

                if api_items:
                    logger.info(f"Page {page_num}: Retrieved {len(api_items)} releases via internal API.")
                    for item in api_items:
                        title = item.get("anime_title") or item.get("title", "")
                        ep_num = item.get("episode", 0)
                        session = item.get("session", "")
                        anime_session = item.get("anime_session", "")
                        
                        if anime_session and session:
                            play_url = urljoin(self.active_base_url, f"/play/{anime_session}/{session}")
                        else:
                            play_url = urljoin(self.active_base_url, f"/play/{session}")

                        releases.append({
                            "title": title.strip(),
                            "episode_num": int(ep_num) if str(ep_num).isdigit() else 0,
                            "play_url": play_url,
                            "anime_session": anime_session
                        })
                    continue

                # Strategy 2: DOM fallback
                logger.debug("Parsing DOM for latest releases...")
                items = await page.evaluate('''() => {
                    const results = [];
                    const cards = document.querySelectorAll('.episode-wrap, .episode, .latest-release');
                    cards.forEach(card => {
                        const titleEl = card.querySelector('.episode-title, .title a, h2 a, a[title]');
                        const playEl = card.querySelector('.play, a.play, a[href*="/play/"]');
                        const epEl = card.querySelector('.episode-number, .episode-num');

                        let title = titleEl ? (titleEl.getAttribute('title') || titleEl.textContent.trim()) : '';
                        let playHref = playEl ? playEl.getAttribute('href') : (titleEl ? titleEl.getAttribute('href') : '');
                        let epText = epEl ? epEl.textContent.trim() : '';

                        if (title && playHref) {
                            results.push({
                                title: title,
                                play_href: playHref,
                                episode_text: epText
                            });
                        }
                    });
                    return results;
                }''')

                for it in items:
                    raw_title = it.get("title", "").strip()
                    play_href = it.get("play_href", "").strip()
                    ep_text = it.get("episode_text", "").strip()

                    ep_match = re.search(r'(\d+)', ep_text) or re.search(r'Episode\s*(\d+)', raw_title, re.IGNORECASE)
                    ep_num = int(ep_match.group(1)) if ep_match else 0

                    full_play_url = urljoin(self.active_base_url, play_href)
                    anime_session_match = re.search(r'/play/([a-zA-Z0-9\-]+)/', play_href)
                    anime_session = anime_session_match.group(1) if anime_session_match else ""

                    releases.append({
                        "title": raw_title,
                        "episode_num": ep_num,
                        "play_url": full_play_url,
                        "anime_session": anime_session
                    })

                await self.jitter(1.0, 2.0)

            logger.info(f"Total scraped releases across {max_pages} pages: {len(releases)}")
            return releases
        except Exception as e:
            logger.error(f"Error scraping recent releases: {e}", exc_info=True)
            return releases

    def match_local_anime(self, web_title: str, local_folder_names: List[str], threshold: int = 85) -> Optional[str]:
        """Fuzzy matching local folder names against web titles."""
        clean_web = re.sub(r'[^\w\s]', ' ', web_title).lower()
        best_match = None
        best_score = 0

        for local_folder in local_folder_names:
            clean_local = re.sub(r'[^\w\s]', ' ', local_folder).lower()
            score = fuzz.token_set_ratio(clean_web, clean_local)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = local_folder

        if best_match:
            logger.debug(f"Fuzzy match: '{web_title}' -> '{best_match}' (score: {best_score}/100)")
        return best_match

    async def _ensure_on_mirror(self, page: Page, allow_rotate: bool = True) -> bool:
        """Ensures the page is currently navigated to the active Animepahe mirror with Cloudflare cleared."""
        try:
            current_url = page.url or ""
            current_title = ""
            try:
                current_title = await page.title()
            except Exception:
                pass

            needs_nav = (
                not current_url
                or current_url == "about:blank"
                or not current_url.startswith(self.active_base_url)
                or "__cf_chl" in current_url
                or "Loading" in current_title
                or "Just a moment" in current_title
                or "Attention Required" in current_title
            )

            if needs_nav:
                logger.debug(f"Ensuring page is on active mirror ({self.active_base_url}), currently at '{current_url}'")
                page, _ = await self._safe_goto(self.active_base_url, wait_until="commit", timeout=20000)
                passed = await self._handle_cloudflare_if_present(page, max_wait=25)
                if not passed and allow_rotate and len(self.base_urls) > 1:
                    logger.warning(f"Active mirror {self.active_base_url} blocked by Cloudflare. Rotating mirror...")
                    await self.rotate_mirror()
                    return await self._ensure_on_mirror(self.page or page, allow_rotate=False)
                return passed
            return True
        except Exception as e:
            logger.debug(f"Error ensuring mirror navigation: {e}")
            return False

    async def _execute_single_search_api_call(self, page: Page, query_str: str) -> List[Dict[str, Any]]:
        """Executes a single search API request against Animepahe via browser page evaluate."""
        try:
            on_mirror = await self._ensure_on_mirror(page)
            if not on_mirror:
                logger.warning(f"Active mirror {self.active_base_url} is not accessible for search API")
                return []
            eval_result = await asyncio.wait_for(
                page.evaluate('''async (queryTitle) => {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 8000);
                    try {
                        const res = await fetch('/api?m=search&q=' + encodeURIComponent(queryTitle), {
                            signal: controller.signal,
                            headers: { 'Accept': 'application/json' }
                        });
                        clearTimeout(timeoutId);
                        if (res.ok) {
                            const json = await res.json();
                            return { status: res.status, data: json.data || [] };
                        }
                        return { status: res.status, error: 'HTTP ' + res.status };
                    } catch (e) {
                        clearTimeout(timeoutId);
                        return { status: 0, error: e.toString() };
                    }
                }''', query_str),
                timeout=12.0
            )

            if isinstance(eval_result, dict):
                status = eval_result.get("status", 0)
                if status in (403, 503, 520):
                    logger.warning(f"Search API returned status {status} (Cloudflare challenge suspected). Waiting for clearance...")
                    passed = await self._handle_cloudflare_if_present(page, max_wait=20)
                    if passed:
                        return await self._execute_single_search_api_call(page, query_str)
                data = eval_result.get("data")
                if data is not None:
                    return data
                if eval_result.get("error"):
                    logger.debug(f"Search API returned error for '{query_str}': {eval_result.get('error')}")
            elif isinstance(eval_result, list):
                return eval_result
            return []
        except Exception as e:
            logger.debug(f"Search API error for '{query_str}': {e}")
            return []

    async def _resolve_metadata_aliases(self, english_title: str) -> List[str]:
        """Queries AniList and Jikan/MAL APIs to resolve official Romaji titles and synonyms."""
        aliases = []
        # 1. AniList GraphQL
        try:
            query = '''
            query ($search: String) {
              Media (search: $search, type: ANIME) {
                title { romaji english native }
                synonyms
              }
            }
            '''
            async with httpx.AsyncClient(timeout=3.5, follow_redirects=True) as client:
                res = await client.post('https://graphql.anilist.co', json={'query': query, 'variables': {'search': english_title}})
                if res.status_code == 200:
                    media = res.json().get('data', {}).get('Media')
                    if media:
                        titles = media.get('title', {})
                        for k in ('romaji', 'english'):
                            v = titles.get(k)
                            if v and v.lower() != english_title.lower() and v not in aliases:
                                aliases.append(v)
                        for s in media.get('synonyms', []):
                            if s and s.lower() != english_title.lower() and s not in aliases:
                                aliases.append(s)
        except Exception as e:
            logger.debug(f"AniList alias resolution error: {e}")

        # 2. Jikan / MAL API
        try:
            clean = re.sub(r'\s+(?:season\s+\d+|s\d+|ii|iii|iv|v|act\.\d+)\b', '', english_title, flags=re.IGNORECASE)
            url = f"https://api.jikan.moe/v4/anime?q={urllib.parse.quote(clean)}&limit=1"
            async with httpx.AsyncClient(timeout=3.5, follow_redirects=True) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    if data:
                        top = data[0]
                        for k in ("title", "title_japanese", "title_english"):
                            v = top.get(k)
                            if v and v.lower() != english_title.lower() and v not in aliases:
                                aliases.append(v)
        except Exception as e:
            logger.debug(f"Jikan alias resolution error: {e}")

        return aliases

    async def search_anime_title(self, title: str) -> List[Dict[str, Any]]:
        """
        Queries Animepahe's internal search API using a multi-tier progressive query strategy:
        1. Full cleaned title.
        2. Base franchise title (stripped of Roman numerals, Season X, arc subtitles).
        3. Distinctive keyword pruning (stopwords removed, sub-clauses).
        4. Public metadata alias bridge (AniList GraphQL & Jikan Romaji/synonyms resolution).
        """
        page = await self._create_page()
        try:
            on_mirror = await self._ensure_on_mirror(page)
            if not on_mirror:
                logger.warning(f"Active mirror {self.active_base_url} is not accessible for search")
                return []

            # Tier 1 - 3: Progressive decomposed queries
            queries = self.ai_helper.decompose_search_queries(title)
            for idx, q in enumerate(queries, start=1):
                logger.debug(f"[Search Tier {idx}] Querying Animepahe: '{q}'")
                results = await self._execute_single_search_api_call(page, q)
                if results:
                    logger.debug(f"[Search Tier {idx}] Found {len(results)} candidate(s) for query: '{q}'")
                    return results

            # Tier 4: Metadata alias bridge (AniList + Jikan synonyms)
            aliases = await self._resolve_metadata_aliases(title)
            if aliases:
                for al in aliases:
                    for al_q in self.ai_helper.decompose_search_queries(al):
                        logger.debug(f"[Search Tier 4 Alias] Querying Animepahe with alias query: '{al_q}'")
                        results = await self._execute_single_search_api_call(page, al_q)
                        if results:
                            return results

            logger.debug(f"All progressive search tiers yielded 0 results for '{title}'")
            return []
        except Exception as e:
            logger.error(f"Error executing search queries for '{title}': {e}")
            return []

    def _select_preferred_source(
        self,
        options: List[Dict[str, str]],
        anime_title: str,
        episode_num: int,
        preferred_resolution: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Selects download option based on AUDIO_PREFERENCE ('sub', 'dub', 'sub_strict', 'dub_strict')
        and PREFERRED_RESOLUTION ('1080', '720', '480', '360') with closest-resolution fallback routing.
        """
        if not options:
            return None

        subbed_options = [
            opt for opt in options
            if not re.search(r'\b(eng|dub|english)\b', opt["text"], re.IGNORECASE)
        ]
        dubbed_options = [
            opt for opt in options
            if re.search(r'\b(eng|dub|english)\b', opt["text"], re.IGNORECASE)
        ]

        # Strict modes
        if self.audio_preference == "sub_strict":
            usable_options = subbed_options
            if not usable_options:
                logger.info(f"Strict Subbed active: Skipping '{anime_title}' Ep {episode_num} (No subbed release available)")
                return None
        elif self.audio_preference == "dub_strict":
            usable_options = dubbed_options
            if not usable_options:
                logger.info(f"Strict Dubbed active: Skipping '{anime_title}' Ep {episode_num} (No dubbed release available)")
                return None
        elif self.audio_preference == "dub":
            usable_options = dubbed_options if dubbed_options else subbed_options
        else:
            # Default "sub"
            usable_options = subbed_options if subbed_options else dubbed_options

        if not usable_options:
            usable_options = options

        target_res = (preferred_resolution or self.preferred_resolution).lower().rstrip("p")
        if target_res not in RESOLUTION_PRIORITY_MAP:
            target_res = DEFAULT_PREFERRED_RESOLUTION

        exact_res_tag = f"{target_res}p"
        priority_list = RESOLUTION_PRIORITY_MAP.get(target_res, ["1080p", "720p", "480p", "360p"])

        # Check for exact preferred resolution
        has_exact = any(exact_res_tag in opt["text"] for opt in usable_options)
        if has_exact:
            for opt in usable_options:
                if exact_res_tag in opt["text"]:
                    self.state_manager.reset_viewed_count(anime_title, episode_num)
                    logger.info(f"Selected exact preferred {exact_res_tag} ({self.audio_preference.upper()}): '{opt['text']}'")
                    return opt

        # Exact preferred resolution missing -> Execute Wait & Retry Protocol
        viewed_count = self.state_manager.increment_viewed_count(anime_title, episode_num)
        logger.info(f"{exact_res_tag} missing for '{anime_title}' Ep {episode_num}. Retry count: {viewed_count}/{FALLBACK_MAX_RETRIES}")

        if viewed_count < FALLBACK_MAX_RETRIES:
            logger.info(f"Skipping episode {episode_num} for this run awaiting {exact_res_tag} release.")
            return None

        # Threshold reached -> Closest resolution fallback routing
        logger.info(f"Threshold reached ({viewed_count} runs). Falling back to closest available resolution.")
        for res_tag in priority_list:
            match = next((opt for opt in usable_options if res_tag in opt["text"]), None)
            if match:
                logger.info(f"Selected closest fallback resolution '{res_tag}': '{match['text']}'")
                return match

        # Final fallback to first usable option
        if usable_options:
            return usable_options[0]

        return None


    async def get_show_episodes(self, play_url: str) -> Tuple[str, Dict[int, str]]:
        """
        Retrieves all available episode numbers and play URLs for a series using Release API and DOM.
        """
        page = await self._create_page()
        try:
            # Normalize play_url to active mirror domain
            for u in self.base_urls:
                if play_url.startswith(u):
                    play_url = play_url.replace(u, self.active_base_url, 1)
                    break

            logger.info(f"Accessing episode catalog for: {play_url}")
            on_mirror = await self._ensure_on_mirror(page)
            if not on_mirror:
                raise RuntimeError(f"Mirror {self.active_base_url} is inaccessible or blocked by Cloudflare challenge")

            # Extract anime session directly from play_url
            anime_session = ""
            m = re.search(r'/(?:play|anime)/([a-zA-Z0-9\-]+)', play_url)
            if m:
                anime_session = m.group(1)

            episodes: Dict[int, str] = {}
            show_title = ""

            # Fetch via release API if anime_session exists
            if anime_session:
                logger.debug(f"Fetching complete episode list via release API for session: {anime_session}")
                current_p = 1
                while current_p <= 15:
                    api_data = None
                    for attempt in range(2):
                        try:
                            api_data = await asyncio.wait_for(
                                page.evaluate(f'''async () => {{
                                    const controller = new AbortController();
                                    const timeoutId = setTimeout(() => controller.abort(), 6000);
                                    try {{
                                        const res = await fetch('/api?m=release&id={anime_session}&sort=episode_asc&page={current_p}', {{
                                            signal: controller.signal,
                                            headers: {{ 'Accept': 'application/json' }}
                                        }});
                                        clearTimeout(timeoutId);
                                        if (res.ok) return await res.json();
                                    }} catch (e) {{
                                        clearTimeout(timeoutId);
                                    }}
                                    return null;
                                }}'''),
                                timeout=10.0
                            )
                            if api_data:
                                break
                        except Exception:
                            await asyncio.sleep(0.5)

                    if not api_data or not api_data.get("data"):
                        break

                    for ep_item in api_data.get("data", []):
                        ep_val = ep_item.get("episode", 0)
                        session_val = ep_item.get("session", "")
                        if str(ep_val).isdigit() and session_val:
                            ep_num = int(ep_val)
                            ep_play_url = urljoin(self.active_base_url, f"/play/{anime_session}/{session_val}")
                            episodes[ep_num] = ep_play_url

                    last_p = api_data.get("last_page", 1)
                    if current_p >= last_p:
                        break
                    current_p += 1

                if episodes:
                    logger.info(f"Retrieved {len(episodes)} total episodes for session '{anime_session}' via API.")
                    return show_title or anime_session, episodes

            # If API yielded 0 episodes or session extraction was absent, fallback to page navigation & DOM
            page, _ = await self._safe_goto(play_url, wait_until="commit", timeout=25000)
            await self._handle_cloudflare_if_present(page, max_wait=20)
            await self.jitter(0.5, 1.5)

            # Extract show title from DOM
            show_info = await page.evaluate('''() => {
                const infoContainer = document.querySelector('.theatre-info');
                let showTitle = '';
                let showHref = '';

                if (infoContainer) {
                    const anchor = infoContainer.querySelector('h1 a, h2 a, a[href*="/anime/"]');
                    if (anchor) {
                        showTitle = anchor.getAttribute('title') || anchor.textContent.trim();
                        showHref = anchor.getAttribute('href') || '';
                    }
                }
                if (!showHref) {
                    const fallbackAnchor = document.querySelector('h1 a, .nav-item a[href*="/anime/"]');
                    if (fallbackAnchor) {
                        showTitle = fallbackAnchor.getAttribute('title') || fallbackAnchor.textContent.trim();
                        showHref = fallbackAnchor.getAttribute('href') || '';
                    }
                }
                return { title: showTitle, href: showHref };
            }''')

            show_title = show_info.get("title", "")
            show_href = show_info.get("href", "")

            episodes_dom = await page.evaluate('''() => {
                const epMap = {};
                const epElements = document.querySelectorAll('.episode-list .episode, .episode-wrap, .episode, a[href*="/play/"]');
                epElements.forEach(el => {
                    const numEl = el.querySelector('.episode-number, .episode-num, .episode-title');
                    const playLink = el.tagName === 'A' ? el : el.querySelector('a[href*="/play/"]');

                    let numText = numEl ? numEl.textContent.trim() : el.textContent.trim();
                    let href = playLink ? playLink.getAttribute('href') : '';

                    if (href) {
                        const m = numText.match(/(\\d+)/);
                        if (m) {
                            const epNum = parseInt(m[1], 10);
                            epMap[epNum] = href;
                        }
                    }
                });
                return epMap;
            }''')

            episodes = {int(k): urljoin(self.active_base_url, v) for k, v in episodes_dom.items()}
            logger.info(f"Retrieved {len(episodes)} total episodes for '{show_title}' via DOM.")
            return show_title, episodes

        except Exception as e:
            logger.error(f"Error fetching show episodes from {play_url}: {e}")
            try:
                await self._reset_page()
            except Exception:
                pass
            raise

    async def download_episode_to_temp(
        self,
        anime_title: str,
        episode_num: int,
        play_url: str,
        temp_target_file: Path,
        preferred_resolution: Optional[str] = None,
        progress_callback: Optional[Callable[[float, int, int, float], None]] = None
    ) -> bool:
        """
        Resolves stream and downloads video directly into temp_target_file using the browser session.
        Guarantees 100% authorization and cookie alignment with Kwik / CDN.
        """
        page = await self._create_page()
        try:
            logger.info(f"Resolving download stream for '{anime_title}' Ep {episode_num}: {play_url}")
            page, _ = await self._safe_goto(play_url, wait_until="domcontentloaded", timeout=35000)
            await self._handle_cloudflare_if_present(page, max_wait=30)
            await self.jitter(1.0, 2.0)

            # Wait for and click #downloadMenu button to open #pickDownload
            btn = None
            for _ in range(2):
                try:
                    btn = await page.wait_for_selector("#downloadMenu, button.dropdown-toggle, .download", timeout=18000)
                    if btn:
                        break
                except Exception:
                    await self._handle_cloudflare_if_present(page, max_wait=10)

            if not btn:
                logger.error(f"Download menu button not found on play page for '{anime_title}' Ep {episode_num}")
                return False

            logger.debug("Clicking #downloadMenu dropdown button...")
            try:
                await btn.click()
            except Exception as click_err:
                logger.debug(f"Direct click on #downloadMenu failed ({click_err}). Dispatching JS click...")
                await page.evaluate('''() => {
                    const el = document.querySelector('#downloadMenu, button.dropdown-toggle, .download');
                    if (el) el.click();
                }''')
            
            # Poll for #pickDownload options with JS click fallback
            options = []
            for poll_idx in range(8):
                await asyncio.sleep(0.75)
                options = await page.evaluate(r'''() => {
                    const containers = document.querySelectorAll('#pickDownload, .dropdown-menu');
                    const res = [];
                    containers.forEach(c => {
                        c.querySelectorAll('a').forEach(a => {
                            const text = a.textContent.trim();
                            const href = a.getAttribute('href');
                            if (text && href && (href.startsWith('http') || href.includes('pahe.win') || href.includes('/f/') || /\d+p/.test(text))) {
                                res.push({ text: text, href: href });
                            }
                        });
                    });
                    return res;
                }''')
                if options:
                    break
                if poll_idx == 3:
                    logger.debug("Dropdown options not yet visible. Dispatching synthetic MouseEvent click to #downloadMenu...")
                    await page.evaluate('''() => {
                        const el = document.querySelector('#downloadMenu, button.dropdown-toggle, .download');
                        if (el) {
                            el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                        }
                    }''')

            if not options:
                logger.warning(f"No download options found in dropdown for '{anime_title}' Ep {episode_num}")
                await self._reset_page()
                return False

            # Select target option using audio preference and resolution rules
            target_option = self._select_preferred_source(
                options=options,
                anime_title=anime_title,
                episode_num=episode_num,
                preferred_resolution=preferred_resolution
            )
            if not target_option:
                await self._reset_page()
                return False

            target_href = target_option["href"]
            logger.info(f"Selected resolution link: '{target_option['text']}' -> {target_href}")

            # Navigate to redirect page
            logger.debug(f"Navigating to redirect page: {target_href}")
            page, _ = await self._safe_goto(target_href, wait_until="commit", timeout=35000)
            await self._handle_cloudflare_if_present(page, max_wait=30)
            await self.jitter(1.0, 2.0)

            # Extract kwik link
            current_page_url = page.url or ""
            html_content = await page.content()
            m = re.search(r'https?://(?:kwik\.[a-z]+|pahe\.win)/f/([a-zA-Z0-9]+)', html_content)
            kwik_url = m.group(0) if m else current_page_url

            # Only perform explicit navigation if we are not already on the destination Kwik page
            if ("kwik" in kwik_url or "/f/" in kwik_url) and kwik_url != current_page_url and "/f/" not in current_page_url:
                logger.debug(f"Navigating to Kwik page: {kwik_url}")
                page, _ = await self._safe_goto(kwik_url, wait_until="domcontentloaded", timeout=35000)
                await self._handle_cloudflare_if_present(page, max_wait=45)
                await self.jitter(1.0, 2.0)
            else:
                await self._handle_cloudflare_if_present(page, max_wait=45)

            if temp_target_file.exists():
                temp_target_file.unlink()

            logger.info(f"Triggering browser download to temporary path: {temp_target_file}")
            dl_selector = "form button, button[type='submit'], .button.is-success, .button.is-primary, a.button, input[type='submit'], button:has-text('Download'), .btn-download, button"
            
            dl_submit = None
            try:
                dl_submit = await page.wait_for_selector(dl_selector, timeout=25000)
            except Exception:
                logger.debug("Download selector not immediately visible. Checking Cloudflare clearance and DOM state...")
                await self._handle_cloudflare_if_present(page, max_wait=15)
                try:
                    dl_submit = await page.wait_for_selector(dl_selector, timeout=10000)
                except Exception:
                    pass

            # Fallback: check if form exists even if button isn't directly matched
            if not dl_submit:
                has_form = await page.evaluate('''() => Boolean(document.querySelector('form'))''')
                if has_form:
                    logger.debug("Found form in DOM, acquiring submit element...")
                    dl_submit = await page.query_selector("form button, form input[type='submit'], form")

            if not dl_submit:
                logger.error("Download submit button not found on Kwik page")
                return False

            start_dl_time = time.time()
            async with page.expect_download(timeout=90000) as download_info:
                try:
                    await dl_submit.click()
                except Exception:
                    await page.evaluate("() => { const f = document.querySelector('form'); if (f) f.submit(); }")
            download = await download_info.value

            logger.info(f"Browser download streaming from CDN: {download.url[:80]}...")
            
            # Save download to temp target file
            await download.save_as(str(temp_target_file))

            elapsed = time.time() - start_dl_time
            if temp_target_file.exists() and temp_target_file.stat().st_size > 1024 * 1024:
                file_size = temp_target_file.stat().st_size
                file_mb = file_size / (1024 * 1024)
                speed = file_mb / elapsed if elapsed > 0 else 0
                logger.info(f"Download complete: {file_mb:.2f} MB in {elapsed:.1f}s ({speed:.2f} MB/s)")
                
                if progress_callback:
                    progress_callback(100.0, file_size, file_size, speed)
                return True
            else:
                logger.error(f"Download finished but file {temp_target_file} is missing or too small")
                if temp_target_file.exists():
                    temp_target_file.unlink()
                return False

        except Exception as e:
            logger.error(f"Failed to download '{anime_title}' Ep {episode_num}: {e}", exc_info=True)
            if temp_target_file.exists():
                try:
                    temp_target_file.unlink()
                except Exception:
                    pass
            try:
                await self._reset_page()
            except Exception:
                pass
            return False
