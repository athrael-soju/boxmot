"""
Simplified Tools for Query Service Agents

This module defines standalone tool functions that work with the OpenAI Agents SDK.
"""

import json
import logging
from typing import List, Dict, Any, Optional

from agents import function_tool
from .data_access import DataAccessLayer

logger = logging.getLogger(__name__)

# Global data access instance (will be set by QueryTools)
_data_access: Optional[DataAccessLayer] = None

def set_data_access(data_access: DataAccessLayer):
    """Set the global data access instance"""
    global _data_access
    _data_access = data_access

@function_tool
def count_entities_by_type() -> str:
    """
    Get count of entities by their class/type.
    
    Returns:
        JSON string containing entity counts by class
    """
    try:
        if _data_access is None:
            return json.dumps({"error": "Data access not initialized"})
        
        counts = _data_access.count_entities_by_class()
        return json.dumps({"entity_counts": counts})
    except Exception as e:
        logger.error(f"Error in count_entities_by_type: {e}")
        return json.dumps({"error": str(e)})

@function_tool
def execute_custom_cypher(cypher_query: str, parameters: str = "{}") -> str:
    """
    Execute a custom Cypher query against the Neo4j database.
    
    Args:
        cypher_query: The Cypher query to execute
        parameters: JSON string of parameters for the query
        
    Returns:
        JSON string containing query results
    """
    try:
        if _data_access is None:
            return json.dumps({"error": "Data access not initialized"})
        
        # Parse parameters
        params = json.loads(parameters) if parameters else {}
        
        # Execute query
        results = _data_access.execute_cypher_query(cypher_query, params)
        
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
def find_entities_in_frame_range(start_frame: int, end_frame: int) -> str:
    """
    Find all entities that appear within a specific frame range.
    
    Args:
        start_frame: Starting frame number
        end_frame: Ending frame number
        
    Returns:
        JSON string containing entities found in the frame range
    """
    try:
        if _data_access is None:
            return json.dumps({"error": "Data access not initialized"})
        
        cypher_query = """
        MATCH (e:Entity)-[:DETECTED_IN]->(f:Frame)
        WHERE f.frame_idx >= $start_frame AND f.frame_idx <= $end_frame
        RETURN DISTINCT e.entity_id as entity_id, e.name as name, e.class_name as class_name,
               count(f) as appearances,
               collect(f.frame_idx) as frame_indices
        ORDER BY appearances DESC
        """
        
        results = _data_access.execute_cypher_query(
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

class SimpleQueryTools:
    """Simplified collection of tools for data querying"""
    
    def __init__(self, data_access: DataAccessLayer):
        self.data_access = data_access
        # Set the global data access for the standalone functions
        set_data_access(data_access)
    
    def get_all_tools(self) -> List:
        """Get all available tools for agents"""
        return [
            count_entities_by_type,
            execute_custom_cypher,
            find_entities_in_frame_range
        ] 