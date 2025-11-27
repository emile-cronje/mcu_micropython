import os
import machine
import sdcard
from machine import SPI, Pin
import gc
import uasyncio as asyncio
import time
from ramblock import RAMBlockDevExt, RAMBlockDev

entityCount = 50
threadCount = 4
finalResult = True
sdDir = '/fc'
rbDir = '/rb'
sleepFor = 0.05

async def sdtest(id, sdDir, mustDelete = False):
    global finalResult
    
    counter = 0
    
    for count in range(entityCount):
        counter += 1
        s = "Thread: " + str(id) + " Count: " + str(count + 1)
        print(s)
            
        line = 'abcdefghijklmnopqrstuvwxyz_' + str(id + count) + '\n'
        lines = line * entityCount
        short = '1234567890\n'

        fn = sdDir + '/rats_long_' + str(id) + '.txt'
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

        fn = sdDir + '/rats_short.txt'
        log('Single block read/write')
        
        with open(fn,'w') as f:
            n = f.write(short) # one block
            log(str(n) + ' bytes written')

        with open(fn,'r') as f:
            result_short = f.read()
            log(str(len(result_short)) + ' bytes read')

        log('Verifying data read back')
        success = True
        
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

    if (success == True):
        success = (counter == entityCount)
    
    if (success == False):
        finalResult = False
        return
        
    print('Tests', 'passed' if success else 'failed', str(id))

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
        task = asyncio.create_task(sdtest(id + 1, sdDir, True))
        tasks.append(task)        

    for id in range(threadCount):    
        task = asyncio.create_task(sdtest(id + 1, rbDir, True))
        tasks.append(task)        

    asyncio.create_task(showMemUsage())    
    print('Tasks are running...')

    await asyncio.gather(*tasks)
    
    end = time.time()    
    print(end - start)
    print('seconds')
    print('All Tests', 'passed' if finalResult else 'failed')
    
spi = SPI(1, baudrate = 40000000, sck = Pin(10), mosi = Pin(11), miso = Pin(12))
sd = sdcard.SDCard(spi, Pin(13))
vfs=os.VfsFat(sd)    
os.mount(sd, sdDir)

bdev = RAMBlockDevExt(512, 100)
os.VfsFat.mkfs(bdev)
os.mount(bdev, rbDir)
dir = rbDir    

asyncio.run(main(sdDir, rbDir))


