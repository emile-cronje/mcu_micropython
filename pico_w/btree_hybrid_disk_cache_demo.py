import os
import json
import utime
import time
import btree_hybrid_disk_cache
from btree_hybrid_disk_cache import BTree
import gc
import pyb
from machine import SPI, Pin
from ramblock import RAMBlockDevExt
import random
from AdrHelper import AdrHelper

class MeterReading:
    def __init__(self, id, meter_id, reading_on, reading):
        self.id = id
        self.meterId = meter_id
        self.readingOn = reading_on
        self.reading = reading

def free(full=True):
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
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

useRam = True

if (useRam == True):
    rootDir = '/rb'    
    bdev = RAMBlockDevExt(512, 1000)
    os.VfsFat.mkfs(bdev)
    os.mount(bdev, rootDir)
    dir = rootDir + '/btree_storage'    
    os.mkdir(dir)
else:
    rootDir = '/sd'    
    os.mount(sd, rootDir)
    dir = rootDir + '/btree_storage'    
    #os.mkdir(sdDir)

ramBefore = free(True)
start = time.time()
B = BTree(10, cache_dir=dir)
itemCount = 10
idList = []
reading = 1
manual = False
readingCount = 10
adrHelper = AdrHelper()

YY = 2024
MM = 7
DD = 1

hh = 12
mm = 2
ss = 34

if (manual == False):
    for index in range(itemCount):
        for readingIndex in range(readingCount):        
            reading += 10#random.uniform(5, 10)
            readingOn = f'{YY}-{MM}-{DD}T{hh}:{mm}:{ss}.6645813Z'
            
            meterReading = MeterReading(readingIndex, index, readingOn, reading)    
            idList.append(readingIndex)        
            B.insert((meterReading.id, meterReading.__dict__))
            DD += 1

#            print("Reading: " + str(meterReading.__dict__))
else:
    index = 1
    meterReading = MeterReading(index, index, f'2025-05-05T14:01:04.078801Z', 5.3478)    
    idList.append(index)        
    B.insert((meterReading.id, meterReading.__dict__))

    index = 2
    meterReading = MeterReading(index, index, f'2025-05-07T14:01:04.462379Z', 3.8688)    
    idList.append(index)        
    B.insert((meterReading.id, meterReading.__dict__))

    index = 3
    meterReading = MeterReading(index, index, f'2025-05-06T14:01:04.287917Z', 12.7287)    
    idList.append(index)        
    B.insert((meterReading.id, meterReading.__dict__))

    index = 4
    meterReading = MeterReading(index, index, f'2025-05-08T14:01:04.647752Z', 10.6963)    
    idList.append(index)        
    B.insert((meterReading.id, meterReading.__dict__))

updatedMeterReading = MeterReading(index, index, f'2024-07-{index+1}T11:33:04.6645813Z', reading)

for searchFor in range(0, itemCount):
    result = B.find(searchFor)
    
    if (result == None):    
        print(f'Item : {searchFor} not found...')
    #else:
     #   B.update_value(searchFor, updatedMeterReading.__dict__)

keyCount = 0

for item in B.traverse_keys():
    keyCount += 1

print(f"Keycount: {keyCount}")

if (keyCount == (itemCount * readingCount)):
    print("Keycount OK...")    
else:        
    print("Keycount mismatch...")

print("Prep for adr...")

for index in range(itemCount):
    filter_func = lambda reading: reading["meterId"] == index
    readings = B.traverse_func(filter_func)    
    sorted_readings = adrHelper.sort_json_objects_by_date(readings)

  #  print("Sorted readings for meter: " + str(index))
    
   # for reading in sorted_readings:
    #    print(reading["readingOn"])

    adr = adrHelper.calculate_average_daily_rate(sorted_readings)
    print(f"Average Daily Rate for meter {index}: {adr}")

print("Deleting all items...")

for id in idList:    
    B.delete(B.root, (id,))    

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
