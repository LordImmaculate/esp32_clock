import socket
import time
from machine import Pin  # type: ignore
import globals

from settings import save_settings


def _url_decode(s):
    # simple URL-decode: replace + with space and %XX hex sequences
    s = s.replace("+", " ")
    res = ""
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "%" and i + 2 < len(s):
            try:
                hexv = s[i + 1 : i + 3]
                res += chr(int(hexv, 16))
                i += 3
                continue
            except Exception:
                # if malformed, keep as-is
                pass
        res += ch
        i += 1
    return res


def _parse_form(body):
    # body like: "ssid=My%20Net&password=p%40ssword"
    params = {}
    for pair in body.split("&"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            params[_url_decode(k)] = _url_decode(v)
    return params


def start_web_server():
    led = Pin(2, Pin.OUT)  # On-board LED for ESP32
    # AF_INET = IPv4, SOCK_STREAM = TCP
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 80))  # Bind to all interfaces on port 80 (standard HTTP)
    s.listen(5)  # Listen for up to 5 pending connections

    if globals.SETTINGS is None:
        globals.SETTINGS = {"ssid": ""}

    print("Web Server started. Listening on http://" + globals.IP)
    led.on()
    while True:
        conn = None
        try:
            # Wait for a client connection
            conn, addr = s.accept()
            print("Got a connection from %s" % str(addr))

            # Read the incoming request (read up to 2048 bytes initially)
            request_bytes = conn.recv(2048)
            if not request_bytes:
                conn.close()
                continue
            request = request_bytes.decode("utf-8", "ignore")
            request_line = request.split("\r\n")[0]
            print("Request:", request_line)

            # parse request line
            parts = request_line.split()
            method = parts[0] if len(parts) > 0 else "GET"
            path = parts[1] if len(parts) > 1 else "/"

            # If POST, try to read full body based on Content-Length
            body = ""
            if method.upper() == "POST":
                headers, _, maybe_body = request.partition("\r\n\r\n")
                body = maybe_body
                # check Content-Length
                cl = 0
                for h in headers.split("\r\n")[1:]:
                    if ":" in h:
                        name, val = h.split(":", 1)
                        if name.lower().strip() == "content-length":
                            try:
                                cl = int(val.strip())
                            except Exception:
                                cl = 0
                            break
                # if body shorter than content-length, read the rest
                body_bytes = body.encode("utf-8")
                to_read = cl - len(body_bytes)
                while to_read > 0:
                    more = conn.recv(1024)
                    if not more:
                        break
                    body_bytes += more
                    to_read = cl - len(body_bytes)
                body = body_bytes.decode("utf-8", "ignore")

            # Handle save route for form POST
            if method.upper() == "POST" and path.startswith("/save"):
                form = _parse_form(body)
                ssid = form.get("ssid", "")
                password = form.get("password", "")
                summer = int(form.get("summer", 2))
                winter = int(form.get("winter", 1))

                globals.SETTINGS = {
                    "ssid": ssid,
                    "password": password,
                    "summer": summer,
                    "winter": winter,
                }

                save_settings("settings.json", globals.SETTINGS)
                print(
                    f"Saved settings: SSID={ssid}, PASSWORD={password}, SUMMER={summer}, WINTER={winter}"
                )

                # Respond with a simple redirect back to root (or a confirmation)
                response_header = (
                    "HTTP/1.1 303 See Other\r\nLocation: /\r\nConnection: close\r\n\r\n"
                )
                conn.send(response_header.encode())
                conn.close()
                continue

            # Generate the HTML content (use current settings if available)
            if isinstance(globals.SETTINGS, dict):
                ssid_value = globals.SETTINGS.get("ssid", "")
                pw_value = globals.SETTINGS.get("password", "")
                summer_value = globals.SETTINGS.get("summer", 1)
                winter_value = globals.SETTINGS.get("winter", 0)
            else:
                ssid_value = getattr(globals.SETTINGS, "ssid", "")
                pw_value = getattr(globals.SETTINGS, "password", "")
                summer_value = getattr(globals.SETTINGS, "summer", 1)
                winter_value = getattr(globals.SETTINGS, "winter", 0)

            response_html = web_page(ssid_value, pw_value, summer_value, winter_value)

            # Construct the HTTP Response Header
            response_header = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n"

            # Send the header and the HTML content
            conn.send(response_header.encode())
            conn.send(response_html.encode())

            # Close the connection
            conn.close()

        except OSError as e:
            print("Socket error:", e)
            try:
                if conn:
                    conn.close()
            except Exception:
                pass
            time.sleep(
                1
            )  # Small delay to avoid hammering the connection if errors persist


def web_page(ssid, password, summer, winter):
    try:
        html = open("website.html", "r").read()
    except Exception:
        # Fallback minimal page if website.html is missing or can't be read
        html = """HTML Missing"""
    html = html.replace("{SSID}", ssid)
    html = html.replace("{PASSWORD}", password)
    html = html.replace("{SUMMER}", str(summer))
    html = html.replace("{WINTER}", str(winter))
    return html
