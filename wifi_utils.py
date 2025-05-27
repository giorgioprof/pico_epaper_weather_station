import network
import utime
import time
import json
from machine import reset

AP_SSID = "WeatherStation"  # Access Point name when in setup mode
AP_PASSWORD = "setupmode"  # Password for setup mode (at least 8 characters)
CONFIG_MODE_TIMEOUT = 300

class WiFiCls():
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
    
    @property
    def connected(self):
        return network.WLAN(network.STA_IF).isconnected()
    
    def disconnect(self):
        """Disconnect from WiFi and turn off the WiFi module to save power"""
        try:
            wlan = network.WLAN(network.STA_IF)
            if wlan.active():
                wlan.active(False)
                print("WiFi disconnected")
                return True
        except Exception as e:
            print(f"Error disconnecting WiFi: {e}")
            return False
        return True
    
    def connect(self):
        # Give the WiFi hardware time to initialize
        utime.sleep(3)
        
        wlan = network.WLAN(network.STA_IF)
        
        # First, make sure the interface is inactive before reconfiguring
        wlan.active(False)
        utime.sleep(1)
        
        # Now activate it with a clean slate
        wlan.active(True)
        utime.sleep(1)
        
        # Try to connect
        print(f"Connecting to {self.ssid}...")
        if not wlan.isconnected():
            try:
                wlan.connect(self.ssid, self.password)
                
                # Longer wait for connection with better timeout handling
                max_wait = 30  # Increased from 20 to 30 seconds
                while max_wait > 0:
                    if wlan.isconnected():
                        break
                    
                    # Check for specific error states
                    status = wlan.status()
                    if status == network.STAT_WRONG_PASSWORD:
                        print("Wrong WiFi password!")
                        return False
                    elif status == network.STAT_NO_AP_FOUND:
                        print("WiFi network not found!")
                        return False
                    elif status == network.STAT_CONNECT_FAIL:
                        print("Connection failed!")
                        return False
                    
                    max_wait -= 1
                    print(f"Waiting for connection... Status: {status}")
                    utime.sleep(1)
            except Exception as e:
                print(f"WiFi connection error: {e}")
                return False
        
        if wlan.isconnected():
            print("Connected to WiFi")
            print("IP:", wlan.ifconfig()[0])
            return True
        else:
            print("WiFi connection failed")
            print("Status:", wlan.status())
            
            # Add this retry logic for better reliability
            print("Retrying connection once more...")
            wlan.disconnect()
            utime.sleep(2)
            wlan.connect(self.ssid, self.password)
            
            # Give it one more chance with a longer timeout
            max_wait = 15
            while max_wait > 0:
                if wlan.isconnected():
                    print("Connected on second attempt!")
                    print("IP:", wlan.ifconfig()[0])
                    return True
                max_wait -= 1
                print("Still waiting...")
                utime.sleep(1)
                
            print("WiFi connection failed after retry")
            return False

class WiFiSetup():
    def __init__(self, epd, wifi_file):
        self.epd = epd
        self.wifi_file = wifi_file
        
    def setup_web_server(self):
        """Setup a web server for configuration"""
        import socket
        
        # Create a socket and bind to address
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(('0.0.0.0', 80))
            s.listen(5)
            s.settimeout(2)  # 2 second timeout for accepting connections
        except OSError as ex:
            print(f"Error starting AP: {ex}")
            reset()
        
        print("Web server started")
        
        # HTML template for the configuration page
        # HTML template for the configuration page
        html = """<!DOCTYPE html>
        <html>
        <head>
            <title>Weather Station Setup</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial; margin: 0; padding: 20px; }
                h1 { color: #0066cc; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; }
                input[type="text"], input[type="password"] { width: 100%; padding: 8px; box-sizing: border-box; }
                button { background-color: #0066cc; color: white; border: none; padding: 10px 15px; cursor: pointer; }
                .message { margin-top: 20px; padding: 10px; background-color: #e6f7ff; border-left: 4px solid #0066cc; }
            </style>
        </head>
        <body>
            <h1>Weather Station Wi-Fi Setup</h1>
            <form method="POST" action="/save">
                <div class="form-group">
                    <label for="ssid">Wi-Fi Name (SSID):</label>
                    <input type="text" id="ssid" name="ssid" required>
                </div>
                <div class="form-group">
                    <label for="password">Wi-Fi Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit">Save Configuration</button>
            </form>
            <div class="message">
                <p>After saving, the weather station will restart and connect to your Wi-Fi network.</p>
                <p>If connection fails, it will return to setup mode automatically.</p>
            </div>
        </body>
        </html>
        """
        
        # HTML response for a successful save
        success_html = """<!DOCTYPE html>
        <html>
        <head>
            <title>Configuration Saved</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial; margin: 0; padding: 20px; text-align: center; }
                h1 { color: #00cc66; }
                .message { margin-top: 20px; padding: 20px; background-color: #e6fff2; border-left: 4px solid #00cc66; text-align: left; }
            </style>
            <meta http-equiv="refresh" content="10;url=/" />
        </head>
        <body>
            <h1>Configuration Saved Successfully!</h1>
            <div class="message">
                <p>Your Wi-Fi credentials have been saved.</p>
                <p>The weather station will now restart and connect to your network.</p>
                <p>Please wait while the device restarts...</p>
            </div>
        </body>
        </html>
        """
        
        # Display setup mode on e-paper
        self.epd.fill(0xff)
        self.epd.text("Wi-Fi Setup Mode", 5, 10, 0x00)
        self.epd.text("Connect to Wi-Fi:", 5, 35, 0x00)
        self.epd.text(f"SSID: {AP_SSID}", 5, 50, 0x00)
        self.epd.text(f"Password: {AP_PASSWORD}", 5, 65, 0x00)
        self.epd.text("Then visit in browser:", 5, 90, 0x00)
        self.epd.text("http://192.168.4.1", 5, 105, 0x00)
        self.epd.text("Press button to exit", 5, 130, 0x00)
        self.epd.display(self.epd.buffer)
        
        # Record the start time
        start_time = time.time()
        
        while True:           
            # Check for timeout
            if time.time() - start_time > CONFIG_MODE_TIMEOUT:
                print("Setup mode timeout")
                self.epd.fill(0xff)
                self.epd.text("Setup mode timeout", 5, 10, 0x00)
                self.epd.text("Exiting...", 5, 30, 0x00)
                self.epd.display(epd.buffer)
                return False
            
            try:
                # Wait for a connection
                conn, addr = s.accept()
                print(f"Connection from ** {addr}")
                
                # Get the request
                request = conn.recv(1024).decode('utf-8')
                print('Request', request) 
                
                # Parse the request
                if request.startswith('POST /save'):
                    # Find the form data in the request
                    print("Received a save request")
                    
                    content_length = 0
                    for line in request.split('\r\n'):
                        if line.startswith('Content-Length:'):
                            content_length = int(line.split(':')[1].strip())
                            print(f"Content length: {content_length}")
                    
                    # If we found a content length, look for form data
                    if content_length > 0:
                        # Find the form data after the headers
                        headers_end = request.find('\r\n\r\n')
                        
                        if headers_end > -1:
                            body_start = headers_end + 4  # Skip the \r\n\r\n
                            
                            # If body is incomplete, receive more data
                            body = request[body_start:]
                            
                            # If we don't have enough data yet, read more
                            while len(body) < content_length:
                                more_data = conn.recv(1024).decode('utf-8')
                                if not more_data:
                                    break
                                body += more_data
                            
                            print(f"Form data: {body}")
                        
                    # Parse the form data
                    fields = {}
                    for field in body.split('&'):
                        key, value = field.split('=')
                        fields[key] = value.replace('+', ' ')
                    # Extract the Wi-Fi credentials
                    ssid = fields.get('ssid', '')
                    password = fields.get('password', '')
                    
                    # Save the credentials
                    if ssid and password:
                        if self.write_wifi_credentials(ssid, password):
                            print("Saving WIFI credentials to file")
                            # Send success response
                            conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
                            conn.send(success_html)
                            conn.close()
                            
                            # Display success on e-paper
                            self.epd.fill(0xff)
                            self.epd.text("Wi-Fi Config Saved!", 5, 10, 0x00)
                            self.epd.text("SSID: " + ssid, 5, 40, 0x00)
                            self.epd.text("Restarting...", 5, 70, 0x00)
                            self.epd.display(self.epd.buffer)
                            
                            # Wait a moment for the user to see the message
                            utime.sleep(3)
                            return True
                else:
                    # Send the configuration page
                    conn.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
                    conn.send(html)
                
                conn.close()
            
            except Exception as e:
                # Socket timeout or other error
                pass
            
            # Small delay to prevent CPU overload
            utime.sleep(0.1)
    
    def write_wifi_credentials(self, ssid, password):
        data = json.dumps(
            {
                'ssid': ssid,
                'password': password
            }
        )
        with open(self.wifi_file, 'w') as f:
            f.write(data)
        return True
    
    def start_access_point(self):
        """Start access point for configuration"""
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=AP_SSID, password=AP_PASSWORD)
        
        while not ap.active():
            pass
        
        print("Access point started")
        print(f"SSID: {AP_SSID}")
        print(f"Password: {AP_PASSWORD}")
        print(f"IP address: {ap.ifconfig()[0]}")
        return ap
