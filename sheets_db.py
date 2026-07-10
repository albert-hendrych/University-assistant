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

def guardar_nota(asignatura, evaluacion, porcentaje, nota):
    try:
        hoja = obtener_hoja()
        hoja.append_row([asignatura, evaluacion, porcentaje, nota])
        return True
    except Exception as e:
        print(f"Error guardando nota: {e}")
        return False

def obtener_resumen(asignatura):
    try:
        hoja = obtener_hoja()
        registros = hoja.get_all_records()
        notas_asignatura = [r for r in registros if str(r.get("Asignatura", "")).lower() == asignatura.lower()]
        return notas_asignatura
    except Exception as e:
        print(f"Error obteniendo resumen: {e}")
        return []

def calcular_necesario(asignatura):
    # Calcula la nota necesaria para el porcentaje restante asumiendo que se busca un 5.0
    notas = obtener_resumen(asignatura)
    if not notas:
        return None
    
    nota_acumulada = 0.0
    porcentaje_acumulado = 0.0
    
    for n in notas:
        try:
            porc = float(str(n.get("Porcentaje", 0)).replace("%", "").strip())
            nota = float(str(n.get("Nota", 0)).replace(",", ".").strip())
            # Si el porcentaje está en base 100 (ej. 20), lo pasamos a 0.2
            if porc > 1.0:
                porc = porc / 100.0
            
            nota_acumulada += nota * porc
            porcentaje_acumulado += porc
        except Exception:
            pass
            
    porcentaje_restante = 1.0 - porcentaje_acumulado
    
    if porcentaje_restante <= 0:
        return {"acumulada": nota_acumulada, "restante": 0, "necesaria": 0, "aprobada": nota_acumulada >= 5.0}
        
    nota_necesaria = (5.0 - nota_acumulada) / porcentaje_restante
    
    return {
        "acumulada": nota_acumulada,
        "restante": porcentaje_restante * 100,
        "necesaria": nota_necesaria,
        "aprobada": nota_acumulada >= 5.0
    }
