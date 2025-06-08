import os
from fastapi import FastAPI
from pydantic import BaseModel
from qdrant_client import QdrantClient
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

# --- Configuration ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'

app = FastAPI()

# --- Clients and Models Initialization ---
try:
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=6333)
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print("Query service initialized successfully.")
except Exception as e:
    print(f"Error during query service initialization: {e}")
    qdrant_client = None
    neo4j_driver = None
    embedding_model = None

class QueryRequest(BaseModel):
    prompt: str

@app.post("/query/")
async def query_narrative(request: QueryRequest):
    """
    Accepts a user prompt, searches the narrative graph and vector stores,
    and returns a synthesized response.
    """
    if not all([qdrant_client, neo4j_driver, embedding_model]):
        return {"error": "Query service is not properly initialized."}

    print(f"Received query: {request.prompt}")

    # 1. Generate an embedding for the user's prompt
    prompt_vector = embedding_model.encode(request.prompt).tolist()

    # 2. Search Qdrant for relevant audio and visual information
    audio_hits = qdrant_client.search(
        collection_name='audio_transcripts',
        query_vector=prompt_vector,
        limit=3,
        with_payload=True
    )
    
    frame_hits = qdrant_client.search(
        collection_name='frames',
        query_vector=prompt_vector,
        limit=3,
        with_payload=True
    )

    # 3. Use results from Qdrant to find context in Neo4j
    found_context = []
    relevant_frame_indices = {hit.payload['frame_idx'] for hit in frame_hits}

    with neo4j_driver.session(database="neo4j") as session:
        if relevant_frame_indices:
            # Find audio context around the most relevant frames
            result = session.run("""
                MATCH (f:Frame)-[:HAS_AUDIO]->(a:AudioSegment)
                WHERE f.frame_idx IN $frame_indices
                RETURN f.frame_idx AS frame, a.text AS text
                ORDER BY f.frame_idx
                LIMIT 10
            """, frame_indices=list(relevant_frame_indices))
            found_context.extend([record.data() for record in result])

    # 4. Synthesize a final response
    response_parts = ["Based on your query, I found the following information:"]
    if audio_hits:
        response_parts.append("\nRelevant audio moments:")
        for hit in audio_hits:
            response_parts.append(f"- Speaker {hit.payload['speaker']} said: '{hit.payload['text']}' (Score: {hit.score:.2f})")

    if frame_hits:
        response_parts.append("\nRelevant visual moments (by caption):")
        for hit in frame_hits:
            response_parts.append(f"- Frame {hit.payload['frame_idx']}: '{hit.payload['caption']}' (Score: {hit.score:.2f})")
    
    if found_context:
        response_parts.append("\nRelated context from the graph:")
        for item in found_context:
            response_parts.append(f"- At frame {item['frame']}, someone was speaking about: '{item['text']}'")
            
    if len(response_parts) == 1:
        response_parts.append("I could not find any relevant information for your query.")

    return {
        "prompt": request.prompt,
        "response": "\n".join(response_parts)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
