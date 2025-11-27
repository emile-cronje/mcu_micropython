import uasyncio as asyncio
from queue import Queue
import gc
import sqlite
import os
import time
from ToDoItem import ToDoItem
from ToDoControllerSqlite import ToDoController
from ToDoDaoSqlite import ToDoDaoSqlite
import sdcard
from machine import SPI, Pin

event_test = asyncio.Event()
toDoController = None
dbConn = None

async def produce(queue):
    id = 1
    
    while True:
        item = ToDoItem()
        item.id = id
        item.version = 0
        item.name = "ToDoItem_Name_" + str(item.id)
        item.description = "ToDoItem_Desc_" + str(item.id)
        item.isComplete = False
        
        await queue.put(item)
        await asyncio.sleep(1.5)
        id += 1

async def consume(queue):
    global toDoController
    
    while True:
        while (queue.qsize() > 10):
            item = await queue.get()
            print("Pulled item..." + str(item.name))
            await toDoController.AddItem(item.__dict__)
            print("Saved item..." + str(item.name))            
            
        await asyncio.sleep(1)                        

async def watchQueue(queue):
    while True:
        if (queue.qsize() > 20):
            event_test.set()

        await asyncio.sleep(1)

async def showQueueLength(queue):
    while True:
        itemCount = await toDoController.GetItemCount()

        if (itemCount > 10):
            await toDoController.DeleteAllItems()                        
            print("All items deleted...")            

        print("Queue length..." + str(queue.qsize()))
        print("Record count..." + str(itemCount))        
        await asyncio.sleep(1)

async def showMemUsage():
    while True:
        print(free(True))
        await asyncio.sleep(5)

async def resetDb(dbName):
    global dbConn

    while True:
        await asyncio.sleep(5)        
#        event_db_ready.clear()        
        dbConn.close()
        dbConn = sqlite.connect(dbName)        
 #       event_db_ready.set()

def free(full=True):
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)

  if ((F/T*100) < 20):
    gc.collect()
    print("GC collect...")

  if not full: return P
  else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))

async def main():
    queue = Queue()
    dbName = await init()    
    asyncio.create_task(produce(queue))            
    asyncio.create_task(consume(queue))                
#    asyncio.create_task(watchQueue(queue))                    
    asyncio.create_task(showQueueLength(queue))
    asyncio.create_task(showMemUsage())    
    #asyncio.create_task(resetDb(dbName))        

    print('Tasks are running...')
    while True:
        await asyncio.sleep(5)

async def init():
    global toDoController
    global dbConn    

    dbName = '/sd/test_data'
    dbName = ':memory:'    
    
#    if (dbName in os.listdir()):
 #       os.remove(dbName)
        
    dbConn = sqlite.connect(dbName)
    
    toDoDaoSqlite = ToDoDaoSqlite(dbConn)
    await toDoDaoSqlite.InitDb()
    
    toDoDao = toDoDaoSqlite    
    toDoController = ToDoController(None, toDoDao)    

    return dbName

sdDir = '/sd'
spi = SPI(1, baudrate = 40000000, sck = Pin(10), mosi = Pin(11), miso = Pin(12))
sd = sdcard.SDCard(spi, Pin(13))
vfs=os.VfsFat(sd)    
os.mount(sd, sdDir)

asyncio.run(main())
