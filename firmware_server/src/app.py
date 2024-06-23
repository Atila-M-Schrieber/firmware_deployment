from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Defined in the Dockerfile
firmware_directory = os.environ["FIRMWARE_DIRECTORY"]
# Should not be defined in the Dockerfile, but will do as an example
trusted_firmware_signers = {
    "John Doe": os.environ["PUBLIC_KEY"]
}
known_ids = os.environ["KNOWN_IDS"].split(':')

@app.route('/firmware')
def hello():
	return "Hello World!"

@app.route('/firmware/status', methods=['POST'])
def status():
    try:
        # Should check for valid format
        # Should check for known ID
        data = request.get_json()
    except:
        print("Data was not JSON")
        return "Request must be JSON", 400

    print(data)

    no_update = {
        "update": False
    }
    return jsonify(no_update)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)
