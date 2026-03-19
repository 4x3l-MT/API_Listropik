import re
import os
import yt_dlp
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

app = FastAPI()

CARPETA = "Mi_Musica"

class SolicitudDescarga(BaseModel):
    url: str

@app.on_event("startup")
def limpiar_carpeta():
    if os.path.exists(CARPETA):
        for f in os.listdir(CARPETA):
            try:
                os.remove(os.path.join(CARPETA, f))
            except Exception:
                pass

@app.post("/descargar")
def descargar_musica(solicitud: SolicitudDescarga):
    try:
        if not os.path.exists(CARPETA):
            os.makedirs(CARPETA)

        opciones = {
            'format': 'bestaudio/best',
            'outtmpl': f'{CARPETA}/%(title)s.%(ext)s',
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(solicitud.url, download=True)
            titulo = info.get('title', 'desconocido')

        archivo = None
        for f in os.listdir(CARPETA):
            if f.endswith(".mp3") and titulo[:10] in f:
                archivo = os.path.join(CARPETA, f)
                break

        if archivo is None:
            archivos = [os.path.join(CARPETA, f) for f in os.listdir(CARPETA) if f.endswith(".mp3")]
            if archivos:
                archivo = max(archivos, key=os.path.getctime)
            else:
                return {"status": "error", "mensaje": "No se encontró el archivo"}

        nombre_limpio = os.path.basename(archivo)
        nombre_limpio = re.sub(r'\(.*?\)', '', nombre_limpio)
        nombre_limpio = re.sub(r'\[.*?\]', '', nombre_limpio)
        nombre_limpio = re.sub(r'_', ' ', nombre_limpio)
        nombre_limpio = re.sub(r'\s+', ' ', nombre_limpio).strip()
        if not nombre_limpio.endswith('.mp3'):
            nombre_limpio += '.mp3'

        def borrar():
            try:
                if os.path.exists(archivo):
                    os.remove(archivo)
            except Exception:
                pass

        response = FileResponse(
            path=archivo,
            media_type="audio/mpeg",
            background=BackgroundTask(borrar)
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{nombre_limpio}"'
        return response

    except Exception as e:
        return {"status": "error", "mensaje": str(e)}

@app.get("/")
def inicio():
    return {"mensaje": "API de Listropik funcionando"}
