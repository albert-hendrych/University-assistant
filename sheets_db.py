import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def obtener_cliente():
    json_creds = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if json_creds:
        creds_dict = json.loads(json_creds)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPES)
    return gspread.authorize(creds)

def obtener_hoja():
    gc = obtener_cliente()
    url = os.getenv("SPREADSHEET_URL")
    sh = gc.open_by_url(url)
    return sh.sheet1

def leer_excel_como_texto() -> str:
    """Retorna tot l'Excel com un text (CSV) per donar-li de context a Gemini."""
    try:
        hoja = obtener_hoja()
        valores = hoja.get_all_values()
        if not valores:
            return "L'Excel està buit. Les columnes haurien de ser: Asignatura, Tipo, Porcentaje, Nota"
        
        texto = ""
        for i, fila in enumerate(valores):
            # i+1 per tenir el número real de la fila (com a Sheets)
            texto += f"Fila {i+1}: " + " | ".join([str(v) for v in fila]) + "\n"
        return texto
    except Exception as e:
        print(f"Error llegint l'excel: {e}")
        return "Error llegint la base de dades."

def ejecutar_modificaciones(acciones: list):
    """Executa les instruccions que Gemini ens envia en el JSON."""
    if not acciones:
        return
        
    try:
        hoja = obtener_hoja()
        for accion in acciones:
            tipo_acc = accion.get("accion")
            
            if tipo_acc == "NUEVA_FILA":
                asig = accion.get("asignatura", "")
                tipo = accion.get("tipo", "")
                porc = accion.get("porcentaje", "")
                nota = accion.get("nota", "")
                hoja.append_row([asig, tipo, porc, nota])
                
            elif tipo_acc == "ACTUALIZAR_CELDA":
                fila = accion.get("fila")
                # Assumim que modifiquem la columna 4 (Nota), si Gemini no diu el contrari
                columna = accion.get("columna", 4)
                valor = accion.get("valor", "")
                if fila:
                    hoja.update_cell(fila, columna, valor)
                    
    except Exception as e:
        print(f"Error modificant l'excel: {e}")
