import uasyncio as asyncio
from machine import Pin
from queue import Queue
import gc
import os
from btree_custom_crud import BTree
import time, random
from ToDoItem import ToDoItem
import json
from machine import SPI
import sdcard
import machine, pyb

sd1Dir = '/sd1'
sd2Dir = '/sd2'

event_test = asyncio.Event()

async def produce(queue):
    icount = 0
    sleep_for = random.random()    

    while True:
        item = ToDoItem()
        item.id = time.time_ns()
        item.version = 1
        item.description = 'one_' + str(item.id)
        item.isComplete = False
        
        await queue.put(json.dumps(item.__dict__))
        icount += 1
        await asyncio.sleep(sleep_for)

async def consume(queue, dir, taskId):
    fileNameCustom = dir + '/btree_data_' + str(time.time_ns()) + '_custom.json'    
    dbCustom = BTree(10, fileNameCustom)
    sleep_for = random.random()
    nodeCount = 0
    
    while True:
        await event_test.wait()

        while (queue.qsize() > 20):
            itemJson = await queue.get()
            key = time.time_ns().to_bytes(4, 'little')            
            treeNodeCount = dbCustom.count_all()
            nodeCount += 1            
            
            if (treeNodeCount > 20):
                print("Delete all..." + str(taskId))
                dbCustom.delete_all()
                nodeCount = 0                
                
            dbCustom.insert(key, itemJson)
            savedItem = dbCustom.get_value(key)
            
            #if (treeNodeCount != nodeCount):
             #   print("Item count mismatch...")                
                
            if (itemJson != savedItem):
                print("Items mismatch...")

            await asyncio.sleep(sleep_for)

        event_test.clear()

async def watchQueue(queue):
    while True:
        if (queue.qsize() > 20):
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

async def main(sd1Dir, sd2Dir):
    queue = Queue()
    consumerCount = 2
    producerCount = 2    
    
    for i in range(producerCount):    
        asyncio.create_task(produce(queue))
    
    for i in range(consumerCount):
        asyncio.create_task(consume(queue, sd1Dir, i))
        asyncio.create_task(consume(queue, sd2Dir, i))                

    asyncio.create_task(watchQueue(queue))                    
    asyncio.create_task(showQueueLength(queue))
    asyncio.create_task(showMemUsage())    

    print('Tasks are running...')
    
    while True:
        await asyncio.sleep(5)
    
cs = Pin('D8', mode=Pin.OUT, value=1)
spi = SPI(2, baudrate = 40000000)
sd = sdcard.SDCard(spi, cs)
vfs=os.VfsFat(sd)    
os.mount(pyb.SDCard(), sd1Dir)
os.mount(sd, sd2Dir)

asyncio.run(main(sd1Dir, sd2Dir))


