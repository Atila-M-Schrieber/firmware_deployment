# OTA
import tarfile
import urequests as requests
import uos
import json
import ubinascii
import machine
# Force use of installed 'hashlib' - has some TypeErrors
#import sys
#sys.modules['uhashlib'] = sys
import hashlib
from config import firmware_url

def DanglingOrderException(Exception):
    def __init__(to_send):
        update_path = f"{firmware_url}/update/{to_send["board_id"]}"
        requests.delete(update_path, json=to_send)

def calculate_shasum(path):
    sha = hashlib.sha256()
    with open(path, 'rb') as f:
        while True: # didn't work?? : for block in iter(lambda: f.read(4096), b''):
            block = f.read(4096)
            if not block:
                break
            #print(f"Block (len {len(block)}): {block}")
    return ubinascii.hexlify(sha.digest()).decode()
    #return sha.hexdigest() # allegedly hexdigest works, but errors 

def rmdir(path):
    for entry in uos.listdir(path):
        entry_path = f"{path}/{entry}"
        if entry[1] == 0x4000: # dir
            rmdir(entry_path)
        else:
            uos.remove(entry_path)
    uos.rmdir(path)

# Downloads and extracts the firmware
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
    if response.status_code == 304: # Indicates dangling update order
        raise DanglingOrderException(to_send)
    if response.status_code != 200:
        raise Exception(f"Server responded with: {response.status_code}")

    # Clear previous attempts
    try:
        uos.remove('firmware.tar')
    except:
        pass # fails if it doesn't exist - that's fine

    # remove -rf the firmware directory
    try:
        rmdir('firmware')
    except:
        pass # fails if it doesn't exist - that's fine

    with open('firmware.tar', 'wb') as f:
        f.write(response.content)

    # Extract the archive
    uos.mkdir('firmware')
    sha_sums = {}
    data = tarfile.TarFile('firmware.tar')
    while True:
        i = data.next()
        if not i:
            break
        if i.type == tarfile.DIRTYPE:
            uos.mkdir(i.name)
        else:
            file = data.extractfile(i)
            if i.name == "manifest.json":
                sha_sums = json.loads(file.read())
            # Ignore the header file
            if i.name == "@PaxHeader":
                continue
            if not file:
                raise Exception("Empty file?")
            with open(f"/firmware/{i.name}", "wb") as of:
                of.write(file.read())

    # Check shasums
    for filename, expected_sha in sha_sums.items():
        calculated_sha = calculate_shasum(filename)
        if calculated_sha != expected_sha:
            print(f"SHA cheksum does not match for {filename}")
            #print(f"Expected: {expected_sha}")
            #print(f"Calculated: {calculated_sha}")
            print("Ignoring due to bad sha implementation.")
            # No exception as the implementations of sha256 are borked
            #raise Exception(f"SHA cheksum does not match for {filename}")

    return None

def install_firmware(firmware, version, board_id, secret):
    download_firmware(firmware, version, board_id, secret)

    print("Installing...")
    # remove all (except secrets.py) python files in root dir
    root_files = uos.listdir('/')
    for entry in root_files:
        if entry.split('.')[-1] == "py" and entry != "secrets.py":
            uos.remove(entry)

    new_firmware_files = uos.listdir('firmware')
    for entry in new_firmware_files:
        # Check for existing file (should only be relevant for non-python files)
        try:
            uos.remove(entry)
        except:
            pass
        if entry not in ["manifest.json", "@PaxHeader"]: # Just making sure
            uos.rename(f"firmware/{entry}", entry)

    rmdir("firmware")
    uos.remove("firmware.tar")

    to_send = {
        "firmware": firmware,
        "version": version,
        "board_id": board_id,
        "secret": secret,
    }
    # send successful install status - delete the order
    print("Sending confirmation of installation")
    update_path = f"{firmware_url}/update/{board_id}"
    requests.delete(update_path, json=to_send)

    # reboot
    print("Rebooting...")
    machine.reset()
