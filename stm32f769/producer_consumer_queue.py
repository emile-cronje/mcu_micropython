import uasyncio as asyncio
from machine import Pin
from queue import Queue
import gc

event_test = asyncio.Event()

async def produce(queue):
    icount = 0

    while True:
        await queue.put(str(icount))  # Put result on queue        
        icount += 1
        await asyncio.sleep(.2)

async def consume(queue):
    while True:
        await event_test.wait()

        while (queue.qsize() > 20):
            item = await queue.get()  # Blocks until data is ready            
            print("Pulled item..." + str(item))                    
            await asyncio.sleep(.1)

        event_test.clear()

async def watchQueue(queue):
    while True:
        if (queue.qsize() > 100):
            event_test.set()

        await asyncio.sleep(1)

async def showQueueLength(queue):
    while True:
        print("Queue length..." + str(queue.qsize()))
        await asyncio.sleep(2)

async def showMemUsage():
    while True:
        print(free(True))
        await asyncio.sleep(5)

def free(full=False):
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))

async def main():
    queue = Queue()    
    asyncio.create_task(produce(queue))            
    asyncio.create_task(consume(queue))                
    asyncio.create_task(watchQueue(queue))                    
    asyncio.create_task(showQueueLength(queue))
    asyncio.create_task(showMemUsage())    

    print('Tasks are running...')
    while True:
        await asyncio.sleep(5)

asyncio.run(main())
