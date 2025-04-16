from flask import Flask, jsonify

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
    print("Starting diagnosis on the MyHealthKit...")
    """
    Upcoming code.
    """
    # Return a JSON response with a message indicating the diagnosis has started
    return jsonify(message="Diagnosis started")

# Run the Flask application
if __name__ == '__main__':
    # Start the app, making it listen on all network interfaces (0.0.0.0) and port 5000
    app.run(host='0.0.0.0', port=5000)
