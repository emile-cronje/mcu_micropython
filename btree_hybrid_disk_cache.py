import os
import json
import time

def hinted_tuple_hook(obj):
    if '__tuple__' in obj:
        return tuple(obj['items'])
    else:
        return obj

class BTreeNode:
    def __init__(self, is_leaf=False):
        self.is_leaf = is_leaf
        self.keys = []
        self.children = []
        self.disk_file = None

    def custom_encode(self, obj):
        def hint_tuples(item):
            if isinstance(item, tuple):
                return {'__tuple__': True, 'items': [hint_tuples(e) for e in item]}
            if isinstance(item, list):
                return [hint_tuples(e) for e in item]
            if isinstance(item, dict):
                return {key: hint_tuples(value) for key, value in item.items()}
            else:
                return item

        return json.dumps(hint_tuples(obj))

    @staticmethod    
    def custom_decode(json_data):
        def hinted_tuple_hook(obj):
            if isinstance(obj, dict) and '__tuple__' in obj:
                return tuple(hinted_tuple_hook(item) for item in obj['items'])
            elif isinstance(obj, dict):
                return {key: hinted_tuple_hook(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [hinted_tuple_hook(item) for item in obj]
            else:
                return obj

        parsed_obj = json.loads(json_data)
        return hinted_tuple_hook(parsed_obj)
    
    def traverse_func(self, tree, filter_func, results):
        for i in range(len(self.keys)):
            if not self.is_leaf:
                node = tree.load_node_from_disk(self.children[i])                
                node.traverse_func(tree, filter_func, results)
                
            if filter_func(self.keys[i][1]):
                results.append(self.keys[i][1])
                
        if not self.is_leaf:
            node = tree.load_node_from_disk(self.children[-1])
            node.traverse_func(tree, filter_func, results)

    def serialize(self):
        jsonstring = self.custom_encode(self.keys)        
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
            decoded_result = BTreeNode.custom_decode(json_data['keys'])                    
            node.keys = decoded_result
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
 #       self.print_tree(root)        

        if len(root.keys) == (2 * self.t) - 1:
            temp = BTreeNode()
            self.root = temp
            temp.children.insert(0, root.disk_file)
  #          print(f"before splitting...{key}")
   #         self.print_tree(root)

    #        if (key == (8,8)):
     #           print("before key 8...")                                        

            self.split_child(temp, 0)
      #      print("after splitting...")            
       #     self.print_tree(temp)
        #    print("before insert non full...")            

            self.insert_non_full(temp, key)
         #   print("after insert non full...")                        

            # if (key == (8,8)):
            #     print("after key 8...")                                        
            #     tmp = self.load_node_from_disk(temp)                                        
            #     self.print_tree(tmp)            
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
            file_id = id(node)
            node.disk_file = f'{self.cache_dir}/node_{str(file_id)}.json'
            self.node_counter += 1

        self.storage.save_node(node=node)

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
    
    def traverse_func(self, filter_func):
        results = []

        if self.root:
            self.root.traverse_func(self, filter_func, results)

        return results

    def find(self, key):
        return self.search(self.root, key)

    def search(self, node, key):
        index = 0        
        node = self.load_node_from_disk(node)

        while index < len(node.keys) and key > node.keys[index][0]:
            index += 1

        if index < len(node.keys) and key == node.keys[index][0]:
            return node.keys[index][1]
        
        elif node.is_leaf:
            return None
        else:
            child = self.load_node_from_disk(node.children[index])
            return self.search(child, key)

    def update_value(self, key, new_value):
        node, index = self._find_node_and_index(self.root, key)
        
        if node is not None:
            node.keys[index] = (key, new_value)
            self.save_node_to_disk(node)            
            return True
        else:
            return False

    def _find_node_and_index(self, node, key):
        index = 0
        node = self.load_node_from_disk(node)

        while index < len(node.keys) and key > node.keys[index][0]:
            index += 1
            
        if index < len(node.keys) and key == node.keys[index][0]:
            return node, index
        
        elif node.is_leaf:
            return None, None
        else:
            child = node.children[index]            
            return self._find_node_and_index(child, key)


    def count_nodes(self):
        return self._count_nodes(self.root)

    def _count_nodes(self, node):
        count = 1  # Count the current node
        if not node.is_leaf:
            for child in node.children:
                count += self._count_nodes(child)
        return count
        
    def count_all(self):
        return self._count_all(self.root)

    def _count_all(self, node):
        node = self.load_node_from_disk(node)        
        count = len(node.keys)  # Count the number of keys in the current node
        if not node.is_leaf:
            for child in node.children:
                count += self._count_all(child)
        return count

    def delete_all(self):
        self.root = BTreeNode(True)
