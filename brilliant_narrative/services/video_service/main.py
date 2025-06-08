import json
import os
import uuid
import cv2
import torch
import numpy as np
from pathlib import Path
from PIL import Image
from fastapi import FastAPI
from kafka import KafkaConsumer, KafkaProducer
from qdrant_client import QdrantClient, models

# Assuming boxmot, caption, and embedding models are in the same directory or installed
# This might need adjustment based on the final project structure
from boxmot import DeepOcSort
# from ultralytics import YOLO # Example of a detector you would use
from caption import get_captioning_model
from sentence_transformers import SentenceTransformer

app = FastAPI()

# --- Configuration ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
DEVICE_STR = 'cuda' if torch.cuda.is_available() else 'cpu'
DEVICE = torch.device(DEVICE_STR)

# --- Model & Client Initialization ---
try:
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=6333)
    tracker = DeepOcSort(
        reid_weights=Path('osnet_x1_0_msmt17.pt'),
        device=DEVICE,
        half=False
    )
    caption_model = get_captioning_model(device=DEVICE_STR)
    embedding_model = SentenceTransformer('clip-ViT-B-32', device=DEVICE_STR)
    kafka_producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER,
                                   value_serializer=lambda v: json.dumps(v).encode('utf-8'))
except Exception as e:
    print(f"Error during initialization: {e}")
    # Handle initialization failure gracefully
    # For a real service, you might have retries or exit
    qdrant_client = None
    tracker = None
    # detector = None # Detector would be initialized here
    caption_model = None
    embedding_model = None
    kafka_producer = None


def embed_image(image: np.ndarray) -> np.ndarray:
    pil_img = Image.fromarray(image.astype(np.uint8))
    if pil_img.mode != 'RGB':
        pil_img = pil_img.convert('RGB')
    return embedding_model.encode(pil_img)

def get_caption(image: np.ndarray) -> str:
    pil_img = Image.fromarray(image.astype(np.uint8))
    if pil_img.mode != 'RGB':
        pil_img = pil_img.convert('RGB')
    # The moondream model is called directly for generation
    # It expects a prompt and returns a list of answers.
    answers = caption_model.answer_question(pil_img, "Describe the image.")
    return answers[0] if answers else ""


def process_video_and_populate_qdrant(video_path: str, job_id: str):
    print(f"Processing video for job_id: {job_id} at path: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    frame_idx = 0
    video_results = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # In a real scenario, you'd run a detector like YOLO here
        # The detector output (dets) should be in the format:
        # [[x1, y1, x2, y2, conf], ...]
        # For example:
        # dets = detector(frame) 
        # tracks = tracker.track(frame, dets)
        
        # Since we don't have a detector, we'll simulate tracking on the whole frame
        # In a real implementation, you would loop through `tracks`
        
        # 1. Process and embed the full frame
        frame_embedding = embed_image(frame)
        frame_caption = get_caption(frame)
        frame_vector_id = str(uuid.uuid4())
        
        qdrant_client.upsert(
            collection_name='frames',
            points=[models.PointStruct(
                id=frame_vector_id,
                vector=frame_embedding.tolist(),
                payload={'caption': frame_caption, 'frame_idx': frame_idx, 'job_id': job_id}
            )]
        )
        
        # 2. Process and embed entities (if any were detected)
        # This part is illustrative as we don't have real tracks
        # for track in tracks:
        #   bbox = track.tlbr
        #   entity_crop = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        #   entity_embedding = embed_image(entity_crop)
        #   entity_caption = get_caption(entity_crop)
        #   ... upsert to 'entities' collection ...
        
        video_results.append({
            'frame_idx': frame_idx,
            'frame_vector_id': frame_vector_id,
            # 'entities': [...] # Would be populated from tracks
        })
        
        frame_idx += 1

    cap.release()
    
    # Save results to a temporary file
    output_path = f"/tmp/{job_id}/video_dataset.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(video_results, f)
        
    # Notify fusion service
    kafka_producer.send('results', {
        'job_id': job_id,
        'service': 'video',
        'status': 'success',
        'output_path': output_path
    })
    
    print(f"Finished processing video for job_id: {job_id}")


def consume_processing_jobs():
    if not all([qdrant_client, tracker, caption_model, embedding_model, kafka_producer]):
        print("One or more components failed to initialize. Aborting consumer.")
        return

    consumer = KafkaConsumer(
        'processing_jobs',
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset='earliest',
        group_id='video_processing_group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    print("Video service consumer started and waiting for messages...")
    for message in consumer:
        job_data = message.value
        job_id = job_data.get('job_id')
        video_path = job_data.get('video_path')
        
        if job_id and video_path and os.path.exists(video_path):
            process_video_and_populate_qdrant(video_path, job_id)
        else:
            print(f"Invalid message or file not found: {job_data}")

if __name__ == "__main__":
    # In production, this runs as a long-running service.
    consume_processing_jobs()
