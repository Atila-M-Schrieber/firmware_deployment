from flask import Flask, request, jsonify, session
from pydantic import BaseModel, ValidationError, model_validator
from datetime import datetime, timedelta
import os
from threading import Event, Thread

time_to_expiry = timedelta(minutes=int(os.environ["UPDATE_EXPIRACY_MINUTES"]))
session["orders"] = {}
session["cleanup_events"] = {}

# Info for update orders - terminated by expiration or completion
# Stored in session["orders"] as a dict with the secret as the key for uniqueness
class UpdateOrder(BaseModel):
    board_id: str
    firmware: str
    version: str
    secret: str # given from signing key, unique
    expiration: datetime = datetime.now()

    # Automatic expiration creation
    def __init__(self, **data):
        super().__init__(**data)
        self.expiration = datetime.now() + time_to_expiry;

    def is_expired(self):
        return datetime.now() > self.expiration

def remove_order(secret):
    result = True if session["orders"].pop(secret, None) else False
    if not result:
        print("Tried to remove Update Order which no longer exists")
    session["cleanup_events"].pop(secret, None)
    return result

# Thread to remove update order on expiry or success
class CleanupThread(BaseModel):
    secret: str
    board_id: str
    success_event: Event
    sleep_time: float

    def __init__(self, order: UpdateOrder, success_event: Event):
        self.secret = order.secret
        self.board_id = order.board_id
        self.success_event = success_event
        self.sleep_time = (order.expiration - datetime.now()).total_seconds()

    def run(self) -> None:
        success = self.success_event.wait(timeout=self.sleep_time)
        message = "installed successfully" if success else "timed out"
        print(f"Update {message} on board '{self.board_id}'")
        remove_order(self.secret)

    # Start the thread
    def start(self):
        session["cleanup_events"][self.secret] = self.success_event
        thread = Thread(target=self.run, daemon=True)
        thread.start()

def add_order(order: UpdateOrder):
    success_event = Event()
    thread = CleanupThread(order, success_event)

    session["orders"][order.secret] = order
    session["cleanup_events"][order.secret] = success_event

    thread.start()

def order_complete(secret):
    session["cleanup_events"][secret].set()

def order(id):
    return id

def download(id):
    return jsonify(id)
