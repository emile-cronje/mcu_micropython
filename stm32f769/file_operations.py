import os, pyb

os.mount(pyb.SDCard(), "/sd")

f = open('/sd/data.txt', 'w')
f.write('some data')
f.close()

f = open('/sd/data.txt')
print(f.read())
f.close()

os.remove('/sd/data.txt')
#os.remove('/sd/todoItems')
os.listdir('/sd')