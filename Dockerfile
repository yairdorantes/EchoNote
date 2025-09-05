FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*


COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["fastapi", "run", "main.py", "--port", "8000", "--host", "0.0.0.0"]
