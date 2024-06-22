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
while wlan.status() < 3:
    print(f"Connection not yet established")
    time.sleep(0.5)

# This (for the purposes of status reporting)
# should be replaced with NAT for actual remote deployment
ip = wlan.ifconfig()[0]

print(f"Connection established\nIP address: {ip}")
led.toggle()

# Blink LED

led_timer = Timer()

def blink(_timer):
    led.toggle()

# (Division of 2 so frequency is in Hertz)
led_timer.init(freq=2 / config.blink_frequency, mode=Timer.PERIODIC, callback=blink)

# Ping server for updates

server_timer = Timer()

def ping_server(timer):
    response = requests.post(
        config.firmware_url,
        data = {
            "firmware": config.firmware,
            "version": config.version,
            "uptime": time.time() - start_time,
        }
    ).json()
    process_response(response, timer)

def process_response(response, timer):
    print(response)
    # if response["update"] == True: stop the timer with timer.deinit() and pull the update (OTA module)

# Defined so it can be called again in case update fails
def init_ping_server(timer):
    timer.init(freq=config.polling_rate, mode=Timer.PERIODIC, callback=ping_server)
    


