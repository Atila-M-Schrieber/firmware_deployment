from flask import Flask, request, jsonify
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator
from datetime import datetime, timedelta
from threading import Event, Thread
import os
import pgpy
import util
from util import state

time_to_expiry = timedelta(minutes=int(os.environ["UPDATE_EXPIRACY_MINUTES"]))

# Info for update orders - terminated by expiration or completion
# Stored in session["orders"] as a dict with the board_id for one order/board at a time
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

    def is_expired(self):
        return datetime.now() > self.expiration

def remove_order(board_id):
    result = True if state["orders"].pop(board_id, None) else False
    if not result:
        print("Tried to remove Update Order which no longer exists")
    session["cleanup_events"].pop(board_id, None)
    return result

# Thread to remove update order on expiry or success
class CleanupThread(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    board_id: str
    success_event: Event
    sleep_time: float

    def __init__(self, order: UpdateOrder, success_event: Event):
        self.board_id = order.board_id
        self.success_event = success_event
        self.sleep_time = (order.expiration - datetime.now()).total_seconds()

    def run(self) -> None:
        assert self.success_event
        success = self.success_event.wait(timeout=self.sleep_time)
        message = "installed successfully" if success else "timed out"
        print(f"Update {message} on board '{self.board_id}'")
        remove_order(self.board_id)

    # Start the thread
    def start(self):
        state["cleanup_events"][self.board_id] = self.success_event
        thread = Thread(target=self.run, daemon=True)
        thread.start()

def add_order(order: UpdateOrder, overwrite=False):
    success_event = Event()
    thread = CleanupThread(order, success_event)

    if state["orders"][order.board_id] and not overwrite:
        raise Exception(f"Update Order already exists for '{order.board_id}'!\nUse PUT to overwrite.")
    state["orders"][order.board_id] = order
    state["cleanup_events"][order.board_id] = success_event

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

    # create secret

    # create & add_order
    return id

def download(id):
    # check secret

    # create shasum

    # send files & shasum
    return jsonify(id)
