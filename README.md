# Remote firmware deployment pipeline for Raspberry Pi Pico W

Theoretical usecase:
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
- Ideally this is managed through a fancy WebUI - I will make a basic one.

- Client APIs are form-formatted for the sake of the WebUI
- Board APIs are JSON-formatted

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
  - [ ] Send install confirmation to server in status message
  - [ ] Managing firmware rollbacks
  - [ ] Serving the web portal and APIs

### Update and Rollback

- [ ] **Implement firmware update:**
  - [x] User orders update
  - [x] server informs raspi that it needs to update
  - [ ] Raspberry Pi:
    - [x] downloads update
    - [ ] verifies firmware - SHASUM only, not sinature
    - [ ] installs firmware
    - [ ] reboots with new firmware
- [ ] **Implement rollback**
  - [ ] Should be same as update

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
- [ ] **Conduct thorough tests for firmware integrity and rollback**
- [ ] **Test firmware to make sure it can receive OTA updates**

## Sources
- OTA updating inspired by https://github.com/kevinmcaleer/ota
- Documentation
- LLMs such as ChatGPT for readme and documentation help
  - No LLM-generated code was used, except occasional testing boilerplate
