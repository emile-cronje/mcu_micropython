import sys
sys.path.append('.')
from rp2_dma import *

dma = DMA(0)
src_buf = b"abc!"*5000
dst_buf = bytearray(12*5000)

dma.config(
    src_addr = uctypes.addressof( src_buf ),
    dst_addr = uctypes.addressof( dst_buf ),
    count = len( src_buf ),
    src_inc = True,
    dst_inc = True,
    trig_dreq = DMA.DREQ_PERMANENT
)

t0 = time.ticks_us()
dma.enable()

while(dma.is_busy()):
    pass

dma.disable()
t1 = time.ticks_us()

print( "dst", dst_buf[0:50], "..." )

print( "Transfer speed [B/s]:", len( src_buf )/((t1-t0)*1e-6) )
print( "@CPU freq:", machine.freq() )