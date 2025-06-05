"""
Intent Classification Module for improved agent routing.
"""

import re
from typing import Dict, List, Tuple
from enum import Enum

class QueryIntent(Enum):
    """Query intent categories for routing decisions."""
    DATA_RETRIEVAL = "data_retrieval"
    CONVERSATION_HISTORY = "conversation_history"
    GENERAL_QUESTION = "general_question"
    UNCLEAR_QUERY = "unclear_query"

class IntentClassifier:
    """Semantic intent classifier for query routing."""
    
    def __init__(self):
        # Define keyword patterns for different intents
        self.data_retrieval_patterns = {
            'evidence_investigation': [
                r'\b(evidence|proof|findings|results)\b',
                r'\b(show\s+me|find|search|locate|identify|detect|discover)\b',
                r'\b(shoplifting|theft|crime|security|surveillance|monitoring)\b'
            ],
            'visual_content': [
                r'\b(video|image|frame|visual|see|look|appearance)\b',
                r'\b(person|people|object|activity|behavior)\b',
                r'\b(camera|recording|footage)\b'
            ],
            'audio_content': [
                r'\b(audio|sound|voice|speech|transcript|spoken)\b',
                r'\b(conversation|dialogue|talk|say|said)\b',
                r'\b(microphone|recording|playback)\b'
            ],
            'temporal_queries': [
                r'\b(when|at\s+what\s+time|during|timestamp)\b',
                r'\b(moment|period|time|hour|minute|second)\b',
                r'\b(start|end|begin|finish|duration)\b'
            ],
            'spatial_queries': [
                r'\b(where|location|position|area|room|place)\b',
                r'\b(here|there|nearby|distance|coordinates)\b'
            ],
            'entity_queries': [
                r'\b(who|person|people|individual|character|actor)\b',
                r'\b(what\s+happened|event|incident|occurrence)\b',
                r'\b(activity|action|interaction|relationship)\b'
            ]
        }
        
        self.conversation_history_patterns = [
            r'\b(previous|earlier|before|past)\b',
            r'\b(conversation|history|discussed|mentioned)\b',
            r'\b(said\s+before|recall|remember|past\s+interactions)\b',
            r'\b(what\s+was\s+said|previously\s+talked|earlier\s+discussion)\b'
        ]
        
        self.general_question_patterns = [
            r'\b(hello|hi|hey|greetings)\b',
            r'\b(help|assistance|support)\b',
            r'\b(how\s+does|what\s+is|can\s+you|are\s+you\s+able)\b',
            r'\b(capabilities|features|functions)\b'
        ]
        
        self.unclear_indicators = [
            r'^.{1,10}$',  # Very short queries
            r'^(um|uh|hmm|well)',  # Hesitation words
            r'\?{2,}',  # Multiple question marks
            r'\b(something|anything|stuff|things)\b'  # Vague terms
        ]
    
    def classify_intent(self, query: str) -> Tuple[QueryIntent, float, Dict[str, float]]:
        """
        Classify query intent with confidence scores.
        
        Returns:
            Tuple of (primary_intent, confidence, all_scores)
        """
        query_lower = query.lower().strip()
        
        # Calculate scores for each intent
        scores = {
            QueryIntent.DATA_RETRIEVAL: self._score_data_retrieval(query_lower),
            QueryIntent.CONVERSATION_HISTORY: self._score_conversation_history(query_lower),
            QueryIntent.GENERAL_QUESTION: self._score_general_question(query_lower),
            QueryIntent.UNCLEAR_QUERY: self._score_unclear_query(query_lower)
        }
        
        # Find primary intent
        primary_intent = max(scores.items(), key=lambda x: x[1])
        
        return primary_intent[0], primary_intent[1], {k.value: v for k, v in scores.items()}
    
    def _score_data_retrieval(self, query: str) -> float:
        """Score likelihood that query requires data retrieval."""
        total_score = 0.0
        
        for category, patterns in self.data_retrieval_patterns.items():
            category_score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, query, re.IGNORECASE))
                category_score += matches * 0.3
            
            # Apply category weights
            if category == 'evidence_investigation':
                category_score *= 1.5  # Higher weight for investigation queries
            elif category == 'temporal_queries' or category == 'spatial_queries':
                category_score *= 1.3  # Higher weight for specific questions
            
            total_score += min(category_score, 1.0)  # Cap category contribution
        
        return min(total_score, 1.0)
    
    def _score_conversation_history(self, query: str) -> float:
        """Score likelihood that query is about conversation history."""
        score = 0.0
        
        for pattern in self.conversation_history_patterns:
            matches = len(re.findall(pattern, query, re.IGNORECASE))
            score += matches * 0.4
        
        return min(score, 1.0)
    
    def _score_general_question(self, query: str) -> float:
        """Score likelihood that query is a general question."""
        score = 0.0
        
        for pattern in self.general_question_patterns:
            matches = len(re.findall(pattern, query, re.IGNORECASE))
            score += matches * 0.3
        
        # Boost score for system capability questions
        if any(word in query for word in ['system', 'capability', 'feature', 'function']):
            score += 0.3
        
        return min(score, 1.0)
    
    def _score_unclear_query(self, query: str) -> float:
        """Score likelihood that query is unclear or needs optimization."""
        score = 0.0
        
        for pattern in self.unclear_indicators:
            if re.search(pattern, query, re.IGNORECASE):
                score += 0.4
        
        # Additional heuristics
        if len(query.split()) < 3:  # Very short queries
            score += 0.3
        if not query.strip().endswith(('?', '.', '!')):  # No punctuation
            score += 0.2
        
        return min(score, 1.0)
    
    def get_routing_recommendation(self, query: str) -> Dict[str, any]:
        """
        Get routing recommendation with reasoning.
        
        Returns:
            Dictionary with recommended agent, confidence, and reasoning
        """
        intent, confidence, all_scores = self.classify_intent(query)
        
        # Map intents to agents
        agent_mapping = {
            QueryIntent.DATA_RETRIEVAL: "Librarian Agent",
            QueryIntent.CONVERSATION_HISTORY: "Memory Agent", 
            QueryIntent.GENERAL_QUESTION: "Quick Answer Agent",
            QueryIntent.UNCLEAR_QUERY: "Query Optimization Agent"
        }
        
        recommended_agent = agent_mapping[intent]
        
        # Generate reasoning
        reasoning_parts = []
        for intent_type, score in sorted(all_scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0.1:  # Only include significant scores
                reasoning_parts.append(f"{intent_type}: {score:.2f}")
        
        reasoning = f"Intent analysis: {', '.join(reasoning_parts)}"
        
        return {
            "recommended_agent": recommended_agent,
            "primary_intent": intent.value,
            "confidence": confidence,
            "all_scores": all_scores,
            "reasoning": reasoning,
            "should_fallback": confidence < 0.3  # Low confidence suggests uncertainty
        }

# Global instance
intent_classifier = IntentClassifier() 