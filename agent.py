import os
import json
import re
import google.generativeai as genai
from sheets_db import leer_excel_como_texto, ejecutar_modificaciones

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-flash-latest')

SYSTEM_PROMPT = """
Ets el cervell d'un bot de Telegram universitari superintel·ligent. El teu idioma és el català.
Rebràs el missatge de l'usuari i l'Estat Actual de la Base de Dades (l'Excel amb les notes).

Les columnes de l'Excel solen ser: Asignatura | Tipo (o Avaluació) | Porcentaje | Nota.

EL TEU OBJECTIU:
1. Llegir l'estat de la base de dades per entendre el context (quina nota té ja, què li falta, etc).
2. Si l'usuari fa una pregunta sobre el seu estat o simulacions (ex: "Què passa si trec un 8 a Mates?"), TU faràs els càlculs matemàtics mentalment observant les dades de l'Excel, i generaràs la resposta explicant si aprova, quant li falta, o si falten notes per calcular (ex: falten pràctiques).
3. Si l'usuari vol crear l'estructura d'una assignatura (ex: "Mates s'avalua 30% parcial, 40% final i 3 pràctiques del 10%"), o si vol afegir/modificar una nota real (ex: "He tret un 8 a la pràctica 1 de Mates"), generaràs accions de modificació per a la base de dades.

FORMAT DE SORTIDA OBLIGATORI (només un JSON, sense cap altre text a fora de les claus):
{
  "modificaciones_excel": [
    {"accion": "NUEVA_FILA", "asignatura": "NomAssignatura", "tipo": "NomProva", "porcentaje": 30, "nota": ""},
    {"accion": "ACTUALIZAR_CELDA", "fila": 5, "columna": 4, "valor": 8.5}
  ],
  "respuesta_telegram": "Missatge en català responent a l'usuari. Inclou aquí tots els teus raonaments, càlculs, i confirmacions de les accions. Utilitza format Telegram (negretes, emojis)."
}

*NOTES IMPORTANTS:*
- `modificaciones_excel` pot estar buit `[]` si l'usuari només fa consultes o simulacions sense guardar res.
- Si actualitzes una nota d'una fila que ja existeix, fes servir `ACTUALIZAR_CELDA`. Fixa't en quin número de fila exacte és (al CSV posa "Fila X:"). La 'columna' de la Nota és la 4.
- Si et falten dades per fer un càlcul (ex: l'usuari et demana la nota final però només ha registrat 3 de 4 pràctiques o li falta l'examen), ho has de deduir llegint el CSV i dir-li amablement a la `respuesta_telegram` què li falta exactament per tenir el càlcul precís.
"""

def analizar_con_ia(mensaje: str, bd_context: str) -> dict:
    try:
        prompt_completo = f"{SYSTEM_PROMPT}\n\n--- ESTAT ACTUAL DE L'EXCEL ---\n{bd_context}\n\n--- MISSATGE DE L'USUARI ---\n{mensaje}"
        
        response = model.generate_content(prompt_completo)
        texto = response.text.strip()
        
        match = re.search(r'\{.*\}', texto, re.DOTALL)
        if match:
            texto_json = match.group(0)
        else:
            texto_json = texto
            
        return json.loads(texto_json)
    except Exception as e:
        print(f"Error processant IA: {e}")
        return None

def procesar_mensaje(mensaje: str) -> str:
    # 1. Llegir l'Excel sencer
    bd_context = leer_excel_como_texto()
    
    # 2. Passar-ho a la IA
    datos_ia = analizar_con_ia(mensaje, bd_context)
    
    if not datos_ia:
        return "🤖 Mmmm, sembla que tinc un bloqueig mental. No he pogut analitzar bé les teves notes ara mateix."
        
    # 3. Aplicar canvis a l'Excel
    modificaciones = datos_ia.get("modificaciones_excel", [])
    if modificaciones:
        ejecutar_modificaciones(modificaciones)
        
    # 4. Retornar resposta a l'usuari
    return datos_ia.get("respuesta_telegram", "Fet! He pres nota del que m'has dit.")
