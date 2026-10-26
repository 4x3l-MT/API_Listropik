import os
import shutil
import socket
import tempfile
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
import yt_dlp

app = FastAPI(
    title="YouTube Audio Downloader API",
    description="API asíncrona para conversión y descarga de audio de YouTube a MP3",
    version="2.0.0"
)

# Permite conexiones desde la app móvil en tu red local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]  # Permite que la app lea el nombre original del archivo
)

class DownloadRequest(BaseModel):
    url: HttpUrl

def remove_temp_dir(dir_path: str):
    """Elimina la carpeta temporal después de completar el envío del archivo."""
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path, ignore_errors=True)
        print(f"Directorio temporal limpiado: {dir_path}")

def get_local_ip() -> str:
    """Obtiene la IP local de la laptop en la red Wi-Fi/LAN."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No envía datos realmente; solo le pregunta al sistema qué interfaz usaría
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

@app.get("/ping")
async def ping():
    """Ruta para verificar que la laptop está visible en la red local."""
    return {
        "status": "online",
        "message": "Servidor FastAPI activo en red local"
    }

@app.post("/download")
async def download_audio(payload: DownloadRequest, background_tasks: BackgroundTasks):
    """Descarga el audio de YouTube, lo convierte a MP3 y lo transmite al cliente."""
    url_str = str(payload.url)
    temp_dir = tempfile.mkdtemp(prefix="yt_audio_")

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
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_str, download=True)
            temp_filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(temp_filename)
            final_mp3 = base + ".mp3"

        if not os.path.exists(final_mp3):
            remove_temp_dir(temp_dir)
            raise HTTPException(status_code=500, detail="Error al procesar el archivo MP3.")

        clean_filename = os.path.basename(final_mp3)

        # Se programa la eliminación de la carpeta temporal tras finalizar la descarga
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
    print(f"  Desde tu telefono usa:  http://{ip}:8000")
    print(f"  Probar conexion:        http://{ip}:8000/ping")
    print(f"  Documentacion:          http://{ip}:8000/docs")
    print("=" * 50)

    # Servidor expuesto en el puerto 8000 para red local
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)