from flask import request
from pydantic import BaseModel
import pgpy
import os
import util
from util import state

class Upload(BaseModel):
    firmware: str
    version: str

# Input is expected as form data, as this will probably be done through a webui
def handle_upload():
    if not request.files:
        print("Upload request with no files received")
        return "No files in request", 400
    #print(request.files.to_dict())
    try:
        upload_info = Upload.model_validate(request.form.to_dict())
    except: 
        print("Bad upload request received")
        return "Bad upload request structure", 400

    # Sort incoming files
    try:
        signature, firmware_files = util.sort_files(['py'])
    except Exception as e:
        return e.args

    # Make sure nothing's missing
    if not signature:
        print("Upload requst with no signature received")
        return "No signature file found!", 422
    if not firmware_files:
        print("Upload request with no firmware, only signature received")
        return "No firmware in request", 400

    sorted_filenames = sorted(firmware_files)

    # concatenate firmware as "cat /firmware_files/as/a/directory/*" would
    def decode(name):
        file = firmware_files[name]
        return file.read().decode('utf-8')

    cat_files = ''.join(map(decode, sorted_filenames))

    # Verify signature
    firmware_signer = util.find_signer(signature, cat_files)

    if not firmware_signer:
        print("Bad signature!")
        return "Invalid or unknown signature", 401

    # Skip saving testing files
    if upload_info.firmware == "test":
        return "Test detected, aborting save. Good (bug) hunting!"

    firmware_save_dir = os.path.join(state["firmware_directory"],
                                     f"{upload_info.firmware}-{upload_info.version}")
    try:
        os.mkdir(firmware_save_dir)
    except FileExistsError:
        print("Uploaded firmware overwrite conflict")
        return f"This firmware version ({upload_info.version}) already exists,"\
                "please submit a DELETE request, or a new version!", 409
                # NOTE the DELETE is not implemented, but would be easy - signed request

    for name, file in firmware_files.items():
        file.save(os.path.join(firmware_save_dir, name))

    print(os.listdir(firmware_save_dir))

    return "Firmware uploaded successfully"
