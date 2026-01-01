from mqtt_as_latest import MQTTClient, config
import uasyncio as asyncio
from queue import Queue

SERVER = '192.168.10.174'
config['server'] = SERVER
event_pub = asyncio.Event()
config['ssid'] = 'Cudy24G'
config['wifi_pw'] = 'ZAnne19991214'
_queue = None

def callback(topic, msg, retained):
    print((topic, msg, retained))
    _queue.put_nowait(msg)
    event_pub.set()
    
async def conn_han(client):
    await client.subscribe('file_recv', 1)
    print("Connected to broker...")

async def consume(queue, client):
    while True:
        await event_pub.wait()

        while (True):
            msg = await queue.get()
            await client.publish("file_send", msg, qos = 1)
            await asyncio.sleep(.1)            

        event_pub.clear()

async def main(client):
    await client.connect()
    n = 0
    
    while True:
        await asyncio.sleep(2)
        print('publish', n)

        await client.publish('file_send', '{}'.format(n), qos = 1)
        n += 1

config['subs_cb'] = callback
config['connect_coro'] = conn_han
config['server'] = SERVER

MQTTClient.DEBUG = True
_client = MQTTClient(config)
_queue = Queue()

try:
    asyncio.create_task(consume(_queue, _client))    
    asyncio.run(main(_client))
finally:
    client.close()