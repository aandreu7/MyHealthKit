from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from openai import OpenAI
import sqlite3
from services import *

# Create a Flask application instance
app = Flask(__name__)

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
        # Llamar a OCR.Space para hacer el OCR
        resize_image_if_needed(save_path)
        extracted_text = ocr_space_file(save_path, "K85306455988957")
        print(f"OCR extracted text: {extracted_text}")

        if extracted_text.strip():
            # Crear el mensaje para get_completion
            message = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"I scanned a real medicine box and these are the detected words: \"{extracted_text.strip()}\".\n"
                                "IMPORTANT: Ignore any brand names you detect (like Numark, Boots, Bayer, etc.). "
                                "Focus ONLY on the name of the active drug or medicine (such as Ibuprofen, Amoxicillin, Paracetamol, etc.). "
                                "The product name must correspond to the drug itself, NOT the manufacturer or pharmacy brand. "
                                "Return ONLY the real name of the medicine, without dosage, format or extra information."
                            )
                        }
                    ]
                }
            ]

            # Llamada a get_completion
            answer = get_completion(client, message).choices[0].message.content.strip()
            print("Detected medicine name:", answer)

            return jsonify(message=f"Medicine '{answer}' has been successfully added.")

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

    # Create a new connection and cursor inside the function
    conn = sqlite3.connect("../database/pharmacy.db")
    cursor = conn.cursor()

    sql_statement = "SELECT m.name FROM MEDICINES m WHERE m.remaining_units>0"
    existing_medicines = [medicine[0] for medicine in cursor.execute(sql_statement).fetchall()]

    # Close the cursor and connection once the query is done
    cursor.close()
    conn.close()

    message = [
            {
            "role": "system",
            "content": "You are a doctor. When a patient asks for a diagnosis and medicine, you must follow this format exactly:\n"
                        "1. **State a possible diagnosis** clearly, starting with 'The diagnosis could be [diagnosis]'.\n"
                        "2. Then, **provide one or more medicines** that you think could be helpful. For each medicine:\n"
                        "    - If the medicine is in the following list: " + str(existing_medicines) + ", say it is **available**.\n"
                        "    - If the medicine is **not** in the list, say it is **not available currently**.\n"
                        "The list of available medicines is: " + str(existing_medicines) + ".\n"
                        "Only provide the diagnosis and the medicines. No additional information or suggestions are allowed.\n"
                        "Be sure to follow this format precisely. Do not deviate from it in any way.\n"
                        "Finally, at the end of the message, provide **ONLY** the list of medicines that are available from the provided list, in the following format:\n"
                        "['medicine1', 'medicine2', 'medicine3', ...]\n"
                        "This **list** must appear **only at the very end** of your response. If list is void, provide [] at **at the very end**.\n"
                        "Respond in the following language: " + definedLanguage
            },
            { "role": "user", "content": transcribed_text }
    ]

    # Makes a call to the OpenRouter API to get a response based on the provided message
    # The get_completion function is defined in the services.py file and is responsible for interacting with the OpenRouter API
    answer = get_completion(client, message).choices[0].message.content

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

    return jsonify(message="Diagnosis completed.\n" + answer, medicines=medicines_suggested)

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
