from microWorkers import MicroWorkers
from time import sleep
import os
import machine
from machine import SPI, Pin
import gc
import time
import _thread
from ramblock import RAMBlockDevExt, RAMBlockDev

finalResult = True
rbDir = '/rb'
_entityCount = 1000
sleepFor = 0
   
def fileTest(id, targetDir):
    global finalResult
    print("In fileTest for id...", id)
    sleep(2)
    
    counter = 0
    
    for count in range(_entityCount):
        counter += 1
        s = "Thread: " + str(id) + " Count: " + str(count + 1)
        print(s)
            
        line = 'abcdefghijklmnopqrstuvwxyz_' + str(count) + '\n'
        lines = line * (_entityCount + count)
        short = '1234567890\n'

        fn = targetDir + '/rats_long_' + str(id) + '.txt'
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

        fn = targetDir + '/rats_short_' + str(id) + '.txt'
        log('Single block read/write')
        
        with open(fn,'w') as f:
            n = f.write(short) # one block
            log(str(n) + ' bytes written')

        with open(fn,'r') as f:
            result_short = f.read()
            log(str(len(result_short)) + ' bytes read')

        log('Verifying data read back')
        success = True
        
        result_long = '1000'
        
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

        if (_entityCount == 1) and (result_short == (short + 'a')):
            log('Small file Pass')
        else:
            log('Small file Fail')
            success = False

    sleep(sleepFor)
    
    if (success == True):
        success = counter == (_entityCount)
    
    if (success == False):
        finalResult = False
        
    print('Tests', 'passed' if success else 'failed', str(id))

def writeToFile(fileName, data, targetDir = None):
    fileName += '.txt'
    print(f"Targetdir: {targetDir}")
    
    targetFile = '/rb/' + fileName
    print("Targetfile...:" + targetFile)
    
    with open(targetFile,'w') as f:
        print("opened " + targetFile + "\r\n")        
        n = f.write(data)
        print("writing to file.." + fileName + "\r\n")
        log(str(n) + ' bytes written')

def log(s):
    print(s)
    
def jobA(jobName, jobArg):
    global lock
    
    #lock.acquire()
    fileTest(jobArg, '/rb')
    writeToFile(jobName, str(time.time_ns()), '/rb')
    print("jobArg:", jobArg)
    sleep(.2)
    #lock.release()        
    return '%s:OK:1s' % jobName

def jobFinished(jobName, jobArg, jobResult):
    print('Job %s finished (%s)' % (jobName, jobResult))

def free(full=False):
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))

machine.freq(240000000)
bdev = RAMBlockDevExt(512, 2000)
os.VfsFat.mkfs(bdev)
os.mount(bdev, rbDir)

workers = MicroWorkers(workersCount=10, workersStackSize=1024)
lock = _thread.allocate_lock()
start = time.time()

for x in range(10):
    workers.AddJob('JobA_%s' % x, jobA, arg=x + 1, onFinished=jobFinished)
    workers.AddJob('JobB_%s' % x, jobA, arg=x + 2, onFinished=jobFinished)
    workers.AddJob('JobC_%s' % x, jobA, arg=x + 3, onFinished=jobFinished)    
    
while workers.IsWorking:
    #print("Jobs in progress..." + str(workers.JobsInProcess))
    #print("memory : " + free())    
    #print("Jobs in queue..." + str(workers.JobsInQueue))    
    sleep(1)
    
end = time.time()    
print(end - start)
print('seconds')
print("memory: ", free())

if (finalResult == True):
    print("All tests passed...")
else:
    print("Tests failed...")
    
os.umount('/rb')    