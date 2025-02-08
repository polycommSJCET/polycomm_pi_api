import csv
from flask import Flask, request, jsonify, send_file
from googletrans import Translator
from flask_cors import CORS  
import os
import json
from minutes import generate_minutes
from supabaseupload import save_meeting_data
import ssl
import logging
from meeting_minutes_template import create_document_template_1, create_document_template_2

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

translator = Translator()
def handle_meeting_file(meeting_id, data):
    # Define the file name based on meeting_id
    file_name = f"__temp__/csv/{meeting_id}.csv"

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
        data = request.get_json()
        logging.debug(f"Received data: {data}")

        # Generate meeting minutes
        document = generate_minutes(data.get('m_id'))
        logging.debug(f"Generated document: {document}")

        # Save meeting data to Supabase
        result = save_meeting_data(data)
        logging.debug(f"Supabase result: {result}")

        return jsonify({
            "status": "ok",
            "meeting_data": result
        }), 200

    except Exception as e:
        logging.error(f"Error in end_call: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500



# @app.route('/generate/<meet_id>', methods=['GET'])
# def generate(meet_id):

#     print("meeting_id="+meet_id)
#     document=generate_minutes(meet_id)
#     return document

@app.route('/generate-minutes', methods=['POST'])
def generate():
    data = request.get_json()
    print("Received Data:", data)
    meeting_id = data.get('meetingId')
    template_id = data.get('templateId')

    if not meeting_id or not template_id:
        return jsonify({"error": "Fields 'meetingId' and 'templateId' are required"}), 400

    if template_id == 1:
        print("1");
        create_document_template_1(meeting_id)
        file_path = f'__temp__/docx/{meeting_id}_1.docx'
    elif template_id == 2:
        create_document_template_2(meeting_id)
        file_path = f'__temp__/docx/{meeting_id}_2.docx'
    else:
        return jsonify({"error": "Invalid templateId"}), 400

    return send_file(file_path, as_attachment=True)
    

if __name__ == '__main__':
    # Load SSL certificate and private key
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    
    # Replace these paths with your actual certificate and key files
    cert_path = './certificate.crt'
    key_path = './private.key'

    try:
        if os.path.exists(cert_path) and os.path.exists(key_path):
            ssl_context.load_cert_chain(cert_path, key_path)
            # Run with HTTPS
            app.run(host='0.0.0.0', port=443, ssl_context=ssl_context)
        else:
            raise FileNotFoundError("SSL certificate files not found.")
    except Exception as e:
        print(f"Warning: {str(e)} Running in HTTP mode (not recommended for production)")
        # Fallback to HTTP (development only)
        app.run(host='0.0.0.0', port=5000)