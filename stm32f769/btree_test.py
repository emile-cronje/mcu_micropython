import btree
import ujson

# First, we need to open a stream which holds a database
# This is usually a file, but can be in-memory database
# using io.BytesIO, a raw flash partition, etc.
# Oftentimes, you want to create a database file if it doesn't
# exist and open if it exists. Idiom below takes care of this.
# DO NOT open database with "a+b" access mode.
try:
    f = open("myjohndb", "r+b")
except OSError:
    f = open("myjohndb", "w+b")

# Now open a database itself
db = btree.open(f)

johnname = "john"
johndetails =  '{ "name":"John", "age":30, "city":"New York"}'
itemdetails =  '{ "name":@name, "description":@description, "isComplete":@isComplete}'
itemdetails = itemdetails.replace("@name", "aa")
itemdetails = itemdetails.replace("@description", "bb")
itemdetails = itemdetails.replace("@isComplete", "False")
print("Item details:" + itemdetails)

print(johndetails)
johnb = bytes(johndetails, 'utf8')
print(type(johnb))
john_json = ujson.dumps(johndetails)
print(john_json)

db["aa"] = bytes(ujson.dumps(itemdetails), 'utf8')
db[bytes(johnname, 'utf8')] = john_json
#db[b"john"] = b'{ "name":"John", "age":30, "city":"New York"}'

# Assume that any changes are cached in memory unless
# explicitly flushed (or database closed). Flush database
# at the end of each "transaction".
db.flush()


# Iterate over sorted keys in the database, starting from b"2"
# until the end of the database, returning only values.
# Mind that arguments passed to values() method are *key* values.

for key in db:
    print(key)

for word in db.values(bytes(johnname, 'utf8')):
    print(word)

test = db[bytes(johnname, 'utf8')]
print("John's details: " + str(test))

try:
    john_json = ujson.loads(test)
except (ValueError, TypeError):
    print("json parsing error")

#print("John's details (json): " + str(john_json))
zz = john_json["name"]

itemtest = db["aa"]
print("John's details: " + str(test))

item_json = ujson.loads(itemtest)
#print("Item details (json): " + item_json)
xx = item_json['name']
#print("Item name: " + item_json["name"])

del db[bytes(johnname, 'utf8')]

for key in db:
    print(key)

db.close()

# Don't forget to close the underlying stream!
f.close()
