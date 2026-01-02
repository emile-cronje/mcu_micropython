import os
import ujson as json

class NodeManager:
    """
    Manages the storage and retrieval of B+ Tree nodes on disk.
    
    This class handles the serialization and deserialization of nodes,
    as well as managing metadata about the tree, such as the root node's ID.
    """
    def __init__(self, directory, dataFile):
        self.directory = directory
        self.meta_path = f"{directory}/{dataFile}"
        
        try:
            os.listdir(self.directory)
        except OSError:
            os.mkdir(self.directory)
        self.meta = self._load_meta()

    def _load_meta(self):
        try:
            with open(self.meta_path, 'r') as f:
                return json.load(f)
        except (OSError, ValueError):
            return {'root_id': None, 'next_node_id': 0, 'first_leaf_id': None}

    def _save_meta(self):
        with open(self.meta_path, 'w') as f:
            json.dump(self.meta, f)

    def get_node(self, node_id):
        node_path = f"{self.directory}/{node_id}.node"
        with open(node_path, 'r') as f:
            data = json.load(f)
        
        node = BPlusTreeNode(self, is_leaf=data['is_leaf'], node_id=data['node_id'])
        node.keys = data['keys']
        node.child_ids = data.get('child_ids', [])
        node.next_leaf_id = data.get('next_leaf_id')
        node.parent_id = data.get('parent_id') # Needed for deletion
        return node

    def save_node(self, node):
        node_path = f"{self.directory}/{node.node_id}.node"
        data = {
            'node_id': node.node_id, 
            'is_leaf': node.is_leaf, 
            'keys': node.keys,
            'parent_id': node.parent_id
        }
        if not node.is_leaf:
            data['child_ids'] = node.child_ids
        else:
            data['next_leaf_id'] = node.next_leaf_id

        with open(node_path, 'w') as f:
            json.dump(data, f)

    def delete_node(self, node_id):
        node_path = f"{self.directory}/{node_id}.node"
        try:
            os.remove(node_path)
        except OSError:
            pass

    def get_new_node_id(self):
        node_id = self.meta['next_node_id']
        self.meta['next_node_id'] += 1
        self._save_meta()
        return node_id

    def set_root_id(self, node_id):
        self.meta['root_id'] = node_id
        self._save_meta()

    def get_root_id(self):
        return self.meta.get('root_id')

    def set_first_leaf_id(self, node_id):
        self.meta['first_leaf_id'] = node_id
        self._save_meta()

    def get_first_leaf_id(self):
        return self.meta.get('first_leaf_id')
        
    def delete_all(self):
        for filename in os.listdir(self.directory):
            try:
                os.remove(f"{self.directory}/{filename}")
            except OSError:
                pass
        self.meta = {'root_id': None, 'next_node_id': 0, 'first_leaf_id': None}
        self._save_meta()

class BPlusTreeNode:
    """
    Represents a single node in the B+ Tree.
    """
    def __init__(self, manager, is_leaf=False, node_id=None):
        self.manager = manager
        self.is_leaf = is_leaf
        self.keys = []
        self.child_ids = []
        self.next_leaf_id = None
        self.parent_id = None
        self.node_id = node_id if node_id is not None else self.manager.get_new_node_id()
    
    def save(self):
        self.manager.save_node(self)
    
    def get_child(self, index):
        child_node = self.manager.get_node(self.child_ids[index])
        child_node.parent_id = self.node_id # Set parent reference
        return child_node

    def get_parent(self):
        if self.parent_id is not None:
            return self.manager.get_node(self.parent_id)
        return None

class BPlusTree:
    """
    An implementation of a B+ Tree that persists data to disk.
    """
    def __init__(self, t, directory='./bplustree_data', dataFile='metadata.json'):
        self.t = t
        self.manager = NodeManager(directory, dataFile)
        root_id = self.manager.get_root_id()

        if root_id is None:
            root = BPlusTreeNode(self.manager, is_leaf=True)
            root.save()
            self.manager.set_root_id(root.node_id)
            self.manager.set_first_leaf_id(root.node_id)
            self.root_id = root.node_id
        else:
            self.root_id = root_id

    def _get_root(self):
        return self.manager.get_node(self.root_id)

    def insert(self, key_value):
        key, value = key_value
        root = self._get_root()

        if len(root.keys) == (2 * self.t) - 1:
            old_root = root
            new_root = BPlusTreeNode(self.manager, is_leaf=False)
            new_root.child_ids.append(old_root.node_id)
            old_root.parent_id = new_root.node_id
            old_root.save()
            
            self.root_id = new_root.node_id
            self.manager.set_root_id(new_root.node_id)
            
            self._split_child(new_root, 0)
            self._insert_non_full(new_root, key, value)
        else:
            self._insert_non_full(root, key, value)

    def _insert_non_full(self, node, key, value):
        if node.is_leaf:
            i = 0
            while i < len(node.keys) and key > node.keys[i][0]:
                i += 1
            node.keys.insert(i, [key, value])
            node.save()
        else:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            
            child = node.get_child(i)
            if len(child.keys) == (2 * self.t) - 1:
                self._split_child(node, i)
                if key >= node.keys[i]:
                    i += 1
            
            child_for_insert = node.get_child(i)
            self._insert_non_full(child_for_insert, key, value)

    def _split_child(self, parent_node, child_index):
        t = self.t
        child_to_split = parent_node.get_child(child_index)
        
        new_sibling = BPlusTreeNode(self.manager, is_leaf=child_to_split.is_leaf)
        new_sibling.parent_id = parent_node.node_id
        
        median_index = t - 1
        
        if child_to_split.is_leaf:
            new_sibling.keys = child_to_split.keys[t:]
            child_to_split.keys = child_to_split.keys[:t]
            
            parent_node.keys.insert(child_index, new_sibling.keys[0][0])
            parent_node.child_ids.insert(child_index + 1, new_sibling.node_id)
            
            new_sibling.next_leaf_id = child_to_split.next_leaf_id
            child_to_split.next_leaf_id = new_sibling.node_id
        else: 
            median_key = child_to_split.keys[median_index]
            
            new_sibling.keys = child_to_split.keys[t:]
            child_to_split.keys = child_to_split.keys[:median_index]
            
            new_sibling.child_ids = child_to_split.child_ids[t:]
            child_to_split.child_ids = child_to_split.child_ids[:t]
            
            parent_node.keys.insert(child_index, median_key)
            parent_node.child_ids.insert(child_index + 1, new_sibling.node_id)
            
            for child_id in new_sibling.child_ids:
                child_node = self.manager.get_node(child_id)
                child_node.parent_id = new_sibling.node_id
                child_node.save()

        new_sibling.save()
        child_to_split.save()
        parent_node.save()

    def find(self, key):
        if self.root_id is None: return None
        return self._search(self._get_root(), key)

    def _search(self, node, key):
        if node.is_leaf:
            for k, v in node.keys:
                if k == key: return v
            return None
        else:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            child_node = node.get_child(i)
            return self._search(child_node, key)

    def traverse_keys(self):
        results = []
        first_leaf_id = self.manager.get_first_leaf_id()
        if first_leaf_id is None: return results
            
        current_node = self.manager.get_node(first_leaf_id)
        while current_node:
            results.extend(current_node.keys)
            if current_node.next_leaf_id:
                current_node = self.manager.get_node(current_node.next_leaf_id)
            else: break
        return results

    # --- Start of Added/Fixed Methods ---

    def _find_leaf_node(self, key):
        """Helper to find the leaf node where a key should exist."""
        node = self._get_root()
        while not node.is_leaf:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.get_child(i)
        return node
        
    def count_all(self):
        """Counts all records by traversing the leaf nodes."""
        count = 0
        first_leaf_id = self.manager.get_first_leaf_id()
        if first_leaf_id is None: return 0
            
        node = self.manager.get_node(first_leaf_id)
        while node:
            count += len(node.keys)
            if node.next_leaf_id:
                node = self.manager.get_node(node.next_leaf_id)
            else: break
        return count

    def update_value(self, key, new_value):
        """Finds a key in a leaf and updates its value."""
        leaf_node = self._find_leaf_node(key)
        for i, (k, v) in enumerate(leaf_node.keys):
            if k == key:
                leaf_node.keys[i] = [key, new_value]
                leaf_node.save()
                return True
        return False

    def traverse_func(self, filter_func):
        """Traverses leaf nodes and returns values that match the filter function."""
        results = []
        first_leaf_id = self.manager.get_first_leaf_id()
        if first_leaf_id is None: return results
            
        node = self.manager.get_node(first_leaf_id)
        while node:
            for k, v in node.keys:
                if filter_func(v):
                    results.append(v)
            if node.next_leaf_id:
                node = self.manager.get_node(node.next_leaf_id)
            else: break
        return results

    def delete(self, key):
        """Deletes a key-value pair from a leaf node."""
        leaf_node = self._find_leaf_node(key)
        
        # Find and remove the key from the leaf
        key_found = False
        for i, (k, v) in enumerate(leaf_node.keys):
            if k == key:
                leaf_node.keys.pop(i)
                key_found = True
                break
        
        if not key_found:
            return # Key not in tree
            
        leaf_node.save()
        
        # Note: This is a simplified delete. A full implementation would handle
        # underflow by borrowing from or merging with siblings, and updating parent keys,
        # which is significantly more complex. For your demo script, this will work
        # as long as deletion doesn't cause underflow.

    def delete_all(self):
        self.manager.delete_all()
        # Re-initialize the tree state after deleting all files
        self.__init__(self.t, self.manager.directory, self.manager.meta_path.split('/')[-1])
        print("B+ Tree data has been deleted.")