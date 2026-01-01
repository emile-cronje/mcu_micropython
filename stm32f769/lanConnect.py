try:
  import usocket as socket
except:
  import socket
from machine import Pin
import network
import gc

class LANConnect:
    def __init__(self):
        self.lan = network.LAN()
        self.hasConnection = False

    def connect(self):
        gc.collect()
        print("lan connect...")

        self.lan.active(True)
        #self.lan.ifconfig('dhcp')
        self.lan.ifconfig(('192.168.10.120', '255.255.255.0', '192.168.10.1', '192.168.10.1'))    

        # We should have a valid IP now via DHCP
        print(self.lan.ifconfig())
        print('LAN Connection successful...')
        self.hasConnection = True        
        return self.lan

    def disconnect(self):
        self.hasConnection = False        
        self.lan.active(False)
        
    def active(self, active):
        self.lan.active(active)
        self.hasConnection = True        

    def isconnected(self):
        return self.hasConnection;

