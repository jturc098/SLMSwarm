"""
Documentation lookup tool for common libraries and frameworks.
"""

from typing import Optional, Dict
from loguru import logger

from src.tools.web_search import web_search_tool
from src.tools.scraper import scraper_tool
from src.core.models import ScrapedContent


class DocLookupTool:
    """
    Specialized tool for finding and fetching library documentation.
    """
    
    def __init__(self):
        # Known documentation URLs for popular libraries
        self.doc_urls = {
            # Python
            "fastapi": "https://fastapi.tiangolo.com",
            "django": "https://docs.djangoproject.com",
            "flask": "https://flask.palletsprojects.com",
            "pydantic": "https://docs.pydantic.dev",
            "sqlalchemy": "https://docs.sqlalchemy.org",
            "pytest": "https://docs.pytest.org",
            
            # JavaScript/TypeScript
            "react": "https://react.dev",
            "vue": "https://vuejs.org",
            "nextjs": "https://nextjs.org/docs",
            "express": "https://expressjs.com",
            "typescript": "https://www.typescriptlang.org/docs",
            
            # Go
            "gin": "https://gin-gonic.com/docs",
            "echo": "https://echo.labstack.com",
            
            # Rust
            "actix": "https://actix.rs/docs",
            "tokio": "https://tokio.rs",
        }
    
    async def lookup(
        self,
        library: str,
        topic: Optional[str] = None
    ) -> Optional[ScrapedContent]:
        """
        Lookup documentation for a library.
        
        Args:
            library: Library name (e.g., "fastapi", "react")
            topic: Specific topic to look up (e.g., "authentication")
        
        Returns:
            Scraped documentation content
        """
        library_lower = library.lower()
        
        # If we know the docs URL, construct direct link
        if library_lower in self.doc_urls:
            base_url = self.doc_urls[library_lower]
            
            if topic:
                # Try to construct topic-specific URL
                url = await self._find_topic_url(base_url, topic)
            else:
                url = base_url
            
            logger.info(f"Looking up {library} docs: {url}")
            return await scraper_tool.scrape(url)
        
        # Otherwise, search for docs
        logger.info(f"Searching for {library} documentation")
        search_results = await web_search_tool.search_docs(library, topic or "")
        
        if not search_results:
            logger.warning(f"No documentation found for {library}")
            return None
        
        # Scrape the top result
        top_result = search_results[0]
        return await scraper_tool.scrape(top_result.url)
    
    async def lookup_api_reference(
        self,
        library: str,
        function_or_class: str
    ) -> Optional[ScrapedContent]:
        """
        Lookup specific API reference.
        
        Args:
            library: Library name
            function_or_class: Function or class name
        
        Returns:
            API reference content
        """
        query = f"{library} {function_or_class} api reference"
        results = await web_search_tool.search(query, num_results=3)
        
        if not results:
            return None
        
        # Filter to official documentation
        official_results = [
            r for r in results
            if library.lower() in r.url.lower()
        ]
        
        target_url = official_results[0].url if official_results else results[0].url
        return await scraper_tool.scrape(target_url)
    
    async def lookup_error(
        self,
        error_message: str,
        language: Optional[str] = None
    ) -> list[ScrapedContent]:
        """
        Lookup solutions for error messages.
        
        Args:
            error_message: Error message text
            language: Programming language (for context)
        
        Returns:
            List of potential solutions from Stack Overflow, etc.
        """
        query = f"{language or ''} {error_message}".strip()
        
        # Search code-specific sources
        results = await web_search_tool.search_code(query, num_results=5)
        
        # Scrape top 3 results
        urls = [r.url for r in results[:3]]
        scraped = await scraper_tool.scrape_multiple(urls, max_concurrent=3)
        
        return [s for s in scraped if s is not None]
    
    async def _find_topic_url(self, base_url: str, topic: str) -> str:
        """
        Try to construct topic-specific URL.
        
        For now, just returns base URL. Could implement:
        - Sitemap parsing
        - Search within docs site
        - URL pattern matching
        """
        # Simplified - would implement smarter URL construction
        return base_url


# Global doc lookup instance
doc_lookup_tool = DocLookupTool()