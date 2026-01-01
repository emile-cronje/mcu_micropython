# Python program to display all the prime numbers within an interval
import time
import gc

start = time.time()
lower = 1
upper = 10000

print("Prime numbers between", lower, "and", upper, "are:")

def free(full=False):
#  gc.collect()
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))
  
for num in range(lower, upper + 1):
    if ((num % 100) == 0):
        print(free(True))
    
    # all prime numbers are greater than 1
    if num > 1:
       for i in range(2, num):
           if (num % i) == 0:
               break
       else:
           print(num)
           
end = time.time()
print(end - start)
           