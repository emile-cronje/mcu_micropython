import uasyncio as asyncio
from queue import Queue
import gc
import usqlite
import os
import time
from TodoItem import ToDoItem
from ToDoControllerCustom import ToDoController
from ToDoDaoSqlite import ToDoDaoSqlite
import pyb

event_test = asyncio.Event()
event_db_ready = asyncio.Event()
toDoController = None
dbConn = None

async def produce(queue):
    while True:
        item = ToDoItem()
        item.id = time.time_ns()
        item.version = 0
        item.name = "ToDoItem_Name_" + str(item.id)
        item.description = "ToDoItem_Desc_" + str(item.id)
        item.isComplete = False
        
        await queue.put(item)
        await asyncio.sleep(.2)

async def consume(queue):
    global toDoController
    
    while True:
        await event_test.wait()
        await event_db_ready.wait()

        while (queue.qsize() > 20):
            item = await queue.get()  # Blocks until data is ready            
            print("Pulled item..." + str(item.name))
            await toDoController.AddItem(item.__dict__)            
            await asyncio.sleep(.3)

        event_test.clear()
        event_db_ready.clear()

async def watchQueue(queue):
    while True:
        if (queue.qsize() > 50):
            event_test.set()

        await asyncio.sleep(1)

async def showQueueLength(queue):
    while True:
        itemCount = await toDoController.GetItemCount()

        if (itemCount > 50):
            await toDoController.DeleteAllItems()                        

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
        event_db_ready.clear()        
        dbConn.close()
        dbConn = usqlite.connect(dbName)        
        event_db_ready.set()

def free(full=True):
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))

async def main():
    queue = Queue()
    dbName = await init()    
    asyncio.create_task(produce(queue))            
    asyncio.create_task(consume(queue))                
    asyncio.create_task(watchQueue(queue))                    
    asyncio.create_task(showQueueLength(queue))
    asyncio.create_task(showMemUsage())    
    #asyncio.create_task(resetDb(dbName))        

    print('Tasks are running...')
    while True:
        await asyncio.sleep(5)

async def init():
    global toDoController
    global dbConn    

    dbName = '/sd/test.db'
    
    if (dbName in os.listdir()):
        os.remove(dbName)

    print('sql connecting...')
    
    try:
        dbConn = usqlite.connect(dbName)
    except OSError as e:
        print(str(e))

    print('sql connected...')    
    
    toDoDaoSqlite = ToDoDaoSqlite(dbConn)
    await toDoDaoSqlite.InitDb()
    
    toDoDao = toDoDaoSqlite    
    toDoController = ToDoController(None, toDoDao)    

    return dbName
    
os.mount(pyb.SDCard(), "/sd")
asyncio.run(main())
