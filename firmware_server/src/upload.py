from flask import request, jsonify
from pydantic import BaseModel
import pgpy
import os

class Upload(BaseModel):
    firmware: str
    version: str

# Input is expected as form data, as this will probably be done through a webui
def upload(pgp_keys, firmware_directory):
    if not request.files:
        print("Upload request with no files received")
        return "No files in request", 400
    #print(request.files.to_dict())
    try:
        upload_info = Upload.parse_obj(request.form.to_dict())
    except: 
        print("Bad upload request received")
        return "Bad upload request structure", 400

    signature = None

    firmware_files = {}

    # Sort incoming files
    for _filename, file_contents in request.files.items(multi=True):
        if _filename == 'file':
            if file_contents.filename:
                filename = file_contents.filename
            else:
                return "Unnamed file!", 400
        else:
            filename = _filename
        if filename in ["sig.pgp", "sig.asc"]:
            file_contents.seek(0)
            sig_blob = file_contents.stream.read()#.decode('utf-8')
            signature = pgpy.PGPSignature.from_blob(sig_blob)
        else:
            # duplicates shouldn't happen, assuming no files in directories
            firmware_files[filename] = file_contents
            if filename.split('.')[-1] != "py":
                print("Warning, non-python file sent in firmware upload!")

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

    print(cat_files)

    # Verify signature

    firmware_signer = None
    for signer, key in pgp_keys.items():
        verification = key.verify(cat_files, signature)
        if verification:
            print(f"Firmware signed by: {signer}")
            firmware_signer = signer
            break

    if not firmware_signer:
        print("Bad signature!")
        return "Invalid or unknown signature", 401

    # Skip saving testing files
    if upload_info.firmware == "test":
        return "Test detected, aborting save. Good (bug) hunting!"

    firmware_save_dir = os.path.join(firmware_directory,
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
