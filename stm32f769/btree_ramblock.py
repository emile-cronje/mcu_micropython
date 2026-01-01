import os
import pyb
import gc
import btree
import uasyncio as asyncio
from uasyncio import Lock
import time

class RAMBlockDevExt:
    def __init__(self, block_size, num_blocks):
        self.block_size = block_size
        self.data = bytearray(block_size * num_blocks)

    def readblocks(self, block_num, buf, offset=0):
        addr = block_num * self.block_size + offset
        for i in range(len(buf)):
            buf[i] = self.data[addr + i]

    def writeblocks(self, block_num, buf, offset=None):
        if offset is None:
            # do erase, then write
            for i in range(len(buf) // self.block_size):
                self.ioctl(6, block_num + i)
            offset = 0
        addr = block_num * self.block_size + offset
        for i in range(len(buf)):
            self.data[addr + i] = buf[i]

    def ioctl(self, op, arg):
        if op == 4: # block count
            return len(self.data) // self.block_size
        if op == 5: # block size
            return self.block_size
        if op == 6: # block erase
            return 0

class RAMBlockDev:
    def __init__(self, block_size, num_blocks):
        self.block_size = block_size
        self.data = bytearray(block_size * num_blocks)

    def readblocks(self, block_num, buf):
        print('reading...')
        for i in range(len(buf)):
            buf[i] = self.data[block_num * self.block_size + i]

    def writeblocks(self, block_num, buf):
        print('writing...')        
        for i in range(len(buf)):
            self.data[block_num * self.block_size + i] = buf[i]

    def ioctl(self, op, arg):
        if op == 4: # get number of blocks
            return len(self.data) // self.block_size
        if op == 5: # get block size
            return self.block_size

def free(full=False):
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))

bdev = RAMBlockDevExt(512, 50)
os.VfsFat.mkfs(bdev)
os.mount(bdev, '/ramdisk')
os.mount(pyb.SDCard(), "/sd")
ramBefore = free(True)

try:
    fsd = open("/sd/mydb", "r+b")
    fram = open("/ramdisk/mydb", "r+b")    
except OSError:
    fsd = open("/sd/mydb", "w+b")
    fram = open("/ramdisk/mydb", "w+b")    

dbsd = btree.open(fsd)
dbram = btree.open(fram)
dbram1 = btree.open(fram)

async def writeDoDisk(instance, rangeStart, rangeEnd, db):
    print('Running...' + str(instance))
    print('Start...' + str(rangeStart))
    print('End...' + str(rangeEnd))
    print('db...:' + str(db))

    for x in range(rangeStart, rangeEnd):
        key = str(time.time_ns())
        key = str(x)        
        db[key] = x.to_bytes(4, 'big')
        await asyncio.sleep_ms(10)        
        
    db.flush

        
async def main():
    blocksize = 10
    
    for x in range(1, 11):
        asyncio.create_task(writeDoDisk(x, x, x * blocksize, dbsd))
        asyncio.create_task(writeDoDisk(x, x, x * blocksize, dbsd))
        await asyncio.sleep(1)
        
    print('Tasks are running...')
    await asyncio.sleep(5)
    
    icountdbram = 0
    icountdbsd = 0

    for key in dbram:
        icountdbram += 1
            
    for key in dbsd:
        icountdbsd += 1
    
    print("ram : " + str(icountdbram))
    print("sd : " + str(icountdbsd))
    
#    for item in db.items():
 #       print("ram item : " + str(item))
    
    dbram.close()
    dbram1.close()    
    dbsd.close()    

start = time.time()
print(free(True))
asyncio.run(main())
end = time.time()
print(free(True))
print(os.statvfs('/sd'))
print(os.statvfs('/ramdisk'))

# Don't forget to close the underlying stream!
fsd.close()
fram.close()

print(end - start)

