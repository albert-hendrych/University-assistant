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
    return "Asistente Universitario Activo 🤖☁️", 200

import threading

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    update = request.get_json()
    
    if update and "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        mensaje_usuario = update["message"]["text"]
        
        print(f"Missatge rebut del xat {chat_id}: {mensaje_usuario}")
        
        # Processem el missatge en un fil en segon pla per retornar el "200 OK" a Telegram immediatament.
        # Si no ho fem així, Telegram es pensa que hem fallat per timeout i reenvia el mateix missatge 3 o 4 vegades,
        # esgotant el límit de la API de Gemini (5 RPM) a l'instant!
        threading.Thread(target=processar_en_fons, args=(chat_id, mensaje_usuario)).start()
            
    return "OK", 200

def processar_en_fons(chat_id, mensaje_usuario):
    # 1. Enviar missatge temporal ("⏳ Pensant...") a Telegram
    message_id = enviar_mensaje_carga(chat_id)
    
    # 2. Enviar el missatge al "Cervell" (Agent IA amb context sencer)
    respuesta_agente = procesar_mensaje(mensaje_usuario)
    
    # 3. Editar el missatge original i posar-hi la resposta definitiva
    if message_id:
        editar_mensaje_telegram(chat_id, message_id, respuesta_agente)
    else:
        # Fallback per si no s'ha pogut crear el primer missatge
        enviar_mensaje_telegram(chat_id, respuesta_agente)

def enviar_mensaje_carga(chat_id: int) -> int:
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "⏳ _Llegint la base de dades i fent càlculs..._",
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload, timeout=5)
        if r.status_code == 200:
            return r.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"Error enviant missatge de càrrega: {e}")
    return None

def editar_mensaje_telegram(chat_id: int, message_id: int, texto: str):
    url = f"{TELEGRAM_API_URL}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": texto,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def enviar_mensaje_telegram(chat_id: int, texto: str):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
