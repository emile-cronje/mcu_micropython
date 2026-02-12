"""
Test delete operations extensively to verify merge fixes
"""
from btree_optimized import BTree

def test_delete_operations():
    print("=" * 60)
    print("COMPREHENSIVE DELETE TESTS")
    print("=" * 60)
    
    # Test 1: Simple deletes
    print("\n1. Simple delete from small tree")
    tree = BTree(t=3, use_pool=True)
    for i in range(10):
        tree.insert(i, f"value_{i}")
    
    print(f"   Before: {tree.count_all()} items")
    tree.delete(5)
    print(f"   After deleting 5: {tree.count_all()} items")
    assert tree.search(5) is None
    assert tree.search(4) == "value_4"
    assert tree.search(6) == "value_6"
    print("   ✓ Simple delete works")
    
    # Test 2: Delete multiple items
    print("\n2. Delete multiple items")
    for i in [2, 7, 1, 9]:
        tree.delete(i)
    print(f"   Remaining: {tree.count_all()} items")
    all_items = tree.traverse_keys()
    print(f"   Items: {[k for k, v in all_items]}")
    assert len(all_items) == 5
    print("   ✓ Multiple deletes work")
    
    # Test 3: Delete causing merges
    print("\n3. Delete causing merges (larger tree)")
    tree2 = BTree(t=3, use_pool=True)
    # Insert many items to create a deeper tree
    for i in range(50):
        tree2.insert(i, f"val_{i}")
    
    print(f"   Initial: {tree2.count_all()} items, {tree2.count_nodes()} nodes")
    
    # Delete several items
    for i in range(0, 30, 3):
        tree2.delete(i)
    
    print(f"   After deletes: {tree2.count_all()} items, {tree2.count_nodes()} nodes")
    
    # Verify remaining items
    for i in range(50):
        result = tree2.search(i)
        if i % 3 == 0 and i < 30:
            assert result is None, f"Key {i} should be deleted"
        else:
            assert result == f"val_{i}", f"Key {i} should exist"
    
    print("   ✓ Merge operations work correctly")
    
    # Test 4: Delete all items one by one
    print("\n4. Delete all items sequentially")
    tree3 = BTree(t=5, use_pool=True)
    items = [10, 20, 30, 5, 15, 25, 35, 3, 7, 12, 18, 22, 28, 32, 38]
    for item in items:
        tree3.insert(item, f"v_{item}")
    
    print(f"   Initial: {tree3.count_all()} items")
    
    for item in items:
        tree3.delete(item)
        assert tree3.search(item) is None
    
    print(f"   Final: {tree3.count_all()} items")
    assert tree3.count_all() == 0
    print("   ✓ Sequential deletion works")
    
    # Test 5: Delete from edges
    print("\n5. Delete minimum and maximum values")
    tree4 = BTree(t=4, use_pool=True)
    for i in range(100, 200):
        tree4.insert(i, f"item_{i}")
    
    tree4.delete(100)  # Delete minimum
    tree4.delete(199)  # Delete maximum
    
    assert tree4.search(100) is None
    assert tree4.search(199) is None
    assert tree4.search(101) == "item_101"
    assert tree4.search(198) == "item_198"
    print("   ✓ Edge deletion works")
    
    print("\n" + "=" * 60)
    print("ALL DELETE TESTS PASSED ✓")
    print("=" * 60)

if __name__ == "__main__":
    test_delete_operations()
