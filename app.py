# -*- coding: utf-8 -*-
"""
Webhook principal: recibe los mensajes de WhatsApp, procesa comprobantes
de pago con Claude, actualiza la Google Sheet, y responde al jugador.

Correr localmente:
    pip install -r requirements.txt
    export $(cat .env | xargs)   # o cargar las variables como prefieras
    python app.py

Para que Meta pueda pegarle a este webhook necesitás una URL pública
(en producción: Render/Railway; para probar en tu compu: ngrok).
"""
import os
from flask import Flask, request, jsonify

import config
import whatsapp_client
import sheets_client
import receipt_parser

app = Flask(__name__)


@app.route("/", methods=["GET"])
def salud():
    """Ruta simple para chequear a ojo que el servicio está vivo."""
    return "Bot de comprobantes activo 🏀", 200


@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    """Meta llama a esto una vez, al configurar el webhook, para confirmar que sos vos."""
    modo = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if modo == "subscribe" and token == config.WHATSAPP_VERIFY_TOKEN:
        return challenge, 200
    return "Token de verificación inválido", 403


@app.route("/webhook", methods=["POST"])
def recibir_mensaje():
    payload = request.get_json(force=True, silent=True) or {}
    mensajes = whatsapp_client.extraer_mensajes_entrantes(payload)

    for msg in mensajes:
        try:
            procesar_mensaje(msg)
        except Exception as exc:  # noqa: BLE001 - no queremos que un error tumbe el webhook
            print("Error procesando mensaje:", exc)
            if msg.get("wa_id"):
                whatsapp_client.enviar_mensaje_texto(
                    msg["wa_id"],
                    "Uy, tuve un problema procesando tu comprobante. "
                    "Probá de nuevo en un rato, o avisale a Joaquín directamente.",
                )

    # Siempre 200, si no Meta reintenta el mismo evento una y otra vez.
    return jsonify({"status": "ok"}), 200


def procesar_mensaje(msg: dict):
    wa_id = msg["wa_id"]

    nombre_jugador = sheets_client.buscar_jugador_por_telefono(wa_id)
    if not nombre_jugador:
        whatsapp_client.enviar_mensaje_texto(
            wa_id,
            "Hola! No encontré tu número en la lista del equipo. "
            "Avisale a Joaquín para que te agregue con este teléfono y volvé a mandar el comprobante.",
        )
        return

    if msg["tipo"] not in ("image", "document"):
        whatsapp_client.enviar_mensaje_texto(
            wa_id,
            f"Hola {nombre_jugador}! Para registrar tu pago mandame una foto o captura del comprobante. 📄",
        )
        return

    imagen_bytes = whatsapp_client.descargar_media(msg["media_id"])
    datos = receipt_parser.parsear_comprobante(imagen_bytes)

    if not datos.get("es_comprobante_de_pago") or datos.get("monto") is None:
        whatsapp_client.enviar_mensaje_texto(
            wa_id,
            f"Hola {nombre_jugador}, no pude leer bien el comprobante "
            f"({datos.get('observaciones') or 'imagen poco clara'}). "
            "¿Podés mandar una foto más clara o la captura completa?",
        )
        return

    concepto, monto_esperado = sheets_client.obtener_concepto_y_monto_actual()
    monto_leido = datos["monto"]

    nota_extra = ""
    if monto_esperado and abs(float(monto_leido) - float(monto_esperado)) > 1:
        nota_extra = f" (ATENCIÓN: se esperaba ${monto_esperado} y se leyó ${monto_leido} - revisar a mano)"

    sheets_client.registrar_pago(
        nombre_jugador,
        concepto or "Sin concepto definido",
        monto_leido,
        nota=f"Confianza lectura: {datos.get('confianza')}.{nota_extra}",
    )

    confirmacion = f"¡Recibido, {nombre_jugador}! Registramos tu pago de ${monto_leido:,.0f}".replace(",", ".")
    if concepto:
        confirmacion += f" correspondiente a {concepto}"
    confirmacion += ". Gracias! 🏀"
    if nota_extra:
        confirmacion += "\n\n(Nota: el monto no coincide exactamente con lo esperado, lo va a revisar el encargado del equipo.)"

    whatsapp_client.enviar_mensaje_texto(wa_id, confirmacion)


if __name__ == "__main__":
    config.validar_config()
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
