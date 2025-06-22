from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from openai import OpenAI
from services import *
from flask import send_file

# Create a Flask application instance
app = Flask(__name__)
import re

"""
!!! Important and clarifying information about Python decorators used in this code !!!

Basically, they are indicating that the functions defined under them are going to be executed when, through MyHealthCall application,
a GET/POST/etc message is sent to the concrete route that the decorators specify.

For example:

When this call is made from MyHealthCall:

    const response = await fetch(`${ROBOT_IP}/start-diagnosis`, {
            method: 'POST',
        });

Flask app instance catches it using the following Python decorator:

@app.route('/start-diagnosis', methods=['POST'])

and the function defined under it (start_diagnosis) is executed.
"""

# Route for the main page (GET request)
@app.route('/')
def index():
    # Returns a JSON response with a status of "OK"
    return jsonify(status="OK")

@app.route('/show-medicines', methods=['GET'])
def show_medicines():
    print("Request received at /show-medicines")
    try:
        existing_medicines = get_all_medicines()  
        print(f"Existing medicines: {existing_medicines}")
        return jsonify(message="Showing existing medicines.", medicines=existing_medicines)
    except Exception as e:
        print(f"Error showing medicines: {e}")
        return jsonify(error=f"Failed to show medicines due to: {str(e)}"), 500

@app.route('/diagnosis-output.mp3')
def serve_audio():
    return send_file("diagnosis-output.mp3", mimetype="audio/mpeg")

@app.route('/medicine-details', methods=['POST'])
def medicine_details():
    try:
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify(error="No medicine name provided."), 400
        medicine = get_medicine_by_name(name)
        if not medicine:
            return jsonify(error="Medicine not found."), 404
        return jsonify(medicine)

    except Exception as e:
        print(f"Error in /medicine-details: {e}")
        return jsonify(error="Internal server error."), 500


@app.route('/select-medicine', methods=['POST'])
def select_medicine():
    print("Releasing the selected medicine...")
    try:
        # Substracts selected medicine by the user
        data = request.get_json()
        medicine_id = data.get('medicine_id')

        # Server validation
        if not medicine_id:
            return jsonify(error="Missing 'medicine_id' in request."), 400
        
        # Checks if the medicine selected actually exists
        if (check_existing_medicine(medicine_id)):
            # Releases the medicine
            #release_medicine(medicine_id)
            return jsonify(message=f"Medicine '{medicine_id}' released successfully.")
        else:
            return jsonify(error="Medicine does not exists."), 404
        
    except Exception as e:
        print(f"Error releasing medicine: {e}")
        return jsonify(error=f"Failed to release medicine due to: {str(e)}"), 500

@app.route('/add-medicine', methods=['POST'])
def add_medicine():
    print("Adding a new medicine to MyHealthKit...")

    file = request.files['file']
    filename = file.filename
    _, ext = os.path.splitext(filename)
    save_path = os.path.join(os.getcwd(), f"new_medicine{ext}")
    file.save(save_path)
    print(f"Medicine photo saved at {save_path}")

    try:
        extracted_text = ocr_google_api(save_path)
        print(f"OCR extracted text: {extracted_text}")

        if extracted_text.strip():
            message = [
            {
                "role": "user",
                "content": (
                    f"I scanned a real medicine box and these are the detected words: \"{extracted_text.strip()}\".\n\n"
                    "TASK:\n"
                    "1. Identify the real active ingredient (e.g., 'Paracetamol', 'Amoxicillin') from the provided words.\n"
                    "2. Based on that name, return a structured JSON with:\n"
                    "- name: (exact name of the active drug)\n"
                    "- description: (short drug category or therapeutic use)\n"
                    "- symptoms: (main symptoms or conditions it treats)\n"
                    "- contraindications: (known contraindications or risks)\n"
                    "- url_prospect: (must be from https://www.medicines.org.uk/emc/product/<number>/smpc, or null)\n\n"
                    "IMPORTANT:\n"
                    "- The response must be based ONLY on the name found in the extracted words.\n"
                    "- Ignore brand names (e.g. Numark, Bayer).\n"
                    "- Be medically accurate and concise.\n"
                    "- Return only a valid JSON. No explanation or extra text.\n\n"
                    "EXAMPLE RESPONSE:\n"
                    "{\n"
                    "  \"name\": \"Ibuprofen\",\n"
                    "  \"description\": \"Non-steroidal anti-inflammatory drug\",\n"
                    "  \"symptoms\": \"pain, inflammation, fever\",\n"
                    "  \"contraindications\": \"gastric ulcer, kidney disease\",\n"
                    "  \"url_prospect\": \"https://www.medicines.org.uk/emc/product/5678/smpc\"\n"
                    "}"
                )
            }
        ]

            raw_answer = get_completion(client, message, use_gemini_native=True)

            # SOLUCIÓN: Limpiar el bloque markdown si existe
            def clean_json(raw):
                # Elimina las marcas de código tipo ```json ... ```
                raw = raw.strip()
                if raw.startswith("```json"):
                    raw = raw[len("```json"):].strip()
                if raw.startswith("```"):
                    raw = raw[len("```"):].strip()
                if raw.endswith("```"):
                    raw = raw[:-3].strip()
                return raw

            try:
                clean_answer = clean_json(raw_answer)
                medicine_info = json.loads(clean_answer)

                remaining_units = 10

                add_medicine_to_db(
                    name=medicine_info.get("name", ""),
                    description=medicine_info.get("description", ""),
                    url_prospect=medicine_info.get("url_prospect", ""),
                    symptoms=medicine_info.get("symptoms", ""),
                    contraindications=medicine_info.get("contraindications", "")
                )
                print("Detected medicine info:", medicine_info)
                return jsonify(message=f"Medicine '{medicine_info.get('name', '')}' has been successfully added.")

            except json.JSONDecodeError:
                print("Failed to decode JSON from AI response:", raw_answer)
                return jsonify(error="Could not parse a valid JSON from the AI response."), 500

        else:
            raise ValueError("OCR could not detect text properly.")

    except Exception as e:
        print(f"Error processing medicine image: {e}")
        return jsonify(error=f"Failed to add medicine due to: {str(e)}"), 500

# Route to start a diagnosis (POST request)
@app.route('/start-diagnosis', methods=['POST'])
def start_diagnosis():
    # Prints a message to the console indicating the diagnosis is starting
    print("Starting diagnosis on MyHealthKit...")

    # Obtains message's body from the request
    if 'file' not in request.files:
        return "No file (pacient's audio) part", 400
    file = request.files['file']

    if file.filename == '':
        return "File has no name or is void", 400

    # Saves the audio file to the current working directory with the name "last_request"
    filename = file.filename
    _, ext = os.path.splitext(filename)
    save_path = os.path.join(os.getcwd(), f"last_request{ext}")
    file.save(save_path)
    print("File saved")

    # Transcribes the audio file into text using the transcribe_audio function defined in the services.py file
    transcribed_text = transcribe_audio(file, model=model, language=definedLanguage)

    print(transcribed_text)

    existing_medicines = get_all_medicines()
    message = [
        {
            "role": "system",
            "content": (
                "You are a doctor. When a patient asks for a diagnosis and medicine, follow this format:\n\n"
                "1. **State a possible diagnosis**, starting with: 'The diagnosis could be [diagnosis].'\n"
                "2. **Then mention only the medicines that are available**, grouped naturally in a single sentence like:\n"
                "'[medicine1], [medicine2] and [medicine3] are available.'\n"
                "Do not say 'is available' for each medicine separately.\n"
                "3. Do **not** mention any medicine that is not in this list: " + str(existing_medicines) + "\n"
                "4. Do **not** say anything like 'is not available' or similar. Just ignore the unavailable ones.\n\n"
                "At the end of the message, include **only the list of available medicines**, in the exact format:\n"
                "['medicine1', 'medicine2'] — on a new line and nothing else.\n"
                "If the list is empty, show [].\n\n"
                "Respond in this language: " + definedLanguage + ".\n"
                "Stick to this format strictly and keep the response short and to the point."
            )
        },
        {
            "role": "user",
            "content": transcribed_text
        }
    ]
    # Makes a call to the OpenRouter API to get a response based on the provided message
    # The get_completion function is defined in the services.py file and is responsible for interacting with the OpenRouter API
    answer = get_completion(client, message, use_gemini_native=True)

    try:
        medicines_suggested = extract_medicines_list(answer)
        answer = format_human_readable(answer) # Cleans the text in order to be properly shown to the user
        print("Medicines suggested: ", medicines_suggested)
        speak(answer, definedLanguage)  # Reads (verbally) the diagnosis using the TTS function defined in the services.py file
    except ValueError as e:
        print(f"Error: {e}")
        return jsonify(error="Diagnosis was not succesfully completed.")

    """
    # Remove the existing audios
    if os.path.exists("diagnosis-output.mp3"):
        os.remove("diagnosis-output.mp3")
    if os.path.exists("last_request.m4a"):
        os.remove("last_request.m4a")
    """

    audio_url = f"http://{request.host}/diagnosis-output.mp3"
    return jsonify({
        "success": True,
        "message": answer,
        "medicines": medicines_suggested,
        "audioUri": audio_url
    })

if __name__ == '__main__':

    """
    !!! Important information about SQLite3 database accesses !!!

    As Flask works with multiple threads, and Flask does not support SQLite3 database access from multiple threads,
    it is necessary to create a new connection and cursor inside each function in order to access the SQLite3 database.
    Once the cursor and connection aren no longer neeeded, they MUST be closed.
    """

    definedLanguage = "en-US"

    # Loads Vosk model
    if definedLanguage == "en-US":
        #model = Model("./vosk-models/vosk-model-en-us-0.22") # English
        model = Model("./vosk-models/vosk-model-en-us-0.22-lgraph") # English (light)
    elif definedLanguage == "es-ES":
        model = Model("./vosk-models/vosk-model-es-0.42") # Spanish
    else:
        raise ValueError("Invalid language")

    # Set the API key and base URL for the OpenRouter API
    load_dotenv(dotenv_path="./keys.env")
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    # Enables Cross Origin Resource Sharing (CORS) for the Flask app
    # This allows the app to accept requests from different origins, which is useful for development and API usage
    # In production, it is recommended to restrict CORS to specific origins for security reasons
    #CORS(app)

    # Runs the Flask application. Start the app, making it listen on all network interfaces (0.0.0.0) and port 5000
    app.run(host='0.0.0.0', port=5000) # HTTP
    #app.run(host='0.0.0.0', port=5000, ssl_context=('./certificates/localhost+3.pem', './certificates/localhost+3-key.pem')) # HTTPS
