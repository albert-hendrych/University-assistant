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
1. Llegir l'estat de la base de dades per entendre el context.
2. DEDUCCIÓ DE NOMS: Si l'usuari empra noms escurçats o sigles per a les assignatures (ex: "xarxes"), has de deduir a quina assignatura real de l'Excel es refereix (ex: "Arquitectura de Xarxes"). A l'Excel (modificaciones_excel) fes servir SEMPRE el nom sencer.
3. MÚLTIPLES NOTES: L'usuari et pot passar múltiples notes de cop (ex: "He tret un 7, 9, 8 i 10 a les pràctiques respectivament"). Ets capaç d'identificar quina nota va a cada prova (Pràctica 1, Pràctica 2...) i generar múltiples accions de modificació alhora.
4. SIMULACIONS: Si l'usuari planteja un condicional o simulació ("Si trec un 8...", "quina nota em queda?"), calcula-ho mentalment combinant les dades reals de l'Excel amb les dades hipotètiques de l'usuari.

FORMAT DE SORTIDA OBLIGATORI (ha de ser un JSON vàlid i estrictament parsejable, cap text fora de les claus, escapa bé les cometes):
{
  "modificaciones_excel": [
    {"accion": "NUEVA_FILA", "asignatura": "Arquitectura de Xarxes", "tipo": "Pràctica 1", "porcentaje": 5, "nota": 7},
    {"accion": "ACTUALIZAR_CELDA", "fila": 5, "columna": 4, "valor": 8.5}
  ],
  "respuesta_telegram": "Missatge en català responent a l'usuari. Explica els raonaments matemàtics que has fet i avisa si falten dades."
}

*NOTES IMPORTANTS:*
- `modificaciones_excel` pot estar buit `[]` si l'usuari només fa consultes o simulacions hipotètiques sense voler guardar res.
- Si actualitzes múltiples notes de files que ja existeixen, afegeix múltiples objectes `ACTUALIZAR_CELDA` especificant la "fila" exacta (segons el CSV: Fila X). La 'columna' de la Nota és la 4.
- Fes servir el punt `.` per als decimals al JSON (ex: 8.5, mai 8,5).
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
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg:
            print(f"Error de quota IA: {e}")
            return {"respuesta_telegram": "⚠️ He arribat al límit de missatges per minut de la versió gratuïta de Gemini (5 per minut). Espera uns 60 segons i torna-ho a provar! ⏳"}
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
