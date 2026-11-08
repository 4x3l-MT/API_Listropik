import os
import re
import shutil
import socket
import tempfile
import urllib.request
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
import yt_dlp

app = FastAPI(
    title="Listropik Audio Downloader API",
    description="API asíncrona e independiente para conversión y descarga de audio (YouTube/Spotify) a MP3",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

class DownloadRequest(BaseModel):
    url: HttpUrl

def remove_temp_dir(dir_path: str):
    """Elimina la carpeta temporal después de completar el envío del archivo."""
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path, ignore_errors=True)
        print(f"Directorio temporal limpiado: {dir_path}")

def get_local_ip() -> str:
    """Obtiene la IP local de la máquina en la red Wi-Fi/LAN."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def resolve_spotify_target(spotify_url: str) -> str:
    """
    Extrae la metadata (Título y Artista) desde el HTML público de Spotify
    sin requerir credenciales ni API Keys de desarrollador, y genera
    un string de búsqueda directa para yt-dlp.
    """
    try:
        req = urllib.request.Request(
            spotify_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')

        title_match = re.search(r'<property="og:title"\s+content="([^"]+)"', html) or \
                      re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
        artist_match = re.search(r'<property="og:description"\s+content="([^"]+)"', html) or \
                       re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', html)

        if not title_match:
            raise ValueError("No se pudo extraer el título de Spotify.")

        track_title = title_match.group(1)
        # Extrae el artista limpiando la descripción común de Spotify ("Song · Artist · Year")
        artist_name = ""
        if artist_match:
            desc = artist_match.group(1)
            parts = desc.split('·')
            if len(parts) > 1:
                artist_name = parts[1].strip()
            else:
                artist_name = desc.strip()

        query = f"{track_title} {artist_name}".strip()
        print(f"[Spotify Resolver] Búsqueda generada: {query}")
        return f"ytsearch1:{query}"

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo resolver el enlace de Spotify: {str(e)}"
        )

@app.get("/ping")
async def ping():
    return {
        "status": "online",
        "message": "Servidor FastAPI activo en red local"
    }

@app.post("/download")
async def download_audio(payload: DownloadRequest, background_tasks: BackgroundTasks):
    """Descarga audio de enlaces de YouTube o Spotify y lo sirve en MP3."""
    raw_url = str(payload.url)
    temp_dir = tempfile.mkdtemp(prefix="listropik_audio_")

    # Identifica si la URL viene de Spotify o YouTube
    if "spotify.com" in raw_url:
        target_input = resolve_spotify_target(raw_url)
    else:
        target_input = raw_url

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_input, download=True)
            
            # En búsquedas ytsearch1:, extract_info devuelve una entrada anidada
            if 'entries' in info:
                info = info['entries'][0]

            temp_filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(temp_filename)
            final_mp3 = base + ".mp3"

        if not os.path.exists(final_mp3):
            remove_temp_dir(temp_dir)
            raise HTTPException(status_code=500, detail="Error al procesar el archivo MP3.")

        clean_filename = os.path.basename(final_mp3)

        background_tasks.add_task(remove_temp_dir, temp_dir)

        return FileResponse(
            path=final_mp3,
            media_type="audio/mpeg",
            filename=clean_filename,
            headers={"Content-Disposition": f'attachment; filename="{clean_filename}"'}
        )

    except Exception as e:
        remove_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Error durante el procesamiento: {str(e)}")

if __name__ == "__main__":
    import uvicorn

    ip = get_local_ip()
    print("=" * 50)
    print(f"  Desde tu teléfono usa:  http://{ip}:8000")
    print(f"  Probar conexión:        http://{ip}:8000/ping")
    print(f"  Documentación:          http://{ip}:8000/docs")
    print("=" * 50)

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)