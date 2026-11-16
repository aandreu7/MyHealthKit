"""Transactional eight-slot inventory; no hardware or AI imports."""
from contextlib import contextmanager
import sqlite3
import threading
from filelock import FileLock

try:
    from .settings import DATABASE_PATH
except ImportError:
    from settings import DATABASE_PATH


class InventoryFull(ValueError):
    pass


class MedicineNotFound(LookupError):
    pass


class Inventory:
    def __init__(self, path=DATABASE_PATH):
        from pathlib import Path
        self.path = Path(path).expanduser().resolve()
        self._initialized = False
        self._init_lock = threading.Lock()

    def ensure_initialized(self):
        with self._init_lock:
            if not self._initialized:
                self.initialize()

    @contextmanager
    def operation(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Shared by every worker process using this inventory, not just threads.
        with FileLock(str(self.path) + '.operation.lock', timeout=30):
            yield

    @contextmanager
    def connection(self, write=False):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.path), timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            if write:
                conn.execute('BEGIN IMMEDIATE')
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self):
        with self.operation(), self.connection(write=True) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, description TEXT, url_prospect TEXT,
                symptoms TEXT, contraindications TEXT,
                position INTEGER NOT NULL CHECK(typeof(position) = 'integer' AND position BETWEEN 0 AND 7)
            )''')
            invalid = conn.execute("SELECT id FROM medicines WHERE position IS NULL OR typeof(position) != 'integer' OR position NOT BETWEEN 0 AND 7").fetchone()
            duplicate = conn.execute('SELECT position FROM medicines GROUP BY position HAVING COUNT(*) > 1').fetchone()
            if invalid or duplicate:
                raise ValueError('Existing inventory has invalid or duplicate slots; reconcile with the physical robot before starting')
            conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS medicines_position_unique ON medicines(position)')
            # Triggers protect legacy databases without replacing tables or losing IDs.
            for event in ('INSERT', 'UPDATE'):
                conn.execute('''CREATE TRIGGER IF NOT EXISTS medicines_position_%s
                    BEFORE %s ON medicines
                    WHEN NEW.position IS NULL OR typeof(NEW.position) != 'integer' OR NEW.position NOT BETWEEN 0 AND 7
                    BEGIN SELECT RAISE(ABORT, 'position must be an integer between 0 and 7'); END''' % (event.lower(), event))
        self._initialized = True

    @staticmethod
    def empty_position(conn):
        occupied = {row[0] for row in conn.execute('SELECT position FROM medicines')}
        return next((slot for slot in range(8) if slot not in occupied), -1)

    def find_empty_position(self):
        self.ensure_initialized()
        with self.connection() as conn:
            return self.empty_position(conn)

    def get(self, medicine_id):
        self.ensure_initialized()
        with self.connection() as conn:
            row = conn.execute('SELECT * FROM medicines WHERE id = ?', (medicine_id,)).fetchone()
            return dict(row) if row else None

    def names(self):
        self.ensure_initialized()
        with self.connection() as conn:
            return [row[0] for row in conn.execute('SELECT name FROM medicines ORDER BY id')]

    def items(self):
        self.ensure_initialized()
        with self.connection() as conn:
            return [dict(id=str(row['id']), name=row['name']) for row in conn.execute('SELECT id,name FROM medicines ORDER BY id')]

    @staticmethod
    def insert(conn, info, position):
        conn.execute('''INSERT INTO medicines
            (name, description, url_prospect, symptoms, contraindications, position)
            VALUES (?, ?, ?, ?, ?, ?)''',
            tuple(info[key] for key in ('name', 'description', 'url_prospect', 'symptoms', 'contraindications')) + (position,))

    def add(self, info, actuate):
        self.ensure_initialized()
        with self.operation(), self.connection(write=True) as conn:
            slot = self.empty_position(conn)
            if slot == -1:
                raise InventoryFull('All eight compartments are occupied')
            # Commit only after the closed-trapdoor positioning operation succeeds.
            actuate(slot, False)
            self.insert(conn, info, slot)
            return slot

    def retrieve(self, medicine_id, actuate, delete=False):
        self.ensure_initialized()
        with self.operation(), self.connection(write=True) as conn:
            row = conn.execute('SELECT position FROM medicines WHERE id = ?', (medicine_id,)).fetchone()
            if row is None:
                raise MedicineNotFound('Medicine does not exist')
            position = row[0]
            if type(position) is not int or not 0 <= position < 8:
                raise ValueError('Stored compartment is invalid')
            actuate(position, True)
            if delete:
                conn.execute('DELETE FROM medicines WHERE id = ?', (medicine_id,))
            return position
