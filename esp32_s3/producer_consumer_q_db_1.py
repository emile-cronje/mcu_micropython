import uasyncio as asyncio
from queue import Queue
import gc
import sqlite
import os
import time
from ToDoItem import ToDoItem
from ToDoController import ToDoController
from ToDoDaoSqlite import ToDoDaoSqlite

event_test = asyncio.Event()
toDoController = None
dbConn = None

async def produce(queue):
    id = 1
    
    while True:
        #print("producer...id:" + str(id))        
        item = {}
        item["id"] = id        
        item["version"] = 0
        item["name"] = "ToDoItem_Name_" + str(id)
        item["description"] = "ToDoItem_Desc_" + str(id)
        item["isComplete"] = False
        item["messageId"] = id
        item["clientId"] = 1
        
        await queue.put(item)
        await asyncio.sleep(.5)
        id += 1

async def consume(queue):
    global toDoController

    while True:
        while queue.qsize():
            item = await queue.get()
            await toDoController.AddItem(item)
        await asyncio.sleep(0.1)

async def watchQueue(queue):
    while True:
        if (queue.qsize() > 1):
            event_test.set()

        await asyncio.sleep(1)

async def showQueueLength(queue):
    while True:
        itemCount = await toDoController.GetItemCount()

        if (itemCount > 50):
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
        dbConn.close()
        dbConn = sqlite.connect(dbName)        

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
    await init()    
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

    dbName = 'test_data.db'
    dbName = ':memory:'    
    
#    if (dbName in os.listdir()):
 #       os.remove(dbName)
        
    dbConn = sqlite.connect(dbName)
    
    toDoDaoSqlite = ToDoDaoSqlite(dbConn)
    await toDoDaoSqlite.InitDb()
    
    toDoDao = toDoDaoSqlite    
    toDoController = ToDoController(None, toDoDao, [])    

    return dbName

asyncio.run(main())
