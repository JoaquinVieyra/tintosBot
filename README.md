# Bot de comprobantes - Equipo de básquet

Un jugador manda por WhatsApp una foto del comprobante de transferencia, el bot
la lee con Claude, identifica quién es por su teléfono, y registra el pago en
la misma planilla de Google Sheets que ya venís usando (`Control_Pagos_Basquet.xlsx`).

## Cómo funciona (flujo)

1. El jugador manda una imagen por WhatsApp al número del equipo.
2. Meta (WhatsApp Cloud API) le pega a `/webhook` en este servidor.
3. El bot identifica al jugador comparando el teléfono que manda WhatsApp contra
   la columna **Teléfono** de la hoja `Jugadores`.
4. Le pasa la imagen a Claude, que devuelve monto, fecha y si parece un comprobante válido.
5. Si el monto coincide (o si no coincide, lo marca para revisión) agrega una fila en
   la hoja `Pagos`, y el `Balance` se recalcula solo (ya tiene las fórmulas).
6. Le responde al jugador por WhatsApp confirmando que quedó registrado.

## Límite importante que hay que tener claro

Esto lee lo que la **imagen muestra**, no confirma contra el banco real que la plata
se acreditó. No es a prueba de una imagen trucha. Para un equipo amateur y montos
chicos es un riesgo razonable, pero de tanto en tanto conviene que compares el
estado de cuenta real del banco/Personal Pay contra lo que quedó registrado acá,
sobre todo las primeras semanas mientras confirmás que todo funciona bien.

## Qué tenés que hacer vos (paso a paso)

### 1. WhatsApp Cloud API (Meta)
1. Entrá a [developers.facebook.com](https://developers.facebook.com), creá una cuenta de developer.
2. Creá una App nueva → tipo "Business" → agregale el producto **WhatsApp**.
3. Meta te da automáticamente un número de prueba y hasta 5 números destinatarios
   de test **gratis**, sin necesidad de verificar tu empresa — perfecto para probar
   esto con vos y un par de compañeros antes de ir a producción.
4. De ahí sacás: `WHATSAPP_TOKEN` (token temporal, dura 24hs — para producción
   se genera uno permanente) y `WHATSAPP_PHONE_NUMBER_ID`.
5. Cuando tengas el servidor corriendo con una URL pública (ver paso 4), configurás
   el Webhook en el panel de Meta apuntando a `https://tu-url/webhook`, con el mismo
   `WHATSAPP_VERIFY_TOKEN` que pusiste en tu `.env`. Suscribite al campo `messages`.

### 2. Google Sheets
1. Subí `Control_Pagos_Basquet.xlsx` a tu Google Drive y abrilo con Google Sheets
   (Drive lo convierte automáticamente, o usás Archivo → Importar). Los nombres de
   hoja y columnas ya están armados para que el bot los lea tal cual — no hace
   falta tocar nada de la estructura.
2. Andá a [Google Cloud Console](https://console.cloud.google.com), creá un proyecto,
   habilitá la **Google Sheets API**.
3. Creá una **cuenta de servicio** (Service Account), generá una clave JSON,
   y guardala como `service_account.json` en esta carpeta (no la subas a git).
4. Compartí la Google Sheet con el email de esa cuenta de servicio
   (termina en `...iam.gserviceaccount.com`), dándole permiso de **Editor**.
5. Copiá el ID de la planilla (la parte de la URL entre `/d/` y `/edit`) a `GOOGLE_SHEET_ID`.

### 3. Anthropic (Claude)
1. Sacá una API key en [console.anthropic.com](https://console.anthropic.com).
2. Ponela en `ANTHROPIC_API_KEY`.

### 4. Correrlo
Local, para probar:
```bash
pip install -r requirements.txt
cp .env.example .env    # completá los valores reales
python app.py
```
Para que Meta le pueda pegar a tu compu mientras probás, usá [ngrok](https://ngrok.com)
(`ngrok http 8000`) y usá esa URL en el paso 1.5.

Para producción (24/7, sin depender de tu compu prendida), lo más simple es desplegarlo
gratis en [Render](https://render.com) o [Railway](https://railway.app): conectás este
código a un repo de GitHub, configurás las mismas variables de entorno en su panel
(subiendo el contenido del `service_account.json` como variable o archivo secreto), y listo.

### Probar solo la parte de Claude (sin WhatsApp ni Sheets)
```bash
python test_parser.py ruta/a/una/foto_de_comprobante.jpg
```
Esto te muestra qué extrae Claude de una imagen real, para que ajustemos el prompt
en `receipt_parser.py` si hace falta antes de conectar todo.

## Estructura de archivos
- `app.py` — servidor y lógica del webhook.
- `whatsapp_client.py` — enviar/recibir mensajes y descargar imágenes.
- `receipt_parser.py` — lectura del comprobante con Claude (vision).
- `sheets_client.py` — leer/escribir en la Google Sheet.
- `config.py` — todas las variables de entorno en un solo lugar.
- `test_parser.py` — prueba aislada de la lectura de comprobantes.

## Qué falta / próximos pasos posibles
- Probar `test_parser.py` con 2-3 comprobantes reales tuyos para afinar el prompt.
- Sumar un comando de texto tipo "saldo" para que cualquier jugador consulte su estado.
- Sumar los recordatorios automáticos semanales a los que figuran "Pendiente" en el Balance.
