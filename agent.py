import os
import json
import re
import google.generativeai as genai
from sheets_db import guardar_nota, obtener_resumen, calcular_necesario

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-flash-latest')

SYSTEM_PROMPT = """
Ets el cervell d'un bot de Telegram universitari. L'usuari et parlarà sobre les seves notes. L'idioma principal és el català.
Has d'extreure la intenció i retornar SEMPRE i ÚNICAMENT un JSON vàlid amb aquesta estructura, sense cap text addicional fora de les claus:

{
  "accion": "GUARDAR_NOTA" | "CONSULTAR_NOTA" | "CALCULAR_FINAL" | "OTRO",
  "asignatura": "Nom de l'assignatura (buit si no aplica)",
  "tipo": "Nom de l'examen o pràctica (buit si no aplica)",
  "nota": 8.5 (número float, usa punt per decimals, si no hi ha posa 0.0),
  "porcentaje": 20.0 (número float en base 100, ex: 20 per a 20%, si no hi ha posa 0.0),
  "respuesta_conversacional": "Missatge amable en català en cas que l'acció sigui OTRO"
}

Exemples:
User: "He tret un 10'2 en l'examen final d'aprenentatge automàtic que val un 60%"
JSON: {"accion": "GUARDAR_NOTA", "asignatura": "Aprenentatge automàtic", "tipo": "Examen final", "nota": 10.2, "porcentaje": 60.0, "respuesta_conversacional": ""}

User: "Quines notes tinc a Física?"
JSON: {"accion": "CONSULTAR_NOTA", "asignatura": "Física", "tipo": "", "nota": 0.0, "porcentaje": 0.0, "respuesta_conversacional": ""}

User: "Hola!"
JSON: {"accion": "OTRO", "asignatura": "", "tipo": "", "nota": 0.0, "porcentaje": 0.0, "respuesta_conversacional": "Hola! Estic a punt per gestionar les teves notes. Què necessites?"}
"""

def analizar_con_ia(mensaje: str) -> dict:
    try:
        response = model.generate_content(
            f"{SYSTEM_PROMPT}\n\nMissatge de l'usuari: {mensaje}"
        )
        texto = response.text.strip()
        
        # Expressió regular super robusta per extreure només el JSON i ignorar "Aquí tienes el JSON..."
        match = re.search(r'\{.*\}', texto, re.DOTALL)
        if match:
            texto_json = match.group(0)
        else:
            texto_json = texto
            
        return json.loads(texto_json)
    except Exception as e:
        print(f"Error processant IA: {e}")
        return {"accion": "ERROR"}

def procesar_mensaje(mensaje: str) -> str:
    datos = analizar_con_ia(mensaje)
    accion = datos.get("accion")
    asignatura = str(datos.get("asignatura", "")).capitalize()
    
    if accion == "GUARDAR_NOTA":
        tipo = datos.get("tipo", "Avaluació")
        
        # Robustesa per si Gemini retorna text o comes
        try:
            nota = float(str(datos.get("nota", "0")).replace(",", "."))
            porc = float(str(datos.get("porcentaje", "0")).replace(",", "."))
        except:
            nota = 0.0
            porc = 0.0
            
        exito = guardar_nota(asignatura, tipo, porc, nota)
        if exito:
            return f"✅ **Anotat!**\n📚 {asignatura}\n📝 {tipo}: **{nota}** (Val un {porc}%)"
        else:
            return "❌ Hi ha hagut un error en guardar a l'Excel. Verifica que l'arxiu té les columnes correctes ('Asignatura', 'Tipo', 'Porcentaje', 'Nota') i els permisos adequats."
            
    elif accion == "CONSULTAR_NOTA":
        notas = obtener_resumen(asignatura)
        if not notas:
            return f"No he trobat notes per a **{asignatura}** al teu Excel 🕵️‍♂️"
            
        texto = f"📊 **Resum de {asignatura}**\n\n"
        for n in notas:
            texto += f"🔹 {n.get('Tipo', 'Prova')}: **{n.get('Nota', 0)}** (_{n.get('Porcentaje', 0)}%_)\n"
        return texto
        
    elif accion == "CALCULAR_FINAL":
        calculo = calcular_necesario(asignatura)
        if not calculo:
            return f"Encara no hi ha notes registrades a **{asignatura}** per fer el càlcul."
            
        acumulada = round(calculo["acumulada"], 2)
        restante = round(calculo["restante"], 2)
        necesaria = round(calculo["necesaria"], 2)
        
        if calculo["aprobada"]:
            return f"🎉 Ja tens un **{acumulada}** acumulat a {asignatura}! Estàs aprobadíssim/a."
        
        if restante <= 0:
            return f"Ja s'ha avaluat el 100% de l'assignatura. La teva nota final és un **{acumulada}**."
            
        if necesaria > 10:
            return f"⚠️ Matemàticament impossible... Necessitaries un **{necesaria}** en el {restante}% que queda per arribar al 5.0. A per la recu! 💪"
            
        return f"📐 **Càlcul per a {asignatura}**\n\nDuus acumulat un **{acumulada}** sobre 10.\nEt queda un **{restante}%** per avaluar.\n\n🎯 Necessites treure almenys un **{necesaria}** en el que queda per aprovar amb un 5."
        
    elif accion == "OTRO":
        return datos.get("respuesta_conversacional", "Hola! Digues-me si vols guardar una nota o consultar com vas en una assignatura.")
        
    return "🤖 Mmmm, no he pogut processar el teu missatge. Sembla un error al cervell de Gemini. Torna-ho a provar."
