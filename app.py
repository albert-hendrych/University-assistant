import os
import requests
from flask import Flask, request
from agent import procesar_mensaje
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

@app.route('/', methods=['GET'])
def index():
    return "Asistente Universitario Activo y funcionando en la nube 🤖☁️", 200

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """
    Este endpoint recibe los mensajes que los usuarios envían a tu bot en Telegram.
    Telegram hace una petición HTTP POST aquí en cuanto recibe un mensaje.
    """
    update = request.get_json()
    
    # Asegurarnos de que hay un mensaje de texto
    if update and "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        mensaje_usuario = update["message"]["text"]
        
        print(f"Mensaje recibido del chat {chat_id}: {mensaje_usuario}")
        
        # Mostrar el estado "Escribiendo..." en Telegram
        enviar_accion_escribiendo(chat_id)
        
        # 1. Enviar el mensaje al "Cerebro" (Agente de IA) para que lo procese
        respuesta_agente = procesar_mensaje(mensaje_usuario)
        
        # 2. Responder al usuario en Telegram
        enviar_mensaje_telegram(chat_id, respuesta_agente)
            
    return "OK", 200

def enviar_accion_escribiendo(chat_id: int):
    """
    Muestra el estado 'escribiendo...' en Telegram mientras la IA piensa.
    """
    url = f"{TELEGRAM_API_URL}/sendChatAction"
    payload = {
        "chat_id": chat_id,
        "action": "typing"
    }
    try:
        requests.post(url, json=payload, timeout=2)
    except Exception as e:
        print(f"Error enviando acción de escribir: {e}")

def enviar_mensaje_telegram(chat_id: int, texto: str):
    """
    Envía un mensaje de vuelta al usuario a través de la API HTTP de Telegram.
    """
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown" # Permite usar negritas (*texto*) y cursivas (_texto_) en Telegram
    }
    requests.post(url, json=payload)

if __name__ == '__main__':
    # Puerto dinámico para plataformas Cloud como Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
