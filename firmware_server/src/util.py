from flask import Flask, request, jsonify, session
from pgpy import PGPSignature
from pydantic import BaseModel, ValidationError, model_validator
import pgpy
from werkzeug.datastructures import FileStorage

state = {
    "orders": {},
    "cleanup_events": {},
    "firmware_directory": "",
}

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

def find_signer(signature, text) -> None | str:
    signer = None
    for signer_name, key in state["trusted_firmware_signers"].items():
        verification = key.verify(text, signature)
        if verification:
            print(f"Firmware signed by: {signer_name}")
            signer = signer_name
            break
    return signer
