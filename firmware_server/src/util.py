from flask import Flask, request, jsonify, session
from werkzeug.datastructures import MultiDict
from pgpy import PGPSignature
from pydantic import BaseModel, ValidationError, model_validator
from typing import Optional
import pgpy
from werkzeug.datastructures import FileStorage
import os

# Global state directory with shared data - defined like this so pydantic doesn't get pissed
state = {
    "orders": {},
    "cleanup_events": {},
    "firmware_directory": "",
}

# Sorts files in the request into the signature, and everything else
def sort_files(expected_extensions=[]) -> tuple[None | PGPSignature, dict[str, FileStorage]]:
    signature = None
    other_files = {}
    for _filename, file_contents in request.files.items(multi=True):
        if _filename == 'file':
            if file_contents.filename:
                filename = file_contents.filename
            else:
                raise Exception("Unnamed file!", 400)
        else:
            filename = _filename
        if filename in ["sig.pgp", "sig.asc"]:
            file_contents.seek(0)
            sig_blob = file_contents.stream.read()#.decode('utf-8')
            signature = pgpy.PGPSignature.from_blob(sig_blob)
            if isinstance(signature, tuple):
                signature, _ = signature
        else:
            # duplicates shouldn't happen, assuming no files in directories
            other_files[filename] = file_contents
            extension = filename.split('.')[-1] 
            if expected_extensions and not extension in expected_extensions:
                print(f"Warning, file with unexpected extension '{extension}'"\
                        f"was sent!\n Expected extensions: {expected_extensions}")
    return (signature, other_files)

# Finds the signer of a signature based on text, from the keyring
def find_signer(signature, text) -> None | str:
    signer = None
    for signer_name, key in state["trusted_firmware_signers"].items():
        verification = key.verify(text, signature)
        if verification:
            print(f"Signature by: {signer_name}")
            signer = signer_name
            break
    return signer


class FirmwareInfoRequest(BaseModel):
    firmware: Optional[str] = None
    version: Optional[str] = None
    
    @model_validator(mode='after')
    def no_orphaned_version(self):
        if self.version and not self.firmware:
            raise ValueError("Version alone cannot be requested!")
        return self

# Lists all requested firmware - separated from API call for internal use
# None, None for all; fw_name, None for all versions of fw_name,
# and both to check for a specific version
def available_firmware(req: FirmwareInfoRequest):
    # Get all firmware
    firmware = MultiDict()
    firmware_paths = list(map(lambda fw: fw.split('-'), os.listdir(state["firmware_directory"])))
    # Remove the keys directory
    firmware_paths = filter(lambda pth: pth != ['keys'], firmware_paths)
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

    return firmware
