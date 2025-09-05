import whisper  # Load model: tiny, base, small, medium, large (larger = more accurate but heavier)

model = whisper.load_model("base")  # Transcribe audio file (mp3, wav, m4a, etc.)
print("Model is on device:", next(model.parameters()).device)

result = model.transcribe("xd.mp3", language="es")
print("Transcription:")
print(result["text"])
