from mqtt_as import MQTTClient, config
import uasyncio as asyncio
import gc
import ujson
import uhashlib
import ubinascii

SERVER = '192.168.10.125'
_error_q = []
_success_q = []
_in_hash_md5 = uhashlib.sha256()

def callback(topic, msg_in, retained):
    print((topic, msg_in, retained))
    msg = ujson.loads(msg_in)
    
    if ("Category" in msg.keys()):
        category = msg["Category"]
    
        if (category == 'Files'):
            processFile(msg, _success_q, _error_q)
    
async def conn_han(client):
    await client.subscribe('pico1_files', 1)
    print("subscribed to pico1_files...")
    await client.subscribe('pico1_test', 1)
    print("subscribed to pico1_test...")
   # await client.subscribe('stm32_simple_topic', 1)
    #print("subscribed to stm32_simple_topic...")

def processFile(msg, success_q, error_q):
    global _in_hash_md5, fout
   
    print("process file...")
    step = msg["Step"]
    print("Msg: " + str(msg))
    
    if (step == "Header"):
        print("Processing header...")        
        _in_hash_md5 = uhashlib.sha256()              
        fileName = msg["FileName"]            
        file_out = "backups/copy-" + fileName
        print("creating file: " + file_out)        
        fout = open(file_out, "wb")
        print("created file: " + file_out)

    elif (step == "Content"):
        file_name = msg["FileName"]                            
        file_data = ubinascii.a2b_base64(msg["FileData"])
        _in_hash_md5.update(file_data)      
        fout.write(file_data)

    elif (step == "End"):
        in_hash_final = _in_hash_md5.digest()
        base64_hash_data = ubinascii.b2a_base64(in_hash_final)[:-1]
        base64_hash_data_string = base64_hash_data.decode("utf-8")
        in_msg_hash = msg["HashData"]
        file_name = msg["FileName"]                    
        
        if (base64_hash_data_string == in_msg_hash):
            success_q.append("File copy OK - " + file_name)
        else:
            error_q.append("File copy failed - " + file_name)
            error_q.append("source hash: " + in_msg_hash)
            error_q.append("dest hash: " + base64_hash_data_string)                        
    
async def main(client):
    await client.connect()
    n = 0
    
    while True:
        await asyncio.sleep(2)
        #print('publish', n)
        #await client.publish('stm32_topic', '{}'.format(n), qos = 1)
        n += 1

def free(full=False):
#  gc.collect()
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))

async def monitorStatusQueues(success_q, error_q):
    while True:
        print("Error Queue length..." + str(len(error_q)))
        print("Success Queue length..." + str(len(success_q)))        
        
        for index in range(0, len(success_q)):
            msg = success_q[index]
            print(msg, '\r\n')            
        
        for index in range(0, len(error_q)):
            error_msg = error_q[index]
            print(error_msg, '\r\n')            

        print("Memory status..." + free(True))        
        await asyncio.sleep(3)

config['subs_cb'] = callback
config['connect_coro'] = conn_han
config['server'] = SERVER

MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)

try:
    #asyncio.create_task(monitorStatusQueues(_success_q, _error_q))        
    asyncio.run(main(client))
finally:
    client.close()