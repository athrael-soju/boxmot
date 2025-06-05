"""
BoxMOT Query Service

A multi-agent system for intelligent querying of multimodal video analysis data.
Uses OpenAI Agents SDK for coordinated agent interactions.
"""

from .service import QueryService
from .query_agents import SecretaryAgent, QueryOptimizerAgent, QuickAnswerAgent, LibrarianAgent

__all__ = [
    'QueryService',
    'SecretaryAgent', 
    'QueryOptimizerAgent',
    'QuickAnswerAgent',
    'LibrarianAgent'
] 