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
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.DEBUG)

ANALYTICS_FOLDER = "__temp__/analytics"
os.makedirs(ANALYTICS_FOLDER, exist_ok=True)

CAMERA_ANALYTICS_FOLDER = "__temp__/camera_analytics"
os.makedirs(CAMERA_ANALYTICS_FOLDER, exist_ok=True)

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
        # document = generate_minutes(data.get('m_id'))
        # logging.debug(f"Generated document: {document}")

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
    
    
    
@app.route('/call-ended', methods=['POST'])
def end_call1():
    try:
       print("call ended yes from meeting")

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
    data = request.form
    logging.debug(f"Received Data: {data}")
    meeting_id = data.get('meetingId')
    template_id = data.get('templateId')
    organization_name = data.get('organizationName')
    title = data.get('title')
    meeting_type = data.get('meetingType')
    logo = request.files.get('logo')

    if not meeting_id or not template_id or not organization_name or not title or not meeting_type:
        logging.error("Missing required fields")
        return jsonify({"error": "Fields 'meetingId', 'templateId', 'organizationName', 'title', and 'meetingType' are required"}), 400

    logo_path = None
    if logo:
        logo_filename = secure_filename(logo.filename)
        logo_dir = '__temp__/logos'
        if not os.path.exists(logo_dir):
            os.makedirs(logo_dir)
        logo_path = os.path.join(logo_dir, logo_filename)
        logo.save(logo_path)

    try:
        if template_id == '1':
            create_document_template_1(meeting_id, organization_name, title, meeting_type, logo_path)
            file_path = f'__temp__/docx/{meeting_id}_1.docx'
        elif template_id == '2':
            create_document_template_2(meeting_id, organization_name, title, meeting_type, logo_path)
            file_path = f'__temp__/docx/{meeting_id}_2.docx'
        else:
            logging.error("Invalid templateId")
            return jsonify({"error": "Invalid templateId"}), 400

        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logging.error(f"Error generating document: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/mic-usage', methods=['POST'])
def log_mic_usage():
    try:
        # Create analytics folder if it doesn't exist
        os.makedirs(ANALYTICS_FOLDER, exist_ok=True)
        
        # Extract and validate request data
        data = request.get_json()
        
        # Log received data for debugging
        print(f"Received data: {data}")
        
        # Validate required fields
        required_fields = ["username", "mic_start_time", "mic_end_time", "meeting_id"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Extract validated data
        username = data["username"]
        mic_start_time = data["mic_start_time"]
        mic_end_time = data["mic_end_time"]
        meeting_id = data["meeting_id"]
        
        # Define CSV file path
        csv_filename = os.path.join(ANALYTICS_FOLDER, f"{meeting_id}.csv")
        print(f"Writing to: {csv_filename}")
        
        # Check file existence before opening
        file_exists = os.path.isfile(csv_filename)
        
        try:
            with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                
                # Write header for new files
                if not file_exists:
                    writer.writerow(["Username", "Mic Start Time", "Mic End Time"])
                
                # Write data row
                
                writer.writerow([username, mic_start_time, mic_end_time])
                
                # Flush the file to ensure writing
                file.flush()
                os.fsync(file.fileno())
                
        except IOError as e:
            print(f"Error writing to file: {e}")
            return jsonify({"error": f"Failed to write to CSV: {str(e)}"}), 500
        
        return jsonify({"message": "Mic usage logged successfully"}), 200
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/camera-usage', methods=['POST'])
def log_camera_usage():
    try:
        # Create analytics folder if it doesn't exist
        os.makedirs(CAMERA_ANALYTICS_FOLDER, exist_ok=True)
        
        # Extract and validate request data
        data = request.get_json()
        
        # Log received data for debugging
        print(f"Received data: {data}")
        
        # Validate required fields
        required_fields = ["username", "camera_start_time", "camera_end_time", "meeting_id"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Extract validated data
        username = data["username"]
        camera_start_time = data["camera_start_time"]
        camera_end_time = data["camera_end_time"]
        meeting_id = data["meeting_id"]
        
        # Define CSV file path
        csv_filename = os.path.join(CAMERA_ANALYTICS_FOLDER, f"{meeting_id}.csv")
        print(f"Writing to: {csv_filename}")
        
        # Check file existence before opening
        file_exists = os.path.isfile(csv_filename)
        
        try:
            with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                
                # Write header for new files
                if not file_exists:
                    writer.writerow(["Username", "Camera Start Time", "Camera End Time"])
                
                # Write data row
                
                writer.writerow([username, camera_start_time, camera_end_time])
                
                # Flush the file to ensure writing
                file.flush()
                os.fsync(file.fileno())
                
        except IOError as e:
            print(f"Error writing to file: {e}")
            return jsonify({"error": f"Failed to write to CSV: {str(e)}"}), 500
        
        return jsonify({"message": "Mic usage logged successfully"}), 200
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": str(e)}), 500

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