# Raspberry pico W weather display

Micropython code for weather display using Raspbery pico W / [Waveshare ePaper display](https://www.waveshare.com/pico-oled-2.23.htm)

## Requirements
Create a free account in [OpenWheatherMap](https://openweathermap.org/api) and get your api key

## Functionality breakdown
### WiFi access point for setup
The first time this code runs, or if there are errors connecting to the configured WiFi (either because the WiFi SSID cannot be found or the password is wrong), the device starts in AP mode and advertises a configuration page. The user can add and save the configuration. The device is then restarted and starts fetching adn displaying wheather data.

### Weather api setup
Currenlthy you need to edit the file main.py and add these settings:
- WEATHER_API_KEY = Api key
- LAT = Latitude
- LON: Longitude
