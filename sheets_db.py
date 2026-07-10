import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def obtener_cliente():
    """Conecta a Google Sheets. Prioriza la variable de entorno por seguridad."""
    json_creds = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if json_creds:
        creds_dict = json.loads(json_creds)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPES)
    return gspread.authorize(creds)

def obtener_notas():
    """
    Se conecta a Google Sheets usando gspread para leer las notas.
    """
    # Lógica futura: 
    # gc = obtener_cliente()
    # sh = gc.open_by_url(os.getenv("SPREADSHEET_URL"))
    # worksheet = sh.sheet1
    # ... buscar la asignatura y devolver los datos
    pass

def calcular_nota_necesaria(asignatura):
    """
    Calcula qué nota necesitas en el examen final en base a las prácticas.
    """
    pass
