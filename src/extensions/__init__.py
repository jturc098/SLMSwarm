"""
Custom extensions for Agent Zero integration.
"""

from src.extensions.consensus import ConsensusEngine
from src.extensions.hydration import SpecHydration
from src.extensions.multi_model import MultiModelRouter

__all__ = [
    "ConsensusEngine",
    "SpecHydration", 
    "MultiModelRouter",
]