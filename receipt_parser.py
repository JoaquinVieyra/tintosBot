# -*- coding: utf-8 -*-
"""
Usa Claude (vision) para leer un comprobante de pago (foto/captura) y
devolver los datos estructurados: monto, fecha, y si el destino coincide
con la cuenta del equipo.

IMPORTANTE - limitación honesta: esto lee lo que la imagen MUESTRA, no
verifica contra el banco real que la plata efectivamente se acreditó.
Alguien podría, en teoría, mandar una imagen editada o de un pago falso.
Para un equipo amateur y montos chicos esto suele ser un riesgo aceptable,
pero conviene que el encargado (vos) revise de tanto en tanto el estado de
cuenta real del equipo contra lo que el bot fue registrando, sobre todo al
principio. No es una verificación bancaria real.
"""
import base64
import json
import re

import anthropic

import config

PROMPT = """Estás viendo un comprobante de pago/transferencia bancaria (foto o captura de pantalla).
Extraé la siguiente información y devolvé SOLO un JSON válido, sin texto adicional, con este formato exacto:

{{
  "monto": <número, sin separadores de miles, punto como decimal, o null si no se lee>,
  "fecha": "<YYYY-MM-DD o null si no se lee>",
  "cuenta_destino_o_alias": "<lo que figure como destinatario/alias/CBU, o null>",
  "es_comprobante_de_pago": <true/false - si la imagen realmente parece un comprobante de transferencia/pago>,
  "confianza": "<alta/media/baja - qué tan claro y legible está el comprobante>",
  "observaciones": "<cualquier cosa rara: imagen borrosa, posible edición, datos incompletos, etc., o null>"
}}

Cuenta/alias esperado del equipo (si lo tenés, usalo para comparar): {cuenta_esperada}
"""


def _extraer_json(texto: str) -> dict:
    """Claude a veces rodea el JSON con texto o backticks; esto lo tolera."""
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if not match:
        raise ValueError(f"No se encontró JSON en la respuesta de Claude: {texto!r}")
    return json.loads(match.group(0))


def parsear_comprobante(imagen_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """
    Envía la imagen a Claude y devuelve un dict con los campos definidos en PROMPT.
    Lanza excepción si Claude no devuelve un JSON parseable.
    """
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    imagen_b64 = base64.standard_b64encode(imagen_bytes).decode("utf-8")

    prompt = PROMPT.format(cuenta_esperada=config.CUENTA_DESTINO_ESPERADA or "no especificada")

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": imagen_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    texto_respuesta = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    return _extraer_json(texto_respuesta)
