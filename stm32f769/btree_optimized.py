"""
Optimized B-tree implementation for STM32F769 MicroPython
- Pre-allocated arrays (avoids fragmentation)
- Binary search for O(log n) node lookups
- Separate key/value storage (eliminates tuple overhead)
- Object pooling reduces GC pressure
- Manual memory management to respect constraints
"""

try:
    from bisect import bisect_left
except ImportError:
    # MicroPython compatibility - implement simple binary search
    def bisect_left(a, x):
        lo, hi = 0, len(a)
        while lo < hi:
            mid = (lo + hi) // 2
            if a[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        return lo


class BTreeNode:
    """B-tree node with pre-allocated arrays for efficiency"""
    
    def __init__(self, is_leaf=False, t=5, max_keys=None):
        self.is_leaf = is_leaf
        self.t = t
        self.max_keys = max_keys or (2 * t - 1)
        
        # Pre-allocate arrays to max capacity
        if is_leaf:
            self.keys = [None] * self.max_keys
            self.values = [None] * self.max_keys  # Separate value storage
        else:
            self.keys = [None] * self.max_keys
            self.children = [None] * (2 * t)  # Max children is 2*t
        
        self.key_count = 0  # Actual number of keys in use

    def reset(self):
        """Reset node for reuse in object pool"""
        self.key_count = 0
        for i in range(len(self.keys)):
            self.keys[i] = None
            if self.is_leaf and hasattr(self, 'values'):
                self.values[i] = None
            elif hasattr(self, 'children') and i < len(self.children):
                self.children[i] = None

    def get_child_count(self):
        """Get actual number of children"""
        if self.is_leaf:
            return 0
        count = 0
        for child in self.children:
            if child is not None:
                count += 1
        return count

    def get_child(self, idx):
        """Safe child access"""
        if idx < len(self.children):
            return self.children[idx]
        return None

    def traverse_func(self, filter_func, results):
        """Traverse and filter using callback function"""
        if self.is_leaf:
            for i in range(self.key_count):
                if filter_func(self.values[i]):
                    results.append(self.values[i])
        else:
            for i in range(self.get_child_count()):
                child = self.children[i]
                if child:
                    child.traverse_func(filter_func, results)

    def traverse_keys(self, results):
        """Traverse all key-value pairs"""
        if self.is_leaf:
            for i in range(self.key_count):
                results.append((self.keys[i], self.values[i]))
        else:
            for i in range(self.get_child_count()):
                child = self.children[i]
                if child:
                    child.traverse_keys(results)


class BTreeNodePool:
    """Object pool to reduce garbage collection pressure"""
    
    def __init__(self, max_nodes=50, t=5):
        self.t = t
        self.available_leaf = []
        self.available_internal = []
        
        # Pre-create leaf nodes
        for _ in range(max_nodes // 2):
            node = BTreeNode(is_leaf=True, t=t)
            self.available_leaf.append(node)
        
        # Pre-create internal nodes
        for _ in range(max_nodes // 2):
            node = BTreeNode(is_leaf=False, t=t)
            self.available_internal.append(node)

    def get_leaf(self):
        """Get or create a leaf node"""
        if self.available_leaf:
            node = self.available_leaf.pop()
            node.reset()
            return node
        return BTreeNode(is_leaf=True, t=self.t)

    def get_internal(self):
        """Get or create an internal node"""
        if self.available_internal:
            node = self.available_internal.pop()
            node.reset()
            return node
        return BTreeNode(is_leaf=False, t=self.t)

    def release(self, node):
        """Return node to pool for reuse"""
        node.reset()
        if node.is_leaf and len(self.available_leaf) < 25:
            self.available_leaf.append(node)
        elif not node.is_leaf and len(self.available_internal) < 25:
            self.available_internal.append(node)


class BTree:
    """Optimized B-tree for MicroPython/STM32F769"""
    
    def __init__(self, t=5, use_pool=True):
        """
        Initialize B-tree
        
        Args:
            t: B-tree order (smaller values use less memory)
            use_pool: Enable object pooling
        """
        self.t = t
        self.use_pool = use_pool
        if use_pool:
            self.pool = BTreeNodePool(max_nodes=50, t=t)
            self.root = self.pool.get_leaf()
        else:
            self.root = BTreeNode(is_leaf=True, t=t)

    def insert(self, key, value=None):
        """Insert key-value pair into tree"""
        root = self.root

        # Root is full, split it
        if root.key_count == (2 * self.t - 1):
            if self.use_pool:
                temp = self.pool.get_internal()
            else:
                temp = BTreeNode(is_leaf=False, t=self.t)
            
            temp.children[0] = root
            self.root = temp
            self._split_child(temp, 0)
            self._insert_non_full(temp, key, value)
        else:
            self._insert_non_full(root, key, value)

    def _insert_non_full(self, node, key, value):
        """Insert into non-full node"""
        index = node.key_count - 1

        if node.is_leaf:
            # Insert into leaf node (linear shift for small arrays)
            node.keys[node.key_count] = None
            node.values[node.key_count] = None
            
            while index >= 0 and key < node.keys[index]:
                node.keys[index + 1] = node.keys[index]
                node.values[index + 1] = node.values[index]
                index -= 1
            
            node.keys[index + 1] = key
            node.values[index + 1] = value
            node.key_count += 1
        else:
            # Find correct child using binary search on keys
            child_idx = bisect_left(node.keys[:node.key_count], key)

            child = node.children[child_idx]
            if child.key_count == (2 * self.t - 1):
                self._split_child(node, child_idx)
                if key > node.keys[child_idx]:
                    child_idx += 1
            
            self._insert_non_full(node.children[child_idx], key, value)

    def _split_child(self, parent, child_idx):
        """Split full child node"""
        t = self.t
        child = parent.children[child_idx]
        
        if self.use_pool:
            new_child = self.pool.get_leaf() if child.is_leaf else self.pool.get_internal()
        else:
            new_child = BTreeNode(is_leaf=child.is_leaf, t=t)

        mid_idx = t - 1
        mid_key = child.keys[mid_idx]

        # Handle leaf node split
        if child.is_leaf:
            # Copy right half to new node
            for i in range(t - 1):
                new_child.keys[i] = child.keys[mid_idx + 1 + i]
                new_child.values[i] = child.values[mid_idx + 1 + i]
            
            new_child.key_count = t - 1
            child.key_count = t

            # Insert separating key into parent
            for i in range(parent.key_count, child_idx, -1):
                parent.keys[i] = parent.keys[i - 1]
            parent.keys[child_idx] = mid_key
            
            # Insert new child into parent
            for i in range(parent.get_child_count() - 1, child_idx - 1, -1):
                parent.children[i + 1] = parent.children[i]
            parent.children[child_idx + 1] = new_child
            parent.key_count += 1
        else:
            # Handle internal node split
            for i in range(t - 1):
                new_child.keys[i] = child.keys[mid_idx + 1 + i]
            
            for i in range(t):
                new_child.children[i] = child.children[mid_idx + 1 + i]
            
            new_child.key_count = t - 1
            child.key_count = t - 1

            # Insert separating key into parent
            for i in range(parent.key_count, child_idx, -1):
                parent.keys[i] = parent.keys[i - 1]
            parent.keys[child_idx] = mid_key
            
            # Insert new child into parent
            for i in range(parent.get_child_count() - 1, child_idx - 1, -1):
                parent.children[i + 1] = parent.children[i]
            parent.children[child_idx + 1] = new_child
            parent.key_count += 1

    def search(self, key):
        """Search for key in tree"""
        return self._search(self.root, key)

    def _search(self, node, key):
        """Recursive search using binary search"""
        if node.is_leaf:
            # Binary search in leaf for key
            idx = bisect_left(node.keys[:node.key_count], key)
            if idx < node.key_count and node.keys[idx] == key:
                return node.values[idx]
            return None
        else:
            # Find child with binary search
            idx = bisect_left(node.keys[:node.key_count], key)
            
            # Handle edge case where key equals node key
            if idx < node.key_count and node.keys[idx] == key:
                # For range searches, could return value from internal node
                # For now, continue to leaf
                pass
            
            child = node.children[idx]
            if child:
                return self._search(child, key)
            return None

    def find(self, key):
        """Public search interface"""
        return self.search(key)

    def update_value(self, key, new_value):
        """Update value for existing key"""
        node, index = self._find_node_and_index(self.root, key)
        if node is not None:
            node.values[index] = new_value
            return True
        return False

    def _find_node_and_index(self, node, key):
        """Find node containing key and its index"""
        if node.is_leaf:
            idx = bisect_left(node.keys[:node.key_count], key)
            if idx < node.key_count and node.keys[idx] == key:
                return node, idx
            return None, None
        else:
            idx = bisect_left(node.keys[:node.key_count], key)
            child = node.children[idx]
            if child:
                return self._find_node_and_index(child, key)
            return None, None

    def traverse_func(self, filter_func):
        """Traverse tree applying filter function"""
        results = []
        if self.root:
            self.root.traverse_func(filter_func, results)
        return results

    def traverse_keys(self):
        """Get all key-value pairs"""
        results = []
        if self.root:
            self.root.traverse_keys(results)
        return results

    def count_all(self):
        """Count total key-value pairs"""
        return self._count_all(self.root)

    def _count_all(self, node):
        """Recursive count"""
        if node.is_leaf:
            return node.key_count
        count = 0
        for i in range(node.get_child_count()):
            child = node.children[i]
            if child:
                count += self._count_all(child)
        return count

    def count_nodes(self):
        """Count total nodes"""
        return self._count_nodes(self.root)

    def _count_nodes(self, node):
        """Recursive node count"""
        count = 1
        if not node.is_leaf:
            for i in range(node.get_child_count()):
                child = node.children[i]
                if child:
                    count += self._count_nodes(child)
        return count

    def print_tree(self, node=None, level=0):
        """Debug: print tree structure"""
        if node is None:
            node = self.root
        
        print(f"Level {level}: {node.key_count} keys - ", end="")
        for i in range(node.key_count):
            print(node.keys[i], end=" ")
        print()
        
        if not node.is_leaf:
            for i in range(node.get_child_count()):
                child = node.children[i]
                if child:
                    self.print_tree(child, level + 1)

    def delete(self, key):
        """Delete key from tree"""
        if self.root is None:
            return False
        
        result = self._delete(self.root, key)
        
        # If root is empty and has children, make first child new root
        if self.root.key_count == 0 and not self.root.is_leaf:
            old_root = self.root
            self.root = self.root.children[0]
            if self.use_pool:
                self.pool.release(old_root)
        
        return result

    def _delete(self, node, key):
        """Recursive delete implementation"""
        t = self.t
        
        if node.is_leaf:
            # Remove from leaf
            idx = bisect_left(node.keys[:node.key_count], key)
            if idx < node.key_count and node.keys[idx] == key:
                # Shift remaining elements
                for i in range(idx, node.key_count - 1):
                    node.keys[i] = node.keys[i + 1]
                    node.values[i] = node.values[i + 1]
                node.key_count -= 1
                return True
            return False
        else:
            # Find child containing key
            idx = bisect_left(node.keys[:node.key_count], key)
            
            if idx < node.key_count and node.keys[idx] == key:
                # Key is in internal node - handle later if needed
                pass
            
            # Ensure child has enough keys
            child = node.children[idx]
            if child and child.key_count < t:
                self._fill(node, idx)
                # Recalculate index after fill
                idx = bisect_left(node.keys[:node.key_count], key)
            
            child = node.children[idx]
            if child:
                return self._delete(child, key)
            return False

    def _fill(self, node, idx):
        """Fill child with minimum keys"""
        t = self.t
        child = node.children[idx]
        
        if not child:
            return

        # Try borrow from previous sibling
        if idx > 0:
            prev_sibling = node.children[idx - 1]
            if prev_sibling and prev_sibling.key_count >= t:
                self._borrow_from_prev(node, idx)
                return

        # Try borrow from next sibling
        if idx < node.get_child_count() - 1:
            next_sibling = node.children[idx + 1]
            if next_sibling and next_sibling.key_count >= t:
                self._borrow_from_next(node, idx)
                return

        # Merge with sibling
        if idx < node.get_child_count() - 1:
            self._merge(node, idx)
        else:
            self._merge(node, idx - 1)

    def _borrow_from_prev(self, node, child_idx):
        """Borrow a key from previous sibling"""
        child = node.children[child_idx]
        sibling = node.children[child_idx - 1]

        if child.is_leaf:
            # Move a key from sibling through parent to child
            for i in range(child.key_count, 0, -1):
                child.keys[i] = child.keys[i - 1]
                child.values[i] = child.values[i - 1]
            
            child.keys[0] = sibling.keys[sibling.key_count - 1]
            child.values[0] = sibling.values[sibling.key_count - 1]
            node.keys[child_idx - 1] = child.keys[0]
            
            sibling.key_count -= 1
            child.key_count += 1

    def _borrow_from_next(self, node, child_idx):
        """Borrow a key from next sibling"""
        child = node.children[child_idx]
        sibling = node.children[child_idx + 1]

        if child.is_leaf:
            child.keys[child.key_count] = sibling.keys[0]
            child.values[child.key_count] = sibling.values[0]
            
            for i in range(sibling.key_count - 1):
                sibling.keys[i] = sibling.keys[i + 1]
                sibling.values[i] = sibling.values[i + 1]
            
            node.keys[child_idx] = sibling.keys[0]
            sibling.key_count -= 1
            child.key_count += 1

    def _merge(self, node, idx):
        """Merge child with its sibling"""
        child = node.children[idx]
        sibling = node.children[idx + 1]

        if child.is_leaf:
            # Merge leaf nodes
            for i in range(sibling.key_count):
                child.keys[child.key_count + i] = sibling.keys[i]
                child.values[child.key_count + i] = sibling.values[i]
            child.key_count += sibling.key_count
        else:
            # Merge internal nodes - move separator key down
            child.keys[child.key_count] = node.keys[idx]
            for i in range(sibling.key_count):
                child.keys[child.key_count + 1 + i] = sibling.keys[i]
            for i in range(sibling.get_child_count()):
                child.children[child.key_count + 1 + i] = sibling.children[i]
            child.key_count += sibling.key_count + 1

        # Remove separator key from parent
        for i in range(idx, node.key_count - 1):
            node.keys[i] = node.keys[i + 1]
        node.key_count -= 1

        # Remove sibling from parent's children
        for i in range(idx + 1, node.get_child_count() - 1):
            node.children[i] = node.children[i + 1]
        
        if self.use_pool:
            self.pool.release(sibling)

    def delete_all(self):
        """Clear the tree"""
        if self.use_pool:
            self.pool.release(self.root)
            self.root = self.pool.get_leaf()
        else:
            self.root = BTreeNode(is_leaf=True, t=self.t)
