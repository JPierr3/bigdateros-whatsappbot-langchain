
# Whatsapp Bot con Python

Impulsa tu negocio con un bot usando las apis oficiales de whatsapp.
pueden ver el video paso a paso en el siguiente enlace: https://youtu.be/puYWiZDJnL0

## Descarga el proyecto


```bash
git clone https://github.com/JPierr3/bigdateros-whatsappbot-python.git
```
    
## Funcionalidades

- Enviar mensaje de texto
- Enviar menus como botones o listas
- Enviar stickers
- Marcar los mensajes como "visto" (doble check azul)
- Reaccionar con emojis los mensajes del usuario
- Enviar documentos pdf



## Para probarlo localmente

1. Dirigete al directorio donde descargaste el proyecto

```bash
  cd bigdateros-whatsappbot-python
```
2. Crea un ambiente virtual con la version de python 3.10

```bash
  virtualenv -p 3.10.11 .venv
```
3. Activa el ambiente virtual

```bash
  source .venv/bin/activate
```
4. Instala las dependencias

```bash
  pip install -r requirements.txt
```

5. Corre el aplicativo

```bash
  python app.py
```


## Simular mensajes del usuario con postman

```javascript
Ingresar la URL
http://127.0.0.1:5000/webhook

1. obtener media_id desde whatsapp
   en body, seleccionar "form-data" e ingresar key: messaging_product   y Value: whatsapp
   adicional agregar key: file  y marcarlo como archivo

2. simular mensaje pdf
   en body seleccionar "raw" y marcar tipo JSON
{
  "object": "whatsapp_business_account",
  "entry": [{
      "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
      "changes": [{
          "value": {
              "messaging_product": "whatsapp",
              "metadata": {
                  "display_phone_number": "PHONE_NUMBER",
                  "phone_number_id": "PHONE_NUMBER_ID"
              },
              "contacts": [{
                  "profile": {
                    "name": "NAME"
                  },
                  "wa_id": "WHATSAPP_ID"
                }],
              "messages": [{
                  "from": "ingresa tu numero",
                  "id": "wamid.ID0",
                  "timestamp": "1689257642",
                  "type": "document",
                  "document": {
                    "filename": "HarryPotter_la_piedra_filosofal.pdf",
                    "mime_type": "application/pdf",
                    "sha256": "IMAGE_HASH",
                    "id": " ingresa id del archivo"
                  }
                }]
          },
          "field": "messages"
        }]
    }]
}


3. simular mensaje texto
   en body seleccionar "raw" y marcar tipo JSON
{
  "object": "whatsapp_business_account",
  "entry": [{
      "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
      "changes": [{
          "value": {
              "messaging_product": "whatsapp",
              "metadata": {
                  "display_phone_number": "PHONE_NUMBER",
                  "phone_number_id": "PHONE_NUMBER_ID"
              },
              "contacts": [{
                  "profile": {
                    "name": "NAME"
                  },
                  "wa_id": "PHONE_NUMBER"
                }],
              "messages": [{
                  "from": "ingresa tu numero",
                  "id": "wamid.ID7",
                  "timestamp": "1689257642",
                  "text": {
                    "body": "asd?"
                  },
                  "type": "text"
                }]
          },
          "field": "messages"
        }]
  }]
}
```

