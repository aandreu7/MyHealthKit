import re
import subprocess
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

def release_medicine(medicine_id):
    pass

#S'ha de modificar, pel moment sols passem el nom a la bd.
def add_medicine_to_db(name: str):
    conn = sqlite3.connect("../database/pharmacy.db")
    cursor = conn.cursor()

    sql = """
    INSERT INTO medicines (name, description, remaining_units, url_prospect, symptoms, contraindications)
    VALUES (?, ?, ?, ?, ?, ?)
    """

    cursor.execute(sql, (
        name,
        "",
        50,  
        "",  
        "",  
        ""   
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

    sql_statement = "SELECT name FROM MEDICINES WHERE remaining_units > 0"

    existing_medicines = [row[0] for row in cursor.execute(sql_statement).fetchall()]
    print(f"Existing medicines fetched: {existing_medicines}")
    cursor.close()
    conn.close()

    return existing_medicines

def ocr_space_file(filename):
    """
    Sends image to OCR.Space API and returns detected text.
    """
    payload = {
        'isOverlayRequired': False,
        'apikey': os.getenv("OCR_SPACE_API_KEY"),
        'language': 'eng',
    }
    with open(filename, 'rb') as f:
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={filename: f},
            data=payload,
        )
    try:
        result = response.json()
    except Exception as e:
        print(f"Error parsing OCR.Space response as JSON: {e}")
        print("OCR.Space raw response text:", response.text)
        raise e

    print("OCR.Space result:", result)

    if isinstance(result, dict) and result.get('ParsedResults'):
        return result['ParsedResults'][0]['ParsedText']
    else:
        raise ValueError(f"OCR failed or bad API response: {result}")

def resize_image_if_needed(image_path, max_size_kb=1024):
    """
    Reduces image size in case it is bigger than allowed (OCR.Space = 1MB)
    """
    max_size_bytes = max_size_kb * 1024
    img = Image.open(image_path)

    # Keeps in quality 85% so as to reduce size
    img.save(image_path, optimize=True, quality=85)

    # Verifies size
    if os.path.getsize(image_path) > max_size_bytes:
        print("Image still too big after compression. Trying to resize...")
        width, height = img.size
        new_width = width // 2
        new_height = height // 2
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        img.save(image_path, optimize=True, quality=85)
    
    print(f"Final image size: {os.path.getsize(image_path) / 1024:.2f} KB")

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
    play_mp3("diagnosis-output.mp3")


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

def get_completion(client, message, temperature=0.2, max_tokens=300):
    """
    Makes calls to the OpenRouter API to get a response based on the provided message.
    """

    def evaluate_LLM_response(answer):
        """
        Evaluates the response from the LLM to ensure it is valid and contains the expected structure.
        """

        if not answer:
            return False

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
        Calls the LLM with the provided model name.
        """
        if defaultOption: # OpenRouter models
            return client.chat.completions.create(
                extra_body={
                    "temperature": temperature, # Controlls model creativity.
                    "max_tokens": max_tokens # Output length in tokens.
                },
                model=model_name,
                messages=message
            )
        else: # Together.ai models
            clientTogether = Together()
            return clientTogether.chat.completions.create(
                temperature=temperature,
                max_tokens=max_tokens,
                model=model_name,
                messages=message,
            )
        
    try:
        # First chance at Google Gemini (OpenRouter)
        answer = call_LLM("google/gemini-2.0-flash-exp:free")

        if evaluate_LLM_response(answer):
            return answer
        
        # Second chance at Nvidia/Meta Llama 3.3 (OpenRouter)
        answer = call_LLM("nvidia/llama-3.3-nemotron-super-49b-v1:free")

        if evaluate_LLM_response(answer):
            return answer
        
        # Third chance at Meta Llama 3.3 (Together.ai)
        answer = call_LLM("meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", False)
        
        if evaluate_LLM_response(answer):
            return answer

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