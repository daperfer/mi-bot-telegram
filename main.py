import os
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

# Cargar las variables secretas del archivo .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")

# Crear la aplicación web
app = FastAPI(
    title="Notificador a Telegram",
    description="Aplicación para enviar mensajes desde ChatGPT a mi Telegram personal.",
    version="1.0"
)

# Definimos cómo debe ser la información que recibimos (solo un campo de texto llamado "message")
class MessageRequest(BaseModel):
    message: str

# Función de seguridad: comprueba que quien envíe el mensaje sepa la contraseña
def verify_api_key(x_api_key: str = Header(...)):
    if not API_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Falta configurar la API_SECRET_KEY en el servidor")
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta. Acceso denegado.")
    return x_api_key

# Esta es la "ruta" o el punto de acceso que usará ChatGPT
@app.post("/send-message", summary="Enviar mensaje a mi Telegram")
def send_message(req: MessageRequest, api_key: str = Depends(verify_api_key)):
    """
    Recibe un texto y lo envía directamente al Telegram configurado.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": req.message
    }
    
    # Enviar la petición a los servidores oficiales de Telegram
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return {"status": "success", "detail": "Mensaje enviado a Telegram correctamente"}
    else:
        raise HTTPException(status_code=500, detail=f"Error de Telegram: {response.text}")
