import sys
from faster_whisper import WhisperModel


def transcribe(path, model_size="base"):
    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, info = model.transcribe(path, beam_size=5)
    print(f"Language: {info.language} ({info.language_probability:.2f})")
    return " ".join(s.text.strip() for s in segments)


if __name__ == "__main__":
    file = sys.argv[1] if len(sys.argv) > 1 else "sample.wav"
    print(transcribe(file))
