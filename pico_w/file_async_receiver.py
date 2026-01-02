from mqtt_as import MQTTClient, config
import uasyncio as asyncio
import gc
import ujson
import uhashlib
import ubinascii
import machine
import os, uos
import time
from machine import SPI, Pin
import sdcard
from cpu_monitor_class import CPUMon
from aclock_class import AClock

SERVER = '192.168.10.124'
SERVER = '192.168.10.135'
SERVER = '192.168.10.174'

_error_q = {}
_success_q = {}
_in_hash_md5 = uhashlib.sha256()
fout = None
backupDir = '/sd/backups_new'

def callback(topic, msg_in, retained):
    global _success_q, _error_q
    #print((topic, msg_in, retained))
    msg = ujson.loads(msg_in)
    
    if ("Category" in msg.keys()):
        category = msg["Category"]
    
        if (category == 'Files'):
            step = msg["Step"]
            
            if (step == 'Start'):
                print("starting sync...")
                _success_q.clear()
                _error_q.clear()
            else:
                print("processing file...")                
                processFile(msg, _success_q, _error_q)
                
        if (category == 'Test'):
            message = msg["Message"]
            print("Test: " + message)
    
async def conn_han(client):
    await client.subscribe('pico1_files', 1)
    print("subscribed to pico1_files...")
    await client.subscribe('pico1_test', 1)
    print("subscribed to pico1_test...")

def processFile(msg, success_q, error_q):
    global _in_hash_md5, fout
   
    print("process file...")
    step = msg["Step"]
    #print("Msg: " + str(msg))
    
    if (step == "Header"):
        print("Processing header...")        
        _in_hash_md5 = uhashlib.sha256()              
        file_name = msg["FileName"]            
        file_out = backupDir + "/copy-" + file_name
        print("creating file: " + file_out)        
        fout = open(file_out, "wb")
        print("created file: " + file_out)
        success_q[file_name] = 'File copy starting...'

        if (file_name in error_q.keys()):
            del error_q[file_name]

    elif (step == "Content"):
        print("Processing content...")                
        file_name = msg["FileName"]                            
        file_data = ubinascii.a2b_base64(msg["FileData"])
        _in_hash_md5.update(file_data)
        progress = msg["ProgressPercentage"]                                    
        success_q[file_name] = 'File copy in progress...' + str(progress) + '%'
        
        if (fout != None):
            fout.write(file_data)

    elif (step == "End"):
        print("Processing end...")
        file_name = msg["FileName"]                        
        in_hash_final = _in_hash_md5.digest()
        base64_hash_data = ubinascii.b2a_base64(in_hash_final)[:-1]
        base64_hash_data_string = base64_hash_data.decode("utf-8")
        in_msg_hash = msg["HashData"]
        
        if (base64_hash_data_string == in_msg_hash):
            success_q[file_name] = "File copy OK"
        else:
            error_q[file_name] = "File copy failed"
            print("msg hash:" + in_msg_hash)
            print("file hash:" + base64_hash_data_string)            
    
def file_exist(filename):
    try:
        f = open(filename, "r")
        exists = True
        f.close()
    except OSError:
        exists = False
    return exists        
    
async def main(client):
    await client.connect()
    n = 0
    
    while True:
        await asyncio.sleep(2)
        #print('publish', n)
        #await client.publish('stm32_topic', '{}'.format(n), qos = 1)
        n += 1

def free(full=False):
#  gc.collect()
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))

def dir_exists(path):
    try:
        f = os.listdir(path)
        
        if f != []:
            return True
        else:
            return False
    except OSError:
        return False

async def monitorStatusQueues(success_q, error_q):
    while True:
        print("Error Queue length..." + str(len(error_q)))
        print("Success Queue length..." + str(len(success_q)))        

        for key, value in success_q.items():
            print(key, ' : ', value)

        for key, value in error_q.items():
            print(key, ' : ', value)

        print("Memory status..." + free(True))
        print("Time..." + str(time.gmtime()))                
        await asyncio.sleep(3)

def clockTest():
    clock = AClock()
    clock.run()

config['subs_cb'] = callback
config['connect_coro'] = conn_han
config['server'] = SERVER

# Assign chip select (CS) pin (and start it high)
cs = machine.Pin(22, machine.Pin.OUT)

# Intialize SPI peripheral (start with 1 MHz)
spi = machine.SoftSPI(
                  baudrate=1000000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(5),
                  mosi=machine.Pin(18),
                  miso=machine.Pin(19))

# Initialize SD card
sd = sdcard.SDCard(spi, cs)

# Mount filesystem
vfs = uos.VfsFat(sd)
uos.mount(vfs, "/sd")

#spi = SPI(1, baudrate = 40000000, sck = Pin(10), mosi = Pin(11), miso = Pin(12))
#sd = sdcard.SDCard(spi, Pin(13))
#vfs=os.VfsFat(sd)    
#os.mount(sd, "/sd")

if (dir_exists(backupDir) == True):
#    print("removing: " + backupDir)    
 #   os.rmdir(backupDir)
  #  print("removed: " + backupDir)
   # os.mkdir(backupDir)
    #print("created: " + backupDir)
    print("dir exists: " + backupDir)    
else:
    print("making new " + backupDir)    
    os.mkdir(backupDir)
    print("created: " + backupDir)    

MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)

try:
    asyncio.create_task(monitorStatusQueues(_success_q, _error_q))
    
    cpuMon = CPUMon()
    useCore1 = True
    asyncio.create_task(cpuMon.main(worker_func = clockTest, useCore1 = useCore1, showUsage = True))
    
    asyncio.run(main(client))
finally:
    client.close()