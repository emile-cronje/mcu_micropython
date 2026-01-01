import os, time
import machine
from machine import SPI, Pin
import gc
import time
import utime
import pyb

sdDir = "/sd"
TESTFILE = "/sd/test.bin"
SIZE = 1024 * 1000   # 100 KB file for quick test
CHUNK = 512         # 512 bytes at a time

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

os.mount(pyb.SDCard(), sdDir)    

print("Running SD card benchmark...")
test_write()
test_read()
