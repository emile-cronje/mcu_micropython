class BTreeNode:
    def __init__(self, is_leaf=False, name='root'):
        self.name = name
        self.is_leaf = is_leaf
        self.key_values = {}  # Stores key: value pairs
        self._sorted_own_keys = []  # Sorted list of keys in this node
        self.child_nodes = {}  # Stores index: BTreeNode child

    def traverse_func(self, filter_func, results):
        num_keys = len(self._sorted_own_keys)
        for i in range(num_keys):
            if not self.is_leaf and i in self.child_nodes:
                self.child_nodes[i].traverse_func(filter_func, results)
            
            key = self._sorted_own_keys[i]
            value = self.key_values[key]
            if filter_func(value):
                results.append(value)
                
        if not self.is_leaf and num_keys in self.child_nodes: # Last child
            self.child_nodes[num_keys].traverse_func(filter_func, results)

    def traverse_keys(self, results):
        num_keys = len(self._sorted_own_keys)
        for i in range(num_keys):
            if not self.is_leaf and i in self.child_nodes:
                self.child_nodes[i].traverse_keys(results)
            
            key = self._sorted_own_keys[i]
            value = self.key_values[key]
            results.append((key, value)) # Append (key, value) tuple
            
        if not self.is_leaf and num_keys in self.child_nodes: # Last child
            self.child_nodes[num_keys].traverse_keys(results)

class BTree:
    def __init__(self, t):
        self.root = BTreeNode(True, name='root')
        self.t = t # Minimum degree

    def insert(self, key, value): # Changed signature
        item_pair = (key, value)
        root_node = self.root

        if len(root_node._sorted_own_keys) == (2 * self.t) - 1:
            temp_new_root = BTreeNode(is_leaf=False, name=f"new_root_after_split_of_{root_node.name}")
            self.root = temp_new_root
            temp_new_root.child_nodes[0] = root_node # Old root becomes child of new root
            self.split_child(temp_new_root, 0) # Split old root
            self.insert_non_full(temp_new_root, item_pair)
        else:
            self.insert_non_full(root_node, item_pair)

    def insert_non_full(self, node, item_pair):
        item_k, item_v = item_pair
        
        # Find the position for the new key in the sorted list of keys
        idx = len(node._sorted_own_keys) - 1
        if node.is_leaf:
            # Make space for the new key
            node._sorted_own_keys.append(None) 
            while idx >= 0 and item_k < node._sorted_own_keys[idx]:
                node._sorted_own_keys[idx + 1] = node._sorted_own_keys[idx]
                idx -= 1
            node._sorted_own_keys[idx + 1] = item_k
            node.key_values[item_k] = item_v
        else:
            # Find the child to insert into
            while idx >= 0 and item_k < node._sorted_own_keys[idx]:
                idx -= 1
            idx += 1 # This is the child index

            if len(node.child_nodes[idx]._sorted_own_keys) == (2 * self.t) - 1:
                self.split_child(node, idx) # idx is the child index in parent's children
                # After split, the median key from child moves to parent at node._sorted_own_keys[idx]
                if item_k > node._sorted_own_keys[idx]:
                    idx += 1 # New key goes to the new right child
            self.insert_non_full(node.child_nodes[idx], item_pair)

    def split_child(self, parent_node, child_idx_in_parent):
        t = self.t
        child_to_split = parent_node.child_nodes[child_idx_in_parent]
        new_sibling_node = BTreeNode(child_to_split.is_leaf, name=f"split_sibling_of_{child_to_split.name}")

        # Median key from child_to_split moves up to parent_node
        median_key = child_to_split._sorted_own_keys[t - 1]
        median_value = child_to_split.key_values[median_key]

        # Insert median key and value into parent_node
        parent_node._sorted_own_keys.insert(child_idx_in_parent, median_key)
        parent_node.key_values[median_key] = median_value

        # Adjust children in parent_node: make space for new_sibling_node
        # Shift children from child_idx_in_parent + 1 onwards to the right
        num_parent_children_before_split = len(parent_node.child_nodes)
        for i in range(num_parent_children_before_split -1 , child_idx_in_parent, -1): # Iterate backwards
            parent_node.child_nodes[i + 1] = parent_node.child_nodes[i]
        parent_node.child_nodes[child_idx_in_parent + 1] = new_sibling_node
        
        # Distribute keys/values from child_to_split to new_sibling_node
        new_sibling_node._sorted_own_keys = child_to_split._sorted_own_keys[t : (2 * t) - 1]
        for k_for_sibling in new_sibling_node._sorted_own_keys:
            new_sibling_node.key_values[k_for_sibling] = child_to_split.key_values[k_for_sibling]
            del child_to_split.key_values[k_for_sibling] # Remove from original child's data

        # Update keys in original child_to_split (and ensure its key_values is consistent)
        original_child_remaining_keys = child_to_split._sorted_own_keys[0 : t - 1]
        new_original_child_key_values = {}
        for k_original in original_child_remaining_keys:
            # This key should still be in child_to_split.key_values if not moved
            if k_original in child_to_split.key_values:
                 new_original_child_key_values[k_original] = child_to_split.key_values[k_original]
        child_to_split.key_values = new_original_child_key_values
        child_to_split._sorted_own_keys = original_child_remaining_keys


        if not child_to_split.is_leaf:
            # Distribute children of child_to_split
            # Children for new_sibling_node
            new_idx_for_sibling_child = 0
            for original_child_node_idx in range(t, len(child_to_split.child_nodes)):
                if original_child_node_idx in child_to_split.child_nodes:
                    new_sibling_node.child_nodes[new_idx_for_sibling_child] = child_to_split.child_nodes[original_child_node_idx]
                    new_idx_for_sibling_child +=1
            
            # Children remaining in child_to_split (re-index them)
            new_original_child_children = {}
            new_idx_for_original_child_child = 0
            for original_child_node_idx in range(0, t):
                 if original_child_node_idx in child_to_split.child_nodes:
                    new_original_child_children[new_idx_for_original_child_child] = child_to_split.child_nodes[original_child_node_idx]
                    new_idx_for_original_child_child +=1
            child_to_split.child_nodes = new_original_child_children

    def print_tree(self, node, level=0):
        print(f"Level {level}, Node: {node.name}, Keys: {len(node._sorted_own_keys)}", end=": ")
        for k in node._sorted_own_keys:
            print(f"({k}:{node.key_values[k]})", end=" ")
        print(f"IsLeaf: {node.is_leaf}")
        
        level += 1
        if not node.is_leaf:
            # Iterate child_nodes based on their integer keys in sorted order
            for i in sorted(node.child_nodes.keys()):
                if i in node.child_nodes: # Check if child exists
                    self.print_tree(node.child_nodes[i], level)
                else: # Should not happen in a consistent tree
                    print(f"Level {level}, Missing child at index {i} for node {node.name}")


    def search(self, node, key_to_find):
        idx = 0
        # Find the first key greater than or equal to key_to_find
        while idx < len(node._sorted_own_keys) and key_to_find > node._sorted_own_keys[idx]:
            idx += 1

        # If key is found in this node
        if idx < len(node._sorted_own_keys) and key_to_find == node._sorted_own_keys[idx]:
            return node.key_values[key_to_find]
        # If key is not found and this is a leaf node
        elif node.is_leaf:
            return None
        # Go to the appropriate child
        else:
            if idx in node.child_nodes: # Ensure child exists at this index
                 return self.search(node.child_nodes[idx], key_to_find)
            else: # Should not happen if tree is consistent and key is in range
                 return None


    def find(self, key_to_find):
        return self.search(self.root, key_to_find)

    def delete(self, key_to_delete): # Takes only the key
        if not self.root:
            print("Tree is empty")
            return
        self._delete_recursive(self.root, key_to_delete)

        # If the root node has no keys after deletion, and it's not a leaf
        # (meaning it has one child), make that child the new root.
        if not self.root.is_leaf and not self.root._sorted_own_keys:
             if 0 in self.root.child_nodes: # Should have only one child at index 0
                self.root = self.root.child_nodes[0]


    def _delete_recursive(self, node, key_k):
        t = self.t
        idx = 0
        while idx < len(node._sorted_own_keys) and key_k > node._sorted_own_keys[idx]:
            idx += 1

        # Case 1: The key key_k is present in node
        if idx < len(node._sorted_own_keys) and node._sorted_own_keys[idx] == key_k:
            if node.is_leaf: # Case 1a: node is a leaf
                deleted_key = node._sorted_own_keys.pop(idx)
                del node.key_values[deleted_key]
            else: # Case 1b: node is an internal node
                self._delete_internal_node(node, idx, key_k)
        # Case 2: The key key_k is not present in node
        else:
            if node.is_leaf: # Key not found
                # print(f"Key {key_k} not found in the tree.")
                return

            # The child that must contain key_k (if key_k is in the tree)
            # idx is the correct child index to descend to
            child_to_descend = node.child_nodes[idx]
            
            if len(child_to_descend._sorted_own_keys) < t:
                self._fill_child(node, idx) # Ensure child has at least t keys

            # After _fill_child, the key might have moved.
            # If the last key of node was merged into child_to_descend (now node.child_nodes[idx-1]),
            # and key_k was greater than that key, then key_k is now in the merged child node.
            # The child index might change if merging happened with previous sibling.
            # `idx` is the original child index. If fill caused merge with previous sibling,
            # the effective child to go to might be `node.child_nodes[idx-1]` if `idx` was the right child of merge.
            # The `_fill_child` handles merges such that `node.child_nodes[idx]` (or potentially `node.child_nodes[idx-1]`)
            # is the correct node to descend into.
            # If `idx` points beyond the current keys after a merge, it might mean `key_k` went to the new last child.
            if idx > len(node._sorted_own_keys): # This can happen if a merge occurred and idx was the rightmost child
                 self._delete_recursive(node.child_nodes[idx-1], key_k)
            else:
                 self._delete_recursive(node.child_nodes[idx], key_k)


    def _delete_internal_node(self, node, idx, key_k):
        t = self.t
        # key_k is node._sorted_own_keys[idx]
        
        # Option 2a: If child y (node.child_nodes[idx]) has at least t keys,
        # find predecessor, replace key_k, and recursively delete predecessor in y.
        if len(node.child_nodes[idx]._sorted_own_keys) >= t:
            pred_key, pred_value = self._get_predecessor(node, idx)
            # Replace key_k with predecessor
            del node.key_values[key_k] # remove old key-value
            node._sorted_own_keys[idx] = pred_key
            node.key_values[pred_key] = pred_value
            self._delete_recursive(node.child_nodes[idx], pred_key)
        # Option 2b: If child z (node.child_nodes[idx+1]) has at least t keys,
        # find successor, replace key_k, and recursively delete successor in z.
        elif len(node.child_nodes[idx + 1]._sorted_own_keys) >= t:
            succ_key, succ_value = self._get_successor(node, idx)
            # Replace key_k with successor
            del node.key_values[key_k] # remove old key-value
            node._sorted_own_keys[idx] = succ_key
            node.key_values[succ_key] = succ_value
            self._delete_recursive(node.child_nodes[idx + 1], succ_key)
        # Option 2c: Both y and z have t-1 keys. Merge key_k and all of z into y.
        # Now y contains 2t-1 keys. Free z and recursively delete key_k from y.
        else:
            self._merge_children(node, idx)
            # key_k (which was node._sorted_own_keys[idx] before merge) is now in child_nodes[idx]
            # The _merge_children removes the key from parent and child from parent.
            self._delete_recursive(node.child_nodes[idx], key_k)


    def _get_predecessor(self, node, idx): # idx is the index of the key in node
        current = node.child_nodes[idx] # Left child of the key
        while not current.is_leaf:
            # Go to the rightmost child
            current = current.child_nodes[len(current._sorted_own_keys)]
        pred_key = current._sorted_own_keys[-1]
        pred_value = current.key_values[pred_key]
        return pred_key, pred_value

    def _get_successor(self, node, idx): # idx is the index of the key in node
        current = node.child_nodes[idx + 1] # Right child of the key
        while not current.is_leaf:
            # Go to the leftmost child
            current = current.child_nodes[0]
        succ_key = current._sorted_own_keys[0]
        succ_value = current.key_values[succ_key]
        return succ_key, succ_value

    def _fill_child(self, parent_node, child_idx): # child_idx is the index of child in parent_node.child_nodes
        t = self.t
        # Try to borrow from previous sibling
        if child_idx != 0 and len(parent_node.child_nodes[child_idx - 1]._sorted_own_keys) >= t:
            self._borrow_from_prev(parent_node, child_idx)
        # Try to borrow from next sibling
        elif child_idx != len(parent_node._sorted_own_keys) and len(parent_node.child_nodes[child_idx + 1]._sorted_own_keys) >= t:
            # child_idx refers to the key in parent, child[idx+1] is the sibling
            self._borrow_from_next(parent_node, child_idx)
        # Merge child with a sibling
        else:
            if child_idx != len(parent_node._sorted_own_keys): # Merge with next sibling
                self._merge_children(parent_node, child_idx) # Merges child[idx] and child[idx+1] with key[idx]
            else: # Merge with previous sibling (child is the rightmost)
                self._merge_children(parent_node, child_idx - 1) # Merges child[idx-1] and child[idx] with key[idx-1]


    def _borrow_from_prev(self, parent_node, child_idx): # child_idx is of the deficient child
        child = parent_node.child_nodes[child_idx]
        prev_sibling = parent_node.child_nodes[child_idx - 1]

        # Parent's key at parent_node._sorted_own_keys[child_idx-1] moves down to child
        key_from_parent = parent_node._sorted_own_keys[child_idx - 1]
        value_from_parent = parent_node.key_values[key_from_parent]
        
        # Sibling's last key moves up to parent
        key_from_sibling = prev_sibling._sorted_own_keys.pop()
        value_from_sibling = prev_sibling.key_values.pop(key_from_sibling)

        # Insert key from parent as the first key in child
        child._sorted_own_keys.insert(0, key_from_parent)
        child.key_values[key_from_parent] = value_from_parent

        # Update parent's key
        del parent_node.key_values[key_from_parent] # remove old value if key is same
        parent_node._sorted_own_keys[child_idx - 1] = key_from_sibling
        parent_node.key_values[key_from_sibling] = value_from_sibling
        

        if not prev_sibling.is_leaf:
            # Sibling's last child becomes child's first child
            moved_child_node = prev_sibling.child_nodes.pop(len(prev_sibling._sorted_own_keys) + 1) # Sibling now has one less key
            # Shift existing children of child to the right
            for i in range(len(child.child_nodes) -1, -1, -1):
                 child.child_nodes[i+1] = child.child_nodes[i]
            child.child_nodes[0] = moved_child_node


    def _borrow_from_next(self, parent_node, child_idx): # child_idx is of the deficient child (and key parent_node._sorted_own_keys[child_idx])
        child = parent_node.child_nodes[child_idx]
        next_sibling = parent_node.child_nodes[child_idx + 1]

        # Parent's key parent_node._sorted_own_keys[child_idx] moves down to child
        key_from_parent = parent_node._sorted_own_keys[child_idx]
        value_from_parent = parent_node.key_values[key_from_parent]

        # Sibling's first key moves up to parent
        key_from_sibling = next_sibling._sorted_own_keys.pop(0)
        value_from_sibling = next_sibling.key_values.pop(key_from_sibling)

        # Append key from parent as the last key in child
        child._sorted_own_keys.append(key_from_parent)
        child.key_values[key_from_parent] = value_from_parent
        
        # Update parent's key
        del parent_node.key_values[key_from_parent] # remove old value
        parent_node._sorted_own_keys[child_idx] = key_from_sibling
        parent_node.key_values[key_from_sibling] = value_from_sibling


        if not next_sibling.is_leaf:
            # Sibling's first child becomes child's last child
            moved_child_node = next_sibling.child_nodes.pop(0)
            # Re-index remaining children of next_sibling
            temp_sibling_children = {}
            for i, old_idx_key in enumerate(sorted(next_sibling.child_nodes.keys())):
                temp_sibling_children[i] = next_sibling.child_nodes[old_idx_key]
            next_sibling.child_nodes = temp_sibling_children
            
            child.child_nodes[len(child._sorted_own_keys)] = moved_child_node # Child now has one more key


    def _merge_children(self, parent_node, key_idx_in_parent):
        # Merges child at child_nodes[key_idx_in_parent] (left_child)
        # with child at child_nodes[key_idx_in_parent + 1] (right_child)
        # and the key parent_node._sorted_own_keys[key_idx_in_parent] from parent.
        # The result is stored in left_child. right_child is effectively removed.

        left_child = parent_node.child_nodes[key_idx_in_parent]
        right_child = parent_node.child_nodes[key_idx_in_parent + 1]

        # Key from parent to move down to left_child
        key_from_parent = parent_node._sorted_own_keys.pop(key_idx_in_parent)
        value_from_parent = parent_node.key_values.pop(key_from_parent)

        # Add parent key to left_child
        left_child._sorted_own_keys.append(key_from_parent)
        left_child.key_values[key_from_parent] = value_from_parent

        # Add all keys from right_child to left_child
        left_child._sorted_own_keys.extend(right_child._sorted_own_keys)
        for k_rc in right_child._sorted_own_keys:
            left_child.key_values[k_rc] = right_child.key_values[k_rc]

        # If not leaf, move children from right_child to left_child
        if not left_child.is_leaf: # (implies right_child is also not leaf)
            offset = len(left_child.child_nodes)
            for i in sorted(right_child.child_nodes.keys()):
                left_child.child_nodes[offset + i] = right_child.child_nodes[i]
        
        # Remove right_child pointer from parent and re-index subsequent children
        parent_node.child_nodes.pop(key_idx_in_parent + 1)
        # Re-index children in parent_node.child_nodes that were after the removed child
        temp_parent_children = {}
        current_new_idx = 0
        # Iterate through sorted keys of child_nodes to maintain order during re-indexing
        for old_idx_key in sorted(parent_node.child_nodes.keys()):
            if old_idx_key > key_idx_in_parent +1: # If it was after the removed child
                 temp_parent_children[current_new_idx] = parent_node.child_nodes[old_idx_key]
                 # this simple re-index might be wrong if keys are not contiguous.
                 # a safer re-index would be based on their sorted order directly.
            elif old_idx_key <= key_idx_in_parent: # children before or at the merge point (left_child)
                 temp_parent_children[current_new_idx] = parent_node.child_nodes[old_idx_key]

            current_new_idx +=1
        
        # Correct re-indexing for parent's children after removing one
        new_parent_children_reindexed = {}
        idx_counter = 0
        for i in sorted(parent_node.child_nodes.keys()): # Iterate through remaining children by their original indices
            if i == (key_idx_in_parent + 1): # This child was removed
                continue
            new_parent_children_reindexed[idx_counter] = parent_node.child_nodes[i]
            idx_counter += 1
        parent_node.child_nodes = new_parent_children_reindexed


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
    
    def update_value(self, key_to_update, new_value):
        node, _ = self._find_node_and_key_index(self.root, key_to_update)
        if node is not None and key_to_update in node.key_values:
            node.key_values[key_to_update] = new_value
            return True
        return False

    def _find_node_and_key_index(self, current_node, key_to_find):
        idx = 0
        while idx < len(current_node._sorted_own_keys) and key_to_find > current_node._sorted_own_keys[idx]:
            idx += 1
        
        if idx < len(current_node._sorted_own_keys) and key_to_find == current_node._sorted_own_keys[idx]:
            return current_node, idx # Node and index of key in _sorted_own_keys
        elif current_node.is_leaf:
            return None, -1
        else:
            if idx in current_node.child_nodes:
                return self._find_node_and_key_index(current_node.child_nodes[idx], key_to_find)
            else: # Should not happen in a consistent tree if key is in range
                return None, -1
    
    def count_nodes(self): # Counts BTreeNodes
        return self._count_nodes_recursive(self.root)

    def _count_nodes_recursive(self, node):
        if node is None:
            return 0
        count = 1 
        if not node.is_leaf:
            for child_idx in sorted(node.child_nodes.keys()):
                count += self._count_nodes_recursive(node.child_nodes[child_idx])
        return count
        
    def count_all(self): # Counts total key-value items
        return self._count_all_items_recursive(self.root)

    def _count_all_items_recursive(self, node):
        if node is None:
            return 0
        count = len(node._sorted_own_keys) 
        if not node.is_leaf:
            for child_idx in sorted(node.child_nodes.keys()):
                 count += self._count_all_items_recursive(node.child_nodes[child_idx])
        return count

    def delete_all(self):
        self.root = BTreeNode(True, name='root_after_delete_all')