import sys
import json
from faster_whisper import WhisperModel

model = WhisperModel("base", device="auto", compute_type="int8")
segments, info = model.transcribe(sys.argv[1], beam_size=5, vad_filter=True)

output = {"language": info.language, "segments": []}

for s in segments:
    output["segments"].append({
        "start": round(s.start, 2),
        "end": round(s.end, 2),
        "text": s.text.strip()
    })

print(json.dumps(output, indent=2))
