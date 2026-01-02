class BTreeNode:
    def __init__(self, is_leaf = False, name = 'root'):
        self.name = name
        self.is_leaf = is_leaf
        if is_leaf:
            self.keys = []  # For leaf nodes: [(key, value), ...]
        else:
            self.keys = []  # For internal nodes: [key1, key2, ...] (routing keys only)
        self.children = []

    def traverse_func(self, filter_func, results):
        if self.is_leaf:
            # Only leaf nodes contain actual data to filter
            for key_value in self.keys:
                if filter_func(key_value[1]):
                    results.append(key_value[1])
        else:
            # Internal nodes: traverse children
            for i in range(len(self.children)):
                self.children[i].traverse_func(filter_func, results)

    def traverse_keys(self, results):
        if self.is_leaf:
            # Only leaf nodes contain actual data
            for key_value in self.keys:
                results.append(key_value)
        else:
            # Internal nodes: traverse children
            for child in self.children:
                child.traverse_keys(results)

class BTree:
    def __init__(self, t):
        self.root = BTreeNode(True)
        self.t = t

    def insert(self, key):
        root = self.root

        if len(root.keys) == (2 * self.t) - 1:
            temp = BTreeNode()
            self.root = temp
            temp.children.insert(0, root)
            self.split_child(temp, 0)
            self.insert_non_full(temp, key)
        else:
            self.insert_non_full(root, key)

    def insert_non_full(self, node, key):
        index = len(node.keys) - 1
        
        if node.is_leaf:
            # Leaf node: insert the (key, value) tuple
            node.keys.append((None, None))
            
            while index >= 0 and key[0] < node.keys[index][0]:
                node.keys[index + 1] = node.keys[index]
                index -= 1
                
            node.keys[index + 1] = key
        else:
            # Internal node: find correct child and insert routing key only
            while index >= 0 and key[0] < node.keys[index]:
                index -= 1
                
            index += 1

            if len(node.children[index].keys) == (2 * self.t) - 1:
                self.split_child(node, index)
                
                if key[0] > node.keys[index]:
                    index += 1
                    
            self.insert_non_full(node.children[index], key)

    def split_child(self, node, index):
        t = self.t
        y = node.children[index]
        z = BTreeNode(y.is_leaf)
        node.children.insert(index + 1, z)
        
        if y.is_leaf:
            # Splitting leaf node: promote key only, keep data in leaves
            mid_key = y.keys[t - 1][0]  # Extract just the key for promotion
            node.keys.insert(index, mid_key)
            z.keys = y.keys[t:]  # Right half keeps (key, value) tuples
            y.keys = y.keys[0: t]  # Left half keeps (key, value) tuples
        else:
            # Splitting internal node: promote routing key
            mid_key = y.keys[t - 1]  # This is already just a key
            node.keys.insert(index, mid_key)
            z.keys = y.keys[t: (2 * t) - 1]
            y.keys = y.keys[0: t - 1]
            
            # Move children
            z.children = y.children[t: 2 * t]
            y.children = y.children[0: t]

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
        if node.is_leaf:
            # Leaf node: search for actual data
            for key_value in node.keys:
                if key_value[0] == key:
                    return key_value[1]
            return None
        else:
            # Internal node: use routing keys to find correct child
            index = 0
            while index < len(node.keys) and key > node.keys[index]:
                index += 1
            
            child = node.children[index]
            return self.search(child, key)

    def find(self, key):
        return self.search(self.root, key)

    def delete(self, key):
        """Public method to delete a key from the B-tree"""
        if self.root is None:
            return False
            
        result = self._delete(self.root, key)
        
        # If root becomes empty and has children, make first child the new root
        if len(self.root.keys) == 0 and not self.root.is_leaf:
            self.root = self.root.children[0]
            
        return result

    def _delete(self, node, key):
        t = self.t
        
        # Handle both (key,) and key formats
        search_key = key[0] if isinstance(key, tuple) else key
        
        if node.is_leaf:
            # Leaf node: remove the actual data
            for i, key_value in enumerate(node.keys):
                if key_value[0] == search_key:
                    node.keys.pop(i)
                    return True
            return False  # Key not found
        else:
            # Internal node: find which child should contain the key
            i = 0
            while i < len(node.keys) and search_key > node.keys[i]:
                i += 1

            # Ensure child has enough keys before descending
            if len(node.children[i].keys) < t:
                self.fill(node, i)
                
                # After filling, recalculate index as structure may have changed
                i = 0
                while i < len(node.keys) and search_key > node.keys[i]:
                    i += 1
                
            return self._delete(node.children[i], key)

    def fill(self, node, idx):
        t = self.t
        
        # Check bounds
        if idx < 0 or idx >= len(node.children):
            return

        # Try to borrow from previous sibling
        if idx != 0 and len(node.children[idx - 1].keys) >= t:
            self.borrow_from_prev(node, idx)
        # Try to borrow from next sibling
        elif idx != len(node.children) - 1 and len(node.children[idx + 1].keys) >= t:
            self.borrow_from_next(node, idx)
        # Must merge
        else:
            if idx != len(node.children) - 1:
                self.merge(node, idx)
            else:
                self.merge(node, idx - 1)

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
        
        if child.is_leaf:
            # Merging leaf nodes: just combine data
            child.keys.extend(sibling.keys)
        else:
            # Merging internal nodes: include the routing key from parent
            child.keys.append(node.keys[idx])
            child.keys.extend(sibling.keys)
            child.children.extend(sibling.children)
            
        node.keys.pop(idx)
        node.children.pop(idx + 1)



    def borrow_from_prev(self, node, idx):
        child = node.children[idx]
        sibling = node.children[idx - 1]
        
        if child.is_leaf:
            # Borrowing between leaf nodes
            borrowed_item = sibling.keys.pop()
            child.keys.insert(0, borrowed_item)
            # Update parent's routing key to reflect the new minimum in child
            node.keys[idx - 1] = child.keys[0][0]
        else:
            # Borrowing between internal nodes
            child.keys.insert(0, node.keys[idx - 1])
            if sibling.children:
                child.children.insert(0, sibling.children.pop())
            node.keys[idx - 1] = sibling.keys.pop()

    def borrow_from_next(self, node, idx):
        child = node.children[idx]
        sibling = node.children[idx + 1]
        
        if child.is_leaf:
            # Borrowing between leaf nodes
            borrowed_item = sibling.keys.pop(0)
            child.keys.append(borrowed_item)
            # Update parent's routing key to reflect the new minimum in sibling
            node.keys[idx] = sibling.keys[0][0] if sibling.keys else borrowed_item[0]
        else:
            # Borrowing between internal nodes
            child.keys.append(node.keys[idx])
            if sibling.children:
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
        if node.is_leaf:
            # Leaf node: search for actual data
            for i, key_value in enumerate(node.keys):
                if key_value[0] == key:
                    return node, i
            return None, None
        else:
            # Internal node: use routing keys to find correct child
            index = 0
            while index < len(node.keys) and key > node.keys[index]:
                index += 1
            
            child = node.children[index]
            return self._find_node_and_index(child, key)
        
    def count_all(self):
        return self._count_all(self.root)

    def _count_all(self, node):
        if node.is_leaf:
            return len(node.keys)  # Count actual data entries
        else:
            count = 0
            for child in node.children:
                count += self._count_all(child)
            return count

    def delete_all(self):
        self.root = BTreeNode(True)