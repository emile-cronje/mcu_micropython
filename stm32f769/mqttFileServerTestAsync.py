from file_server_stm32f769_async import MQTTFileServerAsync
import uasyncio as asyncio
from lanConnect import LANConnect

mqttFileServer = MQTTFileServerAsync()

asyncio.run(mqttFileServer.main())
