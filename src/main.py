# MicroPython HTTP Web Server for ESP32
#
# Connects to Wi-Fi and starts a simple socket server on port 80.
# Serves a basic HTML page showing the device's IP address.

import network  # type: ignore
import socket
import time
from settings import save_settings, load_settings
from webserver import start_web_server

# --- 1. WiFi Connection Setup ---


def connect_to_wifi(ssid, password):
    # Initializes and connects the ESP32 to the specified Wi-Fi network.
    sta_if = network.WLAN(network.STA_IF)

    if not sta_if.isconnected():
        print("Connecting to network...")
        sta_if.active(True)
        sta_if.connect(ssid, password)

        # Wait up to 10 seconds for connection
        max_wait = 10
        while max_wait > 0:
            if sta_if.isconnected():
                break
            max_wait -= 1
            print(".", end="")
            time.sleep(1)

        if sta_if.isconnected():
            ip_info = sta_if.ifconfig()
            print("\nConnection successful!")
            print("IP Address:", ip_info[0])
            return ip_info[0]  # Return the assigned IP address
        else:
            print("\nConnection failed! Check credentials.")
            return None

    else:
        # Already connected
        ip_info = sta_if.ifconfig()
        print("Already connected. IP:", ip_info[0])
        return ip_info[0]


# --- 2. HTML Content Generator ---


# --- 3. Main Server Loop ---


def main():
    settings = load_settings("settings.json")
    if (settings["ssid"] is None) or (settings["password"] is None):
        print("SSID or password missing in settings.")
        return

    if not settings:
        print("No settings found. Please flash manually.")
        return

    print("Loaded settings:", settings)

    # 3a. Connect to WiFi
    ip_address = connect_to_wifi(settings["ssid"], settings["password"])
    if not ip_address:
        print("WiFi Connection failed. Please flash manually.")
        return

    start_web_server(ip_address, settings)


# --- 4. Initialization ---
if __name__ == "__main__":
    main()
