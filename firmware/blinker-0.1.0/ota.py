# OTA
import urequests as requests
import os
import ubinascii
import hashlib
from config import firmware_url

def sha_cheksum(path):
    sha = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            sha.update(data)
    return ubinascii.hexlify(sha.digest()).decode()

# Downloads and unzips the firmware
def download_firmware(firmware, version, board_id, secret):
    download_path = f"{firmware_url}/update/{board_id}"
    print(f"Requesting download from {download_path}...")
    to_send = {
        "firmware": firmware,
        "version": version,
        "board_id": board_id,
        "secret": secret,
    }
    response = requests.get(download_path, json=to_send)
    if response.status_code != 200:
        raise Exception(f"Server responded with: {response.status_code}")
    print("Starting download...")

    with open('firmware.zip', 'wb') as f:
        f.write(response.content)

    return None

def install_firmware(firmware, version, board_id, secret):
    download_firmware(firmware, version, board_id, secret)

    # remove stuff?

    # reboot

    return None

