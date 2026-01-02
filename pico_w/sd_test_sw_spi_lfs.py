import os
import machine

#import sdcard_lfs_patched_v2 as sdcard
#from sdcard_lfs_patched_v2 import SDCard

import sdcard as sdcard
from sdcard import SDCard

from machine import SPI, Pin
import gc
import uasyncio as asyncio
import time
from ramblock import RAMBlockDevExt, RAMBlockDev
from cpu_monitor_class import CPUMon
import utime
import _thread

entityCount = 25
threadCount = 4
sdFinalResult = True
ramFinalResult = True
sdDir = '/sd'
rbDir = '/rb'
sleepFor = 0.05
useCore1 = True

def ramDiskTest():
    global ramFinalResult
    success = True
    
    print("Worker thread started on Core 1...")        
    counter = 0
    id = 0
    dir = rbDir
    limit = entityCount * threadCount
    
    for count in range(limit):
        counter += 1
        s = "Sync thread: " + dir + " " + str(id) + " Count: " + str(count + 1)
        print(s)
            
        line = 'abcdefghijklmnopqrstuvwxyz_' + str(id + count) + '\n'
        lines = line * entityCount
        short = '1234567890\n'

        fn = dir + '/rats_long_' + str(id) + '.txt'
        
        with open(fn,'w') as f:
            n = f.write(lines)
            log(str(n) + ' bytes written')
            n = f.write(short)
            log(str(n) + ' bytes written')
            n = f.write(lines)
            log(str(n) + ' bytes written')

        with open(fn,'r') as f:
            result_long = f.read()

        fn = dir + '/rats_short.txt'
        
        with open(fn,'w') as f:
            n = f.write(short) # one block

        with open(fn,'r') as f:
            result_short = f.read()

        if result_long == ''.join((lines, short, lines)):
            log('Large file Pass')
        else:
            log('Large file Fail')
            success = False
            
#        short += 'rr'
        
        if result_short == short:
            log('Small file Pass')
        else:
            log('Small file Fail')
            success = False

        log("Count: " + str(count))

#    if (success == False):
 #       ramFinalResult = False

  #  print("ramFinalResult: " + str(ramFinalResult))
   # print("success: " + str(success))    
    #print('RAM Tests', 'passed' if success else 'failed')
    
    final_success = success and (counter == limit)   # or just drop the counter check entirely
    ramFinalResult = final_success
#    print("ramFinalResult: " + str(ramFinalResult))
 #   print("success: " + str(final_success))
  #  print('RAM Tests', 'passed' if final_success else 'failed')    

async def diskTestAsync(id, dir):
    global sdFinalResult
    success = True    
    
    counter = 0
    id = time.time_ns()
    
    for count in range(entityCount):
        counter += 1
        s = "Async thread: " + dir + " " + str(id) + " Count: " + str(count + 1)
        print(s)
            
        line = 'abcdefghijklmnopqrstuvwxyz_' + str(id + count) + '\n'
        lines = line * entityCount
        short = '1234567890\n'

        fn = dir + '/rats_long_' + str(id) + '.txt'
        log('Multiple block read/write')
        
        with open(fn,'w') as f:
            n = f.write(lines)
            log(str(n) + ' bytes written')
            n = f.write(short)
            log(str(n) + ' bytes written')
            n = f.write(lines)
            log(str(n) + ' bytes written')

        with open(fn,'r') as f:
            result_long = f.read()
            log(str(len(result_long)) + ' bytes read')

        fn = dir + '/rats_short.txt'
        log('Single block read/write')
        
        with open(fn,'w') as f:
            n = f.write(short) # one block
            log(str(n) + ' bytes written')

        with open(fn,'r') as f:
            result_short = f.read()
            log(str(len(result_short)) + ' bytes read')

        log('Verifying data read back...')
        
        if result_long == ''.join((lines, short, lines)):
            log('Large file Pass')
        else:
            log('Large file Fail')
            success = False
        
        if result_short == short:
            log('Small file Pass')
        else:
            log('Small file Fail')
            success = False

        await asyncio.sleep(sleepFor)            

    if (success == False):
        sdFinalResult = False
        
   # print(dir + ' Tests', 'passed' if success else 'failed')

def free(full=True):
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  #else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))
  else : return ('Free:{0}'.format(P))  

def rm(d):  # Remove file or tree
    try:
        #print(os.stat(d))
        
        if os.stat(d)[0] & 0x4000:  # Dir
            for f in os.ilistdir(d):
                if f[0] not in ('.', '..'):
                    rm("/".join((d, f[0])))  # File or Dir
            os.rmdir(d)
        else:  # File
            os.remove(d)
    except:
        print("rm of '%s' failed" % d)
        
def log(s):
    return
    print(s)
    
async def showMemUsage():
    while True:
        print(free(True))        
        await asyncio.sleep(4)
    
async def main(sdDir, rbDir):
    tasks = []
    start = time.time()
    
    for id in range(threadCount):    
        task = asyncio.create_task(diskTestAsync(id + 1, sdDir))
        tasks.append(task)        

    if (useCore1 == True):
        cpuMon = CPUMon()        
        core1Task = asyncio.create_task(cpuMon.main(worker_func = ramDiskTest,
                                                    useCore1 = useCore1,
                                                    showUsage = False))
        tasks.append(core1Task)        
    else:
        for id in range(threadCount):    
            task = asyncio.create_task(diskTestAsync(id + 1, rbDir))
            tasks.append(task)

#    memUsageTask = asyncio.create_task(showMemUsage())
#    tasks.append(memUsageTask)    
    print('Tasks are running...')

    await asyncio.gather(*tasks)
    
    end = time.time()    
    print(end - start)
    print('seconds')
    
    print("SD Result: " + str(sdFinalResult))
    print("RAM Result: " + str(ramFinalResult))
    print('Tests', 'passed' if (sdFinalResult & ramFinalResult) else 'failed')
    
spi = SPI(1, baudrate = 40000000, sck = Pin(10), mosi = Pin(11), miso = Pin(12))
sd = sdcard.SDCard(spi, Pin(13))
#sd._cache.reset_cache(cache_max_size=1, read_ahead=1)  # or cache_max_size=0

vfs=os.VfsFat(sd)    
os.mount(sd, sdDir)

#if (useCore1 == True):
bdev = RAMBlockDevExt(512, 100)
os.VfsFat.mkfs(bdev)
os.mount(bdev, rbDir)

asyncio.run(main(sdDir, rbDir))