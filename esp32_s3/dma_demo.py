from rp2 import DMA
from uctypes import addressof
from array import array
import time

def gather_strings(string_list, buf, gather_dma, buffer_dma):
    # We use two DMA channels. The first sends lengths and source addresses from the gather
    # list to the registers of the second. The second copies the data itself.

    # Pack up length/address pairs to be sent to the registers.
    gather_list = array("I")

    for s in string_list:
        gather_list.append(len(s))
        gather_list.append(addressof(s))

    gather_list.append(0)
    gather_list.append(0)

    # When writing to the registers of the second DMA channel, we need to wrap the
    # write address on an 8-byte (1<<3 bytes) boundary. We write to the ``TRANS_COUNT``
    # and ``READ_ADD_TRIG`` registers in the last register alias (registers 14 and 15).
    gather_ctrl = gather_dma.pack_ctrl(ring_size=3, ring_sel=True)
    gather_dma.config(
        read=gather_list, write=buffer_dma.registers[14:16],
        count=2, ctrl=gather_ctrl
    )

    # When copying the data, the transfer size is single bytes, and when completed we need
    # to chain back to the start another gather DMA transaction.
    buffer_ctrl = buffer_dma.pack_ctrl(size=0, chain_to=gather_dma.channel)
    # The read and count values will be set by the other DMA channel.
    buffer_dma.config(write=buf, ctrl=buffer_ctrl)

    # Set the transfer in motion.
    gather_dma.active(1)

    # Wait until all the register values have been sent
    end_address = addressof(gather_list) + 4 * len(gather_list)
    
    while gather_dma.read != end_address:
        pass

inputStart = ["This is ", "a ", "test", " of the scatter", " gather", " process"]
gather_dma = DMA()
buffer_dma = DMA()

for id in range(10):
    output = bytearray(128)    
    input = inputStart
    print(input)
    input.append(str(id))
    gather_strings(input, output, gather_dma, buffer_dma)
    print(output)
    time.sleep_ms(100)