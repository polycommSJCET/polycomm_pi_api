from flask import Flask, request, jsonify
from googletrans import Translator
from flask_cors import CORS  


app = Flask(__name__)
CORS(app)

translator = Translator()

@app.route('/translate', methods=['POST'])
def translate_text():
    try:

        data = request.get_json()
        text = data.get('text')
        src_lang = data.get('language')

        if not text or not src_lang:
            return jsonify({"error": "Both 'text' and 'language' fields are required"}), 400

        translation = translator.translate(text, src='auto', dest='en')

        response = {
            "original_text": text,
            "detected_language": translation.src,
            "translated_text": translation.text
        }
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
