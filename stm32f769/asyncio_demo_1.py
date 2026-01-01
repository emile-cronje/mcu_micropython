import uasyncio as asyncio
from uasyncio import Lock

static_counter = 0

async def run(x, lock):
    print("running..." + str(x))
    global static_counter
    
    while True:
        #await lock.acquire()        
        static_counter += 1
        print('Instance: {} count: {}'.format(x, static_counter))
        
        #if lock.locked():
         #   lock.release()                
        
        await asyncio.sleep(1)
        
class Counter:
    def __init__(self, counter = 0):
        self.counter = counter
        self.lock = Lock()        

    async def run(self, x):
        self.counter = 0
        print("running..." + str(x))
        print("instance..." + str(self))                
        
        while True:
            #await self.lock.acquire()        
            self.counter += 1
            print('Instance: {} count: {}'.format(x, self.counter))
            
            #if self.lock.locked():
                #self.lock.release()                
            
            await asyncio.sleep(1)  # Pause 1s

async def count(counter, x):
    await counter.run(x)

async def main():
    counter = Counter()
#    lock = Lock()    
    
    for x in range(3):
        asyncio.create_task(count(counter, x))
        #asyncio.create_task(run(x, lock))        
        await asyncio.sleep(5)
        
    print('Tasks are running...')
    await asyncio.sleep(5)

asyncio.run(main())