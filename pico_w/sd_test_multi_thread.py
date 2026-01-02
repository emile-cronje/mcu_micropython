import _thread
import machine
import os
import sdcard
from machine import SPI, Pin

sdDir = '/sd'
spi = SPI(1, baudrate = 40000000, sck = Pin(10), mosi = Pin(11), miso = Pin(12))
sd = sdcard.SDCard(spi, Pin(13))
vfs=os.VfsFat(sd)    
os.mount(sd, sdDir)

sd_lock = _thread.allocate_lock()

def core1_writer():
    # This function runs on Core 1
    while True:
        sd_lock.acquire()
        
        try:
            with open("/sd/data1.txt", "a") as f:
                f.write("Data from Core 1\n")
            print("Core 1 wrote to SD card.")
            
            with open("/sd/data1.txt",'r') as f:
                result_long = f.read()
                print(str(len(result_long)) + ' bytes read')
            
        finally:
            # Always release the lock, even if an error occurs
            sd_lock.release()
        
        # Do other work or sleep
        # ...

def core0_writer():
    # This function runs on Core 0
    while True:
        sd_lock.acquire()
        
        try:
            with open("/sd/data0.txt", "a") as f:
                f.write("Data from Core 0\n")
            print("Core 0 wrote to SD card.")
        finally:
            # Always release the lock
            sd_lock.release()

# Start the thread on Core 1
_thread.start_new_thread(core1_writer, ())

# Core 0 runs its own writer
core0_writer()