"""
Web search tool using Searxng.
"""

import asyncio
from typing import List, Optional
from datetime import datetime
import httpx
from loguru import logger

from src.core.config import settings
from src.core.models import SearchResult


class WebSearchTool:
    """
    Web search using self-hosted Searxng instance.
    """
    
    def __init__(self):
        self.searxng_url = settings.searxng_url
        self.enabled = settings.enable_web_search
        self.timeout = 30.0
        
        # Search preferences
        self.default_engines = [
            "google", "bing", "duckduckgo", "github", "stackoverflow"
        ]
    
    async def search(
        self,
        query: str,
        num_results: int = 5,
        engines: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Perform web search.
        
        Args:
            query: Search query
            num_results: Number of results to return
            engines: List of search engines to use
        
        Returns:
            List of search results
        """
        if not self.enabled:
            logger.warning("Web search is disabled")
            return []
        
        logger.info(f"Searching: {query}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "q": query,
                    "format": "json",
                    "pageno": 1,
                }
                
                if engines:
                    params["engines"] = ",".join(engines)
                
                response = await client.get(
                    f"{self.searxng_url}/search",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                results = data.get("results", [])[:num_results]
                
                return [
                    SearchResult(
                        url=r["url"],
                        title=r["title"],
                        snippet=r.get("content", ""),
                        relevance_score=self._calculate_relevance(r, query),
                        source="searxng",
                        fetched_at=datetime.utcnow()
                    )
                    for r in results
                ]
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def search_code(
        self,
        query: str,
        num_results: int = 5
    ) -> List[SearchResult]:
        """
        Search specifically for code examples.
        
        Uses GitHub and Stack Overflow engines.
        """
        return await self.search(
            query,
            num_results=num_results,
            engines=["github", "stackoverflow"]
        )
    
    async def search_docs(
        self,
        library: str,
        topic: str,
        num_results: int = 3
    ) -> List[SearchResult]:
        """
        Search for documentation on specific library/topic.
        """
        query = f"{library} {topic} documentation"
        return await self.search(query, num_results=num_results)
    
    def _calculate_relevance(self, result: dict, query: str) -> float:
        """
        Calculate relevance score for search result.
        
        Simple heuristic based on:
        - Query terms in title
        - Query terms in snippet
        - Result ranking (from Searxng)
        """
        score = 0.0
        query_terms = set(query.lower().split())
        
        # Check title
        title_lower = result.get("title", "").lower()
        title_matches = sum(1 for term in query_terms if term in title_lower)
        score += (title_matches / len(query_terms)) * 0.5
        
        # Check snippet
        content_lower = result.get("content", "").lower()
        content_matches = sum(1 for term in query_terms if term in content_lower)
        score += (content_matches / len(query_terms)) * 0.3
        
        # Use Searxng's score if available
        searxng_score = result.get("score", 0)
        score += min(searxng_score / 10, 0.2)
        
        return min(score, 1.0)


# Global search tool instance
web_search_tool = WebSearchTool()