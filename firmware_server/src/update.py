from typing import Optional
from flask import Flask, json, request, send_file
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator
from datetime import datetime, timedelta
import time
from threading import Event, Thread
import io
import tarfile
import os
import pgpy
import hashlib
import util
from util import FirmwareInfoRequest, available_firmware, state

time_to_expiry = timedelta(minutes=int(os.environ["UPDATE_EXPIRACY_MINUTES"]))

# Info for update orders - terminated by expiration or completion
# Stored in state["orders"] as a dict with the board_id for one order/board at a time
class UpdateOrder(BaseModel):
    board_id: str
    firmware: str
    version: str
    secret: str
    expiration: datetime = datetime.now()

    # Automatic expiration creation
    def __init__(self, **data):
        super().__init__(**data)
        self.expiration = datetime.now() + time_to_expiry;

# SHOULD ONLY BE USED BY CLEANUP THREAD - activate through setting the event
def remove_order(board_id):
    result = True if state["orders"].pop(board_id, None) else False
    if not result:
        print("Tried to remove Update Order which no longer exists")
    state["cleanup_events"].pop(board_id, None)
    return result

# Thread to remove update order on expiry or success
# Since one thread only touches a single and unique key in the state dict,
# race conditions should not happen
class CleanupThread():
    board_id: str
    cleanup_event: Event
    sleep_time: float

    def __init__(self, order: UpdateOrder, cleanup_event: Event):
        self.board_id = order.board_id
        self.cleanup_event = cleanup_event
        self.sleep_time = (order.expiration - datetime.now()).total_seconds()

    def run(self) -> None:
        assert self.cleanup_event
        success = self.cleanup_event.wait(timeout=self.sleep_time)
        message = "installed successfully" if success else "timed out"
        print(f"Update {message} on board '{self.board_id}'")
        remove_order(self.board_id)

    # Start the thread
    def start(self):
        state["cleanup_events"][self.board_id] = self.cleanup_event
        thread = Thread(target=self.run, daemon=True)
        thread.start()

def add_order(order: UpdateOrder, overwrite=False):
    cleanup_event = Event()
    thread = CleanupThread(order, cleanup_event)

    if order.board_id in state["orders"] and not overwrite:
        raise Exception(f"Update Order already exists for '{order.board_id}'!\nUse PUT to overwrite.")
    elif overwrite:
        # Shut down the previous thread before starting this one to avoid races
        # This currently acts the same as order_complete
        state["cleanup_events"][order.board_id].set()
        time.sleep(1)

    state["orders"][order.board_id] = order
    state["cleanup_events"][order.board_id] = cleanup_event

    thread.start()

def order_complete(board_id):
    state["cleanup_events"][board_id].set()

class OrderRequest(BaseModel): 
    firmware: str
    version: str
    board_id: str

def order(id):
    # process request
    if not request.files:
        print("Order without signature file received.")
        return "Include a signature file (sig.pgp or sig.asc) in your request", 400
    try:
        order_dict = request.form.to_dict()
        order_dict["board_id"] = id
        order = OrderRequest.model_validate(order_dict)
    except:
        print("Bad update order received")
        return "Bad update order request structure", 400
    
    # extract signature
    try:
        signature, other_files = util.sort_files()
    except Exception as e:
        return e.args

    if other_files:
        print("Extra files? How peculiar.")

    if not signature:
        print("Update ordered without a signature")
        return "No signature file found!", 422

    # Verify signature
    order_signable = f"{order.firmware}-{order.version}-{order.board_id}"
    firmware_signer = util.find_signer(signature, order_signable)
    
    if not firmware_signer:
        print("Bad signature!")
        return "Invalid or unknown signature", 401
    
    # check for known ids
    if not order.board_id in state["known_ids"] + state["known_test_ids"]:
        print(f"Order given for unknown board ID: {order.board_id}")
        return f"Unknown board ID: {order.board_id}", 404

    is_test = order.board_id in state["known_test_ids"]
    if is_test:
        print("Test ID detected. Remember to deal with test ID's before production deployment")

    # check for firmware
    firmware = available_firmware(FirmwareInfoRequest(firmware=order.firmware))
    print(list(firmware.listvalues()))#[0])

    if not firmware and not (is_test and order.firmware == "test"):
        print(f"No firmware '{order.firmware}' was found.")
        return f"No firmware '{order.firmware}' was found.", 404

    # check for version
    if (is_test and order.version != "1.0.0") or\
            (not is_test and order.version not in list(firmware.listvalues())[0]):
        print(f"Bad version: '{order.firmware}-{order.version}' was not found.")
        return f"Bad version: '{order.firmware}-{order.version}' was not found.", 404

    # create secret
    secret = hashlib.md5(bytes(signature)).hexdigest()
    order_dict["secret"] = secret

    # create & add_order
    overwrite = request.method == "PUT" # POST doesn't overwrite, PUT does
    update_order = UpdateOrder(**order_dict)

    try:
        add_order(update_order, overwrite)
    except Exception as e:
        print(f"Exception: {e}")
        return str(f"Exception: {e}"), 415

    return secret

def calculate_shasum(file_path):
    sha = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(4096), b''):
            print(f"Block (len {len(block)}): {block}")
            sha.update(block)
    return sha.hexdigest()

class Respond(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __call__(self):
        return self.message, self.status_code

class BoardUpdateRequest(BaseModel):
    firmware: str # misspelled frimware...
    version: str
    board_id: str
    secret: str

    def check_request_get_order(self, id, testing, request_type):
        if id != self.board_id:
            print(f"{request_type.capitalize()} URL is incorrect")
            raise Respond("Mismatch in URL id and reported board id", 400)
        
        # check if ID is known
        if not self.board_id in state["known_ids"] and not self.board_id in state["known_test_ids"]:
            print(f"{request_type.capitalize()} request received from unknown ID: {self.board_id}")
            raise Respond(f"Unknown ID: {self.board_id}", 401)
    
        # check if id has an update order pending
        test_pass = self.board_id == "-2"
        if self.board_id not in state["orders"] and not test_pass:
            print(f"Known board '{self.board_id}'")
            raise Respond("You do not have an update order.", 406)

        order = state["orders"][self.board_id] # Should have used a real test suite
    
        # check secret
        if self.secret != (order.secret if not testing else "test_secret"):
            print(f"Board with update order but bad secret '{self.board_id}'")
            raise Respond("You have an update order, but that's the wrong secet", 403)

        return order

def download(id):
    try:
        dl_req = BoardUpdateRequest.model_validate(request.json, strict=False)
    except ValidationError as e:
        print(f"Badly formatted download request. {str(e)}")
        return "Bad download request structure", 400

    testing = dl_req.board_id in state["known_test_ids"]

    try:
        order = dl_req.check_request_get_order(id, testing, "download")
    except Respond as r:
        return r()

    if testing:
        return {}

    # check if the board already has that version installed
    if dl_req.firmware == order.firmware and dl_req.version == order.version:
        print(f"This version ('{state["firmware_directory"]}') is already installed on the board")
        return f"This version is already installed!", 304

    # load firmware (known to exist, checked in update ordering process)
    firmware_dir = os.path.join(state["firmware_directory"], f"{order.firmware}-{order.version}")
    files = os.listdir(firmware_dir)

    shasums = {}

    # construct tar archive and calculate shasums
    tar_bytes = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes, mode='w') as tar:
        for file in files:
            path = os.path.join(firmware_dir, file)
            if os.path.isfile(path):
                shasums[file] = calculate_shasum(path)
                tar.add(path, arcname=file)
        # include shasums in archive (can't really send separately unless I want to do multipart)
        manifest = json.dumps(shasums).encode('utf-8')
        manifest_info = tarfile.TarInfo(name="manifest.json")
        manifest_info.size = len(manifest)
        tar.addfile(manifest_info, io.BytesIO(manifest))

    tar_bytes.seek(0)

    # send archive
    return send_file(tar_bytes, mimetype='application/tar')

def delete_order(id):
    try:
        dl_req = BoardUpdateRequest.model_validate(request.json, strict=False)
    except ValidationError as e:
        print(f"Badly formatted order delete request. {str(e)}")
        return "Bad order delete request structure", 400

    testing = dl_req.board_id in state["known_test_ids"]

    try:
        dl_req.check_request_get_order(id, testing, "download")
    except Respond as r:
        return r()
    
    state["cleanup_events"][id].set()

    # check stuff
    return "Order deleted"
