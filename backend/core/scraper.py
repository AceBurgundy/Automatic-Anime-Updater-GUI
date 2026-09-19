from asyncio import sleep as asyncio_sleep, wait_for as asyncio_wait_for
from dataclasses import dataclass
from logging import Logger, getLogger
from pathlib import Path
from random import randint, random as random_float, uniform
from re import IGNORECASE, Match, search as re_search, sub as re_sub
from time import time as current_timestamp
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import quote as url_quote, urljoin

from httpx import AsyncClient as HttpAsyncClient, Timeout as HttpTimeout


from thefuzz import fuzz
from playwright.async_api import (
    Browser,
    BrowserContext,
    Download,
    ElementHandle,
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

try:
    from camoufox.async_api import AsyncCamoufox
    CAMOUFOX_AVAILABLE: bool = True
except ImportError:
    CAMOUFOX_AVAILABLE: bool = False

try:
    from playwright_stealth import Stealth
    STEALTH_AVAILABLE: bool = True
except ImportError:
    STEALTH_AVAILABLE: bool = False

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
    DEFAULT_STALL_TIMEOUT_SECONDS,
)
from core.ai_helper import AIHelper
from core.state_manager import StateManager


logger: Logger = getLogger("anime_refresher.scraper")


class DownloadStalledError(Exception):
    """
    Exception raised when a media stream receives zero bytes for the stall timeout threshold.
    """
    pass


@dataclass
class AnimepaheItem:
    """
    Data container representing an individual episode catalog item on Animepahe.

    Attributes
    ----------
    title : str
        Episode title or show name.
    episode_num : int
        Parsed episode sequence number.
    play_url : str
        Direct streaming or episode page URL.
    anime_session : str, default=""
        Unique anime series identifier token.
    """

    title: str
    episode_num: int
    play_url: str
    anime_session: str = ""


class AnimepaheScraper:
    """
    Automated browser scraper and streaming resolver for Animepahe mirror catalogs.

    Attributes
    ----------
    state_manager : StateManager
        State manager for fallback retry tracking.
    base_urls : List[str]
        List of mirror base URLs.
    headless : bool
        Whether the browser engine runs headlessly.
    browser_type : str
        Underlying browser engine name ('camoufox', 'firefox', or 'chrome').
    audio_preference : str
        Language audio preference ('sub', 'dub', 'sub_strict', 'dub_strict').
    preferred_resolution : Optional[str]
        Explicit preferred resolution tier.
    active_base_url : str
        Currently active and responsive mirror URL.
    ai_helper : AIHelper
        Helper for title normalization and fuzzy matching.
    profile_dir : Path
        Persistent browser profile directory.
    debug_dir : Path
        Directory for error and diagnostic screenshots.
    camoufox_cm : Any
        Context manager for Camoufox engine if active.
    playwright : Any
        Playwright driver manager instance.
    browser : Optional[Browser]
        Active Playwright Browser instance.
    context : Optional[BrowserContext]
        Active Playwright BrowserContext instance.
    page : Optional[Page]
        Primary active browser Page.
    """

    state_manager: StateManager
    base_urls: List[str]
    headless: bool
    browser_type: str
    audio_preference: str
    preferred_resolution: Optional[str]
    active_base_url: str
    ai_helper: AIHelper
    profile_dir: Path
    debug_dir: Path
    camoufox_cm: Any
    playwright: Any
    browser: Optional[Browser]
    context: Optional[BrowserContext]
    page: Optional[Page]

    def __init__(
        self,
        state_manager: StateManager,
        base_urls: Optional[List[str]] = None,
        headless: bool = HEADLESS,
        browser_type: str = BROWSER_TYPE,
        audio_preference: str = AUDIO_PREFERENCE,
        preferred_resolution: Optional[str] = None,
    ) -> None:
        """
        Initialize the Animepahe web scraper.

        Parameters
        ----------
        state_manager : StateManager
            State manager instance for persisting retry counts.
        base_urls : Optional[List[str]], default=None
            List of Animepahe mirror URLs.
        headless : bool, default=HEADLESS
            Whether to run the browser in headless mode.
        browser_type : str, default=BROWSER_TYPE
            Browser engine name ('camoufox', 'firefox', or 'chrome').
        audio_preference : str, default=AUDIO_PREFERENCE
            Audio language preference ('sub', 'dub', 'sub_strict', 'dub_strict').
        preferred_resolution : Optional[str], default=None
            Explicit preferred resolution ('1080', '720', '480', '360').
        """
        self.state_manager: StateManager = state_manager
        self.base_urls: List[str] = base_urls or BASE_URLS
        self.headless: bool = headless
        self.browser_type: str = browser_type.lower()
        self.audio_preference: str = audio_preference.lower()
        self.preferred_resolution: Optional[str] = (
            preferred_resolution.lower().rstrip("p") if preferred_resolution else None
        )
        self.active_base_url: str = self.base_urls[0]
        self.ai_helper: AIHelper = AIHelper()
        self.profile_dir: Path = PROJECT_DIR / ".browser_profile"
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.debug_dir: Path = PROJECT_DIR / "debug_screenshots"
        self.debug_dir.mkdir(parents=True, exist_ok=True)

        self.camoufox_cm: Any = None
        self.playwright: Any = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def __aenter__(self) -> "AnimepaheScraper":
        """
        Asynchronously enter the scraper context, starting the browser engine.

        Returns
        -------
        AnimepaheScraper
            The running scraper instance.
        """
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """
        Asynchronously exit the scraper context, terminating the browser engine.

        Parameters
        ----------
        exc_type : Optional[type]
            Exception type if raised.
        exc_val : Optional[BaseException]
            Exception value if raised.
        exc_tb : Optional[Any]
            Traceback if raised.
        """
        await self.close()

    async def start(self) -> None:
        """
        Launch the browser engine and initialize default context and page.
        """
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
                chrome_args: List[str] = [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars",
                    "--disable-dev-shm-usage",
                    "--window-size=1920,1080",
                ]
                user_agent: str = (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                )
                try:
                    self.context = await self.playwright.chromium.launch_persistent_context(
                        str(self.profile_dir.resolve()),
                        headless=self.headless,
                        channel="chrome",
                        ignore_default_args=["--enable-automation"],
                        args=chrome_args,
                        viewport={"width": 1920, "height": 1080},
                        user_agent=user_agent,
                        locale="en-US",
                    )
                except Exception as error:
                    logger.debug(f"Could not launch Chrome channel ({error}). Using bundled chromium...")
                    self.context = await self.playwright.chromium.launch_persistent_context(
                        str(self.profile_dir.resolve()),
                        headless=self.headless,
                        ignore_default_args=["--enable-automation"],
                        args=chrome_args,
                        viewport={"width": 1920, "height": 1080},
                        user_agent=user_agent,
                        locale="en-US",
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

    async def close(self) -> None:
        """
        Close all active pages, contexts, browser processes, and Playwright instances.
        """
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
        """
        Create or return an active, non-closed browser page.

        Returns
        -------
        Page
            Active Playwright Page instance.

        Raises
        ------
        RuntimeError
            If the browser context is not initialized.
        """
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
        """
        Safely resets the active page to clear in-flight navigation states.

        Returns
        -------
        Page
            Newly created active Playwright browser page.
        """
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

        Returns
        -------
        Page
            Newly created active Playwright browser page.
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
            except Exception as error:
                logger.debug(f"Failed to clear cookies: {error}")

        return await self._create_page()

    async def _safe_goto(
        self,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout: float = 30000,
    ) -> Tuple[Page, Optional[Any]]:
        """
        Safely navigates to a URL, retrying once if connection drop occurs.

        Parameters
        ----------
        url : str
            Target URL to navigate to.
        wait_until : str, default "domcontentloaded"
            Playwright navigation lifecycle wait event.
        timeout : float, default 30000
            Maximum navigation timeout in milliseconds.

        Returns
        -------
        Tuple[Page, Optional[Any]]
            Tuple of active Page instance and navigation Response if available.
        """
        page: Page = await self._create_page()
        try:
            response: Optional[Any] = await page.goto(url, wait_until=wait_until, timeout=timeout)
            return page, response
        except Exception as error:
            logger.debug(f"Navigation to {url} encountered error ({error}). Resetting page and retrying...")
            page: Page = await self._reset_page()
            response: Optional[Any] = await page.goto(url, wait_until=wait_until, timeout=timeout)
            return page, response

    async def jitter(self, min_sec: float = 1.0, max_sec: float = 2.5) -> None:
        """
        Variable delay with realistic jitter.

        Parameters
        ----------
        min_sec : float, default 1.0
            Minimum delay duration in seconds.
        max_sec : float, default 2.5
            Maximum delay duration in seconds.

        Returns
        -------
        None
        """
        delay: float = uniform(min_sec, max_sec)
        await asyncio_sleep(delay)

    async def _human_mouse_move(
        self,
        page: Page,
        target_x: float,
        target_y: float,
        steps: int = 15,
    ) -> None:
        """
        Simulates smooth mouse movement.

        Parameters
        ----------
        page : Page
            Playwright page instance.
        target_x : float
            Target X screen coordinate.
        target_y : float
            Target Y screen coordinate.
        steps : int, default 15
            Interpolation steps for smooth mouse motion.

        Returns
        -------
        None
        """
        try:
            if self.browser_type in ("firefox", "camoufox") and CAMOUFOX_AVAILABLE:
                await page.mouse.move(target_x, target_y)
            else:
                viewport_dict: Dict[str, int] = page.viewport_size or {"width": 1920, "height": 1080}
                current_x: float = uniform(viewport_dict["width"] * 0.3, viewport_dict["width"] * 0.7)
                current_y: float = uniform(viewport_dict["height"] * 0.3, viewport_dict["height"] * 0.7)
                for step_index in range(1, steps + 1):
                    time_fraction: float = step_index / steps
                    factor: float = time_fraction * time_fraction * (3 - 2 * time_fraction)
                    x_coordinate: float = current_x + (target_x - current_x) * factor + uniform(-2, 2)
                    y_coordinate: float = current_y + (target_y - current_y) * factor + uniform(-2, 2)
                    await page.mouse.move(x_coordinate, y_coordinate)
                    await asyncio_sleep(uniform(0.015, 0.035))
                await page.mouse.move(target_x, target_y)
        except Exception:
            pass

    async def _human_scroll(self, page: Page) -> None:
        """
        Simulates realistic browsing scroll behavior.

        Parameters
        ----------
        page : Page
            Playwright page instance.

        Returns
        -------
        None
        """
        try:
            delta: int = randint(180, 420)
            await page.mouse.wheel(0, delta)
            await asyncio_sleep(uniform(0.2, 0.5))
            if random_float() < 0.35:
                await page.mouse.wheel(0, -randint(60, 150))
                await asyncio_sleep(uniform(0.1, 0.3))
        except Exception:
            pass

    async def _handle_cloudflare_if_present(self, page: Page, max_wait: int = 30) -> bool:
        """
        Detects and waits for Cloudflare Turnstile / Managed challenge clearance.

        Parameters
        ----------
        page : Page
            Playwright page to monitor for challenge clearance.
        max_wait : int, default 30
            Maximum waiting duration in seconds.

        Returns
        -------
        bool
            True if challenge cleared or not present, False if timeout reached.
        """
        sec: int
        for sec in range(0, max_wait, 2):
            title: str
            current_url: str
            try:
                title: str = await page.title()
                current_url: str = page.url
            except Exception:
                title: str = ""
                current_url: str = ""

            title_clean: str = title.strip()

            # Check DOM for challenge markers
            has_challenge_dom: bool = False
            try:
                has_challenge_dom: bool = await page.evaluate('''() => {
                    return Boolean(
                        document.querySelector('#challenge-stage, #cf-stage, #turnstile-wrapper, .cf-turnstile, iframe[src*="challenges.cloudflare.com"], iframe[src*="cloudflare"], #challenge-running, #challenge-error-title')
                    );
                }''')
            except Exception:
                pass

            is_cf_challenge: bool = (
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
                    content_check: bool = await page.evaluate('''() => {
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
                cf_iframes: Locator = page.locator("iframe[src*='cloudflare'], iframe[src*='turnstile'], iframe[src*='challenges'], iframe[title*='Cloudflare'], iframe[title*='Turnstile']")
                count: int = await cf_iframes.count()
                if count > 0:
                    for iframe_index in range(count):
                        iframe_element: Locator = cf_iframes.nth(iframe_index)
                        bounding_box: Optional[Dict[str, float]] = await iframe_element.bounding_box(timeout=1500)
                        if bounding_box:
                            click_x: float = bounding_box["x"] + min(30.0, bounding_box["width"] / 4.0)
                            click_y: float = bounding_box["y"] + bounding_box["height"] / 2.0
                            await page.mouse.click(click_x, click_y)
            except Exception:
                pass

            # Check inner frame elements for Turnstile checkbox
            try:
                for browser_frame in page.frames:
                    if "cloudflare" in browser_frame.url or "turnstile" in browser_frame.url or "challenge" in browser_frame.url:
                        frame_element: Optional[ElementHandle] = await browser_frame.query_selector("input[type='checkbox'], span.mark, .ctp-checkbox-label, #cf-stage, #challenge-stage")
                        if frame_element:
                            logger.debug("Found Cloudflare Turnstile checkbox inside frame. Clicking...")
                            await frame_element.click(timeout=2000)
            except Exception:
                pass

            await asyncio_sleep(2.0)

        try:
            title: str = await page.title()
            title_clean: str = title.strip()
            current_url: str = page.url
            is_valid: bool = (
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
        """
        Tests base URLs and selects the first responsive Animepahe mirror with fast failover.

        Returns
        -------
        str
            Active responsive base URL for Animepahe.
        """
        page: Page = await self._create_page()
        for url in self.base_urls:
            try:
                logger.info(f"Testing mirror connection: {url}...")
                response: Optional[Any] = await page.goto(url, wait_until="domcontentloaded", timeout=6000)
                passed: bool = await self._handle_cloudflare_if_present(page, max_wait=8)
                if passed:
                    self.active_base_url = url
                    logger.info(f"Selected active Animepahe mirror: {self.active_base_url}")
                    return url
                else:
                    logger.debug(f"Mirror {url} did not clear challenge in 8s. Probing next mirror...")
            except Exception as error:
                logger.debug(f"Mirror {url} probe timed out or failed: {error}")

        # If all mirrors are currently challenged, default immediately to the first mirror without blocking
        logger.info(f"Selected active Animepahe mirror: {self.base_urls[0]}")
        self.active_base_url = self.base_urls[0]
        return self.base_urls[0]

    async def rotate_mirror(self) -> str:
        """
        Rotates to the next available mirror in base_urls, purges corrupted challenge
        state/cookies via _reset_browser_context, and probes connectivity on the new mirror.

        Returns
        -------
        str
            Active base URL after rotation.
        """
        if not self.base_urls:
            return self.active_base_url

        current_mirror_index: int
        try:
            current_mirror_index: int = self.base_urls.index(self.active_base_url)
        except ValueError:
            current_mirror_index: int = 0

        next_mirror_index: int = (current_mirror_index + 1) % len(self.base_urls)
        previous_mirror: str = self.active_base_url
        self.active_base_url = self.base_urls[next_mirror_index]
        logger.warning(f"Mirror rotation triggered: {previous_mirror} -> {self.active_base_url}")

        # Purge cookies & page context to prevent cross-mirror challenge poisoning
        page: Page = await self._reset_browser_context()
        try:
            logger.info(f"Probing rotated mirror {self.active_base_url}...")
            page, _ = await self._safe_goto(self.active_base_url, wait_until="domcontentloaded", timeout=15000)
            await self._handle_cloudflare_if_present(page, max_wait=15)
        except Exception as error:
            logger.warning(f"Error during mirror switch probe to {self.active_base_url}: {error}")

        return self.active_base_url

    async def scrape_recent_releases(self, max_pages: int = 3) -> List[Dict[str, Any]]:
        """
        Scrapes recent episode release cards across pages 1 to max_pages.

        Parameters
        ----------
        max_pages : int, default 3
            Maximum number of pages to scrape.

        Returns
        -------
        list of dict of str to Any
            List of scraped recent episode dictionaries.
        """
        page: Page = await self._create_page()
        releases: List[Dict[str, Any]] = []

        try:
            page_num: int
            for page_num in range(1, max_pages + 1):
                url: str = f"{self.active_base_url}/?page={page_num}" if page_num > 1 else self.active_base_url
                logger.info(f"Scraping recent releases (Page {page_num}/{max_pages}): {url}")
                await page.goto(url, wait_until="commit", timeout=30000)
                await self._handle_cloudflare_if_present(page, max_wait=35)
                await self.jitter(1.0, 2.0)

                # Strategy 1: Fetch internal airing API
                api_items: List[Dict[str, Any]] = await page.evaluate(f'''async () => {{
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
                    for release_item in api_items:
                        title: str = release_item.get("anime_title") or release_item.get("title", "")
                        raw_episode: Any = release_item.get("episode", 0)
                        session: str = release_item.get("session", "")
                        anime_session: str = release_item.get("anime_session", "")
                        
                        play_url: str
                        if anime_session and session:
                            play_url: str = urljoin(self.active_base_url, f"/play/{anime_session}/{session}")
                        else:
                            play_url: str = urljoin(self.active_base_url, f"/play/{session}")

                        releases.append({
                            "title": title.strip(),
                            "episode_num": int(raw_episode) if str(raw_episode).isdigit() else 0,
                            "play_url": play_url,
                            "anime_session": anime_session
                        })
                    continue

                # Strategy 2: DOM fallback
                logger.debug("Parsing DOM for latest releases...")
                dom_items: List[Dict[str, str]] = await page.evaluate('''() => {
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

                for dom_item in dom_items:
                    raw_title: str = dom_item.get("title", "").strip()
                    play_href: str = dom_item.get("play_href", "").strip()
                    episode_text: str = dom_item.get("episode_text", "").strip()

                    episode_match: Optional[Match[str]] = re_search(r'(\d+)', episode_text) or re_search(r'Episode\s*(\d+)', raw_title, IGNORECASE)
                    episode_number: int = int(episode_match.group(1)) if episode_match else 0

                    full_play_url: str = urljoin(self.active_base_url, play_href)
                    anime_session_match: Optional[Match[str]] = re_search(r'/play/([a-zA-Z0-9\-]+)/', play_href)
                    anime_session: str = anime_session_match.group(1) if anime_session_match else ""

                    releases.append({
                        "title": raw_title,
                        "episode_num": episode_number,
                        "play_url": full_play_url,
                        "anime_session": anime_session
                    })

                await self.jitter(1.0, 2.0)

            logger.info(f"Total scraped releases across {max_pages} pages: {len(releases)}")
            return releases
        except Exception as error:
            logger.error(f"Error scraping recent releases: {error}", exc_info=True)
            return releases

    def match_local_anime(self, web_title: str, local_folder_names: List[str], threshold: int = 85) -> Optional[str]:
        """
        Fuzzy matching local folder names against web titles.

        Parameters
        ----------
        web_title : str
            Anime title from web scraper.
        local_folder_names : list of str
            List of local folder names to match against.
        threshold : int, default 85
            Fuzzy matching threshold percentage (0 to 100).

        Returns
        -------
        str or None
            Best matching folder name or None if below threshold.
        """
        clean_web: str = re_sub(r'[^\w\s]', ' ', web_title).lower()
        best_match: Optional[str] = None
        best_score: int = 0

        for local_folder in local_folder_names:
            clean_local: str = re_sub(r'[^\w\s]', ' ', local_folder).lower()
            score: int = fuzz.token_set_ratio(clean_web, clean_local)
            if score > best_score and score >= threshold:
                best_score: int = score
                best_match: Optional[str] = local_folder

        if best_match:
            logger.debug(f"Fuzzy match: '{web_title}' -> '{best_match}' (score: {best_score}/100)")
        return best_match

    async def _ensure_on_mirror(self, page: Page, allow_rotate: bool = True) -> bool:
        """
        Ensures the page is currently navigated to the active Animepahe mirror with Cloudflare cleared.

        Parameters
        ----------
        page : Page
            Playwright page instance.
        allow_rotate : bool, default True
            Whether mirror rotation is permitted if blocked.

        Returns
        -------
        bool
            True if page is successfully on active mirror with Cloudflare cleared, False otherwise.
        """
        try:
            current_url: str = page.url or ""
            current_title: str = ""
            try:
                current_title: str = await page.title()
            except Exception:
                pass

            needs_nav: bool = (
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
                passed: bool = await self._handle_cloudflare_if_present(page, max_wait=25)
                if not passed and allow_rotate and len(self.base_urls) > 1:
                    logger.warning(f"Active mirror {self.active_base_url} blocked by Cloudflare. Rotating mirror...")
                    await self.rotate_mirror()
                    return await self._ensure_on_mirror(self.page or page, allow_rotate=False)
                return passed
            return True
        except Exception as error:
            logger.debug(f"Error ensuring mirror navigation: {error}")
            return False

    async def _execute_single_search_api_call(self, page: Page, query_str: str) -> List[Dict[str, Any]]:
        """
        Executes a single search API request against Animepahe via browser page evaluate.

        Parameters
        ----------
        page : Page
            Playwright page instance.
        query_str : str
            Query string to search.

        Returns
        -------
        list of dict of str to Any
            List of matching anime dictionaries returned by API.
        """
        try:
            on_mirror: bool = await self._ensure_on_mirror(page)
            if not on_mirror:
                logger.warning(f"Active mirror {self.active_base_url} is not accessible for search API")
                return []
            eval_result: Any = await asyncio_wait_for(
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
                status: int = eval_result.get("status", 0)
                if status in (403, 503, 520):
                    logger.warning(f"Search API returned status {status} (Cloudflare challenge suspected). Waiting for clearance...")
                    passed: bool = await self._handle_cloudflare_if_present(page, max_wait=20)
                    if passed:
                        return await self._execute_single_search_api_call(page, query_str)
                data: Optional[List[Dict[str, Any]]] = eval_result.get("data")
                if data is not None:
                    return data
                if eval_result.get("error"):
                    logger.debug(f"Search API returned error for '{query_str}': {eval_result.get('error')}")
            elif isinstance(eval_result, list):
                return eval_result
            return []
        except Exception as error:
            logger.debug(f"Search API error for '{query_str}': {error}")
            return []

    async def _resolve_metadata_aliases(self, english_title: str) -> List[str]:
        """
        Queries AniList and Jikan/MAL APIs to resolve official Romaji titles and synonyms.

        Parameters
        ----------
        english_title : str
            English title to look up synonyms and aliases for.

        Returns
        -------
        list of str
            List of alias title strings.
        """
        aliases: List[str] = []
        # 1. AniList GraphQL
        try:
            query_graphql: str = '''
            query ($search: String) {
              Media (search: $search, type: ANIME) {
                title { romaji english native }
                synonyms
              }
            }
            '''
            async with HttpAsyncClient(timeout=3.5, follow_redirects=True) as client:
                api_response: Any = await client.post('https://graphql.anilist.co', json={'query': query_graphql, 'variables': {'search': english_title}})
                if api_response.status_code == 200:
                    media: Optional[Dict[str, Any]] = api_response.json().get('data', {}).get('Media')
                    if media:
                        titles: Dict[str, str] = media.get('title', {})
                        for key in ('romaji', 'english'):
                            alias_val: Optional[str] = titles.get(key)
                            if alias_val and alias_val.lower() != english_title.lower() and alias_val not in aliases:
                                aliases.append(alias_val)
                        for synonym in media.get('synonyms', []):
                            if synonym and synonym.lower() != english_title.lower() and synonym not in aliases:
                                aliases.append(synonym)
        except Exception as error:
            logger.debug(f"AniList alias resolution error: {error}")

        # 2. Jikan / MAL API
        try:
            cleaned_search: str = re_sub(r'\s+(?:season\s+\d+|s\d+|ii|iii|iv|v|act\.\d+)\b', '', english_title, flags=IGNORECASE)
            jikan_url: str = f"https://api.jikan.moe/v4/anime?q={url_quote(cleaned_search)}&limit=1"
            async with HttpAsyncClient(timeout=3.5, follow_redirects=True) as client:
                jikan_response: Any = await client.get(jikan_url)
                if jikan_response.status_code == 200:
                    jikan_data: List[Dict[str, Any]] = jikan_response.json().get("data", [])
                    if jikan_data:
                        top_result: Dict[str, Any] = jikan_data[0]
                        for key in ("title", "title_japanese", "title_english"):
                            candidate_title: Optional[str] = top_result.get(key)
                            if candidate_title and candidate_title.lower() != english_title.lower() and candidate_title not in aliases:
                                aliases.append(candidate_title)
        except Exception as error:
            logger.debug(f"Jikan alias resolution error: {error}")

        return aliases

    async def search_anime_title(self, title: str) -> List[Dict[str, Any]]:
        """
        Queries Animepahe's internal search API using a multi-tier progressive query strategy:
        1. Full cleaned title.
        2. Base franchise title (stripped of Roman numerals, Season X, arc subtitles).
        3. Distinctive keyword pruning (stopwords removed, sub-clauses).
        4. Public metadata alias bridge (AniList GraphQL & Jikan Romaji/synonyms resolution).

        Parameters
        ----------
        title : str
            Title of the anime to search.

        Returns
        -------
        list of dict of str to Any
            List of matched anime candidate dictionaries from Animepahe API.
        """
        page: Page = await self._create_page()
        try:
            on_mirror: bool = await self._ensure_on_mirror(page)
            if not on_mirror:
                logger.warning(f"Active mirror {self.active_base_url} is not accessible for search")
                return []

            # Tier 1 - 3: Progressive decomposed queries
            queries: List[str] = self.ai_helper.decompose_search_queries(title)
            for tier_index, query_candidate in enumerate(queries, start=1):
                logger.debug(f"[Search Tier {tier_index}] Querying Animepahe: '{query_candidate}'")
                results: List[Dict[str, Any]] = await self._execute_single_search_api_call(page, query_candidate)
                if results:
                    logger.debug(f"[Search Tier {tier_index}] Found {len(results)} candidate(s) for query: '{query_candidate}'")
                    return results

            # Tier 4: Metadata alias bridge (AniList + Jikan synonyms)
            aliases: List[str] = await self._resolve_metadata_aliases(title)
            if aliases:
                for alias_item in aliases:
                    for alias_query in self.ai_helper.decompose_search_queries(alias_item):
                        logger.debug(f"[Search Tier 4 Alias] Querying Animepahe with alias query: '{alias_query}'")
                        alias_results: List[Dict[str, Any]] = await self._execute_single_search_api_call(page, alias_query)
                        if alias_results:
                            return alias_results

            logger.debug(f"All progressive search tiers yielded 0 results for '{title}'")
            return []
        except Exception as error:
            logger.error(f"Error executing search queries for '{title}': {error}")
            return []

    def _select_preferred_source(
        self,
        options: List[Dict[str, str]],
        anime_title: str,
        episode_num: int,
        preferred_resolution: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Select download source option based on audio preference and resolution routing.

        Parameters
        ----------
        options : list of dict of str to str
            List of available download source options.
        anime_title : str
            Title of the anime series.
        episode_num : int
            Episode number being evaluated.
        preferred_resolution : str, optional
            Explicit preferred resolution ('1080', '720', '480', '360').

        Returns
        -------
        dict of str to str or None
            Selected source option dictionary, or None if awaiting release.
        """
        if not options:
            return None

        subbed_options: List[Dict[str, str]] = [
            option for option in options
            if not re_search(r'\b(eng|dub|english)\b', option["text"], IGNORECASE)
        ]
        dubbed_options: List[Dict[str, str]] = [
            option for option in options
            if re_search(r'\b(eng|dub|english)\b', option["text"], IGNORECASE)
        ]

        # Strict modes
        usable_options: List[Dict[str, str]]
        if self.audio_preference == "sub_strict":
            usable_options: List[Dict[str, str]] = subbed_options
            if not usable_options:
                logger.info(f"Strict Subbed active: Skipping '{anime_title}' Ep {episode_num} (No subbed release available)")
                return None
        elif self.audio_preference == "dub_strict":
            usable_options: List[Dict[str, str]] = dubbed_options
            if not usable_options:
                logger.info(f"Strict Dubbed active: Skipping '{anime_title}' Ep {episode_num} (No dubbed release available)")
                return None
        elif self.audio_preference == "dub":
            usable_options: List[Dict[str, str]] = dubbed_options if dubbed_options else subbed_options
        else:
            # Default "sub"
            usable_options: List[Dict[str, str]] = subbed_options if subbed_options else dubbed_options

        if not usable_options:
            usable_options: List[Dict[str, str]] = options

        explicit_resolution: Optional[str] = preferred_resolution or self.preferred_resolution
        if explicit_resolution:
            target_resolution: str = explicit_resolution.lower().rstrip("p")
            if target_resolution not in RESOLUTION_PRIORITY_MAP:
                target_resolution: str = DEFAULT_PREFERRED_RESOLUTION

            exact_resolution_tag: str = f"{target_resolution}p"
            priority_list: List[str] = RESOLUTION_PRIORITY_MAP.get(target_resolution, ["1080p", "720p", "480p", "360p"])

            # Check for exact preferred resolution
            has_exact: bool = any(exact_resolution_tag in option["text"] for option in usable_options)
            if has_exact:
                for option in usable_options:
                    if exact_resolution_tag in option["text"]:
                        self.state_manager.reset_viewed_count(anime_title, episode_num)
                        logger.info(f"Selected exact preferred {exact_resolution_tag} ({self.audio_preference.upper()}): '{option['text']}'")
                        return option

            # Exact preferred resolution missing -> Execute Wait & Retry Protocol
            viewed_count: int = self.state_manager.increment_viewed_count(anime_title, episode_num)
            logger.info(f"{exact_resolution_tag} missing for '{anime_title}' Ep {episode_num}. Retry count: {viewed_count}/{FALLBACK_MAX_RETRIES}")

            if viewed_count < FALLBACK_MAX_RETRIES:
                logger.info(f"Skipping episode {episode_num} for this run awaiting {exact_resolution_tag} release.")
                return None

            # Threshold reached -> Follow explicit fallback routing
            logger.info(f"Threshold reached ({viewed_count} runs). Falling back according to {exact_resolution_tag} priority routing: {priority_list}")
            for resolution_tag in priority_list:
                matched_option: Optional[Dict[str, str]] = next((option for option in usable_options if resolution_tag in option["text"]), None)
                if matched_option:
                    logger.info(f"Selected fallback resolution '{resolution_tag}': '{matched_option['text']}'")
                    return matched_option
        else:
            # Highest Quality First: 1080p -> 720p -> 480p -> 360p
            highest_quality_routing: List[str] = ["1080p", "720p", "480p", "360p"]
            for resolution_tag in highest_quality_routing:
                matched_option: Optional[Dict[str, str]] = next((option for option in usable_options if resolution_tag in option["text"]), None)
                if matched_option:
                    logger.info(f"Highest Quality First selected '{resolution_tag}': '{matched_option['text']}'")
                    return matched_option

        # Final fallback to first usable option
        if usable_options:
            return usable_options[0]

        return None


    async def get_show_episodes(self, play_url: str) -> Tuple[str, Dict[int, str]]:
        """
        Retrieve all available episode numbers and play URLs for a series using Release API and DOM.

        Parameters
        ----------
        play_url : str
            The episode play URL or anime overview URL.

        Returns
        -------
        Tuple[str, Dict[int, str]]
            Series title and mapping of episode numbers to play URLs.

        Raises
        ------
        RuntimeError
            If the active mirror is inaccessible or blocked by Cloudflare challenge.
        """
        page: Page = await self._create_page()
        try:
            # Normalize play_url to active mirror domain
            mirror_url: str
            for mirror_url in self.base_urls:
                if play_url.startswith(mirror_url):
                    play_url: str = play_url.replace(mirror_url, self.active_base_url, 1)
                    break

            logger.info(f"Accessing episode catalog for: {play_url}")
            on_mirror: bool = await self._ensure_on_mirror(page)
            if not on_mirror:
                raise RuntimeError(f"Mirror {self.active_base_url} is inaccessible or blocked by Cloudflare challenge")

            # Extract anime session directly from play_url
            anime_session: str = ""
            session_match: Optional[Match[str]] = re_search(r'/(?:play|anime)/([a-zA-Z0-9\-]+)', play_url)
            if session_match:
                anime_session: str = session_match.group(1)

            episodes: Dict[int, str] = {}
            show_title: str = ""

            # Fetch via release API if anime_session exists
            if anime_session:
                logger.debug(f"Fetching complete episode list via release API for session: {anime_session}")
                current_page: int = 1
                while current_page <= 15:
                    api_data: Optional[Dict[str, Any]] = None
                    for attempt in range(2):
                        try:
                            api_data: Optional[Dict[str, Any]] = await asyncio_wait_for(
                                page.evaluate(f'''async () => {{
                                    const controller = new AbortController();
                                    const timeoutId = setTimeout(() => controller.abort(), 6000);
                                    try {{
                                        const res = await fetch('/api?m=release&id={anime_session}&sort=episode_asc&page={current_page}', {{
                                            signal: controller.signal,
                                            headers: {{ 'Accept': 'application/json' }}
                                        }});
                                        clearTimeout(timeoutId);
                                        if (res.ok) return await res.json();
                                    }} catch (e) {{}}
                                    return null;
                                }}'''),
                                timeout=10.0
                            )
                            if api_data:
                                break
                        except Exception:
                            await asyncio_sleep(0.5)

                    if not api_data or not api_data.get("data"):
                        break

                    episode_item: Dict[str, Any]
                    for episode_item in api_data.get("data", []):
                        episode_value: Any = episode_item.get("episode", 0)
                        session_value: str = str(episode_item.get("session", ""))
                        if str(episode_value).isdigit() and session_value:
                            episode_number: int = int(episode_value)
                            episode_play_url: str = urljoin(self.active_base_url, f"/play/{anime_session}/{session_value}")
                            episodes[episode_number] = episode_play_url

                    last_page: int = int(api_data.get("last_page", 1))
                    if current_page >= last_page:
                        break
                    current_page += 1

                if episodes:
                    logger.info(f"Retrieved {len(episodes)} total episodes for session '{anime_session}' via API.")
                    return show_title or anime_session, episodes

            # If API yielded 0 episodes or session extraction was absent, fallback to page navigation & DOM
            fallback_navigation_url: str = play_url
            if anime_session and play_url.rstrip('/').endswith(f"/play/{anime_session}"):
                fallback_navigation_url: str = f"{self.active_base_url}/anime/{anime_session}"

            page, _ = await self._safe_goto(fallback_navigation_url, wait_until="commit", timeout=25000)
            await self._handle_cloudflare_if_present(page, max_wait=20)
            await self.jitter(0.5, 1.5)

            # Extract show title from DOM
            show_info: Dict[str, str] = await page.evaluate('''() => {
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

            show_title: str = show_info.get("title", "")
            show_href: str = show_info.get("href", "")

            episodes_dom: Dict[str, str] = await page.evaluate('''() => {
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

            episodes: Dict[int, str] = {int(key): urljoin(self.active_base_url, episode_href) for key, episode_href in episodes_dom.items()}
            logger.info(f"Retrieved {len(episodes)} total episodes for '{show_title}' via DOM.")
            return show_title, episodes

        except Exception as error:
            logger.error(f"Error fetching show episodes from {play_url}: {error}")
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
        progress_callback: Optional[Callable[[float, int, int, float], None]] = None,
        stall_timeout: float = float(DEFAULT_STALL_TIMEOUT_SECONDS),
    ) -> bool:
        """
        Resolve streaming source and download media into a temporary file using chunk streaming.

        Stream utilizes an inactivity/stall watchdog that triggers only if zero bytes arrive
        for the duration of stall_timeout, avoiding fixed wall-clock timeouts.

        Parameters
        ----------
        anime_title : str
            Title of the anime series.
        episode_num : int
            Episode sequence number.
        play_url : str
            Episode player or redirect URL.
        temp_target_file : Path
            Destination temporary file path.
        preferred_resolution : str, optional
            Requested video resolution tier.
        progress_callback : callable, optional
            Callback function invoked with progress percentage, downloaded bytes, total bytes, speed mbps.
        stall_timeout : float, default DEFAULT_STALL_TIMEOUT_SECONDS
            Maximum duration in seconds to wait for subsequent chunk packets before aborting.

        Returns
        -------
        bool
            True if the episode was completely downloaded and verified, False otherwise.
        """
        page: Page = await self._create_page()
        try:
            logger.info(f"Resolving download stream for '{anime_title}' Ep {episode_num}: {play_url}")
            page, _ = await self._safe_goto(play_url, wait_until="domcontentloaded", timeout=35000)
            await self._handle_cloudflare_if_present(page, max_wait=30)
            await self.jitter(1.0, 2.0)

            # Wait for and click #downloadMenu button to open #pickDownload
            menu_button: Optional[ElementHandle] = None
            for _ in range(2):
                try:
                    menu_button: Optional[ElementHandle] = await page.wait_for_selector(
                        "#downloadMenu, button.dropdown-toggle, .download",
                        timeout=18000,
                    )
                    if menu_button:
                        break
                except Exception:
                    await self._handle_cloudflare_if_present(page, max_wait=10)

            if not menu_button:
                logger.error(
                    f"Download menu button not found on play page for '{anime_title}' Ep {episode_num}"
                )
                return False

            logger.debug("Clicking #downloadMenu dropdown button...")
            try:
                await menu_button.click()
            except Exception as click_error:
                logger.debug(
                    f"Direct click on #downloadMenu failed ({click_error}). Dispatching JS click..."
                )
                await page.evaluate(
                    """() => {
                    const dropdown_element = document.querySelector('#downloadMenu, button.dropdown-toggle, .download');
                    if (dropdown_element) dropdown_element.click();
                }"""
                )

            # Poll for #pickDownload options with JS click fallback
            download_options: List[Dict[str, str]] = []
            for poll_index in range(8):
                await asyncio_sleep(0.75)
                download_options: List[Dict[str, str]] = await page.evaluate(
                    r"""() => {
                    const containers = document.querySelectorAll('#pickDownload, .dropdown-menu');
                    const results = [];
                    containers.forEach(container => {
                        container.querySelectorAll('a').forEach(anchor => {
                            const text = anchor.textContent.trim();
                            const href = anchor.getAttribute('href');
                            if (text && href && (href.startsWith('http') || href.includes('pahe.win') || href.includes('/f/') || /\d+p/.test(text))) {
                                results.push({ text: text, href: href });
                            }
                        });
                    });
                    return results;
                }"""
                )
                if download_options:
                    break
                logger.debug(
                    f"Poll {poll_index + 1}/8: #pickDownload empty, dispatching JS click fallback..."
                )
                try:
                    await page.evaluate(
                        """() => {
                        const menu = document.querySelector('#downloadMenu');
                        if (menu) menu.click();
                    }"""
                    )
                except Exception:
                    pass

            if not download_options:
                logger.error(
                    f"No download options found in dropdown for '{anime_title}' Ep {episode_num}"
                )
                await self._reset_page()
                return False

            chosen_option: Optional[Dict[str, str]] = self._select_preferred_source(
                options=download_options,
                anime_title=anime_title,
                episode_num=episode_num,
                preferred_resolution=preferred_resolution,
            )
            if not chosen_option:
                logger.error(
                    f"Could not resolve acceptable source/resolution for '{anime_title}' Ep {episode_num}"
                )
                await self._reset_page()
                return False

            kwik_url: str = chosen_option["href"]
            logger.info(
                f"Selected download stream for '{anime_title}' Ep {episode_num}: {kwik_url}"
            )

            # Follow kwik redirect link
            page, _ = await self._safe_goto(kwik_url, wait_until="commit", timeout=45000)
            await self._handle_cloudflare_if_present(page, max_wait=30)
            await self.jitter(1.0, 2.0)

            # Cloudflare Turnstile click resolution on Kwik page
            await self._click_turnstile_if_present(page)

            # Ensure page is on actual kwik download domain
            kwik_title: str = await page.title()
            kwik_current_url: str = page.url or ""
            if "kwik" not in kwik_current_url and "kwik" not in kwik_title.lower():
                logger.debug(
                    f"Page landed at {kwik_current_url} (Title: '{kwik_title}'). Waiting for kwik redirect..."
                )
                await self._handle_cloudflare_if_present(page, max_wait=20)
                await asyncio_sleep(2.0)

            temporary_partial_file: Path = temp_target_file.with_suffix(
                temp_target_file.suffix + ".part"
            )
            if temporary_partial_file.exists():
                temporary_partial_file.unlink()
            if temp_target_file.exists():
                temp_target_file.unlink()

            logger.info(
                f"Triggering browser download resolution for temporary target: {temp_target_file}"
            )
            download_selector: str = (
                "form button, button[type='submit'], .button.is-success, .button.is-primary, "
                "a.button, input[type='submit'], button:has-text('Download'), .btn-download, button"
            )

            submit_element: Optional[ElementHandle] = None
            try:
                submit_element: Optional[ElementHandle] = await page.wait_for_selector(download_selector, timeout=25000)
            except Exception:
                logger.debug(
                    "Download selector not immediately visible. Checking Cloudflare clearance and DOM state..."
                )
                await self._handle_cloudflare_if_present(page, max_wait=15)
                try:
                    submit_element: Optional[ElementHandle] = await page.wait_for_selector(download_selector, timeout=10000)
                except Exception:
                    pass

            # Fallback: check if form exists even if button isn't directly matched
            if not submit_element:
                has_form: bool = await page.evaluate(
                    """() => Boolean(document.querySelector('form'))"""
                )
                if has_form:
                    logger.debug("Found form in DOM, acquiring submit element...")
                    submit_element: Optional[ElementHandle] = await page.query_selector(
                        "form button, form input[type='submit'], form"
                    )

            if not submit_element:
                logger.error("Download submit button not found on Kwik page")
                return False

            start_download_time: float = current_timestamp()
            async with page.expect_download(timeout=90000) as download_info:
                try:
                    await submit_element.click()
                except Exception:
                    await page.evaluate(
                        "() => { const form = document.querySelector('form'); if (form) form.submit(); }"
                    )
            download: Download = await download_info.value

            cdn_url: str = download.url
            logger.info(f"Resolved CDN download link: {cdn_url[:80]}...")

            browser_cookies: List[Dict[str, Any]] = await self.context.cookies()
            cookie_dictionary: Dict[str, str] = {
                cookie["name"]: cookie["value"] for cookie in browser_cookies
            }
            user_agent_header: str = await page.evaluate("() => navigator.userAgent")
            referer_header: str = page.url or "https://kwik.cx/"
            request_headers: Dict[str, str] = {
                "User-Agent": user_agent_header,
                "Referer": referer_header,
                "Accept": "*/*",
            }

            stream_succeeded: bool = False
            download_cancelled: bool = False
            client_timeout: HttpTimeout = HttpTimeout(
                connect=30.0,
                read=stall_timeout,
                write=None,
                pool=None,
            )

            try:
                async with HttpAsyncClient(
                    headers=request_headers,
                    cookies=cookie_dictionary,
                    follow_redirects=True,
                    timeout=client_timeout,
                ) as http_client:
                    async with http_client.stream("GET", cdn_url) as stream_response:
                        if stream_response.status_code == 200:
                            download_cancelled: bool = True
                            try:
                                await download.cancel()
                            except Exception:
                                pass

                            total_bytes: int = int(
                                stream_response.headers.get("content-length", 0)
                            )
                            downloaded_bytes: int = 0
                            last_progress_emit_time: float = start_download_time

                            with open(temporary_partial_file, "wb") as file_handle:
                                async for chunk in stream_response.aiter_bytes(chunk_size=262144):
                                    if not chunk:
                                        continue
                                    file_handle.write(chunk)
                                    downloaded_bytes += len(chunk)
                                    now_time: float = current_timestamp()
                                    elapsed_seconds: float = now_time - start_download_time
                                    speed_mbps: float = (
                                        (downloaded_bytes / (1024.0 * 1024.0)) / elapsed_seconds
                                        if elapsed_seconds > 0.0
                                        else 0.0
                                    )
                                    progress_percentage: float = (
                                        (downloaded_bytes / total_bytes * 100.0)
                                        if total_bytes > 0
                                        else 0.0
                                    )
                                    if progress_callback and (
                                        now_time - last_progress_emit_time >= 0.5
                                    ):
                                        progress_callback(
                                             progress_percentage,
                                             downloaded_bytes,
                                             total_bytes,
                                             speed_mbps,
                                        )
                                        last_progress_emit_time: float = now_time

                            if (
                                temporary_partial_file.exists()
                                and temporary_partial_file.stat().st_size > 1024 * 1024
                            ):
                                temporary_partial_file.replace(temp_target_file)
                                stream_succeeded: bool = True
                                final_elapsed: float = current_timestamp() - start_download_time
                                final_bytes: int = temp_target_file.stat().st_size
                                final_megabytes: float = final_bytes / (1024.0 * 1024.0)
                                final_speed: float = (
                                    final_megabytes / final_elapsed
                                    if final_elapsed > 0.0
                                    else 0.0
                                )
                                logger.info(
                                    f"Direct stream download complete: {final_megabytes:.2f} MB in {final_elapsed:.1f}s ({final_speed:.2f} MB/s)"
                                )
                                if progress_callback:
                                    progress_callback(
                                        100.0,
                                        final_bytes,
                                        final_bytes,
                                        final_speed,
                                    )
                                return True
                            else:
                                logger.error(
                                    f"Stream finished but file {temporary_partial_file} is missing or too small."
                                )
                        else:
                            logger.warning(
                                f"Direct stream received HTTP status {stream_response.status_code}. "
                                "Falling back to browser native download mechanism..."
                            )
            except Exception as stream_error:
                logger.warning(
                    f"Direct stream aborted or encountered error: {stream_error}. "
                    "Checking browser native download fallback..."
                )
                if temporary_partial_file.exists():
                    try:
                        temporary_partial_file.unlink()
                    except Exception:
                        pass

            if not stream_succeeded and not download_cancelled:
                logger.info("Engaging browser native download handler fallback...")
                await download.save_as(str(temp_target_file))
                elapsed_native: float = current_timestamp() - start_download_time
                if (
                    temp_target_file.exists()
                    and temp_target_file.stat().st_size > 1024 * 1024
                ):
                    native_size: int = temp_target_file.stat().st_size
                    native_megabytes: float = native_size / (1024.0 * 1024.0)
                    native_speed: float = (
                        native_megabytes / elapsed_native
                        if elapsed_native > 0.0
                        else 0.0
                    )
                    logger.info(
                        f"Browser native download complete: {native_megabytes:.2f} MB in {elapsed_native:.1f}s ({native_speed:.2f} MB/s)"
                    )
                    if progress_callback:
                        progress_callback(
                            100.0,
                            native_size,
                            native_size,
                            native_speed,
                        )
                    return True
                else:
                    logger.error(
                        f"Browser native download finished but file {temp_target_file} is missing or too small."
                    )
                    if temp_target_file.exists():
                        temp_target_file.unlink()
                    return False

            return False

        except Exception as error:
            logger.error(
                f"Failed to download '{anime_title}' Ep {episode_num}: {error}",
                exc_info=True,
            )
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
