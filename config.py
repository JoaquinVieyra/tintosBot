# -*- coding: utf-8 -*-
"""
Configuración central: todo se lee de variables de entorno.
Copiá .env.example a .env y completá tus credenciales reales.
Nunca subas el .env a un repositorio público.
"""
import os

# --- WhatsApp Cloud API (Meta for Developers) ---
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "cambiar-esto")
WHATSAPP_API_VERSION = os.environ.get("WHATSAPP_API_VERSION", "v20.0")

# --- Google Sheets ---
# En local usamos el archivo service_account.json.
# En Render (o cualquier hosting) no podés subir archivos, así que pegás el
# contenido completo del JSON en la variable GOOGLE_SERVICE_ACCOUNT_JSON y
# el código lo usa desde ahí. Si están las dos, gana la variable.
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")

# --- Anthropic (Claude) ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5")

# --- Reglas del equipo ---
# Nombre de la cuenta/alias/CBU del equipo, para que el prompt de Claude
# pueda avisar si el comprobante fue destinado a otra cuenta.
CUENTA_DESTINO_ESPERADA = os.environ.get("CUENTA_DESTINO_ESPERADA", "")


def validar_config():
    faltantes = []
    for nombre in ["WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "GOOGLE_SHEET_ID", "ANTHROPIC_API_KEY"]:
        if not globals().get(nombre):
            faltantes.append(nombre)
    if faltantes:
        print("ATENCION: faltan variables de entorno:", ", ".join(faltantes))
    return not faltantes
