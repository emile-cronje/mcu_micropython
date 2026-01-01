import os, pyb
import json
import utime
import time
import btree_hybrid_disk_cache
from btree_custom_mem_key_value import BTree
import gc

class MeterReading:
    def __init__(self, id, meter_id, reading_on, reading):
        self.id = id
        self.meterId = meter_id
        self.reading_on = reading_on
        self.reading = reading

def days_between(d1, d2):
    return utime.mktime(d1) // (24*3600) - utime.mktime(d2) // (24*3600)

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

def free(full=True):
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  #else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))
  else : return ('Free:{0}'.format(P))  

data = []
data.append('item 0')
data.append('item 1')
data.append('item 2')
data.append('item 3')
data.append('item 4')
data.append('d')
data.append('e')
data.append('f')
data.append('g')
data.append('h')
data.append('i')
data.append('j')

os.mount(pyb.SDCard(), '/sd')    
dir = '/sd/btree_storage'
#os.mkdir(dir)

ramBefore = free(True)
start = time.time()
B = BTree(10)
itemCount = 500
idList = []
reading = 7

for index in range(itemCount):
    meterReading = MeterReading(index, index+100, f'2024-07-{index+1}T11:33:04.6645813+02:00', reading)
    idList.append(index)        
    B.insert(meterReading.id, meterReading.__dict__)
    reading += 10

updatedMeterReading = MeterReading(index, index+100, f'2024-07-{index+1}T11:33:04.6645813+02:00', reading)

for searchFor in range(0, itemCount):
    result = B.find(searchFor)
    
    if (result == None):    
        print(f'Item : {searchFor} not found...')
    else:
        B.update_value(searchFor, updatedMeterReading.__dict__)

keyCount = 0

for item in B.traverse_keys():
    keyCount += 1

print(f"Keycount: {keyCount}")

if (keyCount == itemCount):
    print("Keycount OK...")    
else:        
    print("Keycount mismatch...")

filter_func = lambda reading: reading["meterId"] != 1
sorted_readings = B.traverse_func(filter_func)    

jsonReadings = []

for reading in sorted_readings:
    jsonReadings.append(reading)
    #print(reading["meterId"])

# Calculate the average daily rate for meter_id 1
average_daily_rate_meter_1 = calculate_average_daily_rate(jsonReadings)
print(f"Average Daily Rate for meter 1: {average_daily_rate_meter_1}")

print("Deleting all items...")
for id in idList:    
    B.delete(id)    

keyCount = 0

for item in B.traverse_keys():
    keyCount += 1

if (keyCount == 0):
    print("Delete OK...")    
else:    
    print("Delete failed...")        
    keyCount = 0

    for item in B.traverse_keys():
        keyCount += 1

    print(f"Keycount after delete: {keyCount}")        

ramAfter = free(True)
print("before:", ramBefore)
print("after:", ramAfter)
end = time.time()    
print(end - start)
print('seconds')
