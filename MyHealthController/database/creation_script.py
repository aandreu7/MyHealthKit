import sqlite3

def insert_data_example(cursor):
    cursor.execute("""
    INSERT INTO medicines (name, description, url_prospect, symptoms, contraindications, position) VALUES
        (
        'Paracetamol',
        'Used to treat mild to moderate pain and fever.',
        'https://www.medicines.org.uk/emc/product/1234/smpc',
        'Headache, Fever, Muscle pain, Toothache',
        'Liver disease, Alcoholism',
        0
        ),
        (
        'Ibuprofen',
        'Non-steroidal anti-inflammatory drug (NSAID) for pain, inflammation and fever.',
        'https://www.medicines.org.uk/emc/product/5678/smpc',
        'Headache, Back pain, Menstrual cramps, Arthritis',
        'Stomach ulcers, Kidney disease, Asthma',
        1
        ),
        (
        'Amoxicillin',
        'Antibiotic used to treat bacterial infections.',
        'https://www.medicines.org.uk/emc/product/91011/smpc',
        'Ear infection, Pneumonia, Urinary tract infection',
        'Penicillin allergy, Mononucleosis',
        2
        ),
        (
        'Aspirin',
        'Used for pain relief, anti-inflammation, and reducing risk of heart attack.',
        'https://www.medicines.org.uk/emc/product/1213/smpc',
        'Headache, Inflammation, Chest pain',
        'Bleeding disorders, Stomach ulcers, Pregnancy',
        5
        ),
        (
        'Loratadine',
        'Antihistamine used to treat allergies.',
        'https://www.medicines.org.uk/emc/product/1415/smpc',
        'Sneezing, Runny nose, Itchy eyes, Hives',
        'Liver disease, Children under 2',
        7
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
        url_prospect TEXT,
        symptoms TEXT,
        contraindications TEXT,
        position INTEGER NOT NULL
    )
    """)

    # Use the following call to insert data into the table as an example
    insert_data_example(cursor)

    conn.commit()

    cursor.close()
    conn.close()
