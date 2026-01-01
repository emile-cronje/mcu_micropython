import btree
import os, machine, pyb

# First, we need to open a stream which holds a database
# This is usually a file, but can be in-memory database
# using io.BytesIO, a raw flash partition, etc.
# Oftentimes, you want to create a database file if it doesn't
# exist and open if it exists. Idiom below takes care of this.
# DO NOT open database with "a+b" access mode.

os.mount(pyb.SDCard(), "/sd")

fileName = 'todoItems'

try:
    f = open("/sd/" + fileName, "r+b")
except OSError:
    f = open("/sd/" + fileName, "w+b")

# Now open a database itself
db = btree.open(f)

for key in db:
    print(key)

db.close()

# Don't forget to close the underlying stream!
f.close()