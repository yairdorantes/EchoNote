FROM nvidia/cuda:12.9.0-base-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y python3 python3-pip

# Install Python packages
RUN pip3 install --upgrade pip
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu122
RUN pip3 install openai-whisper yt-dlp fastapi uvicorn requests pydantic

# Copy project files
COPY . .

# Install additional requirements if any
RUN pip3 install -r requirements.txt

EXPOSE 8001

CMD ["fastapi","run","main.py","--port","80001","--host","0.0.0.0"]