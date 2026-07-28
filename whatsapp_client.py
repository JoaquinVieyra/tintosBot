# -*- coding: utf-8 -*-
"""
Cliente mínimo para la API oficial de WhatsApp Cloud (Meta for Developers).
Documentación: https://developers.facebook.com/docs/whatsapp/cloud-api
"""
import requests

import config

BASE_URL = f"https://graph.facebook.com/{config.WHATSAPP_API_VERSION}"


def _headers():
    return {"Authorization": f"Bearer {config.WHATSAPP_TOKEN}"}


def descargar_media(media_id: str) -> bytes:
    """Descarga el contenido binario de una imagen recibida por WhatsApp."""
    meta_resp = requests.get(f"{BASE_URL}/{media_id}", headers=_headers(), timeout=20)
    meta_resp.raise_for_status()
    media_url = meta_resp.json()["url"]

    file_resp = requests.get(media_url, headers=_headers(), timeout=30)
    file_resp.raise_for_status()
    return file_resp.content


def enviar_mensaje_texto(telefono_destino: str, texto: str) -> None:
    """Envía un mensaje de texto simple a un número (formato wa_id, sin '+')."""
    url = f"{BASE_URL}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": telefono_destino,
        "type": "text",
        "text": {"body": texto},
    }
    resp = requests.post(url, headers=_headers(), json=payload, timeout=20)
    if not resp.ok:
        print("Error enviando mensaje de WhatsApp:", resp.status_code, resp.text)
    resp.raise_for_status()


def extraer_mensajes_entrantes(payload: dict):
    """
    Recorre el body que manda Meta al webhook y devuelve una lista de mensajes
    entrantes simplificados: [{"wa_id": ..., "tipo": ..., "media_id": ..., "texto": ...}]
    Ignora silenciosamente eventos que no son mensajes (ej: confirmaciones de lectura).
    """
    mensajes = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                wa_id = msg.get("from")
                tipo = msg.get("type")
                item = {"wa_id": wa_id, "tipo": tipo, "media_id": None, "texto": None}
                if tipo == "image":
                    item["media_id"] = msg["image"]["id"]
                elif tipo == "document":
                    item["media_id"] = msg["document"]["id"]
                elif tipo == "text":
                    item["texto"] = msg["text"]["body"]
                mensajes.append(item)
    return mensajes
