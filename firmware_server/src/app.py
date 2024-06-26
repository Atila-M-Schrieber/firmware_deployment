from flask import Flask, request, jsonify
from pydantic import BaseModel, ValidationError, model_validator
from typing import Optional
from upload import handle_upload
import update
from util import state
import util
import pgpy
import os

app = Flask(__name__)

# Defined in the Dockerfile
state["firmware_directory"] = os.environ["FIRMWARE_DIRECTORY"]
# In lieu of a database for this simple example
key_path = os.path.join(state["firmware_directory"], 'keys', 'public.asc')
with open(key_path, 'r') as f:
    key_block = f.read()
example_key, _ = pgpy.PGPKey.from_blob(key_block)
state["trusted_firmware_signers"] = {
    "John Doe": example_key # ignore the fact that the name is included in the pubkey 
}
print(state["trusted_firmware_signers"])

state["known_ids"] = os.environ["KNOWN_IDS"].split(':')
state["known_test_ids"] =  os.environ["KNOWN_TEST_IDS"].split(':')

# Placeholder for webui
#@app.route('/firmware')
#def hello():
#	return "Hello World!"


# Receiving status reports from Pi's - board API
class Status(BaseModel):
    firmware: str
    version: str
    board_id: str
    uptime: int

@app.route('/firmware/status', methods=['POST'])
def status():
    status = request.get_json()
    if status == None:
        print("Status data was not JSON")
        return "Request must be JSON", 400

    try:
        status = Status.model_validate(status)
    except ValidationError as e:
        print("Status data is invalid")
        return f"JSON format is invalid: {e}", 400

    if not status.board_id in state["known_ids"] and not status.board_id in state["known_test_ids"]:
        print(f"Status received from unknown ID: {status.board_id}")
        return f"Unknown ID: {status.board_id}", 401
    

    print(status)

    update_ordered = { "update": True, "secret": None }

    # TESTING
    if status.board_id in state["known_test_ids"]:
        print("Test ID detected. Remember to deal with test ID's before production deployment")
    if status.board_id == "-2":
        print("Test update order sent")
        update_ordered["secret"] = "test_secret"
        return jsonify(update_ordered)

    # Check for update order
    if status.board_id in state["orders"]:
        update_ordered["secret"] = state["orders"][status.board_id].secret
        print(f"Update order detected for board '{status.board_id}'")
        return jsonify(update_ordered)

    return jsonify({})


# Firmware upload - client API
@app.route('/firmware/upload', methods=['PUT'])
def upload():
    return handle_upload()

# Update order - client API
@app.route('/firmware/update/<id>', methods=['POST', 'PUT']) # this was 'POST, PUT' for too long...
def order_update(id):
    return update.order(id)

# Firmware update download request - board API
@app.route('/firmware/update/<id>', methods=['GET'])
def download_update(id):
    return update.download(id)

# Firmware update installation complete (pre-reboot) - board API
@app.route('/firmware/update/<id>', methods=['DELETE'])
def update_completion(id):
    return update.delete_order(id)

# Get list of available firmwares - client API
@app.route('/firmware', methods=['GET'])
def get_available_firmware():
    try:
        req = util.FirmwareInfoRequest.model_validate(request.form.to_dict())
    except ValueError as e:
        return str(e), 400
    return jsonify(util.available_firmware(req))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
