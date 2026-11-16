"""Tests use real Flask, SQLite and OS file locks; GPIO/cloud providers are mocked."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch
from urllib.parse import urlsplit

SERVER = Path(__file__).resolve().parents[1]
CONTROLLER = SERVER.parent
sys.path.insert(0, str(CONTROLLER.parent))
application = importlib.import_module('MyHealthController.server.app')
services = application.services
from MyHealthController.server.storage import Inventory, InventoryFull

INFO = dict(name='Example', description='Example description', symptoms='Example symptoms',
            contraindications='Example contraindications', url_prospect=None)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'inventory.db'
        self.inventory = Inventory(self.path)

    def test_exactly_eight_slots_then_full_without_actuating(self):
        callback = Mock()
        self.assertEqual([self.inventory.add(INFO, callback) for _ in range(8)], list(range(8)))
        self.assertEqual(self.inventory.find_empty_position(), -1)
        with self.assertRaises(InventoryFull):
            self.inventory.add(INFO, callback)
        self.assertEqual(callback.call_count, 8)

    def test_failure_does_not_register_medicine(self):
        with self.assertRaises(RuntimeError):
            self.inventory.add(INFO, Mock(side_effect=RuntimeError('servo failed')))
        self.assertEqual(self.inventory.items(), [])
        self.assertEqual(self.inventory.find_empty_position(), 0)

    def test_failed_delete_keeps_record_and_success_releases_slot(self):
        self.inventory.add(INFO, Mock())
        medicine_id = self.inventory.items()[0]['id']
        with self.assertRaises(RuntimeError):
            self.inventory.retrieve(medicine_id, Mock(side_effect=RuntimeError('close failed')), delete=True)
        self.assertIsNotNone(self.inventory.get(medicine_id))
        callback = Mock()
        self.inventory.retrieve(medicine_id, callback, delete=True)
        callback.assert_called_once_with(0, True)
        self.assertIsNone(self.inventory.get(medicine_id))

    def test_retrieval_retains_inventory_entry(self):
        self.inventory.add(INFO, Mock())
        medicine_id = self.inventory.items()[0]['id']
        self.inventory.retrieve(medicine_id, Mock())
        self.assertIsNotNone(self.inventory.get(medicine_id))

    def test_constraints_reject_duplicate_and_invalid_position(self):
        self.inventory.add(INFO, Mock())
        for position in [0, -1, 8, 2.5, None, 'bad']:
            with self.assertRaises(sqlite3.IntegrityError):
                with self.inventory.connection(write=True) as conn:
                    self.inventory.insert(conn, INFO, position)

    def test_legacy_migration_preserves_ids_and_data(self):
        with closing(sqlite3.connect(str(self.path))) as conn, conn:
            conn.execute('CREATE TABLE medicines(id INTEGER PRIMARY KEY, name TEXT, description TEXT, url_prospect TEXT, symptoms TEXT, contraindications TEXT, position INTEGER)')
            conn.execute("INSERT INTO medicines(id,name,position) VALUES (37,'Existing',3)")
        self.inventory.initialize()
        self.assertEqual(self.inventory.get(37)['name'], 'Existing')
        with self.assertRaises(sqlite3.IntegrityError):
            with self.inventory.connection(write=True) as conn:
                conn.execute("UPDATE medicines SET position=8 WHERE id=37")

    def test_legacy_corruption_is_reported_without_deleting_data(self):
        with closing(sqlite3.connect(str(self.path))) as conn, conn:
            conn.execute('CREATE TABLE medicines(id INTEGER PRIMARY KEY, name TEXT, position INTEGER)')
            conn.execute("INSERT INTO medicines VALUES (1,'One',0),(2,'Two',0)")
        with self.assertRaises(ValueError):
            self.inventory.initialize()
        with closing(sqlite3.connect(str(self.path))) as conn, conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM medicines').fetchone()[0], 2)

    def test_independent_threads_never_overlap_actuation_or_duplicate_slots(self):
        active = 0
        peak = 0
        mutex = threading.Lock()
        def actuate(position, release):
            nonlocal active, peak
            with mutex:
                active += 1
                peak = max(peak, active)
            time.sleep(.01)
            with mutex:
                active -= 1
        def add(_):
            return Inventory(self.path).add(INFO, actuate)
        with ThreadPoolExecutor(max_workers=8) as pool:
            positions = list(pool.map(add, range(8)))
        self.assertEqual(sorted(positions), list(range(8)))
        self.assertEqual(peak, 1)

    def test_independent_processes_get_distinct_slots(self):
        code = "import sys,json; sys.path.insert(0,sys.argv[1]); from storage import Inventory; print(Inventory(sys.argv[2]).add(json.loads(sys.argv[3]),lambda p,r:None))"
        def add(_):
            return int(subprocess.check_output([sys.executable, '-B', '-c', code,
                str(SERVER), str(self.path), json.dumps(INFO)], timeout=30, text=True))
        with ThreadPoolExecutor(max_workers=4) as pool:
            positions = list(pool.map(add, range(4)))
        self.assertEqual(sorted(positions), [0, 1, 2, 3])


class ValidationTests(unittest.TestCase):
    def test_medicine_schema_requires_all_fields_and_types(self):
        self.assertTrue(services.validate_medicine_info(INFO))
        for info in [{}, dict(INFO, name=' '), dict(INFO, symptoms=[]), dict(INFO, url_prospect='https://wrong.example')]:
            self.assertFalse(services.validate_medicine_info(info))
        missing = dict(INFO)
        del missing['symptoms']
        self.assertFalse(services.validate_medicine_info(missing))

    def test_empty_list_and_json_or_python_quoted_strings_are_supported(self):
        self.assertEqual(services.extract_medicines_list('Text\n[]'), [])
        self.assertEqual(services.extract_medicines_list('Text\n["A", "A", "B"]'), ['A', 'B'])
        self.assertEqual(services.extract_medicines_list("Text\n['A']", allowed=['A']), ['A'])

    def test_executable_or_wrongly_typed_output_is_never_evaluated(self):
        for answer in ["[__import__('os').getcwd()]", '{}', '[1]', "['']", '']:
            with self.assertRaises(ValueError):
                services.extract_medicines_list(answer)
        with self.assertRaises(ValueError):
            services.extract_medicines_list("['Absent']", allowed=['Present'])

    def test_google_ocr_uses_query_parameter_and_checks_status(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory)/'image'
            image.write_bytes(b'image')
            response = Mock()
            response.json.return_value = {'responses': [{'fullTextAnnotation': {'text': 'Example'}}]}
            with patch.dict(os.environ, {'OCR_API_KEY': 'example-key'}), patch.object(services.requests, 'post', return_value=response) as post:
                self.assertEqual(services.ocr_google_api(image), 'Example')
            self.assertEqual(post.call_args.kwargs['params'], {'key': 'example-key'})
            self.assertIn('timeout', post.call_args.kwargs)
            response.raise_for_status.assert_called_once()


class ServoTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('tested_dispenser', CONTROLLER/'IO_controllers/servomotors/dispenser.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.module.STATE_PATH = Path(self.temp.name)/'position.txt'
        self.module.LOCK_PATH = Path(self.temp.name)/'servo.lock'

    def test_release_is_closed_rotate_open_close(self):
        events = []
        with patch.object(self.module, 'move_servo', side_effect=lambda *args: events.append(args)), patch.object(self.module, 'rotate', side_effect=lambda angle: events.append(('rotate', angle))), patch.object(self.module.time, 'sleep'):
            self.module.actuate(2, True)
        self.assertEqual(events, [(15, 110.15), ('rotate', 67.5), (15, 170), (15, 110.15)])

    def test_finally_closes_after_rotation_or_opening_failure(self):
        with patch.object(self.module, 'move_servo') as move, patch.object(self.module, 'rotate', side_effect=RuntimeError('stuck')):
            with self.assertRaises(RuntimeError):
                self.module.actuate(0, True)
            self.assertEqual(move.call_args.args, (15, 110.15))
            self.assertEqual(move.call_count, 2)
        def fail_open(pin, angle):
            if angle == 170:
                raise RuntimeError('open failed')
        with patch.object(self.module, 'move_servo', side_effect=fail_open) as move, patch.object(self.module, 'rotate'):
            with self.assertRaises(RuntimeError):
                self.module.actuate(0, True)
            self.assertEqual(move.call_args.args, (15, 110.15))

    def test_absolute_servo_does_not_require_prior_position_file(self):
        with patch.object(self.module, 'move_servo'):
            self.module.rotate(90)
        self.assertIn('7.00', self.module.STATE_PATH.read_text())


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.inventory = Inventory(self.directory/'inventory.db')
        self.addCleanup(patch.stopall)
        patch.object(services, 'inventory', self.inventory).start()
        self.actuate = patch.object(services, 'execute_dispenser').start()
        self.client = application.app.test_client()
        self.previous = {k:application.app.config[k] for k in ['AUDIO_DIR','PLAY_DIAGNOSIS_AUDIO','LLM_CLIENT']}
        application.app.config.update(AUDIO_DIR=self.directory/'audio', PLAY_DIAGNOSIS_AUDIO=False, LLM_CLIENT=object())
        self.addCleanup(lambda: application.app.config.update(self.previous))

    def test_inventory_works_without_model_or_keys_and_from_another_cwd(self):
        cwd = os.getcwd()
        try:
            os.chdir(self.temp.name)
            response = self.client.get('/show-medicines')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['medicine_items'], [])
            self.assertFalse((self.directory/'pharmacy.db').exists())
        finally:
            os.chdir(cwd)

    def test_invalid_ids_and_missing_medicine(self):
        for value in [None, True, 1.5, -1, 'bad']:
            self.assertEqual(self.client.post('/select-medicine', json={'medicine_id':value}).status_code, 400)
        self.assertEqual(self.client.post('/select-medicine', json={'medicine_id':999}).status_code, 404)
        self.actuate.assert_not_called()

    def test_delete_dispenses_then_removes_and_selection_preserves_record(self):
        self.inventory.add(INFO, Mock())
        medicine_id = self.inventory.items()[0]['id']
        self.assertEqual(self.client.post('/select-medicine', json={'medicine_id':medicine_id}).status_code, 200)
        self.assertIsNotNone(self.inventory.get(medicine_id))
        self.assertEqual(self.client.post('/delete-medicine', json={'medicine_id':medicine_id}).status_code, 200)
        self.assertIsNone(self.inventory.get(medicine_id))
        self.actuate.assert_called_with(0, True)

    def test_image_is_private_and_removed_after_request(self):
        paths = []
        def ocr(path):
            paths.append(path)
            self.assertEqual(path.read_bytes(), b'photo')
            return 'Example'
        answer = Mock()
        answer.choices = [Mock(message=Mock(content=json.dumps(INFO)))]
        with patch.object(services, 'ocr_google_api', side_effect=ocr), patch.object(services, 'get_completion', return_value=answer):
            for _ in range(2):
                response = self.client.post('/add-medicine', data={'file':(io.BytesIO(b'photo'),'photo.jpg')})
                self.assertEqual(response.status_code, 200)
        self.assertNotEqual(paths[0], paths[1])
        self.assertTrue(all(not path.exists() for path in paths))

    def test_missing_image_and_invalid_model_response_do_not_move_hardware(self):
        self.assertEqual(self.client.post('/add-medicine').status_code, 400)
        answer = Mock(choices=[Mock(message=Mock(content='{}'))])
        with patch.object(services, 'ocr_google_api', return_value='Example'), patch.object(services, 'get_completion', return_value=answer):
            response = self.client.post('/add-medicine', data={'file':(io.BytesIO(b'photo'),'photo.jpg')})
        self.assertEqual(response.status_code, 400)
        self.actuate.assert_not_called()

    def test_full_inventory_is_reported_without_actuating(self):
        for _ in range(8):
            self.inventory.add(INFO, Mock())
        answer = Mock(choices=[Mock(message=Mock(content=json.dumps(INFO)))])
        with patch.object(services, 'ocr_google_api', return_value='Example'), patch.object(services, 'get_completion', return_value=answer):
            response = self.client.post('/add-medicine', data={'file':(io.BytesIO(b'photo'),'photo.jpg')})
        self.assertEqual(response.status_code, 409)
        self.actuate.assert_not_called()

    def test_diagnosis_audio_urls_are_unique_and_serve_only_their_request(self):
        answer = Mock(choices=[Mock(message=Mock(content='Example result\n[]'))])
        sequence = iter([b'first audio', b'second audio'])
        def speak(text, language, *, audio_path):
            audio_path.write_bytes(next(sequence))
        urls = []
        with patch.object(services, 'transcribe_audio', return_value='Symptoms'), patch.object(services, 'get_completion', return_value=answer), patch.object(services, 'speak', side_effect=speak):
            for _ in range(2):
                response = self.client.post('/start-diagnosis', data={'file':(io.BytesIO(b'audio'),'input.m4a')})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json['medicines'], [])
                urls.append(urlsplit(response.json['audioUri']).path)
        self.assertNotEqual(urls[0], urls[1])
        for path, expected in zip(urls, [b'first audio',b'second audio']):
            with self.client.get(path) as response:
                self.assertEqual(response.data, expected)
        self.assertEqual(self.client.get('/diagnosis-output.mp3').status_code, 404)
        self.assertEqual(self.client.get('/diagnosis-output/not-a-token.mp3').status_code, 404)
        self.assertFalse(any((self.directory/'audio').glob('generating-*')))

    def test_concurrent_diagnoses_do_not_exchange_audio(self):
        def completion(client, message):
            return Mock(choices=[Mock(message=Mock(content=message[-1]['content']+'\n[]'))])
        def speak(text, language, *, audio_path):
            time.sleep(.01)
            audio_path.write_bytes(text.encode())
        def diagnose(index):
            expected = ('Symptoms %s' % index).encode()
            with application.app.test_client() as client:
                response = client.post('/start-diagnosis', data={'file':(io.BytesIO(expected),'input.m4a')})
                self.assertEqual(response.status_code, 200)
                path = urlsplit(response.json['audioUri']).path
                with client.get(path) as audio:
                    self.assertEqual(audio.data, expected)
                return path
        with patch.object(services, 'transcribe_audio', side_effect=lambda file, **kw: file.read().decode()), patch.object(services, 'get_completion', side_effect=completion), patch.object(services, 'speak', side_effect=speak):
            with ThreadPoolExecutor(max_workers=4) as pool:
                urls = list(pool.map(diagnose, range(4)))
        self.assertEqual(len(set(urls)), 4)

    def test_failed_tts_cleans_partial_audio(self):
        def fail(text, language, *, audio_path):
            audio_path.write_bytes(b'partial')
            raise RuntimeError('TTS offline')
        answer = Mock(choices=[Mock(message=Mock(content='Example\n[]'))])
        with patch.object(services, 'transcribe_audio', return_value='Symptoms'), patch.object(services, 'get_completion', return_value=answer), patch.object(services, 'speak', side_effect=fail), patch.object(application.app.logger, 'exception'):
            response = self.client.post('/start-diagnosis', data={'file':(io.BytesIO(b'audio'),'input.m4a')})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(list((self.directory/'audio').iterdir()), [])


if __name__ == '__main__':
    unittest.main()
