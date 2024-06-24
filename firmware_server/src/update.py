from typing import Optional
from flask import Flask, request, jsonify
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator
from datetime import datetime, timedelta
import time
from threading import Event, Thread
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
    print(order)
    thread = CleanupThread(order, cleanup_event)

    if order.board_id in state["orders"] and not overwrite:
        raise Exception(f"Update Order already exists for '{order.board_id}'!\nUse PUT to overwrite.")
    else:
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

    if not firmware and not (is_test and order.firmware == "test"):
        print(f"No firmware '{order.firmware}' was found.")
        return f"No firmware '{order.firmware}' was found.", 404

    # check for version
    if not order.version in firmware.values() and not (is_test and order.version == "1.0.0"):
        print(f"Bad version: '{order.firmware}-{order.version}' was not found.")
        return f"Bad version: '{order.firmware}-{order.version}' was not found.", 404

    # create secret
    secret = hashlib.md5(bytes(signature)).hexdigest()
    order_dict["secret"] = secret

    # Return good if test
    #if is_test:
        #return secret

    # create & add_order
    overwrite = request.method == "PUT" # POST doesn't overwrite, PUT does
    update_order = UpdateOrder(**order_dict)

    try:
        add_order(update_order, overwrite)
    except Exception as e:
        print(f"Exception: {e}")
        return str(f"Exception: {e}"), 415

    return secret

def download(id):
    # check secret

    # create shasum

    # send files & shasum
    return jsonify(id)
