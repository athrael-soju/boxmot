"""
Multi-Agent Query Service Package

A sophisticated multi-agent system for querying multimodal data using OpenAI Agents SDK.
"""

from .service import MultiAgentQueryService
from .core import initialize_components
from .main import main

__version__ = "1.0.0"
__all__ = ["MultiAgentQueryService", "initialize_components", "main"] 