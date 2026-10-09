import os
import re
import urllib.parse
import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

app = FastAPI()

CARPETA = "Mi_Musica"


class SolicitudDescarga(BaseModel):
    url: str


def limpiar_texto(texto: str) -> str:
    # Quita paréntesis, corchetes y guiones bajos
    texto = re.sub(r'\(.*?\)', '', texto)
    texto = re.sub(r'\[.*?\]', '', texto)
    texto = re.sub(r'_', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto if texto else "audio"


@app.post("/descargar")
def descargar_musica(solicitud: SolicitudDescarga):
    if not os.path.exists(CARPETA):
        os.makedirs(CARPETA)

    # Forzamos un nombre fijo para el archivo temporal de descarga
    # así sabemos exactamente qué archivo leer sin tener que buscarlo en la carpeta
    archivo_temp = os.path.join(CARPETA, "download_temp.mp3")

    opciones = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(CARPETA, "download_temp.%(ext)s"),
        'noplaylist': True,
        'overwrites': True,  # Sobrescribe el archivo temporal anterior si quedó alguno
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(solicitud.url, download=True)
            titulo_original = info.get('title', 'Musica')

        if not os.path.exists(archivo_temp):
            raise HTTPException(status_code=500, detail="No se pudo procesar el audio")

        # Limpiamos el nombre con el que se guardará en tu celular
        nombre_final = f"{limpiar_texto(titulo_original)}.mp3"

        # Borra el archivo del servidor una vez que el teléfono termine de descargarlo
        def borrar():
            try:
                if os.path.exists(archivo_temp):
                    os.remove(archivo_temp)
            except Exception:
                pass

        # Codificación UTF-8 para que la app del celular interprete tildes y caracteres especiales
        nombre_encoded = urllib.parse.quote(nombre_final)

        response = FileResponse(
            path=archivo_temp,
            media_type="audio/mpeg",
            background=BackgroundTask(borrar)
        )
        response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{nombre_encoded}"
        return response

    except Exception as e:
        if os.path.exists(archivo_temp):
            os.remove(archivo_temp)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def inicio():
    return {"mensaje": "Servidor de música personal activo"}
