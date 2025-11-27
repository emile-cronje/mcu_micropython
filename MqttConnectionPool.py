from mqtt_as import MQTTClient, config
import random

class MqttConnectionPool:
    def __init__(self, mqttBrokers):
        self.mqttBrokers = mqttBrokers
        self.mqttConnectionPool = {}

    async def Initialise(self):
        for broker in self.mqttBrokers:
            config['server'] = broker
            mqtt_client = MQTTClient(config)
            await mqtt_client.connect()
            print("connected to broker:" + str(broker))
            self.mqttConnectionPool[broker] = mqtt_client
                        
    async def Publish(self, topic, message):
        brokerIndex = random.randint(0, len(self.mqttBrokers) - 1)
        mqttClient = self.mqttConnectionPool[self.mqttBrokers[brokerIndex]]
        await mqttClient.publish(topic, message, qos = 1)            
