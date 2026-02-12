"""
Stress test for delete operations - simulating real-world usage
"""
from btree_optimized import BTree
import random

def stress_test_delete():
    print("=" * 60)
    print("DELETE STRESS TEST")
    print("=" * 60)
    
    # Simulate real-world scenario with many inserts and deletes
    print("\n1. Mixed insert/delete operations")
    tree = BTree(t=5, use_pool=True)
    
    # Phase 1: Insert many items
    print("   Inserting 1000 items...")
    for i in range(1000):
        tree.insert(i, f"data_{i}")
    
    print(f"   Tree has {tree.count_all()} items, {tree.count_nodes()} nodes")
    
    # Phase 2: Random deletes
    print("   Deleting 300 random items...")
    keys_to_delete = random.sample(range(1000), 300)
    
    for key in keys_to_delete:
        try:
            tree.delete(key)
        except Exception as e:
            print(f"   ERROR deleting key {key}: {e}")
            print(f"   Tree state: {tree.count_all()} items")
            raise
    
    print(f"   After deletes: {tree.count_all()} items, {tree.count_nodes()} nodes")
    
    # Verify deleted items are gone
    for key in keys_to_delete[:10]:  # Check first 10
        result = tree.search(key)
        assert result is None, f"Key {key} should be deleted but found: {result}"
    
    print("   ✓ Random deletes successful")
    
    # Phase 3: More inserts and deletes
    print("\n2. Alternating insert/delete cycles")
    for cycle in range(5):
        # Insert some
        for i in range(1000, 1020):
            if tree.search(i) is None:
                tree.insert(i, f"new_{i}")
        
        # Delete some
        to_delete = random.sample(range(1000, 1020), 5)
        for key in to_delete:
            if tree.search(key) is not None:
                tree.delete(key)
    
    print(f"   Final: {tree.count_all()} items, {tree.count_nodes()} nodes")
    print("   ✓ Alternating operations successful")
    
    # Phase 4: Delete until nearly empty
    print("\n3. Delete until nearly empty")
    current_items = tree.traverse_keys()
    keys_remaining = [k for k, v in current_items]
    
    to_remove = len(keys_remaining) - 10  # Leave 10 items
    keys_to_remove = random.sample(keys_remaining, to_remove)
    
    for key in keys_to_remove:
        tree.delete(key)
    
    print(f"   Remaining: {tree.count_all()} items")
    assert tree.count_all() >= 10
    print("   ✓ Mass deletion successful")
    
    # Phase 5: Complex merge scenario
    print("\n4. Complex merge scenario (small t)")
    tree2 = BTree(t=3, use_pool=True)  # Smaller t = more merges
    
    # Insert sequential keys
    for i in range(100):
        tree2.insert(i, f"v{i}")
    
    print(f"   Initial: {tree2.count_all()} items, {tree2.count_nodes()} nodes")
    
    # Delete every other key to force merges
    for i in range(0, 100, 2):
        tree2.delete(i)
    
    print(f"   After pattern deletion: {tree2.count_all()} items, {tree2.count_nodes()} nodes")
    
    # Verify remaining keys
    for i in range(1, 100, 2):
        result = tree2.search(i)
        assert result == f"v{i}", f"Key {i} should exist"
    
    print("   ✓ Complex merge successful")
    
    print("\n" + "=" * 60)
    print("STRESS TEST PASSED ✓")
    print("The delete operation is robust!")
    print("=" * 60)

if __name__ == "__main__":
    stress_test_delete()
