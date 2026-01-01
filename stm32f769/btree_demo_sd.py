import os
import ujson as json
import pyb
import gc
import time

class MeterReading:
    def __init__(self, id, meter_id, reading_on, reading):
        self.id = id
        self.meterId = meter_id
        self.reading_on = reading_on
        self.reading = reading

class BTreeNode:
    def __init__(self, is_leaf=False):
        self.is_leaf = is_leaf
        self.keys = []
        self.children = []
        self.disk_file = None

    def serialize(self):
        jsonstring = self.keys
        data = {
            'is_leaf': self.is_leaf,
            'keys': jsonstring,
            'disk_file': self.disk_file,            
            'children': [child.disk_file if isinstance(child, BTreeNode) else child for child in self.children]
        }
        return data

    @staticmethod
    def deserialize(serialized_node, doJsonLoad=True):
        if serialized_node is None:
            return None

        if doJsonLoad:
            json_data = json.loads(serialized_node)
        else:
            json_data = serialized_node

        if isinstance(json_data, dict):
            node = BTreeNode(is_leaf=json_data['is_leaf'])
            node.keys = json_data['keys']
            node.disk_file = json_data['disk_file']
            
            for child_data in json_data['children']:
                node.children.append(child_data)
                
#            print(f"Deserialized node with keys: {node.keys}")  # Debug print
            return node
        else:
            return json_data
       
    def traverse_keys(self, root, results):
        for i in range(len(self.keys)):
            if not self.is_leaf:
                node = root.load_node_from_disk(self.children[i])                    
                node.traverse_keys(root, results)
                
            results.append(self.keys[i])
            
        if not self.is_leaf:
            node = root.load_node_from_disk(self.children[-1])                                
            node.traverse_keys(root, results)        

class DiskStorage:
    def __init__(self, directory):
        self.directory = directory

    def save_node(self, node):
        data = json.dumps(node.serialize()).encode("utf-8")        

        with open(node.disk_file, 'wb') as f:
            f.write(data)

    def load_node(self, disk_file):
        with open(disk_file, 'rb') as f:
            data = f.read()
            
        return BTreeNode.deserialize(data)

class BTree:
    def __init__(self, t, cache_dir='btree_cache'):
        self.root = BTreeNode(True)
        self.storage = DiskStorage(cache_dir)        
        self.t = t
        self.cache_dir = cache_dir
        self.node_counter = 0

    def insert(self, key):
        root = self.root
#        print(f"Inserting key: {key}")  # Debug print
#        self.print_tree(root)        

        if len(root.keys) == (2 * self.t) - 1:
            temp = BTreeNode()
            self.root = temp
            temp.children.insert(0, root.disk_file)
 #           print(f"before splitting...{key}")
  #          self.print_tree(root)
            self.split_child(temp, 0)
   #         print("after splitting...")            
    #        self.print_tree(root)
     #       print("before insert non full...")            

      #      if (key == (8,8)):
       #         print("before key 8...")                                        

            self.insert_non_full(temp, key)
            #print("after insert non full...")                        
        else:
            self.insert_non_full(root, key)

    def insert_non_full(self, node, key):
        node = self.load_node_from_disk(node)                        
        index = len(node.keys) - 1

        if node.is_leaf:
            node.keys.append((None, None))

            while index >= 0 and key[0] < node.keys[index][0]:
                node.keys[index + 1] = node.keys[index]
                index -= 1

            node.keys[index + 1] = key
        else:
            while index >= 0 and key[0] < node.keys[index][0]:
                index -= 1

            index += 1

            child_node = self.load_node_from_disk(node.children[index])                

            if len(child_node.keys) == (2 * self.t) - 1:
                self.split_child(node, index)

                if key[0] > node.keys[index][0]:
                    index += 1

            child_node = self.load_node_from_disk(node.children[index])                
            self.insert_non_full(child_node, key)

        self.save_node_to_disk(node)                

    def split_child(self, node, index):
        t = self.t
        y = self.load_node_from_disk(node.children[index])        
        z = BTreeNode(y.is_leaf)
        node.children.insert(index + 1, z)        
        node.keys.insert(index, y.keys[t - 1])
        z.keys = y.keys[t: (2 * t) - 1]
        y.keys = y.keys[0: t - 1]

        if not y.is_leaf:
            z.children = y.children[t: 2 * t]
            y.children = y.children[0: t]

        self.save_node_to_disk(y)
        self.save_node_to_disk(z)
        self.save_node_to_disk(node)

    def save_node_to_disk(self, node):
        if node.disk_file is None:
            node.disk_file = f'{self.cache_dir}/node_{self.node_counter}.json'
            self.node_counter += 1

        self.storage.save_node(node=node)
        return node.disk_file

    def load_node_from_disk(self, node):
        if isinstance(node, str):                    
            return self.storage.load_node(node)
        else:        
            return node
        
    def print_tree(self, node, level=0):
        node = self.load_node_from_disk(node)
        #print("Level ", level, " ", len(node.keys), end=":")
        print("Level ", level, " ", end=":")        

        for childId in node.keys:
            print(childId, end=" ")

        print()

        level += 1

        if len(node.children) > 0:
            for childId in node.children:
                self.print_tree(childId, level)

    def count_nodes(self):
        return self._count_nodes(self.root)

    def _count_nodes(self, node):
        node = self.load_node_from_disk(node)
        count = 1
        if not node.is_leaf:
            for child in node.children:
                count += self._count_nodes(child)
        return count                

    def search(self, node, key):
        node = self.load_node_from_disk(node)
        index = 0

        while index < len(node.keys) and key > node.keys[index][0]:
            index += 1

        if index < len(node.keys) and key == node.keys[index][0]:
            return node.keys[index]
        
        elif node.is_leaf:
            return None
        else:
            #child = node.children[index]
            child = self.load_node_from_disk(node.children[index])
            return self.search(child, key)

    def find(self, key):
        return self.search(self.root, key)

    def delete(self, node, key):
        node = self.load_node_from_disk(node)
        t = self.t
        i = 0
        while i < len(node.keys) and key[0] > node.keys[i][0]:
            i += 1

        if i < len(node.keys) and node.keys[i][0] == key[0]:
            if node.is_leaf:
                node.keys.pop(i)
            else:
                k = node.keys[i]
                if len(self.load_node_from_disk(node.children[i]).keys) >= t:
                    pred = self.get_pred(node, i)
                    node.keys[i] = pred
                    self.delete(node.children[i], pred)
                elif len(self.load_node_from_disk(node.children[i + 1]).keys) >= t:
                    succ = self.get_succ(node, i)
                    node.keys[i] = succ
                    self.delete(node.children[i + 1], succ)
                else:
                    self.merge(node, i)
                    self.delete(node.children[i], k)
        else:
            if node.is_leaf:
                return
            flag = (i == len(node.keys))
            if len(self.load_node_from_disk(node.children[i]).keys) < t:
                self.fill(node, i)
            if flag and i > len(node.keys):
                self.delete(node.children[i - 1], key)
            else:
                self.delete(node.children[i], key)
        self.save_node_to_disk(node)

    def get_pred(self, node, idx):
        current = self.load_node_from_disk(node.children[idx])
        while not current.is_leaf:
            current = self.load_node_from_disk(current.children[len(current.keys)])
        return current.keys[len(current.keys) - 1]

    def get_succ(self, node, idx):
        current = self.load_node_from_disk(node.children[idx + 1])
        while not current.is_leaf:
            current = self.load_node_from_disk(current.children[0])
        return current.keys[0]

    def merge(self, node, idx):
        if idx < 0 or idx >= len(node.keys):
            return

        child = self.load_node_from_disk(node.children[idx])
        sibling = self.load_node_from_disk(node.children[idx + 1])
        child.keys.append(node.keys[idx])
        child.keys.extend(sibling.keys)

        if not child.is_leaf:
            child.children.extend(sibling.children)

        node.keys.pop(idx)
        node.children.pop(idx + 1)

        self.save_node_to_disk(child)
        self.save_node_to_disk(node)

    def fill(self, node, idx):
        if idx != 0 and len(self.load_node_from_disk(node.children[idx - 1]).keys) >= self.t:
            self.borrow_from_prev(node, idx)
        elif idx != len(node.keys) and len(self.load_node_from_disk(node.children[idx + 1]).keys) >= self.t:
            self.borrow_from_next(node, idx)
        else:
            if idx != len(node.keys):
                self.merge(node, idx)
            else:
                self.merge(node, idx - 1)

    def borrow_from_prev(self, node, idx):
        child = self.load_node_from_disk(node.children[idx])
        sibling = self.load_node_from_disk(node.children[idx - 1])
        child.keys.insert(0, node.keys[idx - 1])
        if not child.is_leaf:
            child.children.insert(0, sibling.children.pop())
        node.keys[idx - 1] = sibling.keys.pop()
        self.save_node_to_disk(child)
        self.save_node_to_disk(sibling)

    def borrow_from_next(self, node, idx):
        child = self.load_node_from_disk(node.children[idx])
        sibling = self.load_node_from_disk(node.children[idx + 1])
        child.keys.append(node.keys[idx])
        if not child.is_leaf:
            child.children.append(sibling.children.pop(0))
        node.keys[idx] = sibling.keys.pop(0)
        self.save_node_to_disk(child)
        self.save_node_to_disk(sibling)

    def traverse_keys(self):
        results = []

        if self.root:
            self.root.traverse_keys(self, results)

        return results

def free(full=False):
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))

data = []
data.append('item 0')
data.append('item 1')
data.append('item 2')
data.append('item 3')
data.append('item 4')
data.append('d')
data.append('e')
data.append('f')
data.append('g')
data.append('h')
data.append('i')
data.append('j')

os.mount(pyb.SDCard(), "/sd")
dir = '/sd/btree_storage'
#os.mkdir(dir)
print("memory before: " + free())

B = BTree(10, cache_dir=dir)
itemCount = 100
idList = []
reading = 6
start = time.ticks_ms()

for index in range(itemCount):
    meterReading = MeterReading(index, index+100, f'2024-07-{index+1}T11:33:04.6645813+02:00', reading)
    #idList.append((index, meterReading.__dict__))
    idList.append(index)        
#    B.insert((mr.id, mr.__dict__))
    B.insert((index, index))    
#    print(f"Key: {index}")
 #   print("Tree:")
  #  B.print_tree(B.root)    
    reading += 10

for searchFor in range(0, itemCount):
    if (not B.find(searchFor)):
        print(f'Item : {searchFor} not found...')        

#B.print_tree(B.root)

keyCount = 0

for item in B.traverse_keys():
#    print(f"Item: {item}")
    keyCount += 1

print(f"Keycount: {keyCount}")

if (keyCount == itemCount):
    print("Keycount OK...")    
else:        
    print("Keycount mismatch...")

#B.print_tree(B.root)    
#print("Deleting all items...")
#for id in idList:    
    #B.delete(B.root, (id,))    

keyCount = 0

for item in B.traverse_keys():
    keyCount += 1

#if (keyCount == 0):
    #print("Delete OK...")    
#else:    
#    print("Delete failed...")        
    #keyCount = 0

    #for item in B.traverse_keys():
        #keyCount += 1

    #print(f"Keycount after delete: {keyCount}")        


# filter_func = lambda reading: reading["meterId"] != 1
# sorted_readings = B.traverse_func(filter_func)    

# jsonReadings = []

# for reading in sorted_readings:
#     jsonReadings.append(reading)
# #    print(reading[1]["id"])

# # Calculate the average daily rate for meter_id 1
# average_daily_rate_meter_1 = calculate_average_daily_rate(jsonReadings)
# print(f"Average Daily Rate for meter 1: {average_daily_rate_meter_1}")

print("memory after: " + free())
end = time.ticks_ms()
print("------")
print((end - start)/1000)
print("seconds...")
