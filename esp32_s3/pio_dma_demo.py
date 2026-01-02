import time, uctypes, machine
from machine import Pin
import rp2
from rp2_dma import DMA

# ==== PIO programs: 8-bit wide with separate clock (sideset) ====

@rp2.asm_pio(
    sideset_init=rp2.PIO.OUT_LOW,               # CLK starts low
    out_init=(rp2.PIO.OUT_LOW,)*8,              # 8 data pins start low
    out_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopull=True, pull_thresh=8                # pull 1 byte at a time
)
def tx8():
    out(pins, 8)         .side(0)   [1]   # present byte on 8 data pins, CLK low
    nop()                .side(1)   [1]   # CLK high (sample edge for receiver)
    nop()                .side(0)   [1]   # CLK low

@rp2.asm_pio(
    in_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopush=True, push_thresh=8
)
def rx8():
    # jmp_pin is the clock line
    wait(1, pin, 0)                     # wait for CLK high
    in_(pins, 8)                         # sample 8 data pins into ISR
    wait(0, pin, 0)                      # wait for CLK low (ready for next)

# ==== Pin plan ====
# TX: data base = GP2..GP9 (8 pins), clk = GP10
# RX: data base = GP12..GP19 (8 pins), clk = GP11
TX_DATA_BASE = 2
TX_CLK_PIN   = 10
RX_DATA_BASE = 12
RX_CLK_PIN   = 11

# Create state machines on PIO0
sm_tx = rp2.StateMachine(
    0, tx8, freq=500_000,                # PIO instruction clock ~500 kHz (slow & stable for demo)
    out_base=Pin(TX_DATA_BASE),
    sideset_base=Pin(TX_CLK_PIN)
)

sm_rx = rp2.StateMachine(
    1, rx8, freq=500_000,
    in_base=Pin(RX_DATA_BASE),
    jmp_pin=Pin(RX_CLK_PIN)
)

# ==== Test buffers ====
N = 32 * 1024                             # bytes to send/receive

if N % 4:
    N += 4 - (N % 4)

# Build a source buffer with 32-bit alignment
import array
src = array.array('I', ( (i & 0xFF) | ((i+1 & 0xFF)<<8) | ((i+2 & 0xFF)<<16) | ((i+3 & 0xFF)<<24)
                          for i in range(0, N, 4) ))
dst = array.array('I', [0] * (N // 4))

#src = bytes((i & 0xFF) for i in range(N)) # known pattern 0..255
#dst = bytearray(N)

# ==== PIO FIFO register addresses (RP2040 datasheet) ====
PIO0_BASE = 0x50200000
PIO_TXF0  = 0x10  # offset to TXF0
PIO_RXF0  = 0x20  # offset to RXF0
txf_sm0   = PIO0_BASE + PIO_TXF0 + 4*0    # SM0 TX FIFO
rxf_sm1   = PIO0_BASE + PIO_RXF0 + 4*1    # SM1 RX FIFO

# ==== DMA setup ====
dma_tx = DMA(0)
dma_tx.config(
    src_addr   = uctypes.addressof(src),
    dst_addr   = txf_sm0,
    count      = len(src),       # number of 32-bit words
    src_inc    = True,
    dst_inc    = False,
    transfer_size = 32,                # or DMA.SIZE_32 / WORD, depending on your lib
    trig_dreq  = 0
)

dma_rx = DMA(1)
dma_rx.config(
    src_addr   = rxf_sm1,
    dst_addr   = uctypes.addressof(dst),
    count      = len(dst),       # number of 32-bit words
    src_inc    = False,
    dst_inc    = True,
    transfer_size = 32,
    trig_dreq  = 5
)

# ==== Run ====
# Ensure FIFOs are empty before start
sm_tx.active(0); sm_rx.active(0)
sm_tx.exec("pull()")  # harmless priming; ensures known state
sm_tx.active(1)
sm_rx.active(1)

t0 = time.ticks_us()
dma_rx.enable()
dma_tx.enable()

# Wait for both transfers to finish
while dma_tx.is_busy() or dma_rx.is_busy():
    pass

dma_tx.disable()
dma_rx.disable()
t1 = time.ticks_us()

sm_tx.active(0)
sm_rx.active(0)

# ==== Verify ====
elapsed_s = (t1 - t0) * 1e-6
dst = dst.tobytes()
ok = (dst == src)
print("Bytes TX/RX:", N)
print("Match      :", ok)
print("First 32   :", dst[:32])
print("Time (s)   :", elapsed_s)
print("Throughput :", int(N / elapsed_s), "B/s @ CPU", machine.freq())

if not ok:
    # Minimal debugging help
    for i, (a, b) in enumerate(zip(src, dst)):
        if a != b:
            print("First mismatch at index", i, "TX:", a, "RX:", b)
            break
