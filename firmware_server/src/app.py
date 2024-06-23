from flask import Flask, request, jsonify
from pydantic import BaseModel, ValidationError
from upload import upload
import pgpy
import os

app = Flask(__name__)

# Defined in the Dockerfile
firmware_directory = os.environ["FIRMWARE_DIRECTORY"]
# In lieu of a database for this simple example
key_path = os.path.join(firmware_directory, 'keys', 'public.asc')
with open(key_path, 'r') as f:
    key_block = f.read()
example_key, _ = pgpy.PGPKey.from_blob(key_block)
trusted_firmware_signers = {
    "John Doe": example_key # ignore the fact that the name is included in the pubkey 
}

known_ids = os.environ["KNOWN_IDS"].split(':')

# Placeholder for webui
@app.route('/firmware')
def hello():
	return "Hello World!"

# Receiving status reports from Pi's
class Status(BaseModel):
    firmware: str
    version: str
    id: str
    uptime: int

@app.route('/firmware/status', methods=['POST'])
def status():
    data = request.get_json()
    if data == None:
        print("Status data was not JSON")
        return "Request must be JSON", 400

    try:
        data = Status.parse_obj(data)
    except ValidationError as e:
        print("Status data is invalid")
        return f"JSON format is invalid: {e}", 400

    if not data.id in known_ids:
        print(f"Status received from unknown ID: {data.id}")
        return f"Unknown ID: {data.id}", 401
    

    print(data)

    no_update = { "update": False }
    update_ordered = { "update": True }

    # TESTING
    if data.id == "-2":
        print("Test update order sent")
        return jsonify(update_ordered)

    return jsonify(no_update)

# Firmware upload API
@app.route('/firmware/upload', methods=['PUT'])
def upload_():
    return upload(trusted_firmware_signers)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)
