import os
from fastapi import FastAPI, Header, HTTPException, Depends, Request
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar las variables secretas del archivo .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 🧠 Configurar el "cerebro" de Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Usamos el modelo rápido y gratuito de Gemini
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

# Crear la aplicación web
app = FastAPI(
    title="Asistente Telegram y Notificador",
    description="Aplicación para recibir notificaciones y conversar con Gemini desde Telegram.",
    version="2.0"
)

class MessageRequest(BaseModel):
    message: str

def verify_api_key(x_api_key: str = Header(...)):
    if not API_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Falta configurar la API_SECRET_KEY en el servidor")
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta. Acceso denegado.")
    return x_api_key

def send_telegram_message(chat_id: str, text: str):
    """Función de ayuda para enviar un mensaje a Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    return requests.post(url, json=payload)


# ---------------------------------------------------------
# RUTA 1: El Notificador (Para ChatGPT, Zapier, etc.)
# ---------------------------------------------------------
@app.post("/send-message", summary="Enviar mensaje a mi Telegram")
def send_message(req: MessageRequest, api_key: str = Depends(verify_api_key)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")
        
    response = send_telegram_message(TELEGRAM_CHAT_ID, req.message)
    if response.status_code == 200:
        return {"status": "success", "detail": "Mensaje enviado a Telegram correctamente"}
    else:
        raise HTTPException(status_code=500, detail=f"Error de Telegram: {response.text}")


# ---------------------------------------------------------
# RUTA 2: ¡NUEVO! El Asistente conversacional de Gemini
# ---------------------------------------------------------
@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Telegram enviará los mensajes que tú escribas en el móvil a esta ruta.
    """
    try:
        data = await request.json()
        
        # Comprobar si hemos recibido un mensaje de texto normal
        if "message" in data and "text" in data["message"]:
            chat_id = str(data["message"]["chat"]["id"])
            user_text = data["message"]["text"]
            
            # ¡SEGURIDAD! Solo respondemos si eres TÚ (comparamos los Chat IDs)
            if chat_id == TELEGRAM_CHAT_ID:
                
                # Le pedimos a Gemini que piense la respuesta
                if model:
                    try:
                        gemini_response = model.generate_content(user_text)
                        respuesta = gemini_response.text
                    except Exception as e:
                        respuesta = f"Uy, ha habido un error con Gemini: {str(e)}"
                else:
                    respuesta = "Error: Falta la llave de Gemini en el servidor."
                
                # Se la enviamos de vuelta a Telegram
                send_telegram_message(chat_id, respuesta)
                
        return {"status": "ok"}
    except Exception as e:
        print(f"Error procesando el webhook: {e}")
        return {"status": "error"}
