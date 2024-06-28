# Remote firmware deployment pipeline for Raspberry Pi Pico W

## Usage:

### General usage:
- This assumes you are running the server on your own machine
  - Deploying to a production server would involve a few changes
- Launching the server:
  - Navigate to the `firmware_server` directory
  - Build the Docker image: `docker build -t firmware_server .`
  - Run the Docker image: `docker run -it --rm -p 8000:8000 firmware_server`
- Configuring the boards:
  - Navigate to the `firmware` directory
  - Run the shell script `configure_boards.sh` and input the URL, wlan ssid and password, and board_id
    - For multiple devices you will have to update `secrets.py` to change the board_id
    - For devices on multiple networks you will have to update `secrets.py` to change the wlan configuration
  - Flashing a board:
    - In a production environment, this can simply be automated.
    - Connect a board to the machine, and install MicroPython
    - Navigate to your desired firmware directory (`{firmware name}-{firmware version}`)
      - For example: `blinker-0.1.0`
    - Modify the `secrets.py` file (this is not updated OTA)
    - Using `mpremote`, copy the firmware files to the board: `mpremote cp *.py :`
    - Hard-reset the device (the soft reset is insufficient with running firmware): `mpremote reset`
    - To read output, enter the REPL: `mpremote repl`
    - All-in-one: `mpremote cp *.py : && mpremote reset && sleep 1 && mpremote repl`
    - Repeat this process for each board
- Interacting with the server through the API:
  - Endpoint Testing:
    - Simply run the `test.py` file in the `firmware_server` directory
      - If the server is running on a different port (not 8000) or a remote machine, change the base_url
  - Prequisites to using the upload and update order scripts:
    - Navigate to the `firmware` directory
    - Import the example private key: `gpg --import private.asc`
    - Find the key fingerprint: `gpg --list-secret-keys | grep -B 1 'John Doe' | grep -Eo '([0-9A-F]{40})'`
  - Uploading firmware to the server: 
    - Currently this is the only way to put firmware on the server,
      but in a production environment the docker image would mount a volume containing the known
      firmware, and pull new firmware from a trusted source (most likely a git repository)
    - Run the script `upload_firmware.sh` with the following arguments: 
      - `--firmware {firmware name}`
      - `--version {firmware version}`
        - Alternatively directory can be given: `--directory {firmware name}-{firmware version}`
      - `--url {firmware server url}`
      - `--gpg-fingerprint {the gpg fingerprint of the example key}`
      - For example: `sh ./upload_frimware.sh -d blinker-0.1.0 -g {your fingerprint}
        --url http://localhost:8000/firmware`
      - To see the boards updating live, upload both blinker versions
  - Run the script `order_update.sh`:
    - This script orders an update on a specific board. The server notifies the board on its
      next ping that it has an update waiting, then the board requests the update, installs it,
      and informs the server of a successful install.
    - Run the script `order_update.sh` with the following arguments:
      - `--firmware {firmware name}`
      - `--version {firmware version}`
      - `--board_id {the board_id of the board to update}`
      - `--url {firmware server url}`
      - `--gpg-fingerprint {the gpg fingerprint of the example key}`
      - For example: `sh ./order_update.sh -f blinker -v 0.1.0 -g {your fingerprint}
        --url http://localhost:8000/firmware -b {your board_id}`
      - You can rapidly update the board from `blinker-0.1.0` to `0.1.1` and rollback the update
        by simply changing the versions.

## Theoretical usecase:
- Board (Pi Pico W in this case) is flashed with MicroPython, and the initial firmware is loaded.
  - A secrets.py file must also be configured for each Board
    - ID, wlan ssid and password
- Board connects to network and runs its firmware (in this case just blinking)
  - Board regularly pings firmware server with status
  - If there is an update ready to download for the device,
    the server indicates this in the response
- Client can upload new firmware to the server
  - Uploaded firmware must be sent alongside a PGP signature
  - Signature is checked against list of trusted public keys
  - Collisions are prevented
  - (Integrating something like Git would be a much better choice in production)
- When the Client wants to update the firmware on a Board, the Board receives a 'time to update'
  response on its next status ping.
  - Client a POST API call to `/firmware/update/<board_id>`,
    with the firmware and version to update to
    - Request contains signature for `firmware_name-version-board_id` for authentication
  - Once the board receives the update command, it sends a GET request to the same endpoint
    - Firmware is downloaded, checked against shasum (no key verification for the Board)
    - Board installs the update, reboots into it
- Rollbacks are handled in the exact same way as updates.
- Ideally this is managed through a fancy WebUI

- Client APIs are form-formatted for the sake of the WebUI
- Board APIs are JSON-formatted

- What could be done better:
  - Using a proper test suite would have made some of the code cleaner
  - Should use logging instead of printing
  - More universalized validation for less boilerplate

## Roadmap

### Firmware Server

- [x] **Create server Docker image**
- [x] **Set up Raspberry Pi with initial (non-OTA) firmware that reports status**
- [ ] **Write (server) software to handle:**
  - [x] Receiving raspi statuses
  - [x] Script to sign, send files to server
    - Note: all firmware files must be flat - just .py files, no directories
  - [x] Storing/uploading firmware
    - Note: pgpy not being compatible with EdCSA wasted a lot of time
  - [x] Sending/downloading firmware
  - [x] Send install confirmation to server in status message
  - [x] Managing firmware rollbacks
  - [ ] Serving the web portal and APIs

### Update and Rollback

- [x] **Implement firmware update:**
  - [x] User orders update
  - [x] server informs raspi that it needs to update
  - [x] Raspberry Pi:
    - [x] downloads update
    - [x] verifies firmware - SHASUM only, not sinature
      - Something is wrong with both uhashlib and micropython-hashlib
        implementations of sha256, so the 'backbone' is there,
        but no exceptions are raised for mismatched cheksums.
    - [x] installs firmware
    - [x] reboots with new firmware
- [x] **Implement rollback**
  - [x] Should be same as update

### Web Portal

- [ ] **Design and implement the web portal**
  - [ ] Interface for viewing Raspberry Pi statuses
  - [ ] Functionality for uploading new firmware versions
    - [ ] Integration of a signing key for security

### Testing and Validation

- [x] **Test connectivity and basic functionality of Raspberry Pi devices**
- [x] **Test firmware server’s management capabilities**
  - Sometimes very annoying, should have used a proper test suite
- [ ] **Validate web portal functionality**
- [x] **Conduct tests for firmware integrity and rollback**

## Sources
- OTA updating inspired by https://github.com/kevinmcaleer/ota
- Documentation
- LLMs such as ChatGPT for readme and documentation help
  - No LLM-generated code was used, except occasional testing boilerplate
