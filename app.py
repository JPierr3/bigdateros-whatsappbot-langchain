from flask import Flask, request
import sett 
import services

app = Flask(__name__)

@app.route('/bienvenido', methods=['GET'])
def  bienvenido():
    return 'Hola mundo bigdateros, desde Flask'

@app.route('/webhook', methods=['GET'])
def verificar_token():
    try:
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if token == sett.token and challenge != None:
            return challenge
        else:
            return 'token incorrecto', 403
    except Exception as e:
        return e,403
    
@app.route('/webhook', methods=['POST'])
def recibir_mensajes():
    try:
        body = request.get_json()
        entry = body['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        message = value['messages'][0]
        number = services.replace_start(message['from'])
        messageId = message['id']
        contacts = value['contacts'][0]
        name = contacts['profile']['name']
        timestamp = int(message['timestamp'])
        text, media_id = services.obtener_Mensaje_whatsapp(message)
        # se debe agregar validaciones para que no se 
        # reprocece el mismo mensaje, cuando demore
        # en responder el bot
        processed_message_ids = services.load_processed_message_ids()
        if messageId in processed_message_ids:
            return "mensaje ya procesado"

        services.flujo_chatbot(text, number, messageId, name, media_id, timestamp)
        services.save_processed_message_ids(messageId)

        
        return 'enviado'

    except Exception as e:
        return 'no enviado ' + str(e)

if __name__ == '__main__':
    app.run()
