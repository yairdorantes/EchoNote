import yt_dlp

url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # test video

ydl_opts = {
    "format": "bestvideo+bestaudio/best",  # highest quality available
    "outtmpl": "%(title)s.%(ext)s",  # save file as video title
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
