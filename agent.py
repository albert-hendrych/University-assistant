import os
import google.generativeai as genai
from sheets_db import obtener_notas, calcular_nota_necesaria

# Configurar la API de Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Instrucciones del sistema
SYSTEM_PROMPT = """
Eres el asistente universitario personal de Albert.
Tu objetivo es ayudarle a gestionar sus notas, fechas de exámenes y recordatorios.
Cuando Albert te haga una pregunta, extrae la intención (ej. consultar notas) y responde.
Utiliza formato Markdown amigable para Telegram (usa **negritas** para resaltar cosas clave) 
y añade emojis para que la conversación sea agradable.
"""

def procesar_mensaje(mensaje: str) -> str:
    """
    Función principal del "Cerebro".
    Toma el mensaje en texto plano, interactúa con la BD y genera la respuesta.
    """
    # Lógica de ejemplo:
    if "nota" in mensaje.lower() and "necesito" in mensaje.lower():
        return "He consultado tu *Google Sheets* 📊.\n\nTe falta un **6.5** en el examen final para hacer media y aprobar. ¡Tú puedes, Albert! 📚"
    
    return f"He recibido tu mensaje: _{mensaje}_\n\nAún estoy conectando mis engranajes en la nube ☁️, pero pronto podré procesar todo tu calendario y notas."
