import os
import json
import google.generativeai as genai
from sheets_db import guardar_nota, obtener_resumen, calcular_necesario

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Usamos el modelo flash porque es rápido y soporta el modo JSON
model = genai.GenerativeModel('gemini-1.5-flash')

SYSTEM_PROMPT = """
Eres el cerebro de un bot de Telegram universitario. El usuario te mandará mensajes sobre sus notas.
Debes extraer la intención y devolver SIEMPRE un JSON válido con esta estructura:

{
  "accion": "GUARDAR_NOTA" | "CONSULTAR_NOTA" | "CALCULAR_FINAL" | "OTRO",
  "asignatura": "Nombre de la asignatura (vacío si no aplica)",
  "evaluacion": "Nombre del examen o práctica (vacío si no aplica)",
  "nota": 8.5 (número float, si no hay pon 0.0),
  "porcentaje": 20.0 (número float en base 100, ej: 20 para 20%, si no hay pon 0.0),
  "respuesta_conversacional": "Mensaje amable en caso de que la acción sea OTRO"
}

Ejemplos:
User: "He sacado un 7.5 en la práctica 1 de Mates que vale 20%"
JSON: {"accion": "GUARDAR_NOTA", "asignatura": "Mates", "evaluacion": "Práctica 1", "nota": 7.5, "porcentaje": 20.0, "respuesta_conversacional": ""}

User: "Qué notas tengo en Física?"
JSON: {"accion": "CONSULTAR_NOTA", "asignatura": "Física", "evaluacion": "", "nota": 0.0, "porcentaje": 0.0, "respuesta_conversacional": ""}

User: "Cuánto necesito en el final de Programación para aprobar?"
JSON: {"accion": "CALCULAR_FINAL", "asignatura": "Programación", "evaluacion": "", "nota": 0.0, "porcentaje": 0.0, "respuesta_conversacional": ""}

User: "Hola!"
JSON: {"accion": "OTRO", "asignatura": "", "evaluacion": "", "nota": 0.0, "porcentaje": 0.0, "respuesta_conversacional": "¡Hola! Estoy listo para gestionar tus notas. Dime qué necesitas."}
"""

def analizar_con_ia(mensaje: str) -> dict:
    try:
        response = model.generate_content(
            f"{SYSTEM_PROMPT}\n\nMensaje del usuario: {mensaje}",
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error procesando IA: {e}")
        return {"accion": "ERROR"}

def procesar_mensaje(mensaje: str) -> str:
    # 1. Analizar el mensaje con Gemini
    datos = analizar_con_ia(mensaje)
    accion = datos.get("accion")
    asignatura = str(datos.get("asignatura", "")).capitalize()
    
    # 2. Ejecutar la acción
    if accion == "GUARDAR_NOTA":
        evaluacion = datos.get("evaluacion", "Evaluación")
        nota = float(datos.get("nota", 0.0))
        porc = float(datos.get("porcentaje", 0.0))
        
        exito = guardar_nota(asignatura, evaluacion, porc, nota)
        if exito:
            return f"✅ **¡Anotado!**\n📚 {asignatura}\n📝 {evaluacion}: **{nota}** (Vale un {porc}%)"
        else:
            return "❌ Hubo un error al guardar en el Excel. Verifica que el archivo tiene las columnas correctas."
            
    elif accion == "CONSULTAR_NOTA":
        notas = obtener_resumen(asignatura)
        if not notas:
            return f"No he encontrado notas para **{asignatura}** en tu Excel 🕵️‍♂️"
            
        texto = f"📊 **Resumen de {asignatura}**\n\n"
        for n in notas:
            texto += f"🔹 {n.get('Evaluacion', 'Prueba')}: **{n.get('Nota', 0)}** (_{n.get('Porcentaje', 0)}%_)\n"
        return texto
        
    elif accion == "CALCULAR_FINAL":
        calculo = calcular_necesario(asignatura)
        if not calculo:
            return f"Aún no hay notas registradas en **{asignatura}** para hacer el cálculo."
            
        acumulada = round(calculo["acumulada"], 2)
        restante = round(calculo["restante"], 2)
        necesaria = round(calculo["necesaria"], 2)
        
        if calculo["aprobada"]:
            return f"🎉 ¡Ya tienes un **{acumulada}** acumulado en {asignatura}! Estás aprobadísimo/a."
        
        if restante <= 0:
            return f"Ya se ha evaluado el 100% de la asignatura. Tu nota final es un **{acumulada}**."
            
        if necesaria > 10:
            return f"⚠️ Matemáticamente imposible... Necesitarías un **{necesaria}** en el {restante}% que queda para llegar al 5.0. ¡A por la recu! 💪"
            
        return f"📐 **Cálculo para {asignatura}**\n\nLlevas acumulado un **{acumulada}** sobre 10.\nTe queda un **{restante}%** por evaluar.\n\n🎯 Necesitas sacar al menos un **{necesaria}** en lo que queda para aprobar con un 5."
        
    elif accion == "OTRO":
        return datos.get("respuesta_conversacional", "¡Hola! Dime si quieres guardar una nota o consultar cómo vas en una asignatura.")
        
    return "🤖 Mmmm, no he conseguido conectarme bien con la base de datos. Inténtalo de nuevo."
