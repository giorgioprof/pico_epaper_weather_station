import math

# Weather icon drawing functions
def draw_sun(epd, x, y, size=20):
    """Draw a sun icon"""
    radius = size // 2
    # Draw the sun circle
    epd.fill_circle(x, y, radius, 0x00)
    epd.fill_circle(x, y, radius-2, 0xff)
    
    # Draw rays
    ray_length = radius // 2
    for i in range(8):
        angle = i * 3.14159 / 4  # 45 degrees apart
        x_end = int(x + (radius + ray_length) * math.cos(angle))
        y_end = int(y + (radius + ray_length) * math.sin(angle))
        x_start = int(x + radius * math.cos(angle))
        y_start = int(y + radius * math.sin(angle))
        epd.line(x_start, y_start, x_end, y_end, 0x00)

def draw_cloud(epd, x, y, size=20):
    """Draw a cloud icon"""
    radius = size // 3
    # Draw cloud puffs
    epd.fill_circle(x, y, radius, 0x00)
    epd.fill_circle(x + radius, y, radius, 0x00)
    epd.fill_circle(x - radius, y, radius, 0x00)
    epd.fill_circle(x, y - radius, radius, 0x00)
    # Draw cloud base
    epd.fill_rect(x - radius, y - radius, radius * 2, radius, 0x00)

def draw_rain(epd, x, y, size=20):
    """Draw a rain icon"""
    # Draw a cloud
    draw_cloud(epd, x, y - size//3, size)
    
    # Draw raindrops
    for i in range(3):
        drop_x = x - size//3 + (i * size//3)
        epd.line(drop_x, y, drop_x, y + size//3, 0x00)

def draw_snow(epd, x, y, size=20):
    """Draw a snow icon"""
    # Draw a cloud
    draw_cloud(epd, x, y - size//3, size)
    
    # Draw snowflakes
    for i in range(3):
        flake_x = x - size//3 + (i * size//3)
        flake_y = y + size//4
        # Draw a small X
        epd.line(flake_x-2, flake_y-2, flake_x+2, flake_y+2, 0x00)
        epd.line(flake_x+2, flake_y-2, flake_x-2, flake_y+2, 0x00)

def draw_thunderstorm(epd, x, y, size=20):
    """Draw a thunderstorm icon"""
    # Draw a cloud
    draw_cloud(epd, x, y - size//3, size)
    
    # Draw lightning bolt
    epd.line(x, y, x-size//4, y+size//2, 0x00)
    epd.line(x-size//4, y+size//2, x, y+size//3, 0x00)
    epd.line(x, y+size//3, x-size//6, y+size//2 + size//4, 0x00)

def draw_wind(epd, x, y, size=20):
    """Draw a wind icon"""
    # Draw three curved lines
    for i in range(3):
        y_pos = y - size//3 + (i * size//3)
        epd.line(x - size//2, y_pos, x, y_pos, 0x00)
        epd.line(x, y_pos, x + size//4, y_pos - size//6, 0x00)

# Helper function to add circle drawing capability if not in the original class
def fill_circle(epd, x0, y0, radius, color):
    """Draw a filled circle"""
    x = radius
    y = 0
    err = 0
    
    while x >= y:
        epd.line(x0 - x, y0 + y, x0 + x, y0 + y, color)
        epd.line(x0 - y, y0 + x, x0 + y, y0 + x, color)
        epd.line(x0 - x, y0 - y, x0 + x, y0 - y, color)
        epd.line(x0 - y, y0 - x, x0 + y, y0 - x, color)
        
        y += 1
        if err <= 0:
            err += 2 * y + 1
        if err > 0:
            x -= 1
            err -= 2 * x + 1

# Add the circle drawing method to the ePaper class
def add_circle_methods(epd):
    """Add circle drawing methods to the ePaper class if they don't exist"""
    if not hasattr(epd, 'fill_circle'):
        epd.fill_circle = lambda x0, y0, radius, color: fill_circle(epd, x0, y0, radius, color)

# Function to choose and draw the appropriate weather icon
def draw_weather_icon(epd, weather_id, x, y, size=20):
    """Draw the appropriate weather icon based on OpenWeatherMap ID"""
    # First make sure we have the circle drawing method
    add_circle_methods(epd)
    
    # Weather condition codes: https://openweathermap.org/weather-conditions
    if weather_id < 300:  # Thunderstorm
        draw_thunderstorm(epd, x, y, size)
    elif weather_id < 400:  # Drizzle
        draw_rain(epd, x, y, size)
    elif weather_id < 600:  # Rain
        draw_rain(epd, x, y, size)
    elif weather_id < 700:  # Snow
        draw_snow(epd, x, y, size)
    elif weather_id < 800:  # Atmosphere (fog, mist, etc.)
        draw_cloud(epd, x, y-8, size)
    elif weather_id == 800:  # Clear sky
        draw_sun(epd, x, y-8, size)
    elif weather_id < 900:  # Clouds
        draw_cloud(epd, x, y-8, size)
    else:  # Extreme weather or additional
        draw_thunderstorm(epd, x, y, size)