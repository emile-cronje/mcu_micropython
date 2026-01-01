import uasyncio as asyncio
import gc
import os
import usqlite
import micropython
import pyb

event_test = asyncio.Event()
resetDbConn = False
dbConn = None
useSql = True
loopCount = 0

# Exception raised by get_nowait().
class QueueEmpty(Exception):
    pass

# Exception raised by put_nowait().
class QueueFull(Exception):
    pass

class Queue:
    def __init__(self, maxsize=0):
        self.maxsize = maxsize
        self._queue = []
        self._evput = asyncio.Event()  # Triggered by put, tested by get
        self._evget = asyncio.Event()  # Triggered by get, tested by put

    def _get(self):
        self._evget.set()  # Schedule all tasks waiting on get
        self._evget.clear()
        return self._queue.pop(0)

    async def get(self):  #  Usage: item = await queue.get()
        while self.empty():  # May be multiple tasks waiting on get()
            # Queue is empty, suspend task until a put occurs
            # 1st of N tasks gets, the rest loop again
            await self._evput.wait()
        return self._get()

    def get_nowait(self):  # Remove and return an item from the queue.
        # Return an item if one is immediately available, else raise QueueEmpty.
        if self.empty():
            raise QueueEmpty()
        return self._get()

    def _put(self, val):
        self._evput.set()  # Schedule tasks waiting on put
        self._evput.clear()
        self._queue.append(val)

    async def put(self, val):  # Usage: await queue.put(item)
        while self.full():
            # Queue full
            await self._evget.wait()
            # Task(s) waiting to get from queue, schedule first Task
        self._put(val)

    def put_nowait(self, val):  # Put an item into the queue without blocking.
        if self.full():
            raise QueueFull()
        self._put(val)

    def qsize(self):  # Number of items in the queue.
        return len(self._queue)

    def empty(self):  # Return True if the queue is empty, False otherwise.
        return len(self._queue) == 0

    def full(self):  # Return True if there are maxsize items in the queue.
        # Note: if the Queue was initialized with maxsize=0 (the default) or
        # any negative number, then full() is never True.
        return self.maxsize > 0 and self.qsize() >= self.maxsize
    
async def produce(queue):
    icount = 0

    while True:
        await queue.put(str(icount))  # Put result on queue        
        icount += 1
        await asyncio.sleep(.02)

async def consume(queue, dbName):
    global resetDbConn, dbConn, loopCount

    while True:
        await event_test.wait()

        while (queue.qsize() > 20):
            item = await queue.get()  # Blocks until data is ready            
#            print("Pulled item..." + str(item))

            if (useSql == True):
                #if (resetDbConn == True):
                 #   await InitDb(dbName, initDb = True)                                    
                    #await resetDb(dbName, closeConn = False)
                    
                # await ExecuteMany(
                #     "BEGIN TRANSACTION;"
                #     f"INSERT INTO items VALUES ({item}, 0, '{item}', '{item}', False);"
                #     "COMMIT;")

                recordCount = 0

                # async with Execute("SELECT COUNT(*) from items;") as cur:
                #     for row in cur:
                #         count = row[0]
                #         print("items count:", count)

                #micropython.mem_info()

                if (loopCount == -1):
                    print("Exec select...")                    
                    #before = gc.mem_free()                    
                    cur = await Execute("SELECT COUNT(ID) from items;")
                    #after = gc.mem_free()                    
#                    print("Select took up", before - after, "bytes.")                    

                    if (cur == None):
                        print("items count: None")                    
                    else:
                        for row in cur:
                            recordCount = row[0]
                            print("items count:", recordCount)

                    cur.close()                

                loopCount += 1
                # if (count > 100):
                #     await ExecuteMany(
                #         "BEGIN TRANSACTION;"
                #         "DELETE FROM items;"
                #         "COMMIT;")

    #                dbConn.execute("DELETE FROM items;")

            with open('/sd/hello.txt', 'w+') as f:
                f.write(item)
            
            await asyncio.sleep(.01)

        event_test.clear()

async def resetDb(dbName, closeConn = False):
    global resetDbConn, dbConn, loopCount

    print("Start dbConn reset...")
    #gc.collect()    

    if (closeConn == True):
        try:
            dbConn.close()
            print('close success')                
        except:
            print('close fail')        

        dbConn = usqlite.connect(dbName)

    resetDbConn = False
    loopCount = 0
    print("Completed dbConn reset...\r\n")

async def ExecuteMany(sql):
    global dbConn

    dbConn.executemany(sql)

async def Execute(sql):
    global dbConn

    return dbConn.execute(sql)


async def watchQueue(queue):
    while True:
        if (queue.qsize() > 50):
            event_test.set()

        await asyncio.sleep(.5)

async def showQueueLength(queue):
    while True:
        print("Queue length..." + str(queue.qsize()))
        await asyncio.sleep(2)

async def showMemUsage():
    while True:
        print(free(True))
        await asyncio.sleep(5)

def free(full=False):
    global resetDbConn
    
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F+A
    P = '{0:.2f}%'.format(F/T*100)
    
    if ((F/T*100) < 35):
        resetDbConn = True;
        
    if not full: return P
    else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))

async def InitDb(dbName, initDb = True):
     global dbConn

     dbConn = usqlite.connect(dbName)    

     if initDb:
         dbConn.execute("DROP TABLE IF EXISTS items")
         dbConn.execute('''CREATE TABLE IF NOT EXISTS items
                         (ID            INTEGER,
                         VERSION        INTEGER NOT NULL,
                         NAME           TEXT    NOT NULL,
                         DESCRIPTION    TEXT    NOT NULL,         
                         IS_COMPLETE    BOOL     NOT NULL);''')
         dbConn.execute("DELETE FROM items")
         dbConn.execute('''CREATE UNIQUE INDEX index_item_name ON items(name, description)''')
         print("Db ok")

#os.rmdir('sd')
#os.mkdir('sd')

os.mount(pyb.SDCard(), '/sd')
dbName="/sd/data.db"
#os.remove("/sd/data.db")

if not usqlite.mem_status():
    usqlite.mem_status(True) # Enable memory usage monitoring

async def main():
    queue = Queue()    

    if (useSql == True):
        await InitDb(dbName, initDb = True)

    asyncio.create_task(produce(queue))            
    asyncio.create_task(consume(queue, dbName))                
    asyncio.create_task(watchQueue(queue))                    
    asyncio.create_task(showQueueLength(queue))
    asyncio.create_task(showMemUsage())    

    print('Tasks are running...')
    while True:
        await asyncio.sleep(5)

asyncio.run(main())
