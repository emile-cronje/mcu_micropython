from machine import Pin
import time

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def bounce():
    pull()
    mov(isr, osr)
    push()

sm = rp2.StateMachine(0, bounce, freq=4000, set_base=Pin(25))

sm.put(31)
print("Number of words in tx",sm.tx_fifo())
print("Number of words in rx",sm.rx_fifo())
print("Run")
sm.active(1)
time.sleep(1)
print("Stop")
sm.active(0)
print("Number of words in tx",sm.tx_fifo())
print("Number of words in rx",sm.rx_fifo())
print("Get from rx", sm.get())