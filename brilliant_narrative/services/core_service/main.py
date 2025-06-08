import uuid
from fastapi import FastAPI, File, UploadFile
from moviepy import VideoFileClip
import os
import json
from kafka import KafkaProducer

app = FastAPI()

# --- Kafka Configuration ---
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = "processing_jobs"

try:
    kafka_producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("Core service connected to Kafka.")
except Exception as e:
    print(f"Failed to connect to Kafka: {e}")
    kafka_producer = None

@app.post("/upload/")
async def upload_video(file: UploadFile = File(...)):
    """
    Accepts a video file, splits it into video and audio,
    and orchestrates the processing pipeline.
    """
    if not kafka_producer:
        return {"error": "Kafka producer not available."}

    job_id = str(uuid.uuid4())
    temp_dir = f"/tmp/{job_id}"
    os.makedirs(temp_dir, exist_ok=True)

    # Use a generic name for the video file to avoid issues with special characters
    video_path = os.path.join(temp_dir, "source_video.mp4")
    audio_path = os.path.join(temp_dir, "source_audio.mp3")

    # Save the uploaded file temporarily
    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())

    # Split video and audio
    try:
        print(f"Splitting video and audio for job {job_id}...")
        with VideoFileClip(video_path) as video_clip:
            audio_clip = video_clip.audio
            audio_clip.write_audiofile(audio_path, codec='mp3')
        print(f"Successfully split audio and video for job {job_id}.")
    except Exception as e:
        # Basic error handling
        print(f"Error splitting video for job {job_id}: {e}")
        return {"error": f"Failed to process video: {e}"}
    
    # Publish to Kafka
    message = {
        'job_id': job_id,
        'video_path': video_path,
        'audio_path': audio_path
    }
    kafka_producer.send(KAFKA_TOPIC, message)
    kafka_producer.flush() # Ensure message is sent
    print(f"Published job {job_id} to Kafka topic '{KAFKA_TOPIC}'.")
    
    return {
        "job_id": job_id,
        "message": "Video and audio split successfully. Processing job started."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
