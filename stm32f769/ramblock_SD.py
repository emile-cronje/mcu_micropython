import os
import pyb
import gc
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
#        print('reading...')
        for i in range(len(buf)):
            buf[i] = self.data[block_num * self.block_size + i]

    def writeblocks(self, block_num, buf):
#        print('writing...')        
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

bdev = RAMBlockDevExt(512, 200)
#bdev = RAMBlockDev(512, 200)
os.VfsFat.mkfs(bdev)
os.mount(bdev, '/ramdisk')
os.mount(pyb.SDCard(), "/sd")
ramBefore = free(True)

icount = 100

start = time.time()

while (icount > 0):
    with open('/ramdisk/hello.txt', 'w+') as f:
        s = 'opening ramdisk...' + str(icount)
        print(s)
        f.write(s)
        
    with open('/sd/hello.txt', 'w+') as f:
        s = 'opening sd...' + str(icount)
        print(s)
#        f.write(s)

    icount -= 1;

#print(open('/ramdisk/hello.txt').read())
#print(open('/sd/hello.txt').read())
ramAfter = free(True)
print("before:", ramBefore)
print("after:", ramAfter)

end = time.time()
print("------")
print(end - start)
print("seconds...")
