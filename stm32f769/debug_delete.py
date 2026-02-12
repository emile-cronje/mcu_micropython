"""
Simple debug test for delete
"""
from btree_optimized import BTree

def debug_delete():
    print("Debug delete test")
    tree = BTree(t=3, use_pool=True)
    
    # Insert sequential keys 0-20
    print("\nInserting 0-20...")
    for i in range(21):
        tree.insert(i, f"v{i}")
    
    print(f"Tree: {tree.count_all()} items, {tree.count_nodes()} nodes")
    tree.print_tree()
    
    # Delete even keys
    print("\nDeleting even keys (0, 2, 4, ...)...")
    for i in range(0, 21, 2):
        print(f"  Deleting {i}...")
        tree.delete(i)
        # Verify it's deleted
        result = tree.search(i)
        if result is not None:
            print(f"  ERROR: {i} still found after delete!")
            tree.print_tree()
            break
    
    print(f"\nAfter deletes: {tree.count_all()} items, {tree.count_nodes()} nodes")
    tree.print_tree()
    
    # Check remaining keys
    print("\nChecking remaining odd keys...")
    all_items = tree.traverse_keys()
    found_keys = sorted([k for k, v in all_items])
    print(f"Found keys: {found_keys}")
    expected_keys = list(range(1, 21, 2))
    print(f"Expected keys: {expected_keys}")
    
    for i in range(1, 21, 2):
        result = tree.search(i)
        if result != f"v{i}":
            print(f"ERROR: Key {i} not found! Got: {result}")
        else:
            print(f"  {i}: OK")

if __name__ == "__main__":
    debug_delete()
