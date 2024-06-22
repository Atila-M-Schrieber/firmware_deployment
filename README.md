# Remote firmware deployment pipeline for Raspberry Pi Pico W

## Roadmap

### Firmware Server

- [x] **Create server Docker image**
- [x] **Set up Raspberry Pi with initial (non-OTA) firmware that reports status**
- [ ] **Write server software to handle:**
  - [ ] Receiving raspi statuses
  - [ ] Storing and sending firmware
  - [ ] Managing firmware rollbacks
  - [ ] Serving the web portal and APIs

### Update and Rollback

- [ ] **Implement firmware update:**
  - [ ] Server detects that update is needed and pushes firmware
  - [ ] Raspberry Pi:
    - [ ] downloads update
    - [ ] verifies firmware
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

- [ ] **Test connectivity and basic functionality of Raspberry Pi devices**
- [ ] **Test firmware server’s management capabilities**
- [ ] **Validate web portal functionality**
- [ ] **Conduct thorough tests for firmware integrity and rollback**
- [ ] **Test firmware to make sure it can receive OTA updates**

## Sources
- OTA updating inspired by https://github.com/kevinmcaleer/ota
- Documentation
- LLMs such as ChatGPT for readme and documentation help
  - No LLM-generated code was used
