
import time
import utime
from btree_custom_hybrid_crud import BTree as BTreeCustomHybridCrud
from btree_hybrid_cached import BTree as BTreeCustom
from btree_custom_crud import BTree as BTree
import json
import os
import machine, pyb

def days_between(d1, d2):
    return utime.mktime(d1) // (24*3600) - utime.mktime(d2) // (24*3600)

# Define a simple structure for a meter reading
class MeterReading:
    def __init__(self, id, meter_id, reading_on, reading):
        self.id = id
        self.meterId = meter_id
        self.reading_on = reading_on
        self.reading = reading

# Simplified B-tree class (simulated with a list)
class BTree:
    def __init__(self):
        self.readings = []

    def insert(self, reading):
        self.readings.append(reading)
        self.readings.sort(key=lambda x: x.reading_on)  # Sort by reading_on date

    def traverse(self):
        return self.readings

def convert_to_epoch_seconds(date_str):
    # Parse the date and time components
    date_part, time_part = date_str.split('T')
    year, month, day = map(int, date_part.split('-'))
    time_part, offset = time_part.split('+')
    hour, minute, second = map(float, time_part.split(':'))
    
    # Calculate the total seconds since the epoch for the given time
    seconds_since_epoch = time.mktime((year, month, day, int(hour), int(minute), int(second), -1, -1, -1))
    
    # Handle the fractional part of the second
    fractional_seconds = second - int(second)
    
    # Calculate the timezone offset in seconds
    offset_hours, offset_minutes = map(int, offset.split(':'))
    offset_seconds = offset_hours * 3600 + offset_minutes * 60
    
    # Subtract the offset to get UTC time
    seconds_since_epoch -= offset_seconds
    
    # Add the fractional part of the second
    seconds_since_epoch += fractional_seconds
    
    non_scientific = "{:.0f}".format(seconds_since_epoch)
    
    return int(non_scientific)

def calculate_average_daily_rate(meter_readings):
    if len(meter_readings) < 2:
        print("Too few readings...")
        return 0

    total_rate = 0
    count = 0

    for i in range(1, len(meter_readings)):
        previous = meter_readings[i - 1]
        current = meter_readings[i]

        delta_reading = current["reading"] - previous["reading"]
        delta_days = days_between(time.localtime(convert_to_epoch_seconds(current["reading_on"])), time.localtime(convert_to_epoch_seconds(previous["reading_on"])))

        if delta_days > 0:
            daily_rate = delta_reading / delta_days
            total_rate += daily_rate
            count += 1

    return total_rate / count if count > 0 else 0

os.mount(pyb.SDCard(), "/sd")    
#os.rmdir('/sd/btree_storage')
btree = BTreeCustomHybridCrud(t=5, cache_capacity=1, storage_directory='/sd/btree_storage')
#btree = BTreeCustom(t=5, cache_capacity=10, storage_directory='/sd/btree_storage')
btree = BTree(t = 10, filename = "test.json")

# Insert meter readings
readings = [
    MeterReading(1, 1, '2024-06-21T11:33:04.6645813+02:00', 100),
    MeterReading(2, 1, '2024-06-22T11:33:04.6645813+02:00', 110),
    MeterReading(3, 1, '2024-06-23T11:33:04.6645813+02:00', 122),
    MeterReading(4, 1, '2024-06-24T11:33:04.6645813+02:00', 130),
    MeterReading(5, 2, '2024-06-25T11:33:04.6645813+02:00', 140),
    MeterReading(6, 2, '2024-06-26T11:33:04.6645813+02:00', 150),
    MeterReading(7, 1, '2024-06-27T11:33:04.6645813+02:00', 166),
    MeterReading(8, 1, '2024-06-28T11:33:04.6645813+02:00', 170),
    MeterReading(9, 1, '2024-06-29T11:33:04.6645813+02:00', 181),
    MeterReading(10, 1, '2024-06-30T11:33:04.6645813+02:00', 192),
    MeterReading(11, 2, '2024-06-31T11:33:04.6645813+02:00', 200),
    MeterReading(12, 2, '2024-07-01T11:33:04.6645813+02:00', 210)        
]

id = 0
reading = 10
limit = 10

for i in range(limit):    
    meterReading = MeterReading(id, 2, '2024-07-01T11:33:04.6645813+02:00', reading)            
    btree.insert(id, meterReading.__dict__)
    id += 1
    reading += 10

# Traverse the B-tree and get sorted readings
filter_func = lambda reading: reading["meterId"] != 1# and reading["id"] == 1
sorted_readings = btree.traverse_func(filter_func)    

jsonReadings = []

for reading in sorted_readings:
    jsonReadings.append(reading)
    print(reading["id"])

# Calculate the average daily rate for meter_id 1
average_daily_rate_meter_1 = calculate_average_daily_rate(jsonReadings)
print(f"Average Daily Rate for meter 1: {average_daily_rate_meter_1}")

# Calculate the average daily rate for meter_id 2
average_daily_rate_meter_2 = calculate_average_daily_rate(jsonReadings)
print(f"Average Daily Rate for meter 2: {average_daily_rate_meter_2}")

# Retrieve values
#print(btree.find(10))
#print(btree.find(11))
#print(btree.find(12))

for i in range(limit):    
    value = btree.get_value(i)
    print("Item : " + str(value))
