"""Fetch and parse a company website to extract structured context."""
from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.company.context_store import WebsiteContext, WebsitePageData

logger = logging.getLogger(__name__)

# Pages we actively look for relative to the root
_INTERESTING_PATHS = [
    "/",
    "/about",
    "/about-us",
    "/pricing",
    "/features",
    "/products",
    "/team",
    "/privacy",
    "/privacy-policy",
    "/terms",
    "/terms-of-service",
    "/contact",
    "/faq",
]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ZBS-Bot/1.0; +https://github.com/baher228/ZBS)"
    ),
    "Accept": "text/html,application/xhtml+xml",
}

_MAX_PAGES = 10
_TIMEOUT = 15


def _classify_page(url: str, title: str, text: str) -> str:
    """Heuristic page-type classifier."""
    path = urlparse(url).path.lower().rstrip("/")
    combined = (path + " " + title).lower()

    if path in ("", "/") or "home" in combined:
        return "homepage"
    if "about" in combined or "team" in combined or "who we are" in combined:
        return "about"
    if "pricing" in combined or "plans" in combined:
        return "pricing"
    if "feature" in combined or "product" in combined:
        return "features"
    if "privacy" in combined:
        return "privacy_policy"
    if "terms" in combined or "tos" in combined:
        return "terms_of_service"
    if "faq" in combined or "help" in combined:
        return "faq"
    if "contact" in combined:
        return "contact"
    if "blog" in combined:
        return "blog"
    return "other"


def _extract_text(html: str) -> tuple[str, str]:
    """Return (title, body_text) from raw HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove scripts, styles, nav, footer
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Get main content area if available
    main = soup.find("main") or soup.find("article") or soup.find(id="content") or soup.body
    if main is None:
        main = soup

    text = main.get_text(separator="\n", strip=True)

    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Truncate to ~4000 chars for LLM processing
    if len(text) > 4000:
        text = text[:4000] + "…"

    return title, text


def _discover_links(html: str, base_url: str) -> list[str]:
    """Find internal links that might be interesting pages."""
    soup = BeautifulSoup(html, "html.parser")
    base_domain = urlparse(base_url).netloc
    found: set[str] = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if parsed.netloc != base_domain:
            continue
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
        if clean not in found and len(found) < 30:
            found.add(clean)

    return list(found)


async def parse_website(url: str) -> WebsiteContext:
    """Crawl a company website and extract structured data.

    Fetches the homepage plus any discoverable internal pages (about, pricing, etc.)
    up to _MAX_PAGES.
    """
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"
        parsed = urlparse(url)

    base = f"{parsed.scheme}://{parsed.netloc}"

    # Build candidate URLs
    candidates = [urljoin(base, p) for p in _INTERESTING_PATHS]

    pages: list[WebsitePageData] = []
    visited: set[str] = set()

    async with httpx.AsyncClient(
        headers=_HEADERS,
        timeout=_TIMEOUT,
        follow_redirects=True,
        verify=False,
    ) as client:
        # Fetch homepage first to discover more links
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            homepage_html = resp.text
            title, text = _extract_text(homepage_html)
            page_type = _classify_page(url, title, text)
            pages.append(
                WebsitePageData(
                    url=url,
                    title=title,
                    page_type=page_type,
                    content_summary=text[:2000],
                )
            )
            visited.add(url.rstrip("/"))

            # Discover links from homepage
            discovered = _discover_links(homepage_html, base)
            candidates.extend(discovered)
        except Exception:
            logger.warning("Failed to fetch homepage: %s", url, exc_info=True)

        # Deduplicate and limit
        seen_normalized: set[str] = {url.rstrip("/")}
        unique_candidates: list[str] = []
        for c in candidates:
            norm = c.rstrip("/")
            if norm not in seen_normalized:
                seen_normalized.add(norm)
                unique_candidates.append(c)

        for candidate_url in unique_candidates:
            if len(pages) >= _MAX_PAGES:
                break
            norm = candidate_url.rstrip("/")
            if norm in visited:
                continue
            visited.add(norm)

            try:
                resp = await client.get(candidate_url)
                if resp.status_code == 404:
                    continue
                resp.raise_for_status()
                title, text = _extract_text(resp.text)
                if not text or len(text) < 50:
                    continue
                page_type = _classify_page(candidate_url, title, text)
                pages.append(
                    WebsitePageData(
                        url=candidate_url,
                        title=title,
                        page_type=page_type,
                        content_summary=text[:2000],
                    )
                )
            except Exception:
                logger.debug("Skipping %s", candidate_url, exc_info=True)

    # Build structured context from pages
    ctx = WebsiteContext(source_url=url, pages=pages)

    for page in pages:
        if page.page_type == "homepage":
            ctx.company_summary = page.content_summary[:1000]
        elif page.page_type == "pricing":
            ctx.pricing_info = page.content_summary[:1000]
        elif page.page_type in ("about", "team"):
            ctx.team_info = (ctx.team_info + " " + page.content_summary[:500]).strip()
        elif page.page_type == "features":
            ctx.products_and_services = page.content_summary[:1000]
        elif page.page_type in ("privacy_policy", "terms_of_service"):
            ctx.legal_info = (ctx.legal_info + " " + page.content_summary[:500]).strip()

    return ctx
