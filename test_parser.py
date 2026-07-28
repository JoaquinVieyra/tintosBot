# -*- coding: utf-8 -*-
"""
Prueba rápida y aislada: ¿Claude lee bien un comprobante?
No necesita WhatsApp ni Google Sheets, solo tu ANTHROPIC_API_KEY.

Uso:
    python test_parser.py ruta/a/un_comprobante.jpg
"""
import sys
import mimetypes

import receipt_parser


def main():
    if len(sys.argv) != 2:
        print("Uso: python test_parser.py ruta/a/comprobante.jpg")
        sys.exit(1)

    ruta = sys.argv[1]
    media_type = mimetypes.guess_type(ruta)[0] or "image/jpeg"

    with open(ruta, "rb") as f:
        imagen_bytes = f.read()

    resultado = receipt_parser.parsear_comprobante(imagen_bytes, media_type=media_type)
    print("Resultado:")
    for k, v in resultado.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
