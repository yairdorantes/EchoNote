import shutil
import subprocess
import tempfile
import traceback
import whisper
import yt_dlp
from typing import Union
from fastapi import FastAPI, File, UploadFile
import glob
import os
from pydantic import BaseModel
import requests
import re

# import torch
from dotenv import load_dotenv

load_dotenv()


app = FastAPI()
# device = "cuda" if torch.cuda.is_available() else "cpu"
# print(f"Using device: {device}")
model = whisper.load_model("small")
SERVER_URL = "http://host.docker.internal"
API_KEY = os.environ.get("API_KEY")
MODEL_URL = os.environ.get("MODEL_URL")


class TranscriptionRequest(BaseModel):
    yt_url: str | None = None
    lang: str = "es"


print(API_KEY, "***")


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/summarize")
def summarize(req: TranscriptionRequest):
    try:
        get_audio_info(req.yt_url.strip())
        print(req.yt_url)
        mp3_files = glob.glob("*.mp3")

        if not mp3_files:
            return {"error": "No audio file found"}

        transcription = model.transcribe(
            mp3_files[0],
            language=req.lang,
        )["text"]

        resume_by_gemini = summarize_video(transcription, req.lang)["candidates"][0][
            "content"
        ]["parts"][0]["text"]

        for mp3_file in glob.glob("*.mp3"):
            os.remove(mp3_file)

        # send summarize via whatsapp
        text = format_direct_text(resume_by_gemini)
        # send_whatsapp_message(text)

        return {"summary": text}
    except Exception as e:
        print(f"Error downloading audio: {e}")
        print("Type:", type(e))
        print("Args:", e.args)
        traceback.print_exc()
        return {"error": "Failed to download audio"}

    # Prepare JSON payload for the API


@app.post("/summarize_video_file")
async def summarize_video_file(file: UploadFile = File(...)):
    tmp_dir = tempfile.mkdtemp()
    try:
        # Save uploaded video
        video_path = os.path.join(tmp_dir, file.filename)
        with open(video_path, "wb") as buffer:
            buffer.write(await file.read())

        # Convert to audio
        audio_path = os.path.join(tmp_dir, "audio.mp3")
        subprocess.run(
            ["ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame", audio_path],
            check=True,
        )

        # Ensure audio file exists
        if not os.path.exists(audio_path):
            return {"error": "No audio file found"}

        # Transcribe
        transcription = model.transcribe(audio_path, language="es")["text"]

        # Return transcription
        return {"transcription": transcription}

    finally:
        # Cleanup temp directory
        shutil.rmtree(tmp_dir)


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


def get_audio_info(url: str):
    # extract audio in mp3 from a youtube video url
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


# Transcribe audio file (mp3, wav, m4a, etc.)


def summarize_video(transcription: str, lang: str = "es"):
    prompts = {
        "es": f"""Usando únicamente la transcripción que te proporciono, genera un resumen **muy conciso** del video.  
            - Extensión máxima: 150 palabras.  
            - Divide el resumen en párrafos cortos.  
            - Cada párrafo debe expresar **una idea principal diferente** en una o dos frases.  
            - No repitas ideas, no des ejemplos, no agregues información extra.  
            - Mantén el texto **claro, directo y fácil de leer**.  
            Transcripción: {transcription}""",
        "en": f"""
            Using only the transcription I provide, generate a **very concise** summary of the video.  
            - Maximum length: 150 words.  
            - Divide the summary into short paragraphs.  
            - Each paragraph must express **a different main idea** in one or two sentences.  
            - Do not repeat ideas, do not give examples, do not add extra information.  
            - Keep the text **clear, direct, and easy to read**.  
            Transcription: {transcription}
            """,
    }
    # Prepare JSON payload for the API
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompts.get(lang, prompts["es"]),
                    }
                ]
            }
        ]
    }

    headers = {"Content-Type": "application/json", "X-goog-api-key": API_KEY}

    # Send POST request to Gemini API
    response = requests.post(MODEL_URL, headers=headers, json=payload)

    # Return JSON response from API directly
    return response.json()


def send_whatsapp_message(message: str):
    try:
        url = f"{SERVER_URL}:3000/whatsapp"
        params = {
            "destiny": "7291434687",
            "msg": message,
        }
        response = requests.post(url, json=params)
        return response.json()

    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return {"error": "Failed to send WhatsApp message"}


def clean_text_formatting(text):
    """
    Cleans up markdown-style formatting and improves readability
    """
    # Remove excessive asterisks (markdown bold/italic)
    text = re.sub(r"\*{2,}", "", text)  # Remove ** (bold)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)  # Remove single * (italic)

    # Fix quotes
    text = text.replace('""', '"').replace("''", "'")

    # Add proper line breaks after periods followed by capital letters
    text = re.sub(r"\.(\s*)([A-Z])", r".\n\n\2", text)

    # Add line breaks before key phrases for better structure
    text = re.sub(r"(\s+)(La razón|Como consecuencia|La conversación)", r"\n\n\2", text)

    # Clean up extra whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)  # Max 2 consecutive newlines
    text = re.sub(r"[ \t]+", " ", text)  # Multiple spaces to single space

    return text.strip()


# Your JSON data
json_data = """
{
    "summary": "El video, basado en la transcripción, presenta una discusión sobre un *nuevo y drástico protocolo de uso de los baños en una empresa. El interlocutor principal informa que, a partir de ahora, el baño es **solo para \\"personal autorizado\\", que consiste únicamente en él mismo y el jefe.\\n\\nLa razón de esta medida es que **la empresa ya no puede costear el jabón, el papel y el agua, alegando un \\"abuso\\" por parte de los empleados. Como consecuencia, se les darán instrucciones absurdas: se les \\"exhortará\\" a **venir a la empresa ya habiendo defecado* (\\"cagaditos\\") y a *no comer ni beber durante su hora de comida* para evitar la necesidad de usar el baño.\\n\\nLa conversación es tensa y satírica, culminando con un incidente (o una exclamación dramatizada) donde alguien parece haber tenido un accidente fecal (\\"¡Te cagaste!\\"), que el interlocutor usa para remarcar las supuestas consecuencias de no seguir el \\"protocolo\\"."
}
"""


# Alternative approach for direct text input
def format_direct_text(text):
    """
    Format text directly without JSON parsing
    """
    # Clean up the text
    cleaned = clean_text_formatting(text)

    # print("=" * 60)
    # print("FORMATTED TEXT (Direct):")
    # print("=" * 60)
    # print(cleaned)
    # print("\n" + "=" * 60)

    return cleaned


# Usage examples:
