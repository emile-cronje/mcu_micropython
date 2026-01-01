from mqtt_as import MQTTClient, config
import uasyncio as asyncio
from ubinascii import hexlify
import time
import ubinascii
import machine
import micropython
import gc
from machine import Pin, I2C
import ujson
import framebuf
import os
import uhashlib
import network

MQTT_SERVER = '192.168.1.104'
client_id = ubinascii.hexlify(machine.unique_id())
topic_files = b'STM32F769'
topic_file_exist_req = b'file_exist_req'
topic_file_not_exist_rsp = b'file_not_exist_rsp'
topic_file_create_req = b'file_create_req'

topic_files_delete_req = b'files_delete_req'
topic_file_delete_rsp = b'file_delete_rsp'
test_topic=b'filetest'
topic_file_pub = b'file_recv_ack'

qos=1
data_block_size=2000
run_flag=True
out_hash_md5 = uhashlib.sha256()
client_ready = False
file_busy = False
backup_in_progress = False
file_block_sequence_nr = 0


def callback(topic, msg, retained):
    print((topic, msg, retained))
#    print("topic received... " + str(topic))
    #print("msg received... " + str(msg))
    
    global client_ready
    global backup_in_progress
    
    if (client_ready == False):
        return
    
    if (backup_in_progress == True):
        return
    
    print("client ready...")

    if (topic == topic_file_create_req):
        print("file msg received...")
        parsed = ujson.loads(msg)
        base64_file_data = ubinascii.a2b_base64(parsed["filecontent"])
        print("base64_file_data... %s" % base64_file_data);
        data = bytearray(base64_file_data, "utf-8")
        filename = parsed["filename"]
        
        with open(filename, 'wb') as f:
            f.write(data)
            f.close()
        print("file written...")

    #issue?
    if (topic == topic_file_exist_req):
        parsed = ujson.loads(msg)        
        filename = parsed["filename"]
        
        if not file_exist(filename):
            await client.publish(topic_file_not_exist_rsp, filename)
            print("file published %s..." % filename)            

    if (topic == topic_files_delete_req):
        parsed = ujson.loads(msg)        
        filenames = parsed["filenames"]
        
        for i in range(0, len(filenames) - 1):
            if file_exist(filenames[i]):
                os.remove(filenames[i])
                print("file deleted...%s" % filenames[i])            

    if (topic == topic_files):
        print("files_topic...%s" % msg)
        try:
            parsed = ujson.loads(msg)
        except (ValueError, TypeError):
            print("json parsing error")
            return

        print("files_topic...message parsed%s" % parsed)                
        operation = parsed["Operation"]        
        if (operation == 'backup_all'):
            print("backup all files...")
            backup_all_files()
            
        if (operation == 'backup_single'):
            print("backup single file...")                        
            try:
                filename = parsed["FileName"]
                backup_file(filename)
            except (ValueError, TypeError):
                print("json parsing error")

def callback_x(topic, msg, retained):
    print("topic received... " + str(topic))
    print("msg received... " + str(msg))
    
    global client_ready
    global backup_in_progress
    
    if (client_ready == False):
        return
    
    if (backup_in_progress == True):
        return
    
    print("client ready...")
    
    if (topic == topic_file_exist_req):
        parsed = ujson.loads(msg)        
        filename = parsed["filename"]
        
        if not file_exist(filename):
            await client.publish(topic_file_not_exist_rsp, filename)
            print("file published %s..." % filename)            

    if (topic == topic_file_create_req):
        print("file msg received...")
        parsed = ujson.loads(msg)
        base64_file_data = ubinascii.a2b_base64(parsed["filecontent"])
        print("base64_file_data... %s" % base64_file_data);
        data = bytearray(base64_file_data, "utf-8")
        filename = parsed["filename"]
        
        with open(filename, 'wb') as f:
            f.write(data)
            f.close()
        print("file written...")

    if (topic == topic_files_delete_req):
        parsed = ujson.loads(msg)        
        filenames = parsed["filenames"]
        
        for i in range(0, len(filenames) - 1):
            if file_exist(filenames[i]):
                os.remove(filenames[i])
                print("file deleted...%s" % filenames[i])            

    if (topic == topic_files):
        print("files_topic...%s" % msg)
        try:
            parsed = ujson.loads(msg)
        except (ValueError, TypeError):
            print("json parsing error")
            return

        print("files_topic...message parsed%s" % parsed)                
        operation = parsed["Operation"]        
        if (operation == 'backup_all'):
            print("backup all files...")
            backup_all_files()
            
        if (operation == 'backup_single'):
            print("backup single file...")                        
            try:
                filename = parsed["FileName"]
                backup_file(filename)
            except (ValueError, TypeError):
                print("json parsing error")

        if (operation == 'file_create'):
            print("create single file...")                        
            parsed = ujson.loads(msg)
            base64_file_data = ubinascii.a2b_base64(parsed["fileContent"])
            print("base64_file_data... %s" % base64_file_data);
            data = bytearray(base64_file_data, "utf-8")
            filename = parsed["fileName"]
            
            with open(filename, 'wb') as f:
                f.write(data)
                f.close()
            print("file written...")

        if (msg == b'get_file_list'):
            print("getting file list...")
            get_file_list()

    if (topic == test_topic):
        if (msg == b'test_file_req'):        
            fo = open("123.py", "rb")
            chunk = fo.read(1000)
            send_test_file_data(chunk)
            fo.close

def get_file_list():
    filenames = []

    for filename in os.listdir():
        filenames.append(filename)

    filelist = ''
    for file in filenames:
        filelist += file + ','
        
    filelist = filelist[:-1]
    file_list_msg = { "files":os.listdir() }
    file_list_msg_json = ujson.dumps(file_list_msg)
    data_out = bytearray(file_list_msg_json, "utf-8")
    print(data_out)
    await client.publish(topic_files, data_out, qos)

def backup_file(filename):
    if (file_busy == True):
        print("still busy...%s" % filename)        
        return;
    
    print("Received single file backup...%s" % filename)        
       
    if file_exist(filename):
        fo = open(filename, "rb")
        file_busy = True;
        send_header(filename)                    
        print("file opened...%s" % filename)
        run_flag = True
        out_hash_md5 = uhashlib.sha256()
        file_block_sequence_nr = 1
        
        while run_flag:
            file_block = fo.read(data_block_size)
            
            if file_block:
                send_file_block(filename, file_block, file_block_sequence_nr)
                file_block_sequence_nr += 1
            else:
                send_end(filename)
                run_flag=False
                fo.close()
                file_busy = False;              
    else:
        print("file %s not found" % filename)

def backup_all_files():
    global run_flag
    global out_hash_md5
    global file_busy
    global backup_in_progress
    global file_block_sequence_nr
    print("Received all files backup...")        
    filenames = []
    backup_in_progress = True

    for filename in os.listdir():
        filenames.append(filename)        

    for i in range(0, len(filenames)):
        filename = filenames[i]
        
        if file_exist(filename):
            fo = open(filename, "rb")
            file_busy = True;
            send_header(filename)                    
            print("file opened...%s" % filename)
            run_flag = True
            out_hash_md5 = uhashlib.sha256()
            file_block_sequence_nr = 1
            
            while run_flag:
                file_block = fo.read(data_block_size)
                
                if file_block:
                    send_file_block(filename, file_block, file_block_sequence_nr)
                    file_block_sequence_nr += 1                    
                else:
                    send_end(filename)
                    run_flag = False
                    fo.close()
                    file_busy = False;              
        else:
            print("file %s not found" % filename)
            
        backup_in_progress = False            
    
def send_header(filename):
    print("Preparing header...")    
    file_data = {"FileName":filename}
    file_data_json = ujson.dumps(file_data)
    header = "header"+",," + file_data_json + ",,"
    header = bytearray(header,"utf-8")
    print(header)
    await client.publish(topic_files, header, qos)
    print("Header published...")    

def send_file_block_test(file_name, file_content):
    out_hash_md5.update(file_content)    
    base64_data = ubinascii.b2a_base64(file_content)
    file_content_msg = {
                    "fileName":file_name,        
                    "fileData":base64_data
                 }
    file_content_msg_json = ujson.dumps(file_content_msg)
    data_out = "file_content"+",," + file_content_msg_json + ",,"
    data_out = bytearray(data_out,"utf-8")
    print(data_out)
    await client.publish(topic_files, data_out, qos)

def send_file_block(file_name, file_content, file_block_sequence_nr):
    out_hash_md5.update(file_content)    
    base64_data = ubinascii.b2a_base64(file_content)
    file_content_msg = {
                    "FileName":file_name,        
                    "FileData":base64_data,
                    "FileBlockSequenceNumber": file_block_sequence_nr
                 }
    file_content_msg_json = ujson.dumps(file_content_msg)
    data_out = "file_content"+",," + file_content_msg_json + ",,"
    data_out = bytearray(data_out,"utf-8")
    print(data_out)
    await client.publish(topic_files, data_out, qos)

def send_end(filename):
    base64_hash_data = ubinascii.b2a_base64(out_hash_md5.digest())[:-1]    
    hash_data = {
                    "FileName":filename,
                    "HashData":base64_hash_data
                }    
    hash_data_json = ujson.dumps(hash_data)
    
    print("send end start hash string...%s" % hash_data_json)
    end = "eof" + ",," + hash_data_json + ",,"
    end=bytearray(end,"utf-8")
    print(end)
    await client.publish(topic_files, end, qos)

def send_test_file_data(filedata):
    print("clearing hash lib...")
    out_hash_md5 = uhashlib.sha256()
    out_hash_md5.update(filedata)    
    base64_data = ubinascii.b2a_base64(filedata)
    base64_hash_data = ubinascii.b2a_base64(ubinascii.hexlify(out_hash_md5.digest()))        
    file_data = {
                    "testfiledata":base64_data,
                    "hashdata":base64_hash_data
                 }
    file_data_json = ujson.dumps(file_data)
    data = "testfiledata"+",," + file_data_json + ",,"
    data = bytearray(data,"utf-8")
    print(data)
    await client.publish(test_topic, data, qos)

def file_exist(filename):
    try:
        f = open(filename, "r")
        exists = True
        f.close()
    except OSError:
        exists = False
    return exists        

async def conn_han(client):
    global client_ready
    await client.subscribe(topic_files, 1)
    print('Connected to %s MQTT broker, subscribed to %s topic' % (MQTT_SERVER, topic_files))
    client_ready = True

async def main(client):
    await client.connect()
    n = 0
    while True:
        await asyncio.sleep(5)
        print('publish', n)
        # If WiFi is down the following will pause for the duration.
        await client.publish('result', '{}'.format(n), qos = 1)
        n += 1

config['subs_cb'] = callback
config['connect_coro'] = conn_han
config['server'] = MQTT_SERVER

MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors