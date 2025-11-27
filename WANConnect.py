try:
    import usocket as socket
except:
    import socket
from machine import Pin
import network
import gc
import utime

class WANConnect:
    def __init__(self):
        self.wan = network.WLAN(network.STA_IF)
        self.hasConnection = False

    def connect_x(self, ssid, password):
        gc.collect()
        print("wan connecting...")

        self.wan.active(True)
        self.wan.connect(ssid, password)

        while self.wan.isconnected() == False:
          pass

        print('Connection successful...')
        print(self.wan.ifconfig())
        self.hasConnection = True        
        return self.wan

    def disconnect_old(self):
        self.hasConnection = False        
        self.wan.active(False)
        
    def active(self, active):
        self.wan.active(active)
        self.hasConnection = True        

    def isconnected(self):
        return self.hasConnection;

    def status(self):
        return self.hasConnection;

    def connect(self, ssid, password):
        count = 0

     #  disconnects AP if it is up
        self.wan.active(False) #  de-activate the AP interface
        utime.sleep(1)

        if not self.wan.isconnected():
            print('connecting to wifi...')
            self.wan.ifconfig(('192.168.10.115', '255.255.255.0', '192.168.10.1', '192.168.10.1'))                
            self.wan.active(True)
            self.wan.connect(ssid, password)

            while (count < 5):
                count += 1

                if (self.wan.isconnected()):
                    count = 0
                    print (' network config:', self.wan.ifconfig())
                    break

                print ('.', end = '')
                utime.sleep(1)

        if (count == 5):
            try:
                with open('errors.txt', 'a') as outfile:
                    outfile.write('failed to connect' + '\n')
            except OSError:
                pass

         #  disconnect or you get errors
            self.disconnect()

        count = 0 #  reset count

        utime.sleep(1)


    def disconnect(self):
        self.wan.disconnect()
        self.wan.active(False)
        utime.sleep(1)
