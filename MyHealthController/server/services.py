"""Application services. Hardware and network clients are loaded on demand."""
import ast
import asyncio
import base64
from functools import lru_cache
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import wave

import requests
from filelock import FileLock

try:
    from .settings import CONTROLLER_DIR, DATA_DIR, MODEL_DIR
    from .storage import Inventory, InventoryFull, MedicineNotFound
except ImportError:
    from settings import CONTROLLER_DIR, DATA_DIR, MODEL_DIR
    from storage import Inventory, InventoryFull, MedicineNotFound

inventory = Inventory()
_model_lock = threading.Lock()


def send_robot(location):
    script = CONTROLLER_DIR / 'SLAM/catkin_ws/src/my_slam_setup/scripts/go_to_point.py'
    subprocess.run([sys.executable, str(script), str(location)], check=True, timeout=15)


def execute_dispenser(position, release=False):
    if type(position) is not int or not 0 <= position < 8:
        raise ValueError('Invalid compartment')
    script = CONTROLLER_DIR / 'IO_controllers/servomotors/dispenser.py'
    command = [sys.executable, str(script), str(position)]
    if release:
        command.append('--release')
    # The servo process owns the full close/rotate/open/close sequence and lock.
    # Do not forcibly kill it on a short timeout while it may be closing the door.
    subprocess.run(command, check=True)


def execute_open_trapdoor(control):
    script = CONTROLLER_DIR / 'IO_controllers/servomotors/open_trapdoor.py'
    subprocess.run([sys.executable, str(script), str(int(bool(control)))], check=True)


def execute_spin_wheel(position):
    execute_dispenser(position, False)


def find_empty_position():
    inventory.ensure_initialized()
    return inventory.find_empty_position()


def get_medicine_by_id(medicine_id):
    inventory.ensure_initialized()
    return inventory.get(medicine_id)


def get_position_medicine(medicine_id):
    row = get_medicine_by_id(medicine_id)
    return row['position'] if row else None


def get_all_medicines():
    inventory.ensure_initialized()
    return inventory.names()


def get_all_medicines_with_ids():
    inventory.ensure_initialized()
    return inventory.items()


def store_medicine(info):
    if not validate_medicine_info(info):
        raise ValueError('Incomplete medicine data')
    inventory.ensure_initialized()
    return inventory.add(info, execute_dispenser)


def select_stored_medicine(medicine_id, delete=False):
    inventory.ensure_initialized()
    return inventory.retrieve(medicine_id, execute_dispenser, delete=delete)


def del_medicine(medicine_id):
    return select_stored_medicine(medicine_id, delete=True)


def ocr_google_api(image_path):
    key = os.getenv('OCR_API_KEY')
    if not key:
        raise RuntimeError('OCR_API_KEY is not configured')
    with open(image_path, 'rb') as stream:
        encoded = base64.b64encode(stream.read()).decode('ascii')
    response = requests.post('https://vision.googleapis.com/v1/images:annotate',
        params={'key': key}, json={'requests': [{'image': {'content': encoded},
        'features': [{'type': 'TEXT_DETECTION'}]}]}, timeout=(10, 60))
    response.raise_for_status()
    result = response.json()
    responses = result.get('responses') or []
    if result.get('error') or not responses or responses[0].get('error'):
        raise RuntimeError('OCR provider returned an error')
    text = responses[0].get('fullTextAnnotation', {}).get('text', '')
    if not isinstance(text, str) or not text.strip():
        raise ValueError('No medicine text could be read')
    return text


def clean_json(raw):
    if not isinstance(raw, str):
        raise ValueError('Model returned no text')
    raw = raw.strip()
    if raw.startswith('```'):
        lines = raw.splitlines()
        if len(lines) < 3 or lines[-1].strip() != '```':
            raise ValueError('Incomplete JSON response')
        raw = '\n'.join(lines[1:-1])
    return json.loads(raw)


def validate_medicine_info(info):
    required = {'name', 'description', 'symptoms', 'contraindications', 'url_prospect'}
    if not isinstance(info, dict) or not required.issubset(info):
        return False
    for key in required - {'url_prospect'}:
        value = info[key]
        if not isinstance(value, str) or not value.strip() or value.strip().lower() in {'none', 'null'}:
            return False
    url = info['url_prospect']
    return url is None or (isinstance(url, str) and re.fullmatch(
        r'https://www\.medicines\.org\.uk/emc/product/[0-9]+/smpc', url) is not None)


def validate_qr_code(qr_content):
    match = re.fullmatch(r'location([0-9]+)', qr_content) if isinstance(qr_content, str) else None
    return int(match.group(1)) if match else -1


def extract_medicines_list(answer, allowed=None):
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError('Model returned no diagnosis')
    try:
        result = ast.literal_eval(answer.strip().splitlines()[-1])
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError) as exc:
        raise ValueError('Expected a list of medicine names on the last line') from exc
    if not isinstance(result, list) or any(not isinstance(x, str) or not x.strip() for x in result):
        raise ValueError('Expected a list of non-empty medicine names')
    if allowed is not None and any(x not in allowed for x in result):
        raise ValueError('Model suggested a medicine absent from the inventory')
    return list(dict.fromkeys(result))


def format_human_readable(text):
    lines = text.strip().splitlines()
    if lines and lines[-1].startswith('[') and lines[-1].endswith(']'):
        lines = lines[:-1]
    return ' '.join(line.lstrip('- ').strip() for line in lines if line.strip())


@lru_cache(maxsize=2)
def _load_model(path):
    from vosk import Model
    return Model(path)


def load_speech_model(language):
    names = {'en-US': 'vosk-model-en-us-0.22-lgraph', 'es-ES': 'vosk-model-es-0.42'}
    if language not in names:
        raise ValueError('Unsupported language')
    path = MODEL_DIR / names[language]
    if not path.is_dir():
        raise RuntimeError('Speech model is missing: %s' % path)
    with _model_lock:
        return _load_model(str(path))


def transcribe_audio(file, *, model=None, language='en-US'):
    from vosk import KaldiRecognizer
    if model is None:
        model = load_speech_model(language)
    file.seek(0)
    completed = subprocess.run([os.getenv('FFMPEG_BINARY', 'ffmpeg'), '-v', 'error', '-i', 'pipe:0',
        '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', 'pipe:1'],
        input=file.read(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=60)
    file.seek(0)
    recognizer = KaldiRecognizer(model, 16000)
    pieces = []
    with wave.open(io.BytesIO(completed.stdout), 'rb') as audio:
        while True:
            data = audio.readframes(4000)
            if not data:
                break
            if recognizer.AcceptWaveform(data):
                pieces.append(json.loads(recognizer.Result()).get('text', ''))
        pieces.append(json.loads(recognizer.FinalResult()).get('text', ''))
    text = ' '.join(pieces).strip()
    if not text:
        raise ValueError('No speech was recognized')
    return text


def play_mp3(filename):
    import pygame
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with FileLock(str(DATA_DIR / 'playback.lock'), timeout=120):
        pygame.mixer.init()
        try:
            pygame.mixer.music.load(str(filename))
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        finally:
            pygame.mixer.music.stop()
            pygame.mixer.quit()


def speak(text, language='en-US', *, audio_path, playback=False):
    import edge_tts
    voice = 'en-US-JennyNeural' if language == 'en-US' else 'es-ES-ElviraNeural'
    async def generate():
        await edge_tts.Communicate(text, voice).save(str(audio_path))
    asyncio.run(generate())
    if playback:
        play_mp3(audio_path)
    return Path(audio_path)


def get_completion(client, message, temperature=0.2, max_tokens=300, use_gemini_native=False):
    """Try configured providers; return the same choices/message response contract."""
    models = [name.strip() for name in os.getenv('OPENROUTER_MODELS',
        'google/gemini-2.0-flash-exp:free,nvidia/llama-3.3-nemotron-super-49b-v1:free').split(',') if name.strip()]
    last_error = None
    for model in models:
        try:
            answer = client.chat.completions.create(model=model, messages=message,
                temperature=temperature, max_tokens=max_tokens)
            if answer.choices and isinstance(answer.choices[0].message.content, str) and answer.choices[0].message.content.strip():
                return answer
        except Exception as exc:
            last_error = exc
    if os.getenv('TOGETHER_API_KEY'):
        try:
            from together import Together
            together_client = Together(timeout=60, max_retries=1)
            answer = together_client.chat.completions.create(
                model=os.getenv('TOGETHER_MODEL', 'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free'),
                messages=message, temperature=temperature, max_tokens=max_tokens)
            if answer.choices and isinstance(answer.choices[0].message.content, str) and answer.choices[0].message.content.strip():
                return answer
        except Exception as exc:
            last_error = exc
    raise RuntimeError('No configured model returned a usable response') from last_error
