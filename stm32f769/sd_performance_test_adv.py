import os, time
try:
    import urandom as random  # MicroPython
except ImportError:
    import random             # fallback (unlikely on MCU)

import machine
import pyb
from machine import SPI, Pin
import gc
import time
import utime

# --------- CONFIG ----------
MOUNT     = "/sd"
TESTFILE  = MOUNT + "/bench.bin"
FILE_SIZE = 2 * 1024 * 1024   # 2 MB test file (adjust as you like)
SEQ_CHUNKS = [512, 4096, 16384]  # try single-block and multi-block-friendly sizes
RAND_BLOCK = 512              # SD sector size
RAND_OPS   = 2000             # number of random ops for read/write
# ---------------------------

def _kbps(bytes_, ms):
    if ms <= 0:
        return 0.0
    return (bytes_ / ms)

def _mbps(bytes_, ms):
    # KB/s -> MB/s
    return _kbps(bytes_, ms) / 1024.0

def _sync_fs():
    # Ensure data hits the card for realistic write timing.
    # Some ports don’t have os.sync().
    try:
        os.sync()
    except AttributeError:
        pass

def _ensure_dir():
    try:
        os.listdir(MOUNT)
    except OSError as e:
        raise OSError("Mount point %s not available; mount the SD first." % MOUNT)

def _preallocate(path, size):
    # Create/extend a file to 'size' bytes without huge RAM usage
    with open(path, "wb") as f:
        f.seek(size - 1)
        f.write(b"\x00")

def bench_seq_write(path, size, chunk):
    buf = b"A" * chunk
    start = time.ticks_ms()
    with open(path, "wb") as f:
        left = size
        while left > 0:
            n = chunk if left >= chunk else left
            if n == chunk:
                f.write(buf)
            else:
                f.write(b"A" * n)
            left -= n
    _sync_fs()
    ms = time.ticks_diff(time.ticks_ms(), start)
    print("SEQ WRITE  chunk=%5d  size=%7d  ->  %7.2f KB/s  (%.2f MB/s)  time=%d ms"
          % (chunk, size, _kbps(size, ms), _mbps(size, ms), ms))

def bench_seq_read(path, size, chunk):
    buf = bytearray(chunk)
    start = time.ticks_ms()
    with open(path, "rb") as f:
        total = 0
        while total < size:
            n = chunk if (size - total) >= chunk else (size - total)
            # readinto avoids extra allocations
            r = f.readinto(memoryview(buf)[:n])
            if r is None or r == 0:
                break
            total += r
    ms = time.ticks_diff(time.ticks_ms(), start)
    print("SEQ READ   chunk=%5d  size=%7d  ->  %7.2f KB/s  (%.2f MB/s)  time=%d ms"
          % (chunk, size, _kbps(size, ms), _mbps(size, ms), ms))

def _rand_idx(n):
    # Cheap uniform-ish random index [0, n-1]
    # Use getrandbits if present; modulo bias is negligible here.
    try:
        return random.getrandbits(30) % n
    except AttributeError:
        return int(random.random() * n)

def bench_random_write(path, size, block, ops):
    # Preallocate so we can seek anywhere
    _preallocate(path, size)
    buf = b"W" * block
    nblocks = size // block
    start = time.ticks_ms()
    with open(path, "r+b") as f:
        for _ in range(ops):
            idx = _rand_idx(nblocks)
            f.seek(idx * block)
            f.write(buf)
    _sync_fs()
    ms = time.ticks_diff(time.ticks_ms(), start)
    total = ops * block
    print("RAND WRITE block=%4d ops=%5d size=%7d -> %7.2f KB/s (%.2f MB/s) time=%d ms"
          % (block, ops, size, _kbps(total, ms), _mbps(total, ms), ms))

def bench_random_read(path, size, block, ops):
    # Ensure file exists and is at least 'size'
    if not _file_at_least(path, size):
        _preallocate(path, size)
    buf = bytearray(block)
    nblocks = size // block
    start = time.ticks_ms()
    with open(path, "rb") as f:
        for _ in range(ops):
            idx = _rand_idx(nblocks)
            f.seek(idx * block)
            r = f.readinto(buf)
            if r != block:
                break
    ms = time.ticks_diff(time.ticks_ms(), start)
    total = ops * block
    print("RAND READ  block=%4d ops=%5d size=%7d -> %7.2f KB/s (%.2f MB/s) time=%d ms"
          % (block, ops, size, _kbps(total, ms), _mbps(total, ms), ms))

def _file_at_least(path, size):
    try:
        st = os.stat(path)
        return st[6] >= size
    except OSError:
        return False

def main():
    _ensure_dir()
    print("SD benchmark on:", MOUNT)
    print("File size: %d bytes (%.2f MB)" % (FILE_SIZE, FILE_SIZE / (1024*1024)))
    print("Sequential I/O:")
    for chunk in SEQ_CHUNKS:
        bench_seq_write(TESTFILE, FILE_SIZE, chunk)
        bench_seq_read(TESTFILE, FILE_SIZE, chunk)

    print("\nRandom I/O (small 512B blocks):")
    bench_random_write(TESTFILE, FILE_SIZE, RAND_BLOCK, RAND_OPS)
    bench_random_read(TESTFILE,  FILE_SIZE, RAND_BLOCK, RAND_OPS)

    # Cleanup (optional)
    try:
        os.remove(TESTFILE)
    except OSError:
        pass

os.mount(pyb.SDCard(), MOUNT)    

if __name__ == "__main__":
    main()
