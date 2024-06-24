from flask import Flask, request, jsonify
from pydantic import BaseModel, ValidationError, field_validator, model_validator, root_validator
from typing import Optional
from werkzeug.datastructures import MultiDict
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
#@app.route('/firmware')
#def hello():
#	return "Hello World!"


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
        data = Status.model_validate(data)
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
    return upload(trusted_firmware_signers, firmware_directory)


# Get list of available firmwares
class FirmwareInfoRequest(BaseModel):
    firmware: Optional[str] = None
    version: Optional[str] = None
    
    @model_validator(mode='after')
    def no_orphaned_version(self):
        if self.version and not self.firmware:
            raise ValueError("Version alone cannot be requested!")
        return self

@app.route('/firmware', methods=['GET'])
def get_available_firmwares():
    try:
        req = FirmwareInfoRequest.model_validate(request.form.to_dict())
    except ValueError as e:
        return str(e), 400

    # Get all firmware
    firmware = MultiDict()
    firmware_paths = list(map(lambda fw: fw.split('-'), os.listdir(firmware_directory)))
    # Remove the keys directory
    firmware_paths = filter(lambda pth: pth != ['keys'], firmware_paths)
    print(firmware_paths)
    for fw_name, version in firmware_paths:
        firmware.add(fw_name, version)

    # Filter to requested firmware
    if req.firmware:
        firmware_versions = firmware.getlist(req.firmware)
        if not firmware_versions:
            return {}
        # Filter to selected version (either 1 or 0 left)
        if req.version: 
            if req.version in firmware_versions:
                firmware = { req.firmware: req.version }
            else:
                return {}
        else:
            firmware.clear()
            firmware.setlist(req.firmware, firmware_versions)

    return jsonify(firmware)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)
