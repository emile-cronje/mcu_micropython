from machine import I2C, SoftI2C, Pin
import time

i2c = SoftI2C(scl=Pin('H7'), sda=Pin('H8'))

x = i2c.scan()                          # returns list of peripheral addresses
print(x)

for address in x:
    #print(hex(address))
    i2c.writeto(0x11, 'hello')          # write 5 bytes to peripheral with address 0x42
#    time.sleep(1)
    i2c.writeto(address, 'hello')          # write 5 bytes to peripheral with address 0x42    
    i2c.readfrom(address, 5)               # read 5 bytes from peripheral

    #i2c.readfrom_mem(address, 0x10, 2)     # read 2 bytes from peripheral 0x42, peripheral memory 0x10
    #i2c.writeto_mem(address, 0x10, 'xy')   # write 2 bytes to peripheral 0x42, peripheral memory 0x10