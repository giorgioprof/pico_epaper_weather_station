import urequests
import utime
from weather_icons import draw_weather_icon

next_days_dict = {
    "Mon": "Tue",
    "Tue": "Wed",
    "Wed": "Thu",
    "Thu": "Fri",
    "Fri": "Sat",
    "Sat": "Sun",
    "Sun": "Mon"
    }
days_dict = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

class Weather():
    def __init__(self, api_key, lat, lon, epd):
        self.api_key = api_key
        self.lat = lat
        self.lon = lon
        self.epd = epd
        self.url_template = f"https://api.openweathermap.org/data/2.5/%s?lat={self.lat}&lon={self.lon}&appid={self.api_key}&units=metric"
    
    @property
    def weather_url(self):
        return self.url_template % 'weather'

    @property
    def forecast_url(self):
        return self.url_template % 'forecast'
        return 
    
    # Updated fetch_weather function to include weather_id
    def fetch_weather(self):
        try:
            response = urequests.get(self.weather_url)
            data = response.json()
            response.close()
            
            # Extract the data we need including the weather ID
            weather = {
                "temp": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "weather_id": data["weather"][0]["id"],  # Added weather ID for icon selection
                "wind_speed": data["wind"]["speed"],
                "city": data["name"],
                "country": data["sys"]["country"]
            }
            
            return weather
        except Exception as e:
            print("Error fetching weather data:", e)
            return None
    

    # Function to fetch 3-day weather forecast
    def fetch_forecast(self):
        try:
            # Use the 5-day/3-hour forecast endpoint
            response = urequests.get(self.forecast_url)
            data = response.json()
            response.close()
            
            # Process the forecast data to get daily forecasts
            # OpenWeatherMap returns forecast in 3-hour increments
            # We'll get one forecast per day at noon
            
            forecast_days = []
            days_processed = set()
            t = utime.localtime()
            today = f"{t[0]}-{t[1]:02d}-{t[2]:02d}"
            cur_day = days_dict[t[6]]
            next_day = next_days_dict[cur_day]
            for item in data["list"]:
                # Extract date from timestamp (format: "2023-04-01 12:00:00")
                date_str = item["dt_txt"].split(" ")[0]
                time_str = item["dt_txt"].split(" ")[1]
                
                # Only process each day once and try to get forecast around noon
                if date_str not in days_processed and "12:00:00" in time_str and date_str != today:
                    days_processed.add(date_str)                
                    
                    forecast = {
                        "date": date_str,
                        "day": next_day,
                        "temp": item["main"]["temp"],
                        "description": item["weather"][0]["description"],
                        "weather_id": item["weather"][0]["id"],
                        "humidity": item["main"]["humidity"],
                        "wind_speed": item["wind"]["speed"]
                    }
                    
                    forecast_days.append(forecast)
                    next_day = next_days_dict[next_day]
                    
                    # Stop after we get 5 days
                    if len(forecast_days) >= 5:
                        break
            
            return forecast_days
        
        except Exception as e:
            print("Error fetching forecast:", e)
            return None

    # Function to display the weather forecast
    def display_forecast(self, forecast_data):
        try:
            if not forecast_data or len(forecast_data) == 0:
                print("No forecast data to display")
                return
            
            # Display area variables
            display_width = self.epd.height  # We are in horizonatl layout so he disth is the height
            forecast_width = display_width // len(forecast_data)
            
            # Draw each forecast day
            for i, forecast in enumerate(forecast_data):
                x_pos = i * forecast_width + forecast_width // 2
                y_pos = 70  # Position in the lower part of the screen
                
                # Draw day of week
                self.epd.text(forecast["day"], x_pos - 10, y_pos, 0x00)
                
                # Draw weather icon
                draw_weather_icon(self.epd, forecast["weather_id"], x_pos, y_pos + 35, 25)
                
                # Draw temperature
                temp_str = f"{forecast['temp']:.1f}C"
                self.epd.text(temp_str, x_pos - 20, y_pos + 45, 0x00)
                
                # Draw vertical separator if not the last forecast
                if i < len(forecast_data) - 1:
                    self.epd.vline(x_pos + forecast_width // 2, y_pos - 5, 70, 0x00)
            
        except Exception as e:
            print("Error displaying forecast:", e)
    
    

    # Updated display function for horizontal layout with icons
    def display_weather_horizontal(self, weather, forecast):
        try:
            self.epd.fill(0xff)  # Clear to white
            
            # Current weather section
            # ======================
            # Display header     
            # Display location and time
            t = utime.localtime()
            time_str = f"{t[3]:02d}:{t[4]:02d}"
            self.epd.text(f"Weather: {weather['city']}, {time_str}", 5, 8, 0x00)
            
            # Draw a line separator
            self.epd.hline(5, 17, 240, 0x00)
            
            # Draw current weather icon
            weather_id = weather['weather_id']
            draw_weather_icon(self.epd, weather_id, 20, 47, 30)
            
            # Display current temperature (large)
            temp_str = f"Curr: {weather['temp']:.1f} C"
            self.epd.text(temp_str, 60, 25, 0x00)
            temp_str = f"Feel: {weather['feels_like']:.1f} C"
            self.epd.text(temp_str, 60, 35, 0x00)
            temp_str = f"Humm: {weather['humidity']}%"
            self.epd.text(temp_str, 60, 45, 0x00)
                    
            # Display feels like and humidity
            #epd.text(f"Feels: {weather['feels_like']:.1f}°C", 80, 65, 0x00)
            #epd.text(f"Humidity: {weather['humidity']}%", 80, 80, 0x00)
            
            # Format description nicely
            desc = weather['description']
            desc = desc[0].upper() + desc[1:]
            self.epd.text(f"{desc}", 60, 55, 0x00)
            self.epd.hline(5, 65, 240, 0x00)
            
            # Draw another separator before forecast
            #epd.hline(5, 115, 240, 0x00)
            
            # Display the forecast
            if forecast and len(forecast) > 0:
                self.display_forecast(forecast)
            else:
                self.epd.text("Forecast unavailable", 5, 70, 0x00)
            
            # Draw final separator
            self.epd.hline(5, 128, 130, 0x00)
                    
            # Display the date in the corner
            t = utime.localtime()
            date_str = f"{t[2]:02d}/{t[1]:02d}"
            self.epd.text(date_str, 180, 225, 0x00)
            
            # Update the display
            self.epd.display(self.epd.buffer)
            print("Display updated with horizontal layout")
            
        except Exception as e:
            print("Error updating display:", e)
