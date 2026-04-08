"""Concrete scraper implementations for different e-commerce sites."""

from typing import Dict, Any, List, Optional
import asyncio
import logging
import random
from datetime import datetime, timezone
from playwright.async_api import async_playwright, Page
from playwright_stealth import stealth_async
from fake_useragent import UserAgent

from config import settings
from .base import BaseScraper
from .validators import DataValidator


logger = logging.getLogger(__name__)


class TestStoreScraper(BaseScraper):
    """
    Professional scraper for webscraper.io test e-commerce site.
    
    Demonstrates real-world Playwright integration with:
    - Async page navigation and element handling
    - Professional data extraction
    - Error handling and validation
    - Comprehensive logging
    """
    
    def __init__(self):
        """Initialize TestStore scraper with site configuration."""
        super().__init__(
            site_name="teststore",
            base_url="https://webscraper.io/test-sites/e-commerce/allinone"
            # Uses default max_retries and timeout from settings
        )
    
    async def scrape(self, product_url: str) -> Dict[str, Any]:
        """
        Scrape product data from webscraper.io test site using Playwright.
        
        Args:
            product_url: URL of the products page to scrape
            
        Returns:
            Dictionary with single product data
            
        Raises:
            Exception: If scraping fails
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.playwright_headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            
            try:
                page = await browser.new_page()
                page.set_default_timeout(settings.scraper_timeout)
                
                self.logger.info(f"Navigating to: {product_url}")
                # Explicit timeout for page navigation (30 seconds should be enough)
                try:
                    await page.goto(
                        product_url,
                        wait_until="domcontentloaded",
                        timeout=30000
                    )
                    self.logger.info("✓ Page loaded successfully")
                except Exception as nav_error:
                    self.logger.error(f"Navigation failed: {nav_error}")
                    raise
                
                # Try to wait for product containers (with fallback selectors)
                selectors = [
                    "div.thumbnail",         # webscraper.io test site
                    "div.product",           # Alternative 1
                    ".product-item",         # Alternative 2
                    ".product",              # Alternative 3
                ]
                
                selector_found = False
                for selector in selectors:
                    try:
                        self.logger.debug(f"Trying selector: {selector}")
                        await page.wait_for_selector(selector, timeout=5000)
                        self.logger.info(f"✓ Found elements with selector: {selector}")
                        selector_found = True
                        break
                    except Exception:
                        self.logger.debug(f"✗ Selector '{selector}' not found")
                        continue
                
                if not selector_found:
                    self.logger.warning(
                        "⚠ No product selectors found. Attempting extraction anyway..."
                    )
                
                # Extract product data
                products = await self._extract_products(page)
                
                self.logger.info(f"✓ Extracted {len(products)} products")
                
                return {
                    "products": products,
                    "url": product_url,
                    "total_products": len(products)
                }
                
            except Exception as e:
                self.logger.error(f"Scraping error for {product_url}: {str(e)}", exc_info=True)
                raise
            finally:
                await browser.close()
    
    async def _extract_products(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract product information from the page.
        
        Targets webscraper.io test site HTML structure:
          div.thumbnail > div.caption > h4 > a.title  (product name + link)
          div.thumbnail > div.caption > h4.price       (price)
          div.thumbnail > div.caption > p.description   (description)
        
        Args:
            page: Playwright page object
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        try:
            self.logger.debug("Extracting products with div.thumbnail selector")
            products_data = await page.evaluate("""
                () => {
                    const cards = document.querySelectorAll('div.thumbnail');
                    const products = [];
                    const baseUrl = window.location.origin;
                    
                    cards.forEach((card, index) => {
                        const titleLink = card.querySelector('a.title');
                        const priceEl = card.querySelector('h4.price, .price, .pull-right.price');
                        const descEl = card.querySelector('p.description, .description');
                        
                        let productUrl = null;
                        if (titleLink && titleLink.href) {
                            productUrl = titleLink.href;
                        } else {
                            const anyLink = card.querySelector('a[href]');
                            if (anyLink && anyLink.href) {
                                productUrl = anyLink.href;
                            } else {
                                productUrl = window.location.href + '#product-' + index;
                            }
                        }
                        
                        const title = titleLink
                            ? titleLink.textContent.trim()
                            : (card.querySelector('h4:not(.price), h2, .title')
                                ? card.querySelector('h4:not(.price), h2, .title').textContent.trim()
                                : null);
                        
                        const priceText = priceEl ? priceEl.textContent.trim() : '0';
                        const desc = descEl ? descEl.textContent.trim() : '';
                        
                        if (title && title.length > 1) {
                            products.push({
                                product_name: title,
                                price: priceText,
                                description: desc.substring(0, 500),
                                url: productUrl,
                                currency: 'USD'
                            });
                        }
                    });
                    
                    return products;
                }
            """)
            
            if products_data and len(products_data) > 0:
                self.logger.info(f"Extraction successful: {len(products_data)} products")
                for product in products_data:
                    product["price"] = DataValidator.sanitize_price(product["price"])
                    product["stock_status"] = "unknown"
                    products.append(product)
                return products
            else:
                self.logger.warning("div.thumbnail selector found 0 products")
        
        except Exception as e:
            self.logger.warning(f"Primary extraction failed: {e}")
        
        return products
    
    async def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate scraped product data.
        
        Args:
            data: Dictionary containing products list and metadata
            
        Returns:
            True if validation succeeds, False otherwise
        """
        try:
            if "products" not in data or not isinstance(data["products"], list):
                self.logger.warning("Invalid data structure: missing products list")
                return False
            
            # Validate at least one product exists
            if len(data["products"]) == 0:
                self.logger.warning("No products found in scraped data")
                return False
            
            self.logger.debug(f"Data validation successful: {len(data['products'])} products")
            return True
            
        except Exception as e:
            self.logger.error(f"Data validation failed: {str(e)}")
            return False
    
    async def scrape_and_validate(self, product_url: str) -> tuple[List[Dict], List[Dict]]:
        """
        Scrape products and validate them, separating valid from invalid.
        
        Args:
            product_url: URL of products page to scrape
            
        Returns:
            Tuple of (valid_products, invalid_products)
        """
        self.logger.info(
            f"Starting scraping for {self.site_name} - URL: {product_url}"
        )
        start_time = datetime.now(timezone.utc)
        
        try:
            # Scrape with retry logic
            scraped_data = await self.scrape_with_retry(product_url)
            
            if not scraped_data:
                self.logger.error(f"Failed to scrape {product_url} after retries")
                return [], []
            
            # Extract products and validate
            products = scraped_data.get("products", [])
            
            # ADD TIMESTAMP BEFORE VALIDATION (required by validator)
            for product in products:
                product["scraped_at"] = datetime.now(timezone.utc).isoformat()
                product["site_name"] = self.site_name
            
            # Now validate - all products have scraped_at
            valid_products, invalid_products = DataValidator.validate_batch(products)
            
            # Log results
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.logger.info(
                f"✓ Scraping completed for {self.site_name} in {elapsed:.2f}s\n"
                f"  Total products: {len(products)}\n"
                f"  Valid products: {len(valid_products)}\n"
                f"  Invalid products: {len(invalid_products)}"
            )
            
            if invalid_products:
                self.logger.warning(
                    f"  Invalid products details:\n"
                    f"  {[item['error'] for item in invalid_products]}"
                )
            
            return valid_products, invalid_products
            
        except Exception as e:
            self.logger.error(
                f"✗ Scraping failed for {self.site_name}: {str(e)}",
                exc_info=True
            )
            return [], []


class AmazonTRScraper(BaseScraper):
    """
    Stealth scraper for Amazon Turkey (amazon.com.tr).

    Anti-detection layers:
    - playwright-stealth hides navigator.webdriver and browser fingerprints
    - fake-useragent rotates a realistic User-Agent per request
    - Random jitter delays between 2–6 s before navigation / interactions
    - Slow scroll simulation to mimic human reading behaviour
    - Turkish Accept-Language + Google Referer headers
    - Captcha / bot-detection page detection with CRITICAL log warning
    """

    BASE_URL = "https://www.amazon.com.tr"
    SEARCH_URL = "https://www.amazon.com.tr/s?k=laptop"

    # Selectors (Amazon.com.tr search-results page)
    RESULT_SELECTOR = 'div[data-component-type="s-search-result"]'
    PRICE_SELECTOR = ".a-price-whole"
    NAME_SELECTOR = "h2 a span"
    LINK_SELECTOR = "h2 a"

    # Pages that signal Amazon blocked us
    BLOCK_SIGNALS = [
        "amazon.com.tr memnuniyet anketi",
        "robot değilim",
        "enter the characters you see below",
        "type the characters you see in this image",
    ]

    def __init__(self):
        super().__init__(
            site_name="amazon_tr",
            base_url=self.BASE_URL,
        )
        self._ua = UserAgent(browsers=["chrome", "firefox", "edge"])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _random_jitter(self, min_s: float = 2.0, max_s: float = 6.0) -> None:
        """Sleep for a random duration to mimic human think-time."""
        delay = random.uniform(min_s, max_s)
        self.logger.debug(f"Jitter: sleeping {delay:.2f}s")
        await asyncio.sleep(delay)

    async def _slow_scroll(self, page: Page, steps: int = 8) -> None:
        """Scroll down the page in small increments to simulate human reading."""
        scroll_height = await page.evaluate("document.body.scrollHeight")
        step_px = scroll_height // max(steps, 1)
        for i in range(1, steps + 1):
            await page.evaluate(f"window.scrollTo(0, {step_px * i})")
            await asyncio.sleep(random.uniform(0.3, 0.8))
        # Scroll back near the top so all product cards are in the DOM
        await page.evaluate("window.scrollTo(0, 0)")

    def _is_blocked(self, title: str) -> bool:
        """Return True if the page title indicates a captcha or survey."""
        low = title.lower()
        return any(sig in low for sig in self.BLOCK_SIGNALS)

    # ------------------------------------------------------------------
    # BaseScraper interface
    # ------------------------------------------------------------------

    async def scrape(self, product_url: str) -> Dict[str, Any]:
        """
        Navigate to the Amazon Turkey search page and extract product cards.

        Args:
            product_url: Search URL (defaults to laptop search if not set).

        Returns:
            {'products': [...], 'url': product_url, 'total_products': n}
        """
        user_agent = self._ua.random

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.playwright_headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = await browser.new_context(
                user_agent=user_agent,
                locale="tr-TR",
                timezone_id="Europe/Istanbul",
                extra_http_headers={
                    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Referer": "https://www.google.com.tr/",
                },
            )

            try:
                page = await context.new_page()
                page.set_default_timeout(settings.scraper_timeout)

                # Apply playwright-stealth fingerprint masking
                await stealth_async(page)

                self.logger.info(f"UA: {user_agent[:60]}...")
                self.logger.info(f"Navigating to: {product_url}")

                # Jitter before navigation
                await self._random_jitter(2.0, 5.0)

                await page.goto(
                    product_url,
                    wait_until="domcontentloaded",
                    timeout=45000,
                )

                # Check for captcha / bot-detection page
                page_title = await page.title()
                if self._is_blocked(page_title):
                    self.logger.critical(
                        "DETECTED: Amazon triggered a Captcha or Block. "
                        f"Page title: '{page_title}'"
                    )
                    return {"products": [], "url": product_url, "total_products": 0}

                self.logger.info(f"Page title: {page_title}")

                # Wait for product cards
                try:
                    await page.wait_for_selector(self.RESULT_SELECTOR, timeout=15000)
                    self.logger.info("Product cards found on page")
                except Exception:
                    self.logger.warning(
                        "No product cards found after 15 s — page may have changed "
                        "structure or we're being throttled."
                    )

                # Simulate human scrolling before extraction
                await self._slow_scroll(page, steps=10)
                await self._random_jitter(1.0, 3.0)

                products = await self._extract_products(page)
                self.logger.info(f"Extracted {len(products)} products")

                return {
                    "products": products,
                    "url": product_url,
                    "total_products": len(products),
                }

            except Exception as e:
                self.logger.error(f"Scraping error: {e}", exc_info=True)
                raise
            finally:
                await context.close()
                await browser.close()

    async def _extract_products(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract product name, price, and URL from each search-result card.

        Uses multiple fallback selectors for each field so that minor DOM
        changes on Amazon do not silently yield 0 results.
        """
        products = []

        try:
            raw = await page.evaluate(
                f"""
                () => {{
                    const baseUrl = "{self.BASE_URL}";

                    // ── helper: first non-empty text from a list of selectors ──
                    function firstText(root, selectors) {{
                        for (const sel of selectors) {{
                            try {{
                                const el = root.querySelector(sel);
                                if (el) {{
                                    const t = el.textContent.trim();
                                    if (t.length > 0) return t;
                                }}
                            }} catch(e) {{}}
                        }}
                        return null;
                    }}

                    // ── helper: first href from a list of selectors ──
                    function firstHref(root, selectors) {{
                        for (const sel of selectors) {{
                            try {{
                                const el = root.querySelector(sel);
                                if (el) {{
                                    const h = el.getAttribute("href");
                                    if (h && h.length > 1) return h;
                                }}
                            }} catch(e) {{}}
                        }}
                        return null;
                    }}

                    // ── clean a raw price string into a plain decimal ──
                    function cleanPrice(raw) {{
                        if (!raw) return "0";
                        // Remove TL, currency symbols and whitespace
                        let s = raw.replace(/TL/gi, "")
                                   .replace(/₺/g, "")
                                   .replace(/\\u20BA/g, "")   // ₺ unicode
                                   .trim();
                        // Turkish format: 1.234,56  → count separators
                        // If string contains both '.' and ',' treat '.' as
                        // thousands sep and ',' as decimal sep
                        if (s.includes(".") && s.includes(",")) {{
                            s = s.replace(/\\./g, "").replace(",", ".");
                        }} else if (s.includes(",") && !s.includes(".")) {{
                            // only comma → might be decimal OR thousands
                            const parts = s.split(",");
                            if (parts.length === 2 && parts[1].length <= 2) {{
                                // treat as decimal
                                s = s.replace(",", ".");
                            }} else {{
                                s = s.replace(/,/g, "");
                            }}
                        }} else if (s.includes(".")) {{
                            // only dot → could be Turkish thousands (1.234) or decimal
                            const parts = s.split(".");
                            if (parts.length === 2 && parts[1].length === 3) {{
                                // thousands separator
                                s = s.replace(/\\./g, "");
                            }}
                            // else leave as-is (decimal dot)
                        }}
                        // keep only digits and one dot
                        s = s.replace(/[^0-9.]/g, "");
                        return s || "0";
                    }}

                    const cards = document.querySelectorAll(
                        '{self.RESULT_SELECTOR}'
                    );
                    const results = [];
                    let debugSnippet = null;

                    // capture a debug snippet from the first card if we get nothing
                    if (cards.length > 0 && !debugSnippet) {{
                        debugSnippet = cards[0].innerHTML.substring(0, 500);
                    }}

                    cards.forEach((card) => {{
                        // ── product name (3 fallbacks) ──
                        const name = firstText(card, [
                            "h2 a span",
                            "h2 span",
                            ".a-size-base-plus.a-color-base.a-text-normal",
                            ".a-size-medium.a-color-base.a-text-normal",
                            ".a-text-normal",
                        ]);

                        // ── price (3 fallbacks) ──
                        const rawPrice = firstText(card, [
                            ".a-price-whole",
                            ".a-price .a-offscreen",
                            ".a-price",
                            ".a-color-base.a-text-bold",
                        ]);

                        // ── URL (2 fallbacks) ──
                        let href = firstHref(card, [
                            "h2 a",
                            "a.a-link-normal[href*='/dp/']",
                            "a.a-link-normal",
                            "a[href*='/dp/']",
                        ]);
                        if (href && !href.startsWith("http")) {{
                            href = baseUrl + href;
                        }}

                        if (name && name.length > 2 && href) {{
                            results.push({{
                                product_name: name,
                                price: cleanPrice(rawPrice),
                                url: href,
                                currency: "TRY",
                                stock_status: "unknown",
                                _debug_raw_price: rawPrice,
                            }});
                        }}
                    }});

                    return {{ results, cardCount: cards.length, debugSnippet }};
                }}
                """
            )

            card_count = raw.get("cardCount", 0)
            items = raw.get("results", [])
            debug_snippet = raw.get("debugSnippet")

            self.logger.info(f"Cards found in DOM: {card_count}, items extracted: {len(items)}")

            if card_count > 0 and len(items) == 0:
                self.logger.warning(
                    "Cards were found but 0 products extracted — "
                    "selectors may not match current DOM."
                )
                if debug_snippet:
                    self.logger.debug(
                        f"First card HTML snippet (500 chars):\n{debug_snippet}"
                    )

            for item in items:
                item.pop("_debug_raw_price", None)
                item["price"] = DataValidator.sanitize_price(item["price"])
                products.append(item)

        except Exception as e:
            self.logger.error(f"Product extraction failed: {e}", exc_info=True)
            # Dump first 500 chars of the full body so we can diagnose
            try:
                body_snippet = await page.evaluate(
                    "() => document.body.innerHTML.substring(0, 500)"
                )
                self.logger.debug(f"Page body snippet:\n{body_snippet}")
            except Exception:
                pass

        return products

    async def validate_data(self, data: Dict[str, Any]) -> bool:
        return (
            "products" in data
            and isinstance(data["products"], list)
            and len(data["products"]) > 0
        )

    async def scrape_and_validate(self, product_url: str):
        """Convenience wrapper matching the TestStoreScraper interface."""
        self.logger.info(f"Starting Amazon TR scrape: {product_url}")
        start = datetime.now(timezone.utc)

        scraped = await self.scrape_with_retry(product_url)
        if not scraped:
            return [], []

        products = scraped.get("products", [])
        for p in products:
            p["scraped_at"] = datetime.now(timezone.utc).isoformat()
            p["site_name"] = self.site_name

        valid, invalid = DataValidator.validate_batch(products)

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        self.logger.info(
            f"Completed in {elapsed:.1f}s — "
            f"valid={len(valid)}, invalid={len(invalid)}"
        )
        return valid, invalid


# Keep the old placeholder name as an alias so existing imports don't break
AmazonScraper = AmazonTRScraper


class EbayScraper(BaseScraper):
    """eBay product scraper implementation."""
    
    def __init__(self):
        super().__init__(
            site_name="ebay",
            base_url="https://www.ebay.com"
        )
    
    async def scrape(self, product_url: str) -> Dict[str, Any]:
        """Implement eBay-specific scraping logic."""
        # Placeholder for Playwright integration
        product = {
            "product_name": "Sample eBay Product",
            "price": 15.99,
            "url": product_url,
            "currency": "USD",
            "stock_status": "in_stock"
        }
        return {
            "products": [product],
            "url": product_url,
            "total_products": 1
        }
    
    async def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate eBay product data."""
        return (
            "products" in data
            and isinstance(data["products"], list)
            and len(data["products"]) > 0
        )
