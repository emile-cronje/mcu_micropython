import uasyncio as asyncio
from machine import Pin

msg_q = []
event_test = asyncio.Event()

async def pushItems():
    icount = 0

    while True:
        msg_q.append(str(icount))
        icount += 1
        await asyncio.sleep(1)

async def pullItems():
    while True:
        await event_test.wait()

        while (len(msg_q) > 5):
            item = msg_q.pop(0)
            print("Pulled item..." + str(item))                    
            await asyncio.sleep(.5)

        event_test.clear()

async def watchItems():
    while True:
        if (len(msg_q) > 10):
            event_test.set()

        await asyncio.sleep(1)

async def showQueueLength():
    while True:
        print("Queue length..." + str(len(msg_q)))
        await asyncio.sleep(2)

async def main():
    asyncio.create_task(pushItems())            
    asyncio.create_task(pullItems())                
    asyncio.create_task(watchItems())                    
    asyncio.create_task(showQueueLength())

    print('Tasks are running...')
    while True:
        await asyncio.sleep(5)

asyncio.run(main())
