import os
import machine
import pyb
from machine import SPI, Pin
import gc

def sdtest(mustDelete = False):
    os.mount(pyb.SDCard(), "/sd")    
    log(os.listdir('/sd'))
    files = os.listdir('/sd')
    
    for count in range(50):
        s = "Count: " + str(count)
        print(s)
    #    print(free())
        
        for file in files:
            rm('/sd/' + file)
            
        line = 'abcdefghijklmnopqrstuvwxyz\n'
        lines = line * 600 # 5400 chars
        short = '1234567890\n'

        fn = '/sd/rats.txt'
#        print()
        log('Multiple block read/write')
        
        with open(fn,'w') as f:
            n = f.write(lines)
            log(str(n) + ' bytes written')
            n = f.write(short)
            log(str(n) + ' bytes written')
            n = f.write(lines)
            log(str(n) + ' bytes written')

        with open(fn,'r') as f:
            result1 = f.read()
            log(str(len(result1)) + ' bytes read')

        fn = '/sd/rats1.txt'
 #       print()
        log('Single block read/write')
        
        with open(fn,'w') as f:
            n = f.write(short) # one block
            log(str(n) + ' bytes written')

        with open(fn,'r') as f:
            result2 = f.read()
            log(str(len(result2)) + ' bytes read')

  #      print()
        log('Verifying data read back')
        success = True
        
        if result1 == ''.join((lines, short, lines)):
            log('Large file Pass')
        else:
            log('Large file Fail')
            success = False
            
        if result2 == short:
            log('Small file Pass')
        else:
            log('Small file Fail')
            success = False
            
    print('Tests', 'passed' if success else 'failed')

def free(full=True):
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  #else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))
  else : return ('Free:{0}'.format(P))  

def rm(d):  # Remove file or tree
    try:
        #print(os.stat(d))
        
        if os.stat(d)[0] & 0x4000:  # Dir
            for f in os.ilistdir(d):
                if f[0] not in ('.', '..'):
                    rm("/".join((d, f[0])))  # File or Dir
            os.rmdir(d)
        else:  # File
            os.remove(d)
    except OSError as e:
        print("rm of '%s' failed" % d)
        print(str(e))
        
def log(s):
    return
    print(s)
    
   
sdtest(True)