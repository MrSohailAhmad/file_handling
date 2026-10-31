import uuid
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile

app = FastAPI(title="Audio Upload Service")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac"}
MAX_FILE_SIZE = 100 * 1024 * 1024


@app.post("/upload", status_code=201)
async def upload_audio(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, f"Unsupported file type '{ext}'")

    file_id = str(uuid.uuid4())
    path = UPLOAD_DIR / f"{file_id}{ext}"
    size = 0

    try:
        with open(path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(413, "File is larger than 100 MB")
                f.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise

    return {
        "file_id": file_id,
        "filename": file.filename,
        "path": str(path),
        "size_bytes": size,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
