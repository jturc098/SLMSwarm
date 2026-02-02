"""
HTTP client for communicating with llama.cpp model servers.
"""

import httpx
from typing import Optional
from loguru import logger

from src.core.models import AgentRole
from src.core.agent_registry import agent_registry


class AgentClient:
    """
    Client for communicating with llama.cpp model servers.
    
    Handles:
    - HTTP requests to model servers
    - Prompt formatting
    - Response parsing
    - Error handling
    """
    
    def __init__(self, role: AgentRole):
        self.role = role
        config = agent_registry.get_agent(role)
        
        if not config:
            raise ValueError(f"No configuration found for agent role: {role}")
        
        self.model_url = config.model_url
        self.model_name = config.model_name
        self.system_prompt = config.system_prompt
        self.temperature = config.temperature
        self.top_p = config.top_p
        self.context_size = config.context_size
        
        logger.info(f"Initialized {role.value} agent client -> {self.model_url}")
    
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop: Optional[list] = None
    ) -> dict:
        """
        Generate response from model.
        
        Args:
            prompt: User prompt
            max_tokens: Max tokens to generate
            temperature: Sampling temperature (overrides default)
            stop: Stop sequences
        
        Returns:
            Response dictionary with 'content' key
        """
        # Prepare request
        request_data = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature if temperature is not None else self.temperature,
            "top_p": self.top_p,
            "max_tokens": max_tokens or 2048,
            "stream": False
        }
        
        if stop:
            request_data["stop"] = stop
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                logger.debug(f"Calling {self.role.value} at {self.model_url}")
                
                response = await client.post(
                    f"{self.model_url}/v1/chat/completions",
                    json=request_data
                )
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                logger.info(
                    f"{self.role.value} generated {len(content.split())} words"
                )
                
                return {
                    "content": content,
                    "model": self.model_name,
                    "usage": data.get("usage", {})
                }
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling {self.role.value}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling {self.role.value}: {e}")
            raise
    
    async def generate_streaming(
        self,
        prompt: str,
        max_tokens: Optional[int] = None
    ):
        """
        Generate response with streaming.
        
        Args:
            prompt: User prompt
            max_tokens: Max tokens to generate
        
        Yields:
            Tokens as they're generated
        """
        request_data = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": max_tokens or 2048,
            "stream": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.model_url}/v1/chat/completions",
                    json=request_data
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            
                            try:
                                import json
                                data = json.loads(data_str)
                                if "choices" in data:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise


def create_agent_client(role: AgentRole) -> AgentClient:
    """Factory function to create agent clients."""
    return AgentClient(role)