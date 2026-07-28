# -*- coding: utf-8 -*-
"""
Lectura/escritura sobre la planilla en Google Sheets (equivalente en la nube
a Control_Pagos_Basquet.xlsx). Usa una cuenta de servicio de Google Cloud
con la hoja compartida como Editor.

Setup necesario (una sola vez, lo hace Joaquín):
1. Crear un proyecto en Google Cloud Console y habilitar "Google Sheets API".
2. Crear una cuenta de servicio, descargar su JSON de credenciales
   (guardarlo como service_account.json en esta carpeta, NO subir a git).
3. Compartir la Google Sheet con el email de la cuenta de servicio
   (algo como nombre@proyecto.iam.gserviceaccount.com), dándole permiso de Editor.
4. Poner el ID de la planilla (lo que aparece en la URL entre /d/ y /edit) en GOOGLE_SHEET_ID.
"""
import json
from datetime import date

import gspread
from google.oauth2.service_account import Credentials

import config

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_client = None


def _get_credentials():
    """
    En producción (Render) las credenciales vienen pegadas como texto en la
    variable GOOGLE_SERVICE_ACCOUNT_JSON, porque no se pueden subir archivos.
    En local seguimos leyendo el archivo service_account.json.
    """
    if config.GOOGLE_SERVICE_ACCOUNT_JSON:
        info = json.loads(config.GOOGLE_SERVICE_ACCOUNT_JSON)
        return Credentials.from_service_account_info(info, scopes=SCOPES)
    return Credentials.from_service_account_file(config.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES)


def _get_client():
    global _client
    if _client is None:
        _client = gspread.authorize(_get_credentials())
    return _client


def _abrir_planilla():
    return _get_client().open_by_key(config.GOOGLE_SHEET_ID)


def buscar_jugador_por_telefono(telefono_wa_id: str):
    """
    Busca en la hoja 'Jugadores' el nombre correspondiente a un teléfono.
    telefono_wa_id llega de WhatsApp sin '+' y sin espacios (ej: 5493511234567).
    Devuelve el nombre (str) o None si no matchea a nadie.
    Compara solo los últimos 10 dígitos para tolerar formatos distintos
    (con/sin 54, con/sin 9, con/sin espacios) cargados en la planilla.
    """
    hoja = _abrir_planilla().worksheet("Jugadores")
    filas = hoja.get_all_records()  # usa la fila 1 como headers
    ultimos_10 = telefono_wa_id[-10:]

    for fila in filas:
        telefono_planilla = str(fila.get("Teléfono", "")).strip()
        telefono_limpio = "".join(ch for ch in telefono_planilla if ch.isdigit())
        if telefono_limpio and telefono_limpio[-10:] == ultimos_10:
            return fila.get("Nombre")
    return None


def obtener_concepto_y_monto_actual():
    """
    Devuelve (concepto, monto) del último cargo cargado en la hoja 'Cargos'.
    Simplificación: asumimos que el cargo más reciente (última fila con datos)
    es el que corresponde cobrar ahora (ej: la cuota del mes en curso).
    Si tenés varios cargos abiertos a la vez, esto hay que ajustarlo a mano.
    """
    hoja = _abrir_planilla().worksheet("Cargos")
    filas = hoja.get_all_records()
    filas_validas = [f for f in filas if f.get("Concepto")]
    if not filas_validas:
        return None, None
    ultima = filas_validas[-1]
    return ultima.get("Concepto"), ultima.get("Monto")


def registrar_pago(nombre_jugador: str, concepto: str, monto, nota: str = ""):
    """Agrega una fila nueva en la hoja 'Pagos'."""
    hoja = _abrir_planilla().worksheet("Pagos")
    fecha_hoy = date.today().isoformat()
    hoja.append_row(
        [fecha_hoy, nombre_jugador, concepto, monto, "Transferencia (WhatsApp)", nota],
        value_input_option="USER_ENTERED",
    )
