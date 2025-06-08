import json
import os
import time
from collections import defaultdict
from kafka import KafkaConsumer
from neo4j import GraphDatabase

# --- Configuration ---
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
RESULTS_TOPIC = "results"
JOB_STATUS_GROUP = "fusion_service_group"

# In-memory store for job results. In a production system,
# you might use Redis or another persistent store for this.
job_results_store = defaultdict(dict)

def get_neo4j_driver():
    """Establishes connection to Neo4j and returns a driver instance."""
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("Successfully connected to Neo4j.")
        return driver
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        return None

def fuse_and_populate_graph(driver, job_id: str, video_data_path: str, audio_data_path: str):
    """
    Fuses video and audio datasets and populates the Neo4j graph.
    """
    print(f"Starting data fusion for job_id: {job_id}")

    try:
        with open(video_data_path, 'r') as f:
            video_data = json.load(f)
        with open(audio_data_path, 'r') as f:
            audio_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data for job {job_id}: {e}")
        return

    # --- Fusion Logic ---
    # Create a lookup for audio segments for efficient access
    for frame in video_data:
        frame_timestamp = frame.get('timestamp', frame.get('frame_idx', 0)) # Fallback to frame_idx if no timestamp
        overlapping_segments = []
        for segment in audio_data:
            if segment['start'] <= frame_timestamp <= segment['end']:
                overlapping_segments.append(segment['segment_id'])
        frame['overlapping_audio_segment_ids'] = overlapping_segments

    print(f"Fusion complete for job_id: {job_id}. Populating graph...")

    # --- Graph Population Logic ---
    with driver.session(database="neo4j") as session:
        # Clear any previous data for this job_id to ensure idempotency
        session.run("MATCH (n {job_id: $job_id}) DETACH DELETE n", job_id=job_id)

        # Create Frame and AudioSegment nodes
        session.execute_write(
            lambda tx: tx.run("""
            UNWIND $video_data AS frame
            CREATE (f:Frame {job_id: $job_id})
            SET f += apoc.map.clean(frame, ["entities", "relationships"], [])

            WITH f, frame.entities AS entities
            UNWIND entities AS entity_data
            MERGE (e:Entity {id: entity_data.id, job_id: $job_id})
            ON CREATE SET e += entity_data
            MERGE (e)-[:APPEARS_IN]->(f)
            """, video_data=video_data, job_id=job_id)
        )
        session.execute_write(
            lambda tx: tx.run("""
            UNWIND $audio_data AS segment
            CREATE (a:AudioSegment {job_id: $job_id})
            SET a += segment
            """, audio_data=audio_data, job_id=job_id)
        )
        
        # Create relationships
        session.execute_write(
            lambda tx: tx.run("""
            UNWIND $video_data AS frame
            MATCH (f:Frame {vector_id: frame.vector_id, job_id: $job_id})
            UNWIND frame.overlapping_audio_segment_ids AS seg_id
            MATCH (a:AudioSegment {segment_id: seg_id, job_id: $job_id})
            MERGE (f)-[:HAS_AUDIO]->(a)
            """, video_data=video_data, job_id=job_id)
        )
        
        # Link frames sequentially
        session.execute_write(
            lambda tx: tx.run("""
            MATCH (f:Frame {job_id: $job_id})
            WITH f ORDER BY f.frame_idx
            WITH collect(f) as frames
            UNWIND range(0, size(frames)-2) as i
            WITH frames[i] as f1, frames[i+1] as f2
            MERGE (f1)-[:NEXT]->(f2)
            """, job_id=job_id)
        )

    print(f"Finished populating graph for job_id: {job_id}")

def consume_results(driver):
    """
    Consumes messages from the 'results' topic, aggregates them by job_id,
    and triggers the fusion process when all data is available.
    """
    print("Fusion service consumer started...")
    consumer = KafkaConsumer(
        RESULTS_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset='earliest',
        group_id=JOB_STATUS_GROUP,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    for message in consumer:
        try:
            result_data = message.value
            job_id = result_data.get('job_id')
            service_name = result_data.get('service')
            output_path = result_data.get('output_path')
            
            if not all([job_id, service_name, output_path]):
                print(f"Malformed message received: {result_data}")
                continue

            print(f"Received result from '{service_name}' for job_id: {job_id}")
            
            job_results_store[job_id][service_name] = output_path
            
            if 'video' in job_results_store[job_id] and 'audio' in job_results_store[job_id]:
                print(f"All results received for job_id: {job_id}. Starting fusion.")
                video_path = job_results_store[job_id]['video']
                audio_path = job_results_store[job_id]['audio']
                
                fuse_and_populate_graph(driver, job_id, video_path, audio_path)
                
                del job_results_store[job_id]

        except json.JSONDecodeError:
            print(f"Error decoding message: {message.value}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    neo4j_driver = None
    while not neo4j_driver:
        neo4j_driver = get_neo4j_driver()
        if not neo4j_driver:
            print("Retrying Neo4j connection in 5 seconds...")
            time.sleep(5)
    
    consume_results(neo4j_driver)
    
    # Clean up driver connection
    if neo4j_driver:
        neo4j_driver.close()
