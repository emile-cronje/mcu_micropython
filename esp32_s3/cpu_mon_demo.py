from cpu_monitor_class import CPUMon
import uasyncio as asyncio

cpuMon = CPUMon()
loop = asyncio.get_event_loop()
useCore1 = True
loop.create_task(cpuMon.main(worker_func = None, useCore1 = useCore1, showUsage = True))
loop.run_forever()
