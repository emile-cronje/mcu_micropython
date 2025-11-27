import os, time
import machine

import sdcard as sdcard
from sdcard import SDCard

from machine import SPI, Pin
import gc
import time
import utime

sdDir = "/sd"
TESTFILE = "/sd/test.bin"
SIZE = 1024 * 500
CHUNK = 512
#CHUNK = 1024

def test_write():
    data = b'A' * CHUNK
    start = time.ticks_ms()
    
    with open(TESTFILE, "wb") as f:
        for _ in range(SIZE // CHUNK):
            f.write(data)
            
    elapsed = time.ticks_diff(time.ticks_ms(), start)
    kbps = SIZE / elapsed
    
    print("Write: %d bytes in %d ms = %.2f KB/s" %
          (SIZE, elapsed, kbps))

def test_read():
    start = time.ticks_ms()
    
    with open(TESTFILE, "rb") as f:
        while f.read(CHUNK):
            pass
        
    elapsed = time.ticks_diff(time.ticks_ms(), start)
    kbps = SIZE / elapsed
    print("Read: %d bytes in %d ms = %.2f KB/s" %
          (SIZE, elapsed, kbps))

spi = SPI(1, baudrate = 1000000, sck = Pin(10), mosi = Pin(11), miso = Pin(12))
sd = sdcard.SDCard(spi, Pin(13))
vfs=os.VfsFat(sd)    
os.mount(sd, sdDir)

print("Running SD card benchmark...")
test_write()
test_read()
