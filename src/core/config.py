"""
Configuration management for Project Hydra-Consensus.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Model Server URLs
    architect_url: str = Field(default="http://localhost:8081", description="Architect model server")
    worker_backend_url: str = Field(default="http://localhost:8082", description="Backend worker model")
    worker_frontend_url: str = Field(default="http://localhost:8083", description="Frontend worker model")
    qa_url: str = Field(default="http://localhost:8084", description="QA sentinel model")
    judge_url: str = Field(default="http://localhost:8085", description="Consensus judge model")
    
    # Supporting Services
    chromadb_url: str = Field(default="http://localhost:8000", description="ChromaDB vector store")
    searxng_url: str = Field(default="http://localhost:8889", description="Searxng search engine")
    redis_url: str = Field(default="redis://localhost:6379", description="Redis cache")
    
    # Model Configuration
    model_dir: Path = Field(default=Path("./models"), description="Model storage directory")
    architect_model: str = "DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf"
    worker_backend_model: str = "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"
    worker_frontend_model: str = "Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf"
    qa_model: str = "DeepSeek-R1-Distill-Qwen-1.5B-Q6_K.gguf"
    judge_model: str = "Phi-4-Mini-Q4_K_M.gguf"
    
    # Memory Configuration
    memory_dir: Path = Field(default=Path("./memory"), description="Memory persistence directory")
    chromadb_persist_dir: Path = Field(default=Path("./memory/chromadb"))
    redis_persist_dir: Path = Field(default=Path("./memory/redis"))
    
    # Consensus Configuration
    consensus_n_candidates: int = Field(default=3, ge=1, le=10, description="Number of parallel candidates")
    consensus_min_votes: int = Field(default=2, ge=1, description="Minimum votes for consensus")
    consensus_timeout_seconds: int = Field(default=300, ge=30, description="Consensus timeout")
    
    # Execution Configuration
    docker_sandbox_enabled: bool = Field(default=True, description="Enable Docker sandboxing")
    docker_sandbox_timeout: int = Field(default=600, ge=60, description="Sandbox timeout")
    max_parallel_tasks: int = Field(default=4, ge=1, le=10, description="Max parallel tasks")
    
    # Web Tools Configuration
    jina_reader_api_url: str = Field(default="https://r.jina.ai", description="Jina Reader API")
    firecrawl_api_key: Optional[str] = Field(default=None, description="Firecrawl API key")
    enable_web_search: bool = Field(default=True, description="Enable web search")
    enable_web_scraping: bool = Field(default=True, description="Enable web scraping")
    
    # Agent Zero Configuration
    agent_zero_max_iterations: int = Field(default=50, ge=1, description="Max agent iterations")
    agent_zero_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    agent_zero_top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Path = Field(default=Path("./logs/hydra.log"), description="Log file path")
    
    # Performance Tuning
    enable_flash_attention: bool = Field(default=True, description="Enable Flash Attention")
    enable_kv_cache_quantization: bool = Field(default=True, description="Enable KV cache quantization")
    kv_cache_precision: str = Field(default="q8_0", description="KV cache precision")
    context_size_architect: int = Field(default=32768, ge=512, description="Architect context size")
    context_size_worker: int = Field(default=16384, ge=512, description="Worker context size")
    context_size_qa: int = Field(default=8192, ge=512, description="QA context size")
    
    # Development
    debug: bool = Field(default=False, description="Debug mode")
    telemetry_enabled: bool = Field(default=False, description="Telemetry enabled")
    
    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.model_dir,
            self.memory_dir,
            self.chromadb_persist_dir,
            self.redis_persist_dir,
            self.log_file.parent,
            Path("./specs"),
            Path("./agent-zero"),
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()