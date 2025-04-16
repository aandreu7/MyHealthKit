from flask import Flask, jsonify
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
    # Return a JSON response with a status of "OK"
    return jsonify(status="OK")

# Route to start a diagnosis (POST request)
@app.route('/start-diagnosis', methods=['POST'])
def start_diagnosis():
    # Print a message to the console indicating the diagnosis is starting
    print("Starting diagnosis on MyHealthKit...")

    # Create a new connection and cursor inside the function
    conn = sqlite3.connect("../database/pharmacy.db")
    cursor = conn.cursor()

    sql_statement = "SELECT m.name FROM MEDICINES m WHERE m.remaining_units>0"
    existing_medicines = [medicine[0] for medicine in cursor.execute(sql_statement).fetchall()]

    # Close the cursor and connection once the query is done
    cursor.close()
    conn.close()

    message = [
            { "role": "system", "content": "You are a doctor. Someone is asking you for a diagnosis and for a concrete medicine. "
            "You have to listen to the patient and give him a diagnosis and a medicine or a group of medicines from the following list: "
            + str(existing_medicines) + ". You can not choose a medicine that does not appear in the list."},
            { "role": "user", "content": "I have a headache and I feel tired. What do you think?" }
        ]

    # Makes a call to the OpenRouter API to get a response based on the provided message
    # The get_completion function is defined in the services.py file and is responsible for interacting with the OpenRouter API
    answer = get_completion(client, message)

    print(answer.choices[0].message.content)

    # Return a JSON response with a message indicating the diagnosis has started
    return jsonify(message="Diagnosis started")

if __name__ == '__main__':

    # Set the API key and base URL for the OpenRouter API
    load_dotenv(dotenv_path="./keys.env")
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    # Run the Flask application. Start the app, making it listen on all network interfaces (0.0.0.0) and port 5000
    app.run(host='0.0.0.0', port=5000)
