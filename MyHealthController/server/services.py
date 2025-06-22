import re
import subprocess
import base64
import requests
import json
import wave
from PIL import Image
import json
from vosk import Model, KaldiRecognizer
import io
import os
import requests
from together import Together
import edge_tts
import pygame
import asyncio
import sqlite3


# ES CANVIARA DE LLOC
#########################
from dotenv import load_dotenv
import os
import google.generativeai as genai
load_dotenv(dotenv_path="./keys.env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OCR_API_KEY = os.getenv("OCR_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
###########################

def ocr_google_api(image_path):
    url = f"https://vision.googleapis.com/v1/images:annotate?key={OCR_API_KEY}"
    headers = {"Content-Type": "application/json"}
    with open(image_path, "rb") as img_file:
        base64_image = base64.b64encode(img_file.read()).decode("utf-8")
    body = {
        "requests": [
            {
                "image": {"content": base64_image},
                "features": [{"type": "TEXT_DETECTION"}]
            }
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    result = response.json()
    try:
        return result['responses'][0]['fullTextAnnotation']['text']
    except KeyError:
        print("No text detected or API error:", result)
        return ""
    
def release_medicine(medicine_id):
    pass

def get_medicine_by_name(name: str):
    """
    Retrieves all fields except remaining_units for a medicine given its name.
    Returns a dict with the medicine's details or None if not found.
    """
    conn = sqlite3.connect("../database/pharmacy.db")
    cursor = conn.cursor()

    sql = """
    SELECT name, description, url_prospect, symptoms, contraindications
    FROM medicines
    WHERE LOWER(name) = LOWER(?)
    """

    cursor.execute(sql, (name,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row and len(row) == 5:
        return {
            'name': row[0],
            'description': row[1],
            'url_prospect': row[2],
            'symptoms': row[3],
            'contraindications': row[4]
        }
    else:
        return None

def add_medicine_to_db(name: str, description: str, url_prospect: str, symptoms: str, contraindications: str):
    conn = sqlite3.connect("../database/pharmacy.db")
    cursor = conn.cursor()

    sql = """
    INSERT INTO medicines
    (name, description, url_prospect, symptoms, contraindications)
    VALUES (?, ?, ?, ?, ?)
    """

    cursor.execute(sql, (
        name,
        description,
        url_prospect,
        symptoms,
        contraindications
    ))

    conn.commit()
    cursor.close()
    conn.close()


def check_existing_medicine(medicine_id) -> bool:
    # Create a new connection and cursor inside the function
    conn = sqlite3.connect("../database/pharmacy.db")
    cursor = conn.cursor()

    sql_statement = "SELECT count(*) FROM MEDICINES m WHERE m.remaining_units>0 AND m.id=?"

    medicineExists = False

    if cursor.execute(sql_statement, (medicine_id)).fetchone()[0] > 0:
        medicineExists = True

    # Close the cursor and connection once the query is done
    cursor.close()
    conn.close()

    return medicineExists

def get_all_medicines() -> list:
    conn = sqlite3.connect("../database/pharmacy.db")
    cursor = conn.cursor()

    sql_statement = "SELECT name FROM MEDICINES"

    existing_medicines = [row[0] for row in cursor.execute(sql_statement).fetchall()]
    print(f"Existing medicines fetched: {existing_medicines}")
    cursor.close()
    conn.close()

    return existing_medicines

def play_mp3(filename):
    """
    Plays the provided MP3 file using pygame.
    """
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.stop()
    pygame.mixer.quit() # Frees file

def format_human_readable(text: str) -> str:
    """
    Cleans the text for TTS/User (human-readable) by removing unnecessary lines and formatting it for better speech synthesis.
    """
    # Remove the last line (the list of medicines)
    lines = text.strip().splitlines()
    if lines and lines[-1].startswith("[") and lines[-1].endswith("]"):
        text = "\n".join(lines[:-1])
    
    # Remove leading dashes and spaces from each line
    lines = text.strip().splitlines()
    clean_lines = [line.lstrip("- ").strip() for line in lines if line.strip()]
    return " ".join(clean_lines)

def speak(text, language = "en-US"):
    """
    Converts the provided text into speech using Edge TTS.
    """
    print("Text to be spoken:", text)

    voice = "en-US-JennyNeural" if language == "en-US" else "es-ES-ElviraNeural"

    audio_path = "diagnosis-output.mp3"


    async def generate_audio():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(audio_path)

    asyncio.run(generate_audio())

    """
    # Communicates with Edge TTS as a subprocess
    command = [
        "edge-tts",
        "--text", text,
        "--write-media", audio_path,
        "--voice", voice,
    ]

    # Execute the command to generate the MP3
    subprocess.run(command, check=True)
    """

    # Play the generated audio file
    #play_mp3("diagnosis-output.mp3")


def transcribe_audio(file, *, model=None, language="en-US") -> str:
    """
    Transcribes the audio file into text using Vosk speech recognition.
    """

    # Loads Vosk model for selected language
    if model is None:
        if language == "en-US":
            model = Model("./vosk-models/vosk-model-en-us-0.22")
        elif language == "es-ES":
            model = Model("./vosk-models/vosk-model-es-0.42")
        else:
            raise ValueError("Unsupported language. Supported languages are 'en-US' and 'es-ES'.")

    # Converts M4A file to WAV (PCM 16-bit mono) using ffmpeg
    # Reads Blob directly and passes it to ffmpeg by stdin
    ffmpeg = subprocess.Popen(
        ['ffmpeg', '-i', 'pipe:0', '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', 'pipe:1'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )

    # Rewinds file pointer to the beginning (always necessary after file.read())
    file.seek(0)

    # file.read() = original m4a audio bytes
    wav_bytes, _ = ffmpeg.communicate(file.read())

    file.seek(0)

    """
    with open("output.wav", "wb") as f:
        f.write(wav_bytes)
    file.seek(0)
    """

    # Processes WAV audio with Vosk
    rec = KaldiRecognizer(model, 16000)

    result_text = ""

    # Vosk works with small audio pieces, so we simulate that by reading the WAV file in chunks of 4000 frames
    buffer = io.BytesIO(wav_bytes)
    with wave.open(buffer, 'rb') as wf:
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                result_text += res.get("text", "") + " "

        final_res = json.loads(rec.FinalResult())
        result_text += final_res.get("text", "")

    return result_text.strip()

def get_completion(client, message, temperature=0.2, max_tokens=300, use_gemini_native=False):
    """
    Makes calls to LLMs (Gemini native, OpenRouter, Together) to get a response based on the provided message.
    Set use_gemini_native=True to prioritize Google Gemini native (using your own API key).
    """

    def evaluate_LLM_response(answer):
        """
        Checks if the LLM response is valid and has the expected structure.
        Handles both object responses (OpenRouter, Together) and plain string (Gemini native).
        """
        if not answer:
            return False

        # Gemini native: response is a string (not an object with choices)
        if isinstance(answer, str):
            try:
                # Try to parse as JSON for minimum validation
                import json
                json.loads(answer)
                return True
            except Exception:
                return False

        # OpenRouter/Together structure
        if hasattr(answer, "error") and answer.error:
            if answer.error.get("code") == 429:
                print("Usage time exceeded.")
            return False

        if not hasattr(answer, "choices") or not answer.choices:
            return False

        first_choice = answer.choices[0]
        if not hasattr(first_choice, "message") or not hasattr(first_choice.message, "content"):
            return False

        return True

    def call_LLM(model_name: str, defaultOption=True):
        """
        Calls the LLM with the given model name.
        - If defaultOption is True: use OpenRouter models.
        - If defaultOption is False: use Together.ai models.
        """
        if defaultOption:  # OpenRouter models
            return client.chat.completions.create(
                extra_body={
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                model=model_name,
                messages=message
            )
        else:  # Together.ai models
            from together import Together
            clientTogether = Together()
            return clientTogether.chat.completions.create(
                temperature=temperature,
                max_tokens=max_tokens,
                model=model_name,
                messages=message,
            )

    # --- Try Gemini native first, if requested ---
    try:
        if use_gemini_native:
            prompt = message if isinstance(message, str) else message[0].get("content", "")
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(prompt)
            answer = response.text
            return answer

        # --- Try OpenRouter (Google Gemini) ---
        answer = call_LLM("google/gemini-2.0-flash-exp:free")

        if evaluate_LLM_response(answer):
            return answer

        # --- Try OpenRouter (Nvidia/Meta Llama 3.3) ---
        answer = call_LLM("nvidia/llama-3.3-nemotron-super-49b-v1:free")

        if evaluate_LLM_response(answer):
            return answer

        # --- Try Together.ai (Meta Llama 3.3) ---
        answer = call_LLM("meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", False)

        if evaluate_LLM_response(answer):
            return answer

        # --- No valid response from any LLM ---
        raise RuntimeError("No valid response from any LLM.")

    except Exception as e:
        raise RuntimeError(f"Error during LLM call: {e}")

def extract_medicines_list(answer):
    """
    Extracts the list of medicines from the last line of the provided answer string by the LLM.
    """
    # Divides the message into lines and obtains the last line (where the list of medicines is expected to be)
    lines = answer.strip().split("\n")
    last_line = lines[-1]
    
    # Validate the format of the last line to ensure it is a list of strings
    pattern = r"^\[(?:'[^']*',\s*)*'[^']*'\]$"
    
    if re.match(pattern, last_line):
        medicines = eval(last_line)
        return medicines
    else:
        raise ValueError("LLM has not provided a list of medicines in its last message.")