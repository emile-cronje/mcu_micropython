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
from mqtt import MQTTClient,MQTTException
import network

class MQTTFileServerSync:
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
    
    def __init__(self, address='192.168.10.125', port=80):
        self.mqtt_server = address
        self.port = port
        self.address = address
    
    def sub_cb(self, topic, msg):
        print("topic received... " + str(topic))
        print("msg received... " + str(msg))
        
        if (self.client_ready == False):
            return
        
        if (self.backup_in_progress == True):
            return
        
        if (topic == self.topic_file_exist_req):
            parsed = ujson.loads(msg)        
            filename = parsed["filename"]
            
            if not self.file_exist(filename):
                self.client.publish(self.topic_file_not_exist_rsp, filename)
                print("file published %s..." % filename)            

        if (topic == self.topic_file_create_req):
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

        if (topic == self.topic_files_delete_req):
            parsed = ujson.loads(msg)        
            filenames = parsed["filenames"]
            
            for i in range(0, len(filenames) - 1):
                if file_exist(filenames[i]):
                    os.remove(filenames[i])
                    print("file deleted...%s" % filenames[i])            

        if (topic == self.topic_files):
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
                self.backup_all_files()
                
            if (operation == 'backup_single'):
                print("backup single file...")                        
                try:
                    filename = parsed["FileName"]
                    self.backup_file(filename)
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
                self.get_file_list()

        if (topic == self.test_topic):
            if (msg == b'test_file_req'):        
                fo = open("123.py", "rb")
                chunk = fo.read(1000)
                self.send_test_file_data(chunk)
                fo.close

    def get_file_list(self):
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
        self.client.publish(self.topic_files, data_out, self.qos)

    def backup_file(self, filename):
        if (self.file_busy == True):
            print("still busy...%s" % filename)        
            return;
        
        print("Received single file backup...%s" % filename)        
           
        if self.file_exist(filename):
            fo = open(filename, "rb")
            self.file_busy = True;
            self.send_header(filename)                    
            print("file opened...%s" % filename)
            self.run_flag = True
            self.out_hash_md5 = uhashlib.sha256()
            self.file_block_sequence_nr = 1
            
            while self.run_flag:
                file_block = fo.read(self.data_block_size)
                
                if file_block:
                    self.send_file_block(filename, file_block, self.file_block_sequence_nr)
                    self.file_block_sequence_nr += 1
                else:
                    self.send_end(filename)
                    self.run_flag=False
                    fo.close()
                    self.file_busy = False;              
        else:
            print("file %s not found" % filename)

    def backup_all_files(self):
        print("Received all files backup...")        
        filenames = []
        self.backup_in_progress = True

        for filename in os.listdir():
            filenames.append(filename)        

        for i in range(0, len(filenames)):
            filename = filenames[i]
            
            if self.file_exist(filename):
                fo = open(filename, "rb")
                self.file_busy = True;
                self.send_header(filename)                    
                print("file opened...%s" % filename)
                self.run_flag = True
                self.out_hash_md5 = uhashlib.sha256()
                self.file_block_sequence_nr = 1
                
                while self.run_flag:
                    file_block = fo.read(self.data_block_size)
                    
                    if file_block:
                        self.send_file_block(filename, file_block, self.file_block_sequence_nr)
                        self.file_block_sequence_nr += 1                    
                    else:
                        self.send_end(filename)
                        self.run_flag = False
                        fo.close()
                        self.file_busy = False;              
            else:
                print("file %s not found" % filename)
                
            self.backup_in_progress = False            
    
    def send_header(self, filename):
        print("Preparing header...")    
        file_data = {"FileName":filename}
        file_data_json = ujson.dumps(file_data)
        header = "header"+",," + file_data_json + ",,"
        header = bytearray(header,"utf-8")
        print(header)
        self.client.publish(self.topic_files, header, self.qos)
        print("Header published...")    

    def send_file_block(self, file_name, file_content, file_block_sequence_nr):
        self.out_hash_md5.update(file_content)    
        base64_data = ubinascii.b2a_base64(file_content)
        file_content_msg = {
                        "FileName":file_name,        
                        "FileData":base64_data,
                        "FileBlockSequenceNumber": file_block_sequence_nr
                     }
        file_content_msg_json = ujson.dumps(file_content_msg)
        data_out = "file_content"+",," + file_content_msg_json + ",,"
        data_out = bytearray(data_out,"utf-8")
        #print(data_out)
        self.client.publish(self.topic_files, data_out, self.qos)

    def send_end(self, filename):
        base64_hash_data = ubinascii.b2a_base64(self.out_hash_md5.digest())[:-1]    
        hash_data = {
                        "FileName":filename,
                        "HashData":base64_hash_data
                    }    
        hash_data_json = ujson.dumps(hash_data)
        
        print("send end start hash string...%s" % hash_data_json)
        end = "eof" + ",," + hash_data_json + ",,"
        end=bytearray(end,"utf-8")
        print(end)
        self.client.publish(self.topic_files, end, self.qos)

    def send_test_file_data(self, filedata):
        print("clearing hash lib...")
        self.out_hash_md5 = uhashlib.sha256()
        self.out_hash_md5.update(filedata)    
        base64_data = ubinascii.b2a_base64(filedata)
        base64_hash_data = ubinascii.b2a_base64(ubinascii.hexlify(self.out_hash_md5.digest()))        
        file_data = {
                        "testfiledata":base64_data,
                        "hashdata":base64_hash_data
                     }
        file_data_json = ujson.dumps(file_data)
        data = "testfiledata"+",," + file_data_json + ",,"
        data = bytearray(data,"utf-8")
        print(data)
        self.client.publish(self.test_topic, data, self.qos)

    def file_exist(self, filename):
        try:
            f = open(filename, "r")
            exists = True
            f.close()
        except OSError:
            exists = False
        return exists        

    def connect_and_subscribe(self):
      self.client = MQTTClient(self.client_id, self.mqtt_server)
      self.client.set_callback(self.sub_cb)
      self.client.connect()
      self.client.subscribe(self.topic_files)
      self.client.subscribe('stm32_simple_topic')          
      print('Connected to %s MQTT broker, subscribed to %s topic' % (self.mqtt_server, self.topic_files))
      return self.client

    def restart_and_reconnect(self):
      print('Failed to connect to MQTT broker. Reconnecting...')
      time.sleep(10)
      machine.reset()

    
    def run(self):
        self.last_message = 0
        self.message_interval = 5

        try:
            self.client = self.connect_and_subscribe()
            self.client_ready = True
        except OSError as e:
          self.restart_and_reconnect()

        if (self.file_busy == True):
            print("file_busy true")
        else:
            print("file_busy false")
            
        while True:
          try:
            self.client.check_msg()
            
            if (time.time() - self.last_message) > self.message_interval:
                msg = b'Hello from stm32f769'
                self.last_message = time.time()
          except OSError as e:
            self.restart_and_reconnect()   