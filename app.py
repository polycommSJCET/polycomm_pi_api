import csv
from flask import Flask, request, jsonify
from googletrans import Translator
from flask_cors import CORS  
import os
import json
from minutes import generate_minutes

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
        fieldnames = ['meeting_id', 'speaker', 'text', 'language', 'detected_language', 'translated_text']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header if the file is being created for the first time
        if not file_exists:
            writer.writeheader()

        # Write the data
        writer.writerow(data)


        

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
            "meeting_id": meeting_id,
            "speaker": speaker,
            "text": text,
            "language": src_lang,
            "detected_language": translation.src,
            "translated_text": translation.text
        }

        # Handle file operations
        handle_meeting_file(meeting_id, request_data)

        # Return the response
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


@app.route('/generate', methods=['GET'])
def generate():

    document=generate_minutes()
    return document
    

if __name__ == '__main__':
    app.run(debug=True)