import os
import sys
import json
import subprocess
from dataclasses import dataclass, asdict
from faster_whisper import WhisperModel


@dataclass
class Segment:
    id: int
    start: float
    end: float
    text: str


@dataclass
class Result:
    language: str
    duration: float
    segments: list
    full_text: str


class TranscriptionPipeline:
    def __init__(self, model_size="base"):
        self.model = WhisperModel(model_size, device="auto", compute_type="int8")

    def to_wav(self, src, dst="temp.wav"):
        if not os.path.exists(src):
            raise FileNotFoundError(src)
        cmd = ["ffmpeg", "-y", "-i", src, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", dst]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(e.stderr.decode())
        return dst

    def run(self, path):
        wav = self.to_wav(path)
        try:
            segs, info = self.model.transcribe(
                wav,
                beam_size=5,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
            )
            segments = [
                Segment(s.id, round(s.start, 2), round(s.end, 2), s.text.strip())
                for s in segs
            ]
            return Result(
                language=info.language,
                duration=round(info.duration, 2),
                segments=segments,
                full_text=" ".join(s.text for s in segments),
            )
        finally:
            if os.path.exists(wav):
                os.remove(wav)


if __name__ == "__main__":
    file = sys.argv[1] if len(sys.argv) > 1 else "sample.mp3"
    result = TranscriptionPipeline().run(file)
    print(json.dumps(asdict(result), indent=2))
