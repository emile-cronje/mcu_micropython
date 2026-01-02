import time
import utime
#from datetime import datetime

class AdrHelper:
    def days_between(self, d1, d2):
        return utime.mktime(d1) // (24*3600) - utime.mktime(d2) // (24*3600)
    
    def sort_json_objects_by_date(self, json_objects):
        n = len(json_objects)
        
        for j in range(n - 1):
            date1_timestamp = self.convert_to_epoch_seconds(json_objects[j]['readingOn'])
            date2_timestamp = self.convert_to_epoch_seconds(json_objects[j + 1]['readingOn'])
            
            if date1_timestamp > date2_timestamp:
                json_objects[j], json_objects[j + 1] = json_objects[j + 1], json_objects[j]
        return json_objects
    
    def convert_to_epoch_seconds(self, date_str):
        date_part, time_part = date_str.split('T')
        year, month, day = map(int, date_part.split('-'))
        time_part, offset = time_part.split('Z')
        hour, minute, second = map(float, time_part.split(':'))
        # Calculate the total seconds since the epoch for the given time
        seconds_since_epoch = time.mktime((year, month, day, int(hour), int(minute), int(second), -1, -1, -1))
        
        # Handle the fractional part of the second
        fractional_seconds = second - int(second)
        
        # Add the fractional part of the second
        seconds_since_epoch += fractional_seconds
        
        non_scientific = "{:.0f}".format(seconds_since_epoch)
        
        return int(non_scientific)
    
    def calculate_average_daily_rate(self, meter_readings):
        if len(meter_readings) < 1:  # Changed from < 2 to match PostgreSQL behavior
            print("No readings...")
            return 0
        
        daily_rates = []
        
        # Process all readings (including first one which will have None/0 rate like PostgreSQL LAG)
        for i in range(len(meter_readings)):
            if i == 0:
                # First reading has no previous reading (like LAG returning NULL)
                # PostgreSQL COALESCE converts this NULL to 0
                daily_rates.append(0)
            else:
                previous = meter_readings[i - 1]
                current = meter_readings[i]
                delta_reading = current["reading"] - previous["reading"]
                
                # Calculate days between as integer days (matching PostgreSQL DATE - DATE)
                current_date = time.localtime(self.convert_to_epoch_seconds(current["readingOn"]))
                previous_date = time.localtime(self.convert_to_epoch_seconds(previous["readingOn"]))
                delta_days = self.days_between(current_date, previous_date)
                
                if delta_days == 0:
                    # Division by zero case - PostgreSQL NULLIF makes this NULL, COALESCE makes it 0
                    daily_rates.append(0)
                else:
                    daily_rate = delta_reading / delta_days
                    daily_rates.append(daily_rate)
        
        # Calculate average of all daily rates (including zeros)
        if len(daily_rates) == 0:
            return 0
        
        average_rate = sum(daily_rates) / len(daily_rates)
        return average_rate