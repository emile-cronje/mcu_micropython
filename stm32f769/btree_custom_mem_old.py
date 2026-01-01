class BTreeNode:
    def __init__(self, is_leaf = False, name = 'root'):
        self.name = name
        self.is_leaf = is_leaf
        self.keys = []
        self.children = []

    def traverse_func(self, filter_func, results):
        for i in range(len(self.keys)):
            if not self.is_leaf:
                self.children[i].traverse_func(filter_func, results)
                
            if filter_func(self.keys[i][1]):
                results.append(self.keys[i][1])
               
        if not self.is_leaf:
            self.children[-1].traverse_func(filter_func, results)

    def traverse_keys(self, results):
        for i in range(len(self.keys)):
            if not self.is_leaf:
                self.children[i].traverse_keys(results)
                
            results.append(self.keys[i])
            
        if not self.is_leaf:
            self.children[-1].traverse_keys(results)        

class BTree:
    def __init__(self, t):
        self.root = BTreeNode(True)
#        print(f"Init: {self.root.name}, self.root.is_leaf:", str(self.root.is_leaf))                    
        self.t = t

    def insert(self, key):
        root = self.root

        if len(root.keys) == (2 * self.t) - 1:
            temp = BTreeNode()
            self.root = temp
            temp.children.insert(0, root)

   #         print("before splitting...")            
            self.split_child(temp, 0)
  #          print("after splitting...")            
            self.insert_non_full(temp, key)
        else:
            #print("before: insert_non_full", key)
#            self.print_tree(root)
 #           print(f"insert: {root.name}, root.is_leaf:", str(root.is_leaf))            
            self.insert_non_full(root, key)

    def insert_non_full(self, node, key):
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

            if len(node.children[index].keys) == (2 * self.t) - 1:
                self.split_child(node, index)
                
                if key[0] > node.keys[index][0]:
                    index += 1
                    
            self.insert_non_full(node.children[index], key)

    def split_child(self, node, index):
        t = self.t
        y = node.children[index]
        z = BTreeNode(y.is_leaf)
        node.children.insert(index + 1, z)
        node.keys.insert(index, y.keys[t - 1])
        z.keys = y.keys[t: (2 * t) - 1]
        y.keys = y.keys[0: t - 1]

        if not y.is_leaf:
            z.children = y.children[t: 2 * t]
            y.children = y.children[0: t]

        #print(y.children)            

    def print_tree(self, x, l=0):
        print("Level ", l, " ", len(x.keys), end=": ")
        for i in x.keys:
            print(i, end=" ")
        print()
        l += 1
        if len(x.children) > 0:
            for i in x.children:
                self.print_tree(i, l)

    def count_nodes(self):
        return self._count_nodes(self.root)

    def _count_nodes(self, node):
        count = 1
        if not node.is_leaf:
            for child in node.children:
                count += self._count_nodes(child)
        return count                

    def search(self, node, key):
        index = 0

        while index < len(node.keys) and key > node.keys[index][0]:
            index += 1

        if index < len(node.keys) and key == node.keys[index][0]:
            return node.keys[index][1]
        elif node.is_leaf:
            return None
        else:
            child = node.children[index]
            return self.search(child, key)

    def find(self, key):
        return self.search(self.root, key)

    def delete(self, node, key):
        t = self.t
        i = 0
        while i < len(node.keys) and key[0] > node.keys[i][0]:
            i += 1

        if i < len(node.keys) and node.keys[i][0] == key[0]:
            if node.is_leaf:
                node.keys.pop(i)
            else:
                k = node.keys[i]
                if len(node.children[i].keys) >= t:
                    pred = self.get_pred(node, i)
                    node.keys[i] = pred
                    self.delete(node.children[i], pred)
                elif len(node.children[i + 1].keys) >= t:
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
            if len(node.children[i].keys) < t:
                self.fill(node, i)
            if flag and i > len(node.keys):
                self.delete(node.children[i - 1], key)
            else:
                self.delete(node.children[i], key)

    def get_pred(self, node, idx):
        current = node.children[idx]
        while not current.is_leaf:
            current = current.children[len(current.keys)]
        return current.keys[len(current.keys) - 1]

    def get_succ(self, node, idx):
        current = node.children[idx + 1]
        while not current.is_leaf:
            current = current.children[0]
        return current.keys[0]

    def merge(self, node, idx):
        if idx < 0 or idx >= len(node.keys):
            return

        child = node.children[idx]
        sibling = node.children[idx + 1]
        child.keys.append(node.keys[idx])
        child.keys.extend(sibling.keys)
        if not child.is_leaf:
            child.children.extend(sibling.children)
        node.keys.pop(idx)
        node.children.pop(idx + 1)

    def fill(self, node, idx):
        if idx < 0 or idx > len(node.keys):
            return

        if idx != 0 and len(node.children[idx - 1].keys) >= self.t:
            self.borrow_from_prev(node, idx)
        elif idx != len(node.keys) and len(node.children[idx + 1].keys) >= self.t:
            self.borrow_from_next(node, idx)
        else:
            if idx != len(node.keys):
                self.merge(node, idx)
            else:
                self.merge(node, idx - 1)

    def borrow_from_prev(self, node, idx):
        child = node.children[idx]
        sibling = node.children[idx - 1]
        child.keys.insert(0, node.keys[idx - 1])
        if not child.is_leaf:
            child.children.insert(0, sibling.children.pop())
        node.keys[idx - 1] = sibling.keys.pop()

    def borrow_from_next(self, node, idx):
        child = node.children[idx]
        sibling = node.children[idx + 1]
        child.keys.append(node.keys[idx])
        if not child.is_leaf:
            child.children.append(sibling.children.pop(0))
        node.keys[idx] = sibling.keys.pop(0)

    def traverse_func(self, filter_func):
        results = []

        if self.root:
            self.root.traverse_func(filter_func, results)

        return results

    def traverse_keys(self):
        results = []

        if self.root:
            self.root.traverse_keys(results)

        return results
    
    def update_value(self, key, new_value):
        node, index = self._find_node_and_index(self.root, key)
        
        if node is not None:
            node.keys[index] = (key, new_value)
            return True  # Update successful
        else:
            return False  # Key not found

    def _find_node_and_index(self, node, key):
        index = 0
        
        while index < len(node.keys) and key > node.keys[index][0]:
            index += 1
            
        if index < len(node.keys) and key == node.keys[index][0]:
            return node, index  # Return the node and index where the key is found
        elif node.is_leaf:
            return None, None  # Key not found
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
        count = len(node.keys)  # Count the number of keys in the current node
        if not node.is_leaf:
            for child in node.children:
                count += self._count_all(child)
        return count

    def delete_all(self):
        self.root = BTreeNode(True)
