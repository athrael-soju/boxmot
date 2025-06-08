import json
import os
import uuid
from fastapi import FastAPI
from kafka import KafkaConsumer, KafkaProducer
from qdrant_client import QdrantClient, models
from pyannote.audio import Pipeline
import speech_recognition as sr
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import torch

app = FastAPI()


load_dotenv()
# --- Configuration ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# --- Model & Client Initialization ---
try:
    hf_token = os.getenv("HF_TOKEN")
    print(f"Attempting to use Hugging Face token: {'Token found' if hf_token else 'Token not found'}")
    if not hf_token:
        raise ValueError("HF_TOKEN environment variable not set. Please provide a Hugging Face token.")

    qdrant_client = QdrantClient(host=QDRANT_HOST, port=6333)
    diarization_pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization",
        use_auth_token=hf_token
    )
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=DEVICE)
    recognizer = sr.Recognizer()
    kafka_producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER,
                                   value_serializer=lambda v: json.dumps(v).encode('utf-8'))
except Exception as e:
    print(f"Error during initialization: {e}")
    qdrant_client = None
    diarization_pipeline = None
    embedding_model = None
    recognizer = None
    kafka_producer = None

def embed_text(text: str):
    return embedding_model.encode(text)

def process_audio_and_populate_qdrant(audio_path: str, job_id: str):
    print(f"Processing audio for job_id: {job_id} at path: {audio_path}")
    
    try:
        diarization = diarization_pipeline(audio_path)
        audio_results = []

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segment_start = turn.start
            segment_end = turn.end
            
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source, offset=segment_start, duration=turn.duration)
                try:
                    transcript_text = recognizer.recognize_google(audio_data)
                except sr.UnknownValueError:
                    transcript_text = ""
            
            if transcript_text:
                embedding = embed_text(transcript_text)
                segment_id = str(uuid.uuid4())
                
                qdrant_client.upsert(
                    collection_name='audio_transcripts',
                    points=[models.PointStruct(
                        id=segment_id,
                        vector=embedding.tolist(),
                        payload={
                            'job_id': job_id,
                            'speaker': speaker,
                            'start': segment_start,
                            'end': segment_end,
                            'text': transcript_text
                        }
                    )]
                )
                
                audio_results.append({
                    'segment_id': segment_id,
                    'speaker': speaker,
                    'start': segment_start,
                    'end': segment_end,
                    'text': transcript_text
                })

    except Exception as e:
        print(f"Error during audio processing for job {job_id}: {e}")
        # Optionally send a failure message to Kafka
        return

    # Save results to a temporary file
    output_path = f"/tmp/{job_id}/audio_dataset.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(audio_results, f)
        
    # Notify fusion service
    kafka_producer.send('results', {
        'job_id': job_id,
        'service': 'audio',
        'status': 'success',
        'output_path': output_path
    })
    
    print(f"Finished processing audio for job_id: {job_id}")

def consume_processing_jobs():
    if not all([qdrant_client, diarization_pipeline, embedding_model, recognizer, kafka_producer]):
        print("One or more components failed to initialize. Aborting consumer.")
        return

    consumer = KafkaConsumer(
        'processing_jobs',
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset='earliest',
        group_id='audio_processing_group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    print("Audio service consumer started and waiting for messages...")
    for message in consumer:
        job_data = message.value
        job_id = job_data.get('job_id')
        audio_path = job_data.get('audio_path')
        
        if job_id and audio_path and os.path.exists(audio_path):
            process_audio_and_populate_qdrant(audio_path, job_id)
        else:
            print(f"Invalid message or file not found: {job_data}")

if __name__ == "__main__":
    consume_processing_jobs()
