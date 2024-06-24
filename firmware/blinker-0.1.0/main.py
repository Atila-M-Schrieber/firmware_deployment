from machine import Pin, Timer
import time
import network
import urequests as requests
import json

import secrets
import config

led = Pin('LED', Pin.OUT)
start_time = time.time()

# Connect to network

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

wlan.connect(secrets.wifi['ssid'], secrets.wifi['password'])

# LED on continuously until connection is established
led.on()
counter = 0
while wlan.status() < 3:
    if counter == 0:
        print("Connection not yet established", end='')
        counter += 1
    else:
        print('.', end='')
    time.sleep(0.2)
print()

# This (for the purposes of status reporting)
# should be replaced with NAT for actual remote deployment
ip = wlan.ifconfig()[0]

print(f"Connection established\nIP address: {ip}")
led.toggle()

# Blink LED

led_timer = Timer()

def blink(_timer):
    led.toggle()

led_timer.init(freq=2 * config.blink_frequency, mode=Timer.PERIODIC, callback=blink)

# Ping server for updates

server_timer = Timer()

def ping_server(timer):
    try:
        response = requests.post(
            f"{config.firmware_url}/status",
            json = {
                "firmware": config.firmware,
                "version": config.version,
                "board_id": secrets.board_id,
                "uptime": time.time() - start_time,
            }
        )
        print("Pinged server.")
        process_response(response, timer)
    except OSError as e:
        print(f"Ping failed: {e}")

    # Visually show ping
    led.toggle()
    time.sleep(0.05)
    led.toggle()
    time.sleep(0.05)
    led.toggle()

def process_response(response, timer):
    print(response.json())
    # if response["update"] == True: stop the timer with timer.deinit() and pull the update (OTA module)

# Defined so it can be called again in case update fails
def init_ping_server(timer):
    timer.init(freq=1/config.polling_rate, mode=Timer.PERIODIC, callback=ping_server)
    
init_ping_server(server_timer)
