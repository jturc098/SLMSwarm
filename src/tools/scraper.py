"""
Web scraping tool using Jina Reader and Firecrawl.
"""

import asyncio
from typing import Optional
from datetime import datetime
import httpx
from loguru import logger

from src.core.config import settings
from src.core.models import ScrapedContent


class ScraperTool:
    """
    Web scraping with clean markdown output.
    
    Uses:
    1. Jina Reader API (free, fast) for simple pages
    2. Firecrawl (optional, paid) for JS-heavy sites
    """
    
    def __init__(self):
        self.jina_url = settings.jina_reader_api_url
        self.firecrawl_key = settings.firecrawl_api_key
        self.enabled = settings.enable_web_scraping
        self.timeout = 30.0
    
    async def scrape(
        self,
        url: str,
        use_firecrawl: bool = False
    ) -> Optional[ScrapedContent]:
        """
        Scrape URL and return clean markdown content.
        
        Args:
            url: URL to scrape
            use_firecrawl: Use Firecrawl for JS rendering (requires API key)
        
        Returns:
            Scraped content or None if failed
        """
        if not self.enabled:
            logger.warning("Web scraping is disabled")
            return None
        
        logger.info(f"Scraping: {url}")
        
        # Try Firecrawl first if requested and available
        if use_firecrawl and self.firecrawl_key:
            result = await self._scrape_firecrawl(url)
            if result:
                return result
        
        # Fall back to Jina Reader
        return await self._scrape_jina(url)
    
    async def _scrape_jina(self, url: str) -> Optional[ScrapedContent]:
        """Scrape using Jina Reader API."""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Jina Reader URL format: https://r.jina.ai/{original_url}
                jina_url = f"{self.jina_url}/{url}"
                
                response = await client.get(jina_url)
                response.raise_for_status()
                
                # Jina returns clean markdown
                content = response.text
                
                # Extract title if present (first line starting with #)
                lines = content.split("\n")
                title = None
                for line in lines:
                    if line.startswith("# "):
                        title = line.lstrip("# ").strip()
                        break
                
                return ScrapedContent(
                    url=url,
                    title=title,
                    content=content,
                    metadata={
                        "scraper": "jina",
                        "content_length": len(content)
                    },
                    scraped_at=datetime.utcnow()
                )
        
        except Exception as e:
            logger.error(f"Jina scraping failed for {url}: {e}")
            return None
    
    async def _scrape_firecrawl(self, url: str) -> Optional[ScrapedContent]:
        """Scrape using Firecrawl API (handles JS-rendered sites)."""
        
        if not self.firecrawl_key:
            logger.warning("Firecrawl API key not configured")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "Authorization": f"Bearer {self.firecrawl_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "url": url,
                    "formats": ["markdown"],
                    "onlyMainContent": True
                }
                
                response = await client.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                
                result = response.json()
                
                return ScrapedContent(
                    url=url,
                    title=result.get("metadata", {}).get("title"),
                    content=result.get("markdown", ""),
                    metadata={
                        "scraper": "firecrawl",
                        **result.get("metadata", {})
                    },
                    scraped_at=datetime.utcnow()
                )
        
        except Exception as e:
            logger.error(f"Firecrawl scraping failed for {url}: {e}")
            return None
    
    async def scrape_multiple(
        self,
        urls: list[str],
        max_concurrent: int = 3
    ) -> list[Optional[ScrapedContent]]:
        """
        Scrape multiple URLs concurrently.
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent scrapes
        
        Returns:
            List of scraped content (None for failed scrapes)
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_limit(url):
            async with semaphore:
                return await self.scrape(url)
        
        return await asyncio.gather(
            *[scrape_with_limit(url) for url in urls],
            return_exceptions=False
        )


# Global scraper instance
scraper_tool = ScraperTool()