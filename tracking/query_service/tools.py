"""
Tools for Query Service Agents

This module defines tools that agents can use to query data.
The tools are designed to work with the OpenAI Agents SDK.
"""

import json
import logging
from typing import List, Dict, Any, Optional

# Note: We'll need to install openai-agents to use these decorators
# For now, I'll create the structure that will work with the SDK
try:
    from agents import function_tool
except ImportError:
    # Fallback for when the package isn't installed yet
    def function_tool(func):
        func._is_tool = True
        return func

from .data_access import DataAccessLayer

logger = logging.getLogger(__name__)

class QueryTools:
    """Collection of tools for data querying"""
    
    def __init__(self, data_access: DataAccessLayer):
        self.data_access = data_access
    
    def search_entities_by_text(self, query: str, limit: int = 10) -> str:
        """
        Search for entities using natural language query.
        
        Args:
            query: Natural language description of what to search for
            limit: Maximum number of results to return
            
        Returns:
            JSON string containing search results
        """
        try:
            # Generate embedding for the query
            query_embedding = self.data_access.embed_text(query)
            if query_embedding is None:
                return json.dumps({"error": "Failed to generate embedding for query"})
            
            # Search entities
            entities = self.data_access.search_entities(query_embedding, limit=limit)
            
            # Format results
            results = []
            for entity in entities:
                payload = entity.get("payload", {})
                results.append({
                    "entity_id": payload.get("entity_id"),
                    "class_name": payload.get("class_name"),
                    "confidence": payload.get("confidence"),
                    "similarity_score": entity.get("score"),
                    "caption": payload.get("image_caption") if payload.get("image_caption") else "No caption available"
                })
            
            return json.dumps({
                "query": query,
                "results_count": len(results),
                "entities": results
            })
            
        except Exception as e:
            logger.error(f"Error in search_entities_by_text: {e}")
            return json.dumps({"error": str(e)})
    
    @function_tool
    def search_audio_transcripts(self, query: str, limit: int = 10) -> str:
        """
        Search audio transcripts using natural language query.
        
        Args:
            query: Natural language description of what to search for
            limit: Maximum number of results to return
            
        Returns:
            JSON string containing search results
        """
        try:
            # Generate embedding for the query
            query_embedding = self.data_access.embed_text(query)
            if query_embedding is None:
                return json.dumps({"error": "Failed to generate embedding for query"})
            
            # Search transcripts
            transcripts = self.data_access.search_audio_transcripts(query_embedding, limit=limit)
            
            # Format results
            results = []
            for transcript in transcripts:
                payload = transcript.get("payload", {})
                results.append({
                    "segment_id": payload.get("audio_segment_unique_id"),
                    "speaker": payload.get("speaker_label"),
                    "start_time": payload.get("start_time_seconds"),
                    "end_time": payload.get("end_time_seconds"),
                    "transcript": payload.get("transcript_text"),
                    "similarity_score": transcript.get("score")
                })
            
            return json.dumps({
                "query": query,
                "results_count": len(results),
                "transcripts": results
            })
            
        except Exception as e:
            logger.error(f"Error in search_audio_transcripts: {e}")
            return json.dumps({"error": str(e)})
    
    @function_tool
    def get_entity_details(self, entity_id: str) -> str:
        """
        Get detailed information about a specific entity.
        
        Args:
            entity_id: The ID of the entity to get details for
            
        Returns:
            JSON string containing entity details
        """
        try:
            summary = self.data_access.get_entity_summary(entity_id)
            return json.dumps(summary)
        except Exception as e:
            logger.error(f"Error in get_entity_details: {e}")
            return json.dumps({"error": str(e)})
    
    @function_tool
    def get_entity_relationships(self, entity_ids: List[str]) -> str:
        """
        Get relationships between entities.
        
        Args:
            entity_ids: List of entity IDs to analyze relationships for
            
        Returns:
            JSON string containing relationship data
        """
        try:
            relationships = self.data_access.get_entity_relationships(entity_ids)
            return json.dumps(relationships)
        except Exception as e:
            logger.error(f"Error in get_entity_relationships: {e}")
            return json.dumps({"error": str(e)})
    
    @function_tool
    def count_entities_by_type(self) -> str:
        """
        Get count of entities by their class/type.
        
        Returns:
            JSON string containing entity counts by class
        """
        try:
            counts = self.data_access.count_entities_by_class()
            return json.dumps({"entity_counts": counts})
        except Exception as e:
            logger.error(f"Error in count_entities_by_type: {e}")
            return json.dumps({"error": str(e)})
    
    @function_tool
    def get_temporal_analysis(self, start_frame: int = None, end_frame: int = None) -> str:
        """
        Get temporal analysis of entity appearances across frames.
        
        Args:
            start_frame: Optional start frame for analysis
            end_frame: Optional end frame for analysis
            
        Returns:
            JSON string containing temporal analysis
        """
        try:
            analysis = self.data_access.get_temporal_analysis(start_frame, end_frame)
            return json.dumps(analysis)
        except Exception as e:
            logger.error(f"Error in get_temporal_analysis: {e}")
            return json.dumps({"error": str(e)})
    
    @function_tool
    def execute_custom_cypher(self, cypher_query: str, parameters: str = "{}") -> str:
        """
        Execute a custom Cypher query against the Neo4j database.
        
        Args:
            cypher_query: The Cypher query to execute
            parameters: JSON string of parameters for the query
            
        Returns:
            JSON string containing query results
        """
        try:
            # Parse parameters
            params = json.loads(parameters) if parameters else {}
            
            # Execute query
            results = self.data_access.execute_cypher_query(cypher_query, params)
            
            return json.dumps({
                "query": cypher_query,
                "parameters": params,
                "results_count": len(results),
                "results": results
            })
            
        except Exception as e:
            logger.error(f"Error in execute_custom_cypher: {e}")
            return json.dumps({"error": str(e)})
    
    @function_tool
    def search_frames_by_content(self, query: str, limit: int = 10) -> str:
        """
        Search video frames by content description.
        
        Args:
            query: Natural language description of frame content
            limit: Maximum number of results to return
            
        Returns:
            JSON string containing search results
        """
        try:
            # Generate embedding for the query
            query_embedding = self.data_access.embed_text(query)
            if query_embedding is None:
                return json.dumps({"error": "Failed to generate embedding for query"})
            
            # Search frames
            frames = self.data_access.search_frames(query_embedding, limit=limit)
            
            # Format results
            results = []
            for frame in frames:
                payload = frame.get("payload", {})
                results.append({
                    "frame_id": frame.get("id"),
                    "frame_idx": payload.get("frame_idx"),
                    "timestamp": payload.get("timestamp"),
                    "entity_count": payload.get("entity_count"),
                    "similarity_score": frame.get("score"),
                    "caption": payload.get("image_caption") if payload.get("image_caption") else "No caption available"
                })
            
            return json.dumps({
                "query": query,
                "results_count": len(results),
                "frames": results
            })
            
        except Exception as e:
            logger.error(f"Error in search_frames_by_content: {e}")
            return json.dumps({"error": str(e)})
    
    @function_tool
    def find_entities_in_frame_range(self, start_frame: int, end_frame: int) -> str:
        """
        Find all entities that appear within a specific frame range.
        
        Args:
            start_frame: Starting frame number
            end_frame: Ending frame number
            
        Returns:
            JSON string containing entities found in the frame range
        """
        try:
            cypher_query = """
            MATCH (e:Entity)-[:DETECTED_IN]->(f:Frame)
            WHERE f.frame_idx >= $start_frame AND f.frame_idx <= $end_frame
            RETURN DISTINCT e.entity_id as entity_id, e.name as name, e.class_name as class_name,
                   count(f) as appearances,
                   collect(f.frame_idx) as frame_indices
            ORDER BY appearances DESC
            """
            
            results = self.data_access.execute_cypher_query(
                cypher_query, 
                {"start_frame": start_frame, "end_frame": end_frame}
            )
            
            return json.dumps({
                "frame_range": f"{start_frame}-{end_frame}",
                "results_count": len(results),
                "entities": results
            })
            
        except Exception as e:
            logger.error(f"Error in find_entities_in_frame_range: {e}")
            return json.dumps({"error": str(e)})

    def get_all_tools(self) -> List:
        """Get all available tools for agents"""
        return [
            self.search_entities_by_text,
            self.search_audio_transcripts,
            self.get_entity_details,
            self.get_entity_relationships,
            self.count_entities_by_type,
            self.get_temporal_analysis,
            self.execute_custom_cypher,
            self.search_frames_by_content,
            self.find_entities_in_frame_range
        ] 