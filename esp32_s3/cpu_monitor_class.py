# Pico htop-like CPU Load Monitor (Dual-Core Method)
#
# This version correctly measures system load on a dual-core MCU like the Pico.
# It works by measuring the degradation in performance of a benchmark task
# when a worker thread is running on the other core.

import uasyncio as asyncio
import machine
import utime
import _thread
import gc
import random

class CPUMon:
    def __init__(self):
        # --- Global Variables ---
        # This dictionary will hold our calibration and load data.
        self.system_info = {
            'max_loops': 0,      # The max loops in the benchmark (0% load)
            'cpu_load': 0.0,     # The calculated CPU load percentage
            'mem_usage_percent': 0.0,
            'mem_free_percent': 0.0,            
            'mem_free': 0
        }
        
    # --- 1. The Worker Thread (to create CPU load) ---
    def busy_worker(self):
        """A simple function to consume CPU cycles on the second core."""
        print("Worker thread started on Core 1...")
        
        while True:
            # This loop will keep Core 1 busy.
            a = random.uniform(10, 200)
            b = random.uniform(5, 100)
            c = random.uniform(5, 100)                        
            z = a * b / c
            #print(z)
            #utime.sleep(1)

    # --- 2. The Measurement Logic ---
    def benchmark_task(self):
        """A computationally-intensive task to measure performance."""
        # This loop is our unit of "work". The number of times it can run
        # in a fixed period is a measure of available CPU power.
        count = 0
        start_time = utime.ticks_ms()
        
        # Run the benchmark for 200ms
        while utime.ticks_diff(utime.ticks_ms(), start_time) < 200:
            a = random.uniform(10, 200)
            b = random.uniform(5, 100)            
            _ = a / b
            count += 1
            
        return count

    def calibrate(self):
        """Measures the maximum performance baseline with no load."""
        print("Calibrating CPU... Please wait a moment.")
        # Run the benchmark to get the max loops possible
        max_loops = self.benchmark_task()
        self.system_info['max_loops'] = max_loops
        print(f"Calibration complete. Max benchmark loops: {self.system_info['max_loops']}")
        utime.sleep(1)

    def update_stats(self, _timer):
        """
        This function is called by a Timer interrupt.
        It runs the benchmark, calculates the load, and gets memory stats.
        """
        # Run the benchmark to see current performance
        current_loops = self.benchmark_task()
        max_loops = self.system_info['max_loops']

        # --- Calculate CPU Load ---
        if max_loops > 0:
            # The new formula:
            # The load is the percentage of performance we've LOST.
            performance_loss = 1 - (current_loops / max_loops)
            load_percentage = performance_loss * 100
            self.system_info['cpu_load'] = max(0, min(100, load_percentage))

        # --- Get Memory Info ---
        #gc.collect()
        mem_free = gc.mem_free()
        mem_alloc = gc.mem_alloc()
        mem_total = mem_free + mem_alloc
        self.system_info['mem_usage_percent'] = (mem_alloc / mem_total) * 100 if mem_total > 0 else 0
        self.system_info['mem_free_percent'] = (mem_free / mem_total) * 100 if mem_total > 0 else 0        
        self.system_info['mem_free'] = mem_free

    # --- 3. The Main Setup and Display Loop ---
    async def main(self, showUsage = False, worker_func = None, useCore1 = True):
        # Calibrate first to get our baseline
        if (showUsage == True):
            self.calibrate()

        # Start the worker thread to generate load on Core 1
        if (useCore1 == True):
            if (worker_func == None):
                worker_func = self.busy_worker
                
            _thread.start_new_thread(worker_func, ())

        if (showUsage == False):
            return
        
        # Set up a periodic timer that calls our stats updater every 1000ms (1s)
        timer = machine.Timer(0)
        timer.init(period=1000, mode=machine.Timer.PERIODIC, callback=self.update_stats)

        print("Starting CPU monitor... Press Ctrl+C to stop.")

        try:
            # The main loop is now just for printing the results.
            # The actual work is done in the timer callback.
            while True:
                load = self.system_info['cpu_load']
                mem_usage_percent = self.system_info['mem_usage_percent']
                mem_free_percent = self.system_info['mem_free_percent']                
                mem_free = self.system_info['mem_free']

                # Create the bar visuals
                cpu_bar = '#' * int(load / 4) + ' ' * (25 - int(load / 4))
                mem_usage_bar = '#' * int(mem_usage_percent / 4) + ' ' * (25 - int(mem_usage_percent / 4))
                mem_free_bar = '#' * int(mem_free_percent / 4) + ' ' * (25 - int(mem_free_percent / 4))                

                # Format the output string
                cpu_string = f"CPU: [{cpu_bar}] {load:5.1f}%"
                mem_usage_string = f"MEM Usage: [{mem_usage_bar}] {mem_usage_percent:5.1f}%"
                mem_free_string = f"MEM Free: [{mem_free_bar}] {mem_free_percent:5.1f}%"

                # Print to console, using carriage return to overwrite the line
                print(cpu_string, end='\r\n')
#                print(mem_usage_string, end='\r\n')
                print(mem_free_string, end='\r\n')                                

                # Sleep for a bit. The 1-second update rate is handled by the timer.
                await asyncio.sleep(1)                

        except KeyboardInterrupt:
            print("\nStopping monitor.")
        finally:
            # Clean up the timer when the program stops
            timer.deinit()
            print("Timer stopped. Program finished.")
