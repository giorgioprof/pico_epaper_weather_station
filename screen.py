import network
import urequests
import utime
import json
from machine import Pin, ADC
from screen import EPD_2in13_V4_Portrait

# Import your e-Paper display code
# Assuming the e-Paper class is in the same file, otherwise import it
from machine import Pin, SPI
import framebuf
import utime

# E-Paper display configuration (from your code)
EPD_WIDTH = 122
EPD_HEIGHT = 250

RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13

# Import your e-Paper class here
# For example: from epaper import EPD_2in13_V4_Portrait
# Or paste your class definition here

# ====================== WIFI CONFIGURATION ======================
WIFI_SSID = "iGiorgio"  # Replace with your WiFi name
WIFI_PASSWORD = "neromilos"  # Replace with your WiFi password

# ====================== WEATHER API CONFIGURATION ======================
# Using OpenWeatherMap API (free tier)
WEATHER_API_KEY = "3e049233575582f12f722201b87dafca"  # Get one from openweathermap.org
CITY = "Athens,gr"  # e.g., "London,uk"
WEATHER_URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric"

# Function to connect to WiFi
def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    print(f"Connecting to {WIFI_SSID}...")
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        
        # Wait for connection with timeout
        max_wait = 20
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1
            print("Waiting for connection...")
            utime.sleep(1)
    
    if wlan.isconnected():
        print("Connected to WiFi")
        print("IP:", wlan.ifconfig()[0])
        return True
    else:
        print("WiFi connection failed")
        print("Status:", wlan.status())
        return False

# Function to get temperature from Pico's internal sensor
def read_pico_temperature():
    sensor = ADC(4)
    raw = sensor.read_u16()
    voltage = raw * (3.3 / 65535)
    temperature = 27 - (voltage - 0.706) / 0.001721
    return temperature

# Function to fetch weather data
def fetch_weather():
    try:
        response = urequests.get(WEATHER_URL)
        data = response.json()
        response.close()
        
        # Extract the data we need
        weather = {
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"],
            "city": data["name"],
            "country": data["sys"]["country"]
        }
        
        return weather
    except Exception as e:
        print("Error fetching weather data:", e)
        return None

# Function to display weather on e-Paper
def display_weather(epd, weather, pico_temp):
    try:
        epd.fill(0xff)  # Clear to white
        
        # Display header
        epd.text("Weather Station", 5, 10, 0x00)
        epd.text(f"{weather['city']}, {weather['country']}", 5, 25, 0x00)
        
        # Draw a line separator
        epd.hline(5, 35, 110, 0x00)
        
        # Display weather data
        epd.text(f"Temp: {weather['temp']:.1f}C", 5, 45, 0x00)
        epd.text(f"Feels: {weather['feels_like']:.1f}C", 5, 60, 0x00)
        epd.text(f"Humidity: {weather['humidity']}%", 5, 75, 0x00)
        
        # Display wind speed
        epd.text(f"Wind: {weather['wind_speed']} m/s", 5, 90, 0x00)
        
        # Format description nicely (capitalize first letter of each word)
        desc = weather['description'].title()
        epd.text(f"{desc}", 5, 105, 0x00)
        
        # Draw another separator
        epd.hline(5, 120, 110, 0x00)
        
        # Display local sensor data
        epd.text("Local Sensor:", 5, 135, 0x00)
        epd.text(f"Temp: {pico_temp:.1f}C", 5, 150, 0x00)
        
        # Display last updated time
        t = utime.localtime()
        time_str = f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
        epd.text(f"Updated: {time_str}", 5, 175, 0x00)
        
        # Update the display
        epd.display(epd.buffer)
        print("Display updated")
        
    except Exception as e:
        print("Error updating display:", e)

# Main function
def main():
    # Initialize the e-Paper display
    epd = EPD_2in13_V4_Portrait()  # Use your display class
    epd.Clear()
    
    # Initial message
    epd.fill(0xff)
    epd.text("Weather Station", 5, 10, 0x00)
    epd.text("Connecting to WiFi...", 5, 30, 0x00)
    epd.display(epd.buffer)
    
    # Connect to WiFi
    wifi_connected = connect_to_wifi()
    
    if not wifi_connected:
        epd.fill(0xff)
        epd.text("WiFi Connection", 5, 10, 0x00)
        epd.text("Failed!", 5, 30, 0x00)
        epd.text("Check credentials", 5, 50, 0x00)
        epd.text("and restart.", 5, 70, 0x00)
        epd.display(epd.buffer)
        return
    
    # Main loop - update every 2 minutes
    while True:
        try:
            # Get Pico's internal temperature
            pico_temp = read_pico_temperature()
            print(f"Pico temperature: {pico_temp:.1f}°C")
            
            # Fetch weather data
            weather = fetch_weather()
            
            if weather:
                print(f"Weather: {weather['temp']:.1f}°C, {weather['description']}")
                display_weather(epd, weather, pico_temp)
            else:
                print("Failed to get weather data")
                epd.fill(0xff)
                epd.text("Weather Station", 5, 10, 0x00)
                epd.text("Error fetching data", 5, 40, 0x00)
                epd.text("Will retry...", 5, 60, 0x00)
                epd.display(epd.buffer)
            
            # Wait for 2 minutes before next update
            # Note: For power saving, you could put the Pico to sleep here
            print("Waiting 2 minutes until next update...")
            utime.sleep(120)
            
        except Exception as e:
            print("Error in main loop:", e)
            # Wait and try again
            utime.sleep(60)

# Run the main function
if __name__ == "__main__":
    main()