import pyb

class CPUMonitor:
    def __init__(self):
        self.busy_count = 0
        self.total_count = 0
        self.timer = pyb.Timer(4, freq=1000)  # 1kHz sampling
        self.timer.callback(self.sample)
    
    def sample(self, timer):
        self.total_count += 1
        # Check if system is busy (this is a simplified example)
        if gc.mem_alloc() > self.last_alloc:
            self.busy_count += 1
        self.last_alloc = gc.mem_alloc()
    
    def get_usage(self):
        if self.total_count > 0:
            return (self.busy_count / self.total_count) * 100
        return 0