FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*


COPY packages ./packages

RUN pip install --no-index --find-links=./packages openai-whisper torch==2.5.1

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["fastapi", "run", "main.py", "--port", "8000", "--host", "0.0.0.0"]

