import requests
import sett
import json
import time
import csv
import os
import shutil
import openai
from datetime import datetime
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import DocArrayInMemorySearch
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from fileinput import filename


def obtener_Mensaje_whatsapp(message):
    media_id = ''
    text = 'Mensaje no reconocido.'
    typeMessage = message.get('type','')

    typeMessage = message['type']
    if typeMessage == 'text':
        text = message['text']['body']
    elif typeMessage == 'document':
        media_id = message[typeMessage]['id']
        text = message[typeMessage].get('filename','')
    else:
        text = 'mensaje no procesado'
    return text, media_id

def enviar_Mensaje_whatsapp(data):
    try:
        whatsapp_token = sett.whatsapp_token
        whatsapp_url = sett.whatsapp_url
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + whatsapp_token}
        print("se envia ", data)
        response = requests.post(whatsapp_url, 
                                 headers=headers, 
                                 data=data)
        
        if response.status_code == 200:
            return 'mensaje enviado', 200
        else:
            return 'error al enviar mensaje', response.status_code
    except Exception as e:
        return e,403
    
def text_Message(number,text):
    data = json.dumps(
            {
                "messaging_product": "whatsapp",    
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "body": text
                }
            }
    )
    return data

#al parecer para mexico, whatsapp agrega 521 como prefijo en lugar de 52,
# este codigo soluciona ese inconveniente.
def replace_start(s):
    if s.startswith("521"):
        return "52" + s[3:]
    else:
        return s


def flujo_chatbot(mensaje_usuario, number, messageId, name, media_id, timestamp):
    # pseudocodigo
    # 1. el usuario envia hola
    # 1.1. le preguntamos que suba un archivo pdf
    list = []
    mensaje = mensaje_usuario.lower()
    if mensaje == 'hola':
        text = 'Hola ' + name + '!, bienvenido a Bigdateros.Por favor sube un documento PDF'
        data = text_Message(number,text)
        list.append(data)

    # 2. si sube un archivo pdf
    # 2.1 procedemos a descargar el archivo localmente
    # 2.2 preguntamos que desea consultar
    elif media_id != '':
        download = administrar_descarga(media_id, number, mensaje)
        data = text_Message(number,download)
        list.append(data)
    # 3. debemos validar si el usuario ya tiene un archivo
    #    previamente en su directorio, solo se admite 1
    elif not valida_archivo_previo(number):
        text = 'No tienes archivo previamente subido, por favor sube un documento PDF'
        data = text_Message(number,text)
        list.append(data)
    # 3.1 en caso que no tenga ningun archivo y escriba
    #     alguna pregunta, preguntarle que suba archivo

    # 4. en este punto el usuario subio su pdf y el bot
    #    esta listo para responder sus preguntas
    else:
        respuesta_bot = preguntar_pdf(messageId, name, mensaje, number, timestamp)
        data = text_Message(number,respuesta_bot)
        list.append(data)

    for item in list:
        enviar_Mensaje_whatsapp(item)



def administrar_descarga(media_id, number, mensaje):
    # 1. obtenemos la metadata del archivo que subio el usuario
    media_info = obtener_media_info(media_id)
    if media_info is None:
        return 'error al obtener metadata'
    
    # 2. conseguimos la url de esa metadata y el tipo doc
    media_url = media_info.get('url')
    mime_type = media_info.get('mime_type')
    # 3. validamos si es un tipo de doc permitido
    if not es_media_type_permitida(mime_type):
        return f'tipo de archivo no permitido {mime_type}'
    # 4. configuramos el directorio donde se guardara el archivo
    ext = sett.media_types[mime_type]
    directory = f'media/{number}/{ext}'
    borrar_media_directorio(directory)

    os.makedirs(directory, exist_ok=True)
    filename = mensaje
    file_path = os.path.join(directory, filename)
    # 5. descargamos el archivo
    if descargar(media_url, file_path):
        # 6. eliminamos conversaciones anteriores de archivos pasados
        r = remove_chat_from_csv(number)
        return '¿Qué desea preguntar sobre el archivo?'
    else:
        return 'error al descargar archivo'
 

def obtener_media_info(media_id):
    url_info = f'https://graph.facebook.com/v17.0/{media_id}?phone_number_id={sett.whatsapp_phone_number_id}'
    headers = {'Authorization': 'Bearer ' + sett.whatsapp_token}

    try:
        response = requests.get(url_info, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f'http error {e} ')
        return None
    except Exception as e:
        print(f'Otros error {e}')
        return None
    
    return response.json()

def es_media_type_permitida(mime_type):
    return mime_type in sett.media_types

def borrar_media_directorio(directory):
    if not os.path.exists(directory):
        #directorio no existe
        return
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Error al borrar {file_path} razon {e}')

def descargar(media_url, file_path):
    headers = {'Authorization': 'Bearer ' + sett.whatsapp_token}
    try:
        response = requests.get(media_url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f'http error {e} ')
        return False
    except Exception as e:
        print(f'Otros error {e}')
        return False
    
    with open(file_path, 'wb') as f:
        f.write(response.content)

    return True

def remove_chat_from_csv(number):
    print('remove_chat_from_csv')
    temp_file = 'temp.csv'
    if not os.path.isfile('conversaciones.csv'):
        print("El archivo 'conversaciones.csv' no existe.")
        return True
    
    try:
        with open('conversaciones.csv', 'r') as infile, open(temp_file, 'w', newline = '') as outfile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames

            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                if row['number'] != number:
                    writer.writerow(row)
    except Exception as e:
        print(f'error al eliminar chat {e}')
        return False
    
    try:
        shutil.move(temp_file, 'conversaciones.csv')
    except Exception as e:
        print(f'error al mover archivo {e}')
        return False
    
    return True

def valida_archivo_previo(number):
    print('valida_archivo_previo')
    directory = f'media/{number}/pdf/'
    return len(os.listdir(directory)) > 0

def preguntar_pdf(messageId, name, mensaje, number, timestamp):
    print('preguntar_pdf')
    # 1. obtenemos el archivo pdf del directorio del user
    directory = f'media/{number}/pdf/'
    qa = load_db(obtener_pdf(directory), chain_type='stuff', k=3)
    
    
    # 2. obtenemos el historial de preeguntas anteriores
    chat_history = get_chat_from_csv(number)

    # 3. enviamos la pregunta al bot
    result = qa({"question": mensaje, 
                 "chat_history": chat_history})
    
    # 4. imprimimos respuestas del bot, langchain y chatgpt
    db_query = result["generated_question"]
    db_response = result["source_documents"]
    answer = result['answer'] 
    print(f'Pregunta user: {mensaje}')
    print(f'Pregunta db: {db_query}')
    print(f'Respuesta: {db_response}')
    print(f'Respuesta del bot: {answer}')
    # 5. guardamos la respuesta del bot en csv
    guardar_conversacion(messageId, number, name, mensaje, timestamp, answer)
    return answer

def obtener_pdf(directory):
    print('obtener_pdf')
    files = os.listdir(directory)
    return os.path.join(directory, files[0])

def load_db(file, chain_type, k):
    print('load_db')
    #1. cargamos el documento PDF
    loader = PyPDFLoader(file)
    documents = loader.load()

    #2. separamos el documentos en documentos más pequeños
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = text_splitter.split_documents(documents)

    #3. definimos el tipo de embedding que usaremos
    embeddings = OpenAIEmbeddings(openai_api_key=sett.openai_api_key)

    #4. creamos la base de datos tipo vector segun esos docs
    db = DocArrayInMemorySearch.from_documents(docs, embeddings)

    #5. definimos el tipo de retriever
    retriever = db.as_retriever(search_type = "similarity", search_kwargs = {"k": k})

    #6. creamos la cadena del chatbot
    qa = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model_name="gpt-3.5-turbo-0301", temperature=0,openai_api_key=sett.openai_api_key), 
        chain_type=chain_type, 
        retriever=retriever, 
        return_source_documents=True,
        return_generated_question=True,
    )
    #7. retornamos la respuesta
    return qa

def get_chat_from_csv(number):
    messages = []
    print('get_chat_from_csv')
    if os.path.exists('conversaciones.csv'):
        with open('conversaciones.csv', 'r') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                if row['number'] == number:
                    user_msg = row['user_msg']
                    bot_msg = row['bot_msg']
                    messages.append((user_msg, bot_msg))

    return messages

def guardar_conversacion(messageId, number, name, user_message, timestamp, answer):
    print('guardar_conversacion')
    try:
        conversacion = [messageId, number, name, user_message,answer, datetime.fromtimestamp(timestamp)]

        with open('conversaciones.csv', 'a+', newline='') as csv_file:
            data = csv.writer(csv_file, delimiter = ',')
            csv_file.seek(0)
            header = csv_file.read(1)
            if not header:
                data.writerow(['messageId', 'number', 'name', 'user_msg', 'bot_msg', 'timestamp'])
            data.writerow(conversacion)
    except Exception as e:
        return e,403

def load_processed_message_ids():
    print('load_processed_message_ids')
    if os.path.exists('mensajes_procesados.csv'):
        with open('mensajes_procesados.csv', 'r') as infile:
            reader = csv.reader(infile)
            return set(id for row in reader for id in row)
    else:
        return set()

def save_processed_message_ids(messageId):
    print('save_processed_message_ids')
    with open('mensajes_procesados.csv', 'a', newline='') as csv_file:
        data = csv.writer(csv_file, delimiter = ',')
        
        data.writerow([messageId])
