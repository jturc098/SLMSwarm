"""
ChromaDB-based persistent memory system.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger
import chromadb
from chromadb.config import Settings

from src.core.config import settings
from src.core.models import MemoryEntry


class PersistentMemory:
    """
    Persistent memory using ChromaDB vector store.
    
    Features:
    - Semantic search over past experiences
    - Long-term knowledge retention
    - Pattern storage and retrieval
    - Episodic memory for debugging
    """
    
    def __init__(self):
        self.client = None
        self.collections = {}
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize ChromaDB client."""
        try:
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(settings.chromadb_persist_dir),
                anonymized_telemetry=False
            ))
            
            # Create collections for different memory types
            self.collections = {
                "code_patterns": self._get_or_create_collection("code_patterns"),
                "solutions": self._get_or_create_collection("solutions"),
                "errors": self._get_or_create_collection("errors"),
                "experiences": self._get_or_create_collection("experiences"),
            }
            
            logger.info("ChromaDB persistent memory initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        try:
            return self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"Failed to create collection {name}: {e}")
            raise
    
    async def store(
        self,
        content: str,
        collection_name: str,
        metadata: Optional[Dict] = None,
        embedding: Optional[List[float]] = None
    ) -> MemoryEntry:
        """
        Store content in persistent memory.
        
        Args:
            content: Text content to store
            collection_name: Which collection to store in
            metadata: Additional metadata
            embedding: Pre-computed embedding (optional)
        
        Returns:
            MemoryEntry with stored data
        """
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")
        
        entry_id = str(uuid.uuid4())
        collection = self.collections[collection_name]
        
        # Add metadata
        full_metadata = metadata or {}
        full_metadata.update({
            "created_at": datetime.utcnow().isoformat(),
            "accessed_count": 0
        })
        
        try:
            # ChromaDB will auto-generate embeddings if not provided
            if embedding:
                collection.add(
                    ids=[entry_id],
                    documents=[content],
                    metadatas=[full_metadata],
                    embeddings=[embedding]
                )
            else:
                collection.add(
                    ids=[entry_id],
                    documents=[content],
                    metadatas=[full_metadata]
                )
            
            logger.info(f"Stored memory entry {entry_id} in {collection_name}")
            
            return MemoryEntry(
                id=entry_id,
                content=content,
                embedding=embedding,
                metadata=full_metadata,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    async def search(
        self,
        query: str,
        collection_name: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[MemoryEntry]:
        """
        Semantic search in memory.
        
        Args:
            query: Search query
            collection_name: Which collection to search
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
        
        Returns:
            List of matching memory entries
        """
        if collection_name not in self.collections:
            raise ValueError(f"Unknown collection: {collection_name}")
        
        collection = self.collections[collection_name]
        
        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Convert to MemoryEntry objects
            entries = []
            for i in range(len(results['ids'][0])):
                entry = MemoryEntry(
                    id=results['ids'][0][i],
                    content=results['documents'][0][i],
                    embedding=results['embeddings'][0][i] if results.get('embeddings') else None,
                    metadata=results['metadatas'][0][i],
                    created_at=datetime.fromisoformat(
                        results['metadatas'][0][i]['created_at']
                    )
                )
                entries.append(entry)
            
            logger.info(f"Found {len(entries)} memories for query: {query[:50]}...")
            return entries
            
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []
    
    async def store_code_pattern(
        self,
        pattern_name: str,
        code: str,
        language: str,
        context: str,
        success_metrics: Dict
    ) -> MemoryEntry:
        """
        Store a successful code pattern for future reuse.
        
        Args:
            pattern_name: Name of the pattern (e.g., "JWT Auth Implementation")
            code: The actual code
            language: Programming language
            context: When/why this pattern works
            success_metrics: Performance/quality metrics
        
        Returns:
            Stored memory entry
        """
        content = f"""Pattern: {pattern_name}
Language: {language}
Context: {context}

Code:
{code}
"""
        
        metadata = {
            "type": "code_pattern",
            "pattern_name": pattern_name,
            "language": language,
            "success_rate": success_metrics.get("success_rate", 1.0),
            "usage_count": 0
        }
        
        return await self.store(content, "code_patterns", metadata)
    
    async def store_solution(
        self,
        problem: str,
        solution: str,
        approach: str,
        verified: bool
    ) -> MemoryEntry:
        """
        Store a successful solution.
        
        Args:
            problem: Problem description
            solution: Solution code/approach
            approach: Which approach was used
            verified: Whether it passed QA
        
        Returns:
            Stored memory entry
        """
        content = f"""Problem: {problem}

Approach: {approach}

Solution:
{solution}
"""
        
        metadata = {
            "type": "solution",
            "approach": approach,
            "verified": verified,
            "reuse_count": 0
        }
        
        return await self.store(content, "solutions", metadata)
    
    async def store_error_resolution(
        self,
        error_message: str,
        context: str,
        resolution: str,
        success: bool
    ) -> MemoryEntry:
        """
        Store error resolution for future reference.
        
        Args:
            error_message: The error that occurred
            context: Context where error happened
            resolution: How it was resolved
            success: Whether resolution worked
        
        Returns:
            Stored memory entry
        """
        content = f"""Error: {error_message}

Context: {context}

Resolution:
{resolution}
"""
        
        metadata = {
            "type": "error_resolution",
            "error_type": self._classify_error(error_message),
            "success": success
        }
        
        return await self.store(content, "errors", metadata)
    
    async def recall_similar_patterns(
        self,
        description: str,
        language: Optional[str] = None,
        n_results: int = 3
    ) -> List[MemoryEntry]:
        """
        Recall similar code patterns from memory.
        
        Args:
            description: Description of what you're trying to do
            language: Optional language filter
            n_results: Number of patterns to return
        
        Returns:
            List of relevant patterns
        """
        filter_metadata = {"type": "code_pattern"}
        if language:
            filter_metadata["language"] = language
        
        return await self.search(
            description,
            "code_patterns",
            n_results=n_results,
            filter_metadata=filter_metadata
        )
    
    async def recall_similar_solutions(
        self,
        problem: str,
        n_results: int = 3
    ) -> List[MemoryEntry]:
        """Recall similar solutions from past work."""
        return await self.search(
            problem,
            "solutions",
            n_results=n_results,
            filter_metadata={"type": "solution", "verified": True}
        )
    
    async def recall_error_solutions(
        self,
        error_message: str,
        n_results: int = 3
    ) -> List[MemoryEntry]:
        """Recall how similar errors were resolved."""
        return await self.search(
            error_message,
            "errors",
            n_results=n_results,
            filter_metadata={"type": "error_resolution", "success": True}
        )
    
    def _classify_error(self, error_message: str) -> str:
        """Classify error type for categorization."""
        error_lower = error_message.lower()
        
        if "syntax" in error_lower:
            return "syntax"
        elif "import" in error_lower or "module" in error_lower:
            return "import"
        elif "type" in error_lower:
            return "type"
        elif "attribute" in error_lower:
            return "attribute"
        elif "name" in error_lower:
            return "name"
        elif "index" in error_lower:
            return "index"
        elif "key" in error_lower:
            return "key"
        else:
            return "general"
    
    async def get_statistics(self) -> Dict:
        """Get memory statistics."""
        stats = {}
        
        for name, collection in self.collections.items():
            count = collection.count()
            stats[name] = {
                "count": count,
                "collection": name
            }
        
        return stats


# Global persistent memory instance
persistent_memory = PersistentMemory()