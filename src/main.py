# MicroPython HTTP Web Server for ESP32
#
# Connects to Wi-Fi and starts a simple socket server on port 80.
# Serves a basic HTML page showing the device's IP address.

from clock import clock_task
import network  # type: ignore
import time
from settings import load_settings, save_settings
from webserver import start_web_server
import _thread
import globals

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
    globals.SETTINGS = load_settings("settings.json")
    if (globals.SETTINGS["ssid"] is None) or (globals.SETTINGS["password"] is None):
        globals.LCD_MESSAGE = "No WiFi settings!\nFlash manually."
        print("No WiFi settings found. Please flash manually.")
        return

    if not globals.SETTINGS:
        globals.LCD_MESSAGE = "No WiFi settings!\nFlash manually."
        print("No WiFi settings found. Please flash manually.")
        return

    print("Loaded settings:", globals.SETTINGS)

    if ("summer" not in globals.SETTINGS) or ("winter" not in globals.SETTINGS):
        globals.SETTINGS["summer"] = 2
        globals.SETTINGS["winter"] = 1
        save_settings("settings.json", globals.SETTINGS)

    _thread.start_new_thread(clock_task, ())

    globals.IP = connect_to_wifi(globals.SETTINGS["ssid"], globals.SETTINGS["password"])
    if not globals.IP:
        globals.LCD_MESSAGE = "WiFi Conn. failed!\nFlash manually."
        print("WiFi Connection failed. Please flash manually.")
        return

    globals.LCD_MESSAGE = None

    start_web_server()


# --- 4. Initialization ---
if __name__ == "__main__":
    main()
