"""HTTP endpoints; no credentials/models are required for inventory/navigation."""
import os
from pathlib import Path
import re
import tempfile
import threading
import time
import uuid

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file, url_for
from filelock import Timeout as LockTimeout

if __package__:
    from . import services
    from .settings import AUDIO_DIR, KEYS_PATH
    from .prompts import medicine_prompt, diagnosis_prompt
else:
    import services
    from settings import AUDIO_DIR, KEYS_PATH
    from prompts import medicine_prompt, diagnosis_prompt

# Preserve the navigation entry points and response contract.
send_robot = services.send_robot
validate_qr_code = services.validate_qr_code
load_dotenv(dotenv_path=KEYS_PATH)
app = Flask(__name__)
app.config.update(LANGUAGE=os.getenv('MYHEALTHKIT_LANGUAGE', 'en-US'),
                  AUDIO_DIR=AUDIO_DIR, AUDIO_TTL=3600,
                  PLAY_DIAGNOSIS_AUDIO=os.getenv('MYHEALTHKIT_PLAY_AUDIO', '1') == '1',
                  LLM_CLIENT=None)
_client_lock = threading.Lock()


def get_client():
    with _client_lock:
        if app.config['LLM_CLIENT'] is None:
            from openai import OpenAI
            key = os.getenv('OPENROUTER_API_KEY')
            if not key:
                raise RuntimeError('OPENROUTER_API_KEY is not configured')
            app.config['LLM_CLIENT'] = OpenAI(base_url='https://openrouter.ai/api/v1',
                                            api_key=key, timeout=60, max_retries=1)
        return app.config['LLM_CLIENT']


def medicine_id_from_request():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError('Expected a JSON object')
    value = data.get('medicine_id')
    if isinstance(value, str) and re.fullmatch(r'[0-9]+', value):
        value = int(value)
    if type(value) is not int or value <= 0:
        raise ValueError('medicine_id must be a positive integer')
    return value


@app.route('/')
def index():
    return jsonify(status='OK')


@app.route('/diagnosis-output/<audio_id>.mp3')
@app.route('/diagnosis-output.mp3', defaults={'audio_id': None})
def serve_audio(audio_id):
    audio_id = audio_id or request.args.get('id', '')
    if not re.fullmatch(r'[0-9a-f]{32}', audio_id):
        return jsonify(error='Use the audioUri returned by the diagnosis request.'), 404
    path = Path(app.config['AUDIO_DIR']) / (audio_id + '.mp3')
    if not path.is_file() or time.time() - path.stat().st_mtime > app.config['AUDIO_TTL']:
        return jsonify(error='Audio does not exist or has expired.'), 404
    return send_file(str(path), mimetype='audio/mpeg', max_age=0)


@app.route('/show-medicines', methods=['GET'])
def show_medicines():
    return jsonify(success=True, medicine_items=services.get_all_medicines_with_ids())


@app.route('/medicine-details', methods=['POST'])
def medicine_details():
    medicine_id = medicine_id_from_request()
    medicine = services.get_medicine_by_id(medicine_id)
    if medicine is None:
        raise services.MedicineNotFound('Medicine does not exist')
    return jsonify(medicine)


@app.route('/request-myhealthkit', methods=['POST'])
def request_myhealthkit():
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error='Expected a JSON object.'), 400
        location = validate_qr_code(data.get('message'))
        if location == -1:
            return jsonify(error='Invalid QR code scanned.'), 400
        send_robot(location)
        return jsonify(message='Navigation goal accepted; arrival not yet confirmed.',
                       location=location, status='accepted'), 202
    except Exception:
        app.logger.exception('Navigation request failed')
        return jsonify(error='Navigation unavailable or destination not configured.'), 503


@app.route('/delete-medicine', methods=['POST'])
def delete_medicine():
    medicine_id = medicine_id_from_request()
    services.del_medicine(medicine_id)
    return jsonify(message="Medicine with ID '%s' deleted successfully." % medicine_id)


@app.route('/select-medicine', methods=['POST'])
def select_medicine():
    medicine_id = medicine_id_from_request()
    position = services.select_stored_medicine(medicine_id)
    return jsonify(message="Medicine '%s' selected at position %s." % (medicine_id, position))


@app.route('/add-medicine', methods=['POST'])
def add_medicine():
    upload = request.files.get('file')
    if upload is None or not upload.filename:
        raise ValueError('A medicine image is required')
    with tempfile.TemporaryDirectory(prefix='myhealthkit-image-') as directory:
        image = Path(directory) / 'medicine.image'
        upload.save(str(image))
        if image.stat().st_size == 0:
            raise ValueError('The uploaded image is empty')
        text = services.ocr_google_api(image)
        answer = services.get_completion(get_client(), medicine_prompt(text))
        info = services.clean_json(answer.choices[0].message.content)
        if not services.validate_medicine_info(info):
            raise ValueError('Incomplete or invalid medicine data returned by the model')
        services.store_medicine(info)
    return jsonify(message="Medicine '%s' has been successfully added." % info['name'])


def cleanup_audio(directory):
    for path in directory.glob('*.mp3'):
        if re.fullmatch(r'[0-9a-f]{32}', path.stem):
            try:
                if time.time() - path.stat().st_mtime > app.config['AUDIO_TTL']:
                    path.unlink()
            except OSError:
                pass  # Another worker may be serving or removing the same expired file.


@app.route('/start-diagnosis', methods=['POST'])
def start_diagnosis():
    upload = request.files.get('file')
    if upload is None or not upload.filename:
        raise ValueError('An audio file is required')
    language = app.config['LANGUAGE']
    text = services.transcribe_audio(upload, language=language)
    existing = services.get_all_medicines()
    answer = services.get_completion(get_client(), diagnosis_prompt(existing, language, text)).choices[0].message.content
    suggested = services.extract_medicines_list(answer, allowed=existing)
    readable = services.format_human_readable(answer)
    if not readable:
        raise ValueError('Model returned no diagnosis text')
    directory = Path(app.config['AUDIO_DIR'])
    directory.mkdir(parents=True, exist_ok=True)
    cleanup_audio(directory)
    audio_id = uuid.uuid4().hex
    target = directory / (audio_id + '.mp3')
    with tempfile.TemporaryDirectory(prefix='generating-', dir=str(directory)) as temp:
        pending = Path(temp) / 'speech.mp3'
        services.speak(readable, language, audio_path=pending)
        os.replace(str(pending), str(target))
    if app.config['PLAY_DIAGNOSIS_AUDIO']:
        try:
            services.play_mp3(target)
        except Exception:
            app.logger.exception('Robot audio playback failed; phone audio is available')
    return jsonify(success=True, message='Diagnosis completed.\n' + readable,
                   medicines=suggested, audioUri=url_for('serve_audio', audio_id=audio_id, _external=True))


@app.errorhandler(services.MedicineNotFound)
def missing_medicine(error):
    return jsonify(error=str(error)), 404


@app.errorhandler(services.InventoryFull)
def full_inventory(error):
    return jsonify(error=str(error)), 409


@app.errorhandler(ValueError)
def invalid_request(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(LockTimeout)
def busy_dispenser(error):
    return jsonify(error='The dispenser is busy. Try again shortly.'), 503


@app.errorhandler(Exception)
def operation_failed(error):
    from werkzeug.exceptions import HTTPException
    if isinstance(error, HTTPException):
        return error
    app.logger.exception('Controller operation failed')
    return jsonify(error='The operation could not be completed.'), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
