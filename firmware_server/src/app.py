from flask import Flask, request, jsonify
import os
from pydantic import BaseModel, ValidationError

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

class Status(BaseModel):
    firmware: str
    version: str
    id: str
    uptime: int

@app.route('/firmware/status', methods=['POST'])
def status():
    data = request.get_json()
    if data == None:
        print("Data was not JSON")
        return "Request must be JSON", 400

    try:
        data = Status.parse_obj(data)
    except ValidationError as e:
        print("Data is invalid")
        return f"JSON format is invalid: {e}", 400

    if not data.id in known_ids:
        return f"Unknown ID: {data.id}", 401
    

    print(data)

    no_update = { "update": False }
    update_ordered = { "update": True }

    # TESTING
    if data.id == "-2":
        return jsonify(update_ordered)

    return jsonify(no_update)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)
