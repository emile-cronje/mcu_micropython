"""
Benchmark comparing original and optimized B-tree implementations
Run on STM32F769 to measure memory and performance improvements
"""

import gc
import time

print("=" * 60)
print("B-TREE OPTIMIZATION BENCHMARK")
print("=" * 60)

def measure_memory():
    """Get current free memory"""
    gc.collect()
    return gc.mem_free()

def benchmark_btree(btree_class, name, num_items=1000, num_searches=500):
    """Benchmark a B-tree implementation"""
    print(f"\n{name}")
    print("-" * 40)
    
    mem_start = measure_memory()
    print(f"Memory start: {mem_start} bytes")
    
    # Create tree with t=5
    tree = btree_class(t=5)
    mem_after_init = measure_memory()
    print(f"After init: {mem_after_init} bytes (used: {mem_start - mem_after_init})")
    
    # Insertion benchmark
    gc.collect()
    mem_before_insert = measure_memory()
    start_time = time.ticks_ms()
    
    for i in range(num_items):
        tree.insert(i, f"value_{i}")
    
    insert_time = time.ticks_diff(time.ticks_ms(), start_time)
    mem_after_insert = measure_memory()
    
    print(f"Inserted {num_items} items in {insert_time}ms")
    print(f"Memory used: {mem_before_insert - mem_after_insert} bytes")
    print(f"Per-item overhead: {(mem_before_insert - mem_after_insert) / num_items:.1f} bytes")
    
    # Search benchmark
    gc.collect()
    start_time = time.ticks_ms()
    
    for i in range(0, num_items, num_items // num_searches):
        result = tree.search(i)
        if result is None:
            print(f"ERROR: Search failed for key {i}")
    
    search_time = time.ticks_diff(time.ticks_ms(), start_time)
    print(f"Searched {num_searches} items in {search_time}ms")
    print(f"Per-search: {search_time / num_searches:.2f}ms")
    
    # Count nodes
    node_count = tree.count_nodes()
    item_count = tree.count_all()
    print(f"Tree structure: {node_count} nodes, {item_count} items")
    
    # Final memory
    mem_final = measure_memory()
    print(f"Final memory: {mem_final} bytes")
    print(f"Total used: {mem_start - mem_final} bytes")
    
    return {
        'insert_time': insert_time,
        'search_time': search_time,
        'memory_used': mem_start - mem_final,
        'per_item': (mem_start - mem_final) / num_items
    }

# Test both implementations
try:
    from btree_custom_mem import BTree as BTreeOriginal
    original_available = True
except ImportError:
    original_available = False
    print("Original btree_custom_mem not available")

try:
    from btree_optimized import BTree as BTreeOptimized
    optimized_available = True
except ImportError:
    optimized_available = False
    print("Optimized btree_optimized not available")

num_items = 500  # Adjust based on available memory
num_searches = 100

if original_available:
    results_original = benchmark_btree(BTreeOriginal, "ORIGINAL B-TREE", num_items, num_searches)

if optimized_available:
    results_optimized = benchmark_btree(BTreeOptimized, "OPTIMIZED B-TREE", num_items, num_searches)

# Compare results
if original_available and optimized_available:
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    
    insert_improvement = (results_original['insert_time'] - results_optimized['insert_time']) / results_original['insert_time'] * 100
    search_improvement = (results_original['search_time'] - results_optimized['search_time']) / results_original['search_time'] * 100
    memory_improvement = (results_original['memory_used'] - results_optimized['memory_used']) / results_original['memory_used'] * 100
    
    print(f"Insert time improvement: {insert_improvement:.1f}% faster")
    print(f"Search time improvement: {search_improvement:.1f}% faster")
    print(f"Memory usage improvement: {memory_improvement:.1f}% savings")
    print(f"Per-item memory: {results_original['per_item']:.1f} → {results_optimized['per_item']:.1f} bytes")

print("\n" + "=" * 60)
print("Recommendations for STM32F769:")
print("=" * 60)
print("1. Use t=4 or t=5 (balance between depth and memory)")
print("2. Enable object pooling (use_pool=True) to reduce GC")
print("3. Update t value based on available SRAM (typically 512KB)")
print("4. Monitor memory with gc.mem_free() during operation")
print("5. Consider using delete sparingly (complex operation)")
