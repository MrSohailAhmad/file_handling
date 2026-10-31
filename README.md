# Audio Transcription Pipeline
 
A simple pipeline that takes an audio file, transcribes it to text, and returns the result with timestamps for each segment.
 
## Tech Stack
 
- Python
- Faster-Whisper for speech-to-text
- FFmpeg for audio conversion
- FastAPI for the upload service
## Setup
 
Requires Python 3.9+ and FFmpeg (`brew install ffmpeg`, `sudo apt install ffmpeg`, or `winget install ffmpeg`).

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

The first run downloads the Whisper model, so it may take a minute.
 
## Usage
 
Transcribe a file (plain text):
 
```bash
python transcribe.py audio.mp3
```
 
Get transcription with timestamps (JSON):
 
```bash
python timestamps.py audio.mp3
```

Run the full pipeline (FFmpeg conversion + VAD + structured JSON with language, duration, segments and full text):

```bash
python pipeline.py audio.mp3
```
 
Start the upload service (interactive docs at http://localhost:8000/docs):
 
```bash
python server.py
curl -X POST "http://localhost:8000/upload" -F "file=@audio.mp3"
```

The upload endpoint stores the file in `uploads/` and returns its `file_id`, `path` and size. It does not transcribe it; pass the saved path to the scripts above.
 
## Sample Output
 
```json
{
  "language": "en",
  "segments": [
    { "start": 0.0, "end": 3.12, "text": "Welcome to the system demo." },
    { "start": 3.45, "end": 7.8, "text": "Today we are discussing speech to text pipelines." }
  ]
}
```
 
## Design Decisions
 
**Why Faster-Whisper?**
It's an optimized version of OpenAI's Whisper. It runs much faster, uses less memory with int8 quantization, works on CPU, and gives segment timestamps out of the box. No need to train anything.
 
**Handling different audio formats**
`pipeline.py` converts every file with FFmpeg to 16kHz mono WAV before transcription, since that's what Whisper expects. So MP3, WAV, M4A, OGG and even video files all end up in one format. (`transcribe.py` and `timestamps.py` pass the file straight to Faster-Whisper, which decodes it itself.) The upload service accepts only audio extensions (.wav, .mp3, .m4a, .ogg, .flac, .aac) and enforces a 100 MB size limit.
 
**Handling long audio files**
Faster-Whisper processes audio in 30-second windows through a generator, so memory stays low. VAD is enabled to skip silences, which speeds things up and stops the model from making up text in quiet parts. For very long files, the audio can be split into chunks at silence points, transcribed in parallel, and merged by shifting each chunk's timestamps by its start time.
 
**Upload service**
Files are streamed to disk in 1 MB chunks so large uploads don't spike memory. Each file gets a UUID name to avoid collisions and path traversal issues. Partial files are deleted if the upload fails.
 
## System Design (Production)
 
**Concurrent uploads**
The API only saves the file and returns a job ID. Transcription runs in background workers through a queue (Celery + Redis or AWS SQS), so the API stays fast and workers can scale with load.
 
**Storage**
Audio goes to S3. Transcripts and job info (status, language, segments) go to PostgreSQL, with segments stored as JSONB.
 
**Retries and recovery**
Each job has a status: pending, processing, done or failed. Failed jobs are retried automatically with a delay. After max retries, the job is marked failed with the error saved. Since the original audio stays in S3, any job can be rerun.
 
**API**
- `POST /transcriptions` upload audio, get a job ID
- `GET /transcriptions/{id}` get status and transcript
- Optional webhook to notify the client when the job is done
## Future Improvements
 
- Speaker diarization (who said what)
- Export to SRT/VTT subtitles
- GPU workers for faster processing
- Auth and rate limiting on the API
 