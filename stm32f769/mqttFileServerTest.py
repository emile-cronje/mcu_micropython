from file_server_stm32f769 import MQTTFileServerSync
from lanConnect import LANConnect

lanConnect = LANConnect()
lanConnect.connect()
mqttFileServer = MQTTFileServerSync()
mqttFileServer.run()