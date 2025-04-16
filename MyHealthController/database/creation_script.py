import sqlite3

def insert_data_example(cursor):
    cursor.execute("""
    INSERT INTO medicines (name, description, remaining_units, url_prospect, symptoms, contraindications) VALUES
        (
        'Paracetamol',
        'Used to treat mild to moderate pain and fever.',
        100,
        'https://www.medicines.org.uk/emc/product/1234/smpc',
        'Headache, Fever, Muscle pain, Toothache',
        'Liver disease, Alcoholism'
        ),
        (
        'Ibuprofen',
        'Non-steroidal anti-inflammatory drug (NSAID) for pain, inflammation and fever.',
        80,
        'https://www.medicines.org.uk/emc/product/5678/smpc',
        'Headache, Back pain, Menstrual cramps, Arthritis',
        'Stomach ulcers, Kidney disease, Asthma'
        ),
        (
        'Amoxicillin',
        'Antibiotic used to treat bacterial infections.',
        0,
        'https://www.medicines.org.uk/emc/product/91011/smpc',
        'Ear infection, Pneumonia, Urinary tract infection',
        'Penicillin allergy, Mononucleosis'
        ),
        (
        'Aspirin',
        'Used for pain relief, anti-inflammation, and reducing risk of heart attack.',
        75,
        'https://www.medicines.org.uk/emc/product/1213/smpc',
        'Headache, Inflammation, Chest pain',
        'Bleeding disorders, Stomach ulcers, Pregnancy'
        ),
        (
        'Loratadine',
        'Antihistamine used to treat allergies.',
        60,
        'https://www.medicines.org.uk/emc/product/1415/smpc',
        'Sneezing, Runny nose, Itchy eyes, Hives',
        'Liver disease, Children under 2'
    );
    """)

if __name__=="__main__":
    # Creates SQLite3 database file
    conn = sqlite3.connect("./pharmacy.db")
    cursor = conn.cursor()

    # Creates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        remaining_units INTEGER DEFAULT 0,
        url_prospect TEXT,
        symptoms TEXT,
        contraindications TEXT
    )
    """)

    # Use the following call to insert data into the table as an example
    insert_data_example(cursor)

    conn.commit()

    cursor.close()
    conn.close()