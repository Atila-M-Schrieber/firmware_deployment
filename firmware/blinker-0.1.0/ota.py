# OTA
import tarfile
import urequests as requests
import uos
import json
import ubinascii
import hashlib
from config import firmware_url

def calculate_shasum(path):
    sha = hashlib.sha256()
    with open(path, 'rb') as f:
        while True: # didn't work?? : for block in iter(lambda: f.read(4096), b''):
            block = f.read(4096)
            if not block:
                break
            sha.update(block)
    return ubinascii.hexlify(sha.digest()).decode()
    # return sha.hexdigest() # allegedly hexdigest works, but errors 

def rmdir(path):
    for entry in uos.listdir(path):
        entry_path = f"{path}/{entry}"
        if entry[1] == 0x4000: # dir
            rmdir(entry_path)
        else:
            print(f"removing {entry_path}")
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

    print(response.headers)
    with open('firmware.tar', 'wb') as f:
        f.write(response.content)

    # Extract the archive
    uos.mkdir('firmware')
    sha_sums = {}
    data = tarfile.TarFile('firmware.tar')
    while True:
        i = data.next()
        print(i)
        if not i:
            break
        print(i.name)
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
        if calculate_shasum(filename) != expected_sha:
            print(f"SHA cheksum does not match for {filename}")
            raise Exception(f"SHA cheksum does not match for {filename}")

    return None

def install_firmware(firmware, version, board_id, secret):
    download_firmware(firmware, version, board_id, secret)

    # remove stuff?

    # reboot

    return None

