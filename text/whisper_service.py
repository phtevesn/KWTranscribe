from faster_whisper import WhisperModel
import os


def load_model(model_size: str, hw: str, ctype: str ):
    model_path = os.path.join("models", "faster-whisper-"+model_size)
    print(model_path)
    model = WhisperModel(model_path, device=hw, compute_type=ctype)
    return model

def transcribe(model: WhisperModel, files):
    files = list(files)
    files.sort()
    
    all_segments: list = []
    for file in files:
        segments, info = model.transcribe(
            file, 
            language = "en", 
            beam_size = 5
        )
        all_segments.extend(segments)
    return all_segments
