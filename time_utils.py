import ntptime
import utime
from machine import RTC

def sync_time():
    """Synchronize the Pico's time with an NTP server with fallback"""
    # Set timezone offset in seconds (Greece is GMT+2 or GMT+3 during DST)
    timezone_offset = 3600 * 3  # GMT+3 for summer time
    
    # Try to synchronize with an NTP server
    print("Synchronizing time with NTP server...")
    ntptime.settime()  # This sets to UTC
    
    # Get current time (UTC)
    utc_time = utime.time()
    
    # Apply timezone offset
    local_time = utc_time + timezone_offset
    
    # Convert to tuple
    local_tuple = utime.gmtime(local_time)
    
    # Get the RTC instance
    rtc = RTC()
    
    # Set the RTC time (year, month, day, weekday, hour, minute, second, microsecond)
    # Note: we use 0 for weekday as it's not important and 0 for microseconds
    rtc.datetime((local_tuple[0], local_tuple[1], local_tuple[2], 0,
                  local_tuple[3], local_tuple[4], local_tuple[5], 0))
    
    # Get the updated time
    t = utime.localtime()
    time_str = f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
    date_str = f"{t[2]:02d}/{t[1]:02d}/{t[0]}"
    
    print(f"Time synchronized: {date_str} {time_str}")
    return True