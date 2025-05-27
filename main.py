import network
import urequests
import utime
import time
import math
import json
import os
from machine import Pin, ADC, reset, RTC, deepsleep, Timer
from epaper_screen import EPD_2in13_V4_Landscape
from weather_forecast import Weather
from time_utils import sync_time
from wifi_utils import WiFiCls, WiFiSetup

# ====================== WEATHER API CONFIGURATION ======================
WEATHER_API_KEY = "xxxxxxxxxxxxxx"
LAT = "xx.xxxxxxx"
LON = "xx.xxxxxxx"
minutes_remaining = 60
WIFI_FILE = "wifi.json"

def read_wifi_credentials():
    if WIFI_FILE not in os.listdir():
        return None, None
    with open(WIFI_FILE, 'r') as f:
        raw = f.read()
        data = json.loads(raw)
    return data['ssid'], data['password']


# Function to get temperature from Pico's internal sensor
def read_pico_temperature():
    sensor = ADC(4)
    raw = sensor.read_u16()
    voltage = raw * (3.3 / 65535)
    temperature = 27 - (voltage - 0.706) / 0.001721
    return temperature

# Main function
def main():
    # Add a delay at startup to allow all hardware to initialize
    print("Starting weather station...")
    utime.sleep(5)
    
    # Initialize the e-Paper display in landscape orientation
    try:
        epd = EPD_2in13_V4_Landscape()  # Now using landscape orientation
        epd.Clear()
        
        # Initial message
        epd.fill(0xff)
        epd.text("Weather Station", 5, 10, 0x00)
        epd.text("Initializing...", 5, 30, 0x00)
        epd.display(epd.buffer)
        
        print("Display initialized")
    except Exception as e:
        print(f"Display initialization error: {e}")
        utime.sleep(10)
        # Try one more time
        epd = EPD_2in13_V4_Landscape()
        epd.Clear()
    
    # Show connecting message
    epd.fill(0xff)
    epd.text("Weather Station", 5, 10, 0x00)
    epd.text("Connecting to WiFi...", 5, 30, 0x00)
    epd.display(epd.buffer)
    
    
    ssid, password = read_wifi_credentials()
    if ssid is None:
        wifi_config = WiFiSetup(epd, WIFI_FILE)
        ap = wifi_config.start_access_point()
        config_saved = wifi_config.setup_web_server()
        
        # Clean up
        ap.active(False)
        
        if config_saved:
            # If configuration was saved, restart the device
            print("Restarting after configuration...")
            reset()
    
    
    # Connect to WiFi with retries
    wifi_connected = False
    wifi = WiFiCls(ssid, password) 
    for attempt in range(3):
        print(f"WiFi connection attempt {attempt+1}...")
        wifi_connected = wifi.connect()
        if wifi_connected:
            break
        
        epd.fill(0xff)
        epd.text("WiFi Connection", 5, 10, 0x00)
        epd.text(f"Attempt {attempt+1} failed", 5, 30, 0x00)
        epd.text("Retrying...", 5, 50, 0x00)
        epd.display(epd.buffer)
        utime.sleep(5)
    
    if not wifi_connected:
        epd.fill(0xff)
        epd.text("WiFi Connection", 5, 10, 0x00)
        epd.text("Failed!", 5, 30, 0x00)
        epd.text("Check credentials", 5, 50, 0x00)
        epd.text("and restart.", 5, 70, 0x00)
        epd.display(epd.buffer)
        utime.sleep(60)
        reset()
    
    # Synchronize time if WiFi is connected
    if wifi_connected:
        epd.fill(0xff)
        epd.text("Weather Station", 5, 10, 0x00)
        epd.text("Synchronizing time...", 5, 30, 0x00)
        epd.display(epd.buffer)
        
        time_synced = sync_time()
        if time_synced:
            t = utime.localtime()
            time_str = f"{t[3]:02d}:{t[4]:02d}"
            date_str = f"{t[2]:02d}/{t[1]:02d}/{t[0]}"
            
            epd.fill(0xff)
            epd.text("Time synchronized", 5, 10, 0x00)
            epd.text(f"Date: {date_str}", 5, 30, 0x00)
            epd.text(f"Time: {time_str}", 5, 50, 0x00)
            epd.display(epd.buffer)
            utime.sleep(3)
    
    # Main loop - update every 15 minutes
    error_count = 0
    last_forecast_time = 0
    forecast_data = None
    
    weather_cls = Weather(WEATHER_API_KEY, LAT, LON, epd)
    while True:
        try:
            # Get Pico's internal temperature
            pico_temp = read_pico_temperature()
            print(f"Pico temperature: {pico_temp:.1f}°C")
            
            # Fetch current weather data
            weather = weather_cls.fetch_weather()
            
            # Fetch forecast data every 3 hours (to save API calls)
            current_time = utime.time()
            if forecast_data is None or (current_time - last_forecast_time) > 10800:  # 3 hours
                print("Fetching forecast data...")
                forecast_data = weather_cls.fetch_forecast()
                last_forecast_time = current_time
            
            if weather:
                print(f"Weather: {weather['temp']:.1f}°C, {weather['description']}")
                # Use the new horizontal display function
                weather_cls.display_weather_horizontal(weather, forecast_data)
                error_count = 0
            else:
                print("Failed to get weather data")
                epd.fill(0xff)
                epd.text("Weather Station", 5, 10, 0x00)
                epd.text("Error fetching data", 5, 40, 0x00)
                epd.text("Will retry...", 5, 60, 0x00)
                epd.display(epd.buffer)
                error_count += 1
            
            # If we have too many consecutive errors, reset the device
            if error_count >= 5:
                print("Too many errors, resetting device...")
                epd.fill(0xff)
                epd.text("Too many errors", 5, 10, 0x00)
                epd.text("Resetting device...", 5, 30, 0x00)
                epd.display(epd.buffer)
                utime.sleep(5)
                reset()
            
            # Wait for 15 minutes before next update
            print("Waiting 60 minutes until next update...")
            epd.text("ETA:", 190, 8, 0x00)
            epd.display(epd.buffer)  # Full refresh first time

            epd.init()
            for i in range(60):  # 60 * 60 seconds = 60 minutes
                epd.fill_rect(220, 8, 40, 6, 0xff)
                epd.text(str(60+1-i), 220, 8, 0x00)
                epd.displayPartial(epd.buffer)
         
                utime.sleep(60)
                # Check WiFi still connected periodically
                if i % 15 == 0 and not wifi.connected:
                    print("WiFi disconnected, attempting to reconnect...")
                    wifi.connect()                            
        except Exception as e:
            print(f"Error in main loop: {e}")
            error_count += 1
            # Wait and try again
            utime.sleep(60)

# Run the main function
if __name__ == "__main__":
    main()
