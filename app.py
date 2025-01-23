import csv
from flask import Flask, request, jsonify
from googletrans import Translator
from flask_cors import CORS  
import os
import json
from minutes import generate_minutes
from supabaseupload import upload_file
import ssl

app = Flask(__name__)
CORS(app)

translator = Translator()
def handle_meeting_file(meeting_id, data):
    # Define the file name based on meeting_id
    file_name = f"{meeting_id}.csv"

    # Check if file exists
    file_exists = os.path.exists(file_name)

    # Open the file in append mode
    with open(file_name, 'a', newline='', encoding='utf-8') as csvfile:
        # Define CSV writer
        fieldnames = ['speaker', 'translated_text']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header if the file is being created for the first time
        if not file_exists:
            writer.writeheader()

        # Write the data
        writer.writerow(data)


@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Hello, World!"})
        

@app.route('/translate', methods=['POST'])
def translate_text():
    try:
        # Extract request data
        data = request.get_json()
        text = data.get('text')
        src_lang = data.get('language')
        meeting_id = data.get('meeting_id')
        speaker = data.get('speaker')  # New field for the speaker

        # Validate input
        if not text or not src_lang or not meeting_id or not speaker:
            return jsonify({"error": "Fields 'text', 'language', 'meeting_id', and 'speaker' are required"}), 400

        # Translate the text
        translation = translator.translate(text, src='auto', dest='en')

        # Prepare response data
        response_data = {
            "original_text": text,
            "detected_language": translation.src,
            "translated_text": translation.text
        }

        # Add the meeting ID and speaker to the data
        request_data = {
            
            "speaker": speaker,
            "translated_text": translation.text
        }

        # Handle file operations
        handle_meeting_file(meeting_id, request_data)

        # Return the response
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/endcall', methods=['POST'])
def end_call():
    try:
        # Parse the request body
        data = request.get_json()
        meeting_id=data.get('m_id')
        
        document=generate_minutes(meeting_id)

        # Print the request body
        print("Request body:", data)

        # Respond with "ok"
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# @app.route('/generate/<meet_id>', methods=['GET'])
# def generate(meet_id):

#     print("meeting_id="+meet_id)
#     document=generate_minutes(meet_id)
#     return document
    

if __name__ == '__main__':
    #app.run(debug=True)
    # Load SSL certificate and private key
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    
    # Replace these paths with your actual certificate and key files
    #cert_path = os.environ.get('SSL_CERT_PATH', 'path/to/certificate.pem')

    #key_path = os.environ.get('SSL_KEY_PATH', 'path/to/private_key.pem')
    cert_path ='./certificate.crt'
    key_path = './private.key'
    
    if os.path.exists(cert_path) and os.path.exists(key_path):
        ssl_context.load_cert_chain(cert_path, key_path)
        # Run with HTTPS
        app.run(host='0.0.0.0', port=443, ssl_context=ssl_context)
    else:
        print("Warning: SSL certificate files not found. Running in HTTP mode (not recommended for production)")
        # Fallback to HTTP (development only)
        app.run(host='0.0.0.0', port=5000)