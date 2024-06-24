# Remote firmware deployment pipeline for Raspberry Pi Pico W

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
  - [ ] Sending firmware
  - [ ] Managing firmware rollbacks
  - [ ] Serving the web portal and APIs

### Update and Rollback

- [ ] **Implement firmware update:**
  - [ ] User orders update - server informs raspi is needed and pushes firmware
  - [ ] Raspberry Pi:
    - [ ] downloads update
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
- [ ] **Test firmware server’s management capabilities**
- [ ] **Validate web portal functionality**
- [ ] **Conduct thorough tests for firmware integrity and rollback**
- [ ] **Test firmware to make sure it can receive OTA updates**

## Sources
- OTA updating inspired by https://github.com/kevinmcaleer/ota
- Documentation
- LLMs such as ChatGPT for readme and documentation help
  - No LLM-generated code was used, except occasional testing boilerplate
