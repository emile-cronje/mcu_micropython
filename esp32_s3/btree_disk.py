import os
import ujson as json

class NodeManager:
    def __init__(self, directory, dataFile):
        self.directory = directory
        self.meta_path = f"{directory}/{dataFile}"
        
        try:
            print("NodeManager: " + self.meta_path)
            os.listdir(self.directory)
        except OSError:
            os.mkdir(self.directory)
        self.meta = self._load_meta()

    def _load_meta(self):
        try:
            with open(self.meta_path, 'r') as f:
                return json.load(f)
        except (OSError, ValueError):
            return {'root_id': None, 'next_node_id': 0}

    def _save_meta(self):
        with open(self.meta_path, 'w') as f:
            json.dump(self.meta, f)

    def get_node(self, node_id):
        node_path = f"{self.directory}/{node_id}.node"
        with open(node_path, 'r') as f:
            data = json.load(f)
        
        node = BTreeNode(self, is_leaf=data['is_leaf'], node_id=data['node_id'])
        node.keys = data['keys']
        node.child_ids = data['child_ids']
        return node

    def save_node(self, node):
        node_path = f"{self.directory}/{node.node_id}.node"
        data = {'node_id': node.node_id, 'is_leaf': node.is_leaf, 'keys': node.keys, 'child_ids': node.child_ids}
        with open(node_path, 'w') as f:
            json.dump(data, f)

    def delete_node(self, node_id):
        """Removes a node file from the disk."""
        node_path = f"{self.directory}/{node_id}.node"
        try:
            os.remove(node_path)
        except OSError:
            pass # Ignore if file doesn't exist

    def get_new_node_id(self):
        node_id = self.meta['next_node_id']
        self.meta['next_node_id'] += 1
        self._save_meta()
        return node_id

    def set_root_id(self, node_id):
        self.meta['root_id'] = node_id
        self._save_meta()

    def get_root_id(self):
        return self.meta['root_id']

    def delete_all(self):
        for filename in os.listdir(self.directory):
            try:
                os.remove(f"{self.directory}/{filename}")
                print("Delete all: " + f"{self.directory}/{filename}")
            except OSError:
                pass
        self.meta = {'root_id': None, 'next_node_id': 0}
        self._save_meta()

class BTreeNode:
    def __init__(self, manager, is_leaf=False, node_id=None):
        self.manager = manager
        self.is_leaf = is_leaf
        self.keys = []
        self.child_ids = []
        self.node_id = node_id if node_id is not None else self.manager.get_new_node_id()
    def save(self): self.manager.save_node(self)
    
    def get_child(self, index): return self.manager.get_node(self.child_ids[index])
    
    def traverse_keys(self, results):
        if self.is_leaf:
            results.extend(self.keys)
        else:
            for child_id in self.child_ids: self.manager.get_node(child_id).traverse_keys(results)
            
    def traverse_func(self, filter_func, results):
        if self.is_leaf:
            for k, v in self.keys:
                if filter_func(v): results.append(v)
        else:
            for child_id in self.child_ids:
                self.manager.get_node(child_id).traverse_func(filter_func, results)
            
class BTree:
    def __init__(self, t, directory='./btree_data', dataFile = 'data.json'):
        self.t = t
        self.manager = NodeManager(directory, dataFile)
        root_id = self.manager.get_root_id()

        if root_id is None:
            root = BTreeNode(self.manager, is_leaf=True)
            root.save()
            self.manager.set_root_id(root.node_id)
            self.root_id = root.node_id
        else:
            self.root_id = root_id

    def _get_root(self):
        return self.manager.get_node(self.root_id)

    def insert(self, key_value):
        if not isinstance(key_value, list):
             key_value = list(key_value)
             
        root = self._get_root()
        if len(root.keys) == (2 * self.t) - 1:
            old_root = root
            new_root_id = self.manager.get_new_node_id()
            new_root = BTreeNode(self.manager, is_leaf=False, node_id=new_root_id)
            new_root.child_ids.append(old_root.node_id)
            self._split_child(new_root, 0)
            
            self.root_id = new_root.node_id
            self.manager.set_root_id(new_root.node_id)
            
            self._insert_non_full(new_root, key_value)
        else:
            self._insert_non_full(root, key_value)

    def _insert_non_full(self, node, key_value):
        i = len(node.keys) - 1
        key_to_insert = key_value[0]

        if node.is_leaf:
            node.keys.append([None, None])
            while i >= 0 and key_to_insert < node.keys[i][0]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = key_value
            node.save()
        else:
            while i >= 0 and key_to_insert < node.keys[i]:
                i -= 1
            i += 1
            
            child = node.get_child(i)

            if len(child.keys) == (2 * self.t) - 1:
                self._split_child(node, i)
                if key_to_insert > node.keys[i]:
                    i += 1
            
            child_for_insert = node.get_child(i)
            self._insert_non_full(child_for_insert, key_value)

    def _split_child(self, parent_node, child_index):
        t = self.t
        child_to_split = parent_node.get_child(child_index)
        new_sibling = BTreeNode(self.manager, is_leaf=child_to_split.is_leaf)
        parent_node.child_ids.insert(child_index + 1, new_sibling.node_id)

        if child_to_split.is_leaf:
            median_key = child_to_split.keys[t - 1][0]
            parent_node.keys.insert(child_index, median_key)
            new_sibling.keys = child_to_split.keys[t - 1:]
            child_to_split.keys = child_to_split.keys[:t - 1]
        else:
            median_key = child_to_split.keys[t - 1]
            parent_node.keys.insert(child_index, median_key)
            new_sibling.keys = child_to_split.keys[t:]
            child_to_split.keys = child_to_split.keys[:t - 1]
            new_sibling.child_ids = child_to_split.child_ids[t:]
            child_to_split.child_ids = child_to_split.child_ids[:t]

        new_sibling.save()
        child_to_split.save()
        parent_node.save()

    def find(self, key):
        if self.root_id is None: return None
        return self._search(self._get_root(), key)

    def _search(self, node, key):
        if node.is_leaf:
            for k, v in node.keys:
                if k == key:
                    return v
            return None
        else:
            i = 0
            
            while i < len(node.keys) and key >= node.keys[i]:                
                i += 1
            
            child_node = node.get_child(i)
            return self._search(child_node, key)
    
    def print_tree(self):
        if self.root_id is None: return
        self._print_node(self._get_root(), 0)

    def _print_node(self, node, level):
        print(f"Level {level}, Node {node.node_id}, Leaf: {node.is_leaf}")
        print("  Keys:", node.keys)
        if not node.is_leaf:
            print("  Child IDs:", node.child_ids)
            for i in range(len(node.child_ids)):
                child_node = node.get_child(i)
                self._print_node(child_node, level + 1)
                
    def delete_all(self):
        self.manager.delete_all()
        self.__init__(self.t, self.manager.directory)
        print("B-Tree data has been deleted.")
        
    def traverse_keys(self):
        results = []
        if self.root_id is not None:
            self._get_root().traverse_keys(results)
        return results        

    def traverse_func(self, filter_func):
        results = []
        if self.root_id is not None:
            self._get_root().traverse_func(filter_func, results)
        return results

    def delete(self, key):
        if self.root_id is None: return
        self._delete(self._get_root(), key)
        root = self._get_root()
        if len(root.keys) == 0 and not root.is_leaf:
            new_root_id = root.child_ids[0]
            self.manager.delete_node(self.root_id)
            self.root_id = new_root_id
            self.manager.set_root_id(new_root_id)

    def _delete(self, node, key):
        if node.is_leaf:
            original_len = len(node.keys)
            node.keys = [kv for kv in node.keys if kv[0] != key]
            if len(node.keys) != original_len:
                node.save()
            return
        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1
        
        child = node.get_child(i)
        if len(child.keys) < self.t:
            self._fill(node, i)
            # After fill, the path might have changed, re-find the correct child index
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
        
        child_to_delete_from = node.get_child(i)
        self._delete(child_to_delete_from, key)


    def _fill(self, parent_node, child_idx):
        if child_idx != 0:
            left_sibling = parent_node.get_child(child_idx - 1)
            if len(left_sibling.keys) >= self.t:
                self._borrow_from_prev(parent_node, child_idx)
                return
        if child_idx != len(parent_node.child_ids) - 1:
            right_sibling = parent_node.get_child(child_idx + 1)
            if len(right_sibling.keys) >= self.t:
                self._borrow_from_next(parent_node, child_idx)
                return
        if child_idx != len(parent_node.child_ids) - 1:
            self._merge(parent_node, child_idx)
        else:
            self._merge(parent_node, child_idx - 1)

    def _borrow_from_prev(self, parent_node, child_idx):
        child = parent_node.get_child(child_idx)
        sibling = parent_node.get_child(child_idx - 1)
        borrowed_item = sibling.keys.pop()
        child.keys.insert(0, borrowed_item)
        
        # --- Start of fix ---
        if child.is_leaf:
            parent_node.keys[child_idx - 1] = child.keys[0][0]
        else:
            parent_node.keys[child_idx - 1] = child.keys[0]
        # --- End of fix ---

        if not child.is_leaf:
            borrowed_child_id = sibling.child_ids.pop()
            child.child_ids.insert(0, borrowed_child_id)
        
        child.save()
        sibling.save()
        parent_node.save()

    def _borrow_from_next(self, parent_node, child_idx):
        child = parent_node.get_child(child_idx)
        sibling = parent_node.get_child(child_idx + 1)
        borrowed_item = sibling.keys.pop(0)
        child.keys.append(borrowed_item)

        # --- Start of fix ---
        if sibling.is_leaf:
            parent_node.keys[child_idx] = sibling.keys[0][0]
        else:
            parent_node.keys[child_idx] = sibling.keys[0]
        # --- End of fix ---

        if not child.is_leaf:
            borrowed_child_id = sibling.child_ids.pop(0)
            child.child_ids.append(borrowed_child_id)

        child.save()
        sibling.save()
        parent_node.save()

    def _merge(self, parent_node, child_idx):
        child = parent_node.get_child(child_idx)
        sibling = parent_node.get_child(child_idx + 1)
        child.keys.extend(sibling.keys)
        if not child.is_leaf:
            child.child_ids.extend(sibling.child_ids)
        parent_node.keys.pop(child_idx)
        parent_node.child_ids.pop(child_idx + 1)
        child.save()
        parent_node.save()
        self.manager.delete_node(sibling.node_id)

    def count_all(self):
        """
        Counts all data records in the tree in a memory-efficient way.
        """
        if self.root_id is None:
            return 0
        return self._count_all(self.manager.get_node(self.root_id))

    def _count_all(self, node):
        """
        Recursive helper that counts records starting from a given node.
        """
        # If the node is a leaf, return the number of records it holds.
        if node.is_leaf:
            return len(node.keys)
        
        # If it's an internal node, sum the counts from all its children.
        count = 0
        for child_id in node.child_ids:
            child_node = self.manager.get_node(child_id)
            count += self._count_all(child_node)
        return count

    def update_value(self, key, new_value):
        """
        Finds a key in the tree and updates its value.
        The change is saved persistently to disk.
        """
        # Find the node containing the key and the key's index within that node.
        node, index = self._find_node_and_index(self._get_root(), key)
        
        if node is not None:
            # If found, update the value in the key-value pair.
            # Note: We use a list, as ujson serializes tuples to lists anyway.
            node.keys[index] = [key, new_value]
            
            # *** Crucially, save the modified node back to disk. ***
            node.save()
            return True  # Update successful
        else:
            return False # Key not found

    def _find_node_and_index(self, node, key):
        """
        Recursively finds the node and the index of a key within that node.
        Returns (node, index) if found, otherwise (None, None).
        """
        if node.is_leaf:
            # In a leaf, search for the key directly.
            for i, key_value in enumerate(node.keys):
                if key_value[0] == key:
                    return node, i # Return the node object and the index
            return None, None # Not found in this leaf
        else:
            # In an internal node, find the correct child to descend into.
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            
            # Load the child from disk and continue the search.
            child_node = node.get_child(i)
            return self._find_node_and_index(child_node, key)
