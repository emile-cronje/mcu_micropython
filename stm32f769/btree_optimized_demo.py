"""
Example: Using Optimized B-tree in place of Original
Drop-in replacement for btree_custom_mem_demo.py

This shows how to migrate from the original to optimized B-tree
with minimal code changes.
"""

import os
import json
import time
import gc
from btree_optimized import BTree  # Changed import
import random

# MicroPython compatibility helpers
def ticks_ms():
    """Get millisecond timestamp - MicroPython compatible"""
    try:
        return time.ticks_ms()
    except AttributeError:
        return int(time.time() * 1000)

def ticks_diff(end, start):
    """Calculate time difference - MicroPython compatible"""
    try:
        return time.ticks_diff(end, start)
    except AttributeError:
        return end - start

class MeterReading:
    def __init__(self, id, meter_id, reading_on, reading):
        self.id = id
        self.meterId = meter_id
        self.readingOn = reading_on
        self.reading = reading

def mem_free():
    """Get free memory - MicroPython compatible"""
    try:
        return gc.mem_free()
    except AttributeError:
        return None

def mem_alloc():
    """Get allocated memory - MicroPython compatible"""
    try:
        return gc.mem_alloc()
    except AttributeError:
        return None

def free(full=True):
    """Calculate free memory percentage"""
    F = mem_free()
    A = mem_alloc()
    if F is None or A is None:
        return None
    T = F + A
    P = '{0:.2f}%'.format(F / T * 100)
    if not full:
        return P
    else:
        return ('Free:{0}'.format(P))

def test_optimized_btree():
    """Test optimized B-tree performance"""
    
    print("=" * 60)
    print("OPTIMIZED B-TREE DEMO")
    print("=" * 60)
    
    # Create tree with optional pooling
    print("\n1. Creating optimized B-tree with t=5")
    print(f"   Memory before: {free()}")
    
    tree = BTree(t=5, use_pool=True)  # use_pool=True recommended for STM32F769
    
    print(f"   Memory after init: {free()}")
    
    # Test data
    test_items = [
        (1, "value_1"),
        (5, "value_5"),
        (3, "value_3"),
        (7, "value_7"),
        (2, "value_2"),
        (4, "value_4"),
        (6, "value_6"),
        (8, "value_8"),
        (9, "value_9"),
        (10, "value_10"),
    ]
    
    # 2. Insert items
    print("\n2. Inserting items")
    start_time = ticks_ms()
    
    for key, value in test_items:
        tree.insert(key, value)
        print(f"   Inserted: {key} -> {value}")
    
    insert_time = ticks_diff(ticks_ms(), start_time)
    print(f"   Insertion time: {insert_time}ms")
    print(f"   Memory after inserts: {free()}")
    
    # 3. Search for items
    print("\n3. Searching for items")
    search_items = [1, 3, 5, 7, 9]
    
    for key in search_items:
        result = tree.search(key)
        if result:
            print(f"   Found: {key} -> {result}")
        else:
            print(f"   NOT FOUND: {key}")
    
    # 4. Update values
    print("\n4. Updating values")
    tree.update_value(5, "updated_value_5")
    result = tree.search(5)
    print(f"   Updated 5: new value = {result}")
    
    # 5. Traverse all items
    print("\n5. Traversing all items")
    all_items = tree.traverse_keys()
    print(f"   Total items: {len(all_items)}")
    for key, value in all_items:
        print(f"   {key} -> {value}")
    
    # 6. Tree structure
    print("\n6. Tree structure")
    node_count = tree.count_nodes()
    item_count = tree.count_all()
    print(f"   Nodes: {node_count}")
    print(f"   Items: {item_count}")
    print(f"   Memory: {free()}")
    
    # 7. Delete item
    print("\n7. Deleting item 5")
    tree.delete(5)
    result = tree.search(5)
    print(f"   After delete 5: search result = {result}")
    print(f"   Items remaining: {tree.count_all()}")
    
    # 8. Larger insertion test
    print("\n8. Large insertion test (100 items)")
    #print(f"   Memory before: {gc.mem_free()} bytes")
    
    for i in range(100):
        tree.insert(1000 + i, f"large_value_{i}")
        #if i % 20 == 0:
            #gc.collect()
    
    gc.collect()
    mem_after = mem_free()
    if mem_after is not None:
        print(f"   Memory after: {mem_after} bytes")
    print(f"   Total items: {tree.count_all()}")
    print(f"   Total nodes: {tree.count_nodes()}")
    
    # 9. Filter with traversal
    print("\n9. Traverse with filter (values > 'large_value_50')")
    results = tree.traverse_func(lambda x: x > "large_value_50")
    print(f"   Filtered results: {len(results)} items")
    
    # 10. Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Final memory: {free()}")
    print(f"Total items in tree: {tree.count_all()}")
    print(f"Tree nodes: {tree.count_nodes()}")
    print(f"\nOptimized B-tree is ready for production use!")
    print("See BTREE_OPTIMIZATION.md for detailed information.")

def benchmark_insert_performance():
    """Benchmark insertion performance"""
    
    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARK")
    print("=" * 60)
    
    num_items = 500
    tree = BTree(t=5, use_pool=True)
    
    print(f"\nInserting {num_items} items...")
    mem_start = mem_free()
    if mem_start is not None:
        print(f"Memory start: {mem_start} bytes")
    
    gc.collect()
    start_time = ticks_ms()
    
    for i in range(num_items):
        tree.insert(i, f"value_{i}")
        if i % 100 == 0:
            gc.collect()
    
    elapsed = ticks_diff(ticks_ms(), start_time)
    gc.collect()
    
    mem_used = mem_free()
    mem_allocated = mem_alloc()
    
    print(f"Time elapsed: {elapsed}ms")
    print(f"Items per second: {(num_items * 1000) // elapsed}")
    if mem_used is not None:
        print(f"Memory used: {mem_used} bytes")
    if mem_used is not None and mem_allocated is not None:
        print(f"Per-item overhead: {((mem_used - mem_allocated) / num_items):.1f} bytes")

if __name__ == "__main__":
    test_optimized_btree()
    benchmark_insert_performance()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Run benchmark_btree.py to compare with original")
    print("2. Adjust t value based on your SRAM (512KB typical)")
    print("3. Monitor memory with gc.mem_free() during operation")
    print("4. Consider use_pool=False for single-use trees")
    print("=" * 60)
