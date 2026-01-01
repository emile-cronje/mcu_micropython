import uasyncio as asyncio

class Counter:
    def __init__(self, counter = 0):
        self.counter = counter

    async def run(self, x):
        self.counter = 0
        print("running..." + str(x))
        print("instance..." + str(self))                
        
        while True:
            self.counter += 1
            print('Instance: {} count: {}'.format(x, self.counter))
            await asyncio.sleep(1)  # Pause 1s

async def count(counter, x):
    await counter.run(x)

async def run():
    counter = 0
    
    while True:
        counter += 1
        print('Count: {}'.format(counter))
        await asyncio.sleep(1)  # Pause 1s

async def main():
    counter = Counter()
    
    for x in range(50):
#        asyncio.create_task(count(counter, x))
        asyncio.create_task(run())                
        
    print('Tasks are running...')
    await asyncio.sleep(2)

asyncio.run(main())