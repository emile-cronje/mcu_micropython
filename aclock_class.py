# aclock_large.py Test/demo program for displays of 240x240 pixels or larger

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2018-2021 Peter Hinch

# Initialise hardware and framebuf before importing modules.
from color_setup import ssd  # Create a display instance
from gui.core.nanogui import refresh
refresh(ssd, True)  # Initialise and clear display.

# Now import other modules
from gui.widgets.label import Label
from gui.widgets.dial import Dial, Pointer
import cmath
import utime
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.freesans20 as font
from gui.core.colors import *

class AClock:
    def __init__(self):
        self.uv = lambda phi : cmath.rect(1, phi)  # Return a unit vector of phase phi
        self.pi = cmath.pi
        self.days = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
                'Sunday')
        self.months = ('Jan', 'Feb', 'March', 'April', 'May', 'June', 'July',
                  'Aug', 'Sept', 'Oct', 'Nov', 'Dec')
        
        # Instantiate CWriter
        CWriter.set_textpos(ssd, 0, 0)  # In case previous tests have altered it
        self.wri = CWriter(ssd, font, GREEN, BLACK, verbose=False)
        self.wri.set_clip(True, True, False)

        # Instantiate displayable objects
        self.dial = Dial(self.wri, 2, 2, height = 150, ticks = 12, bdcolor=None, label=240, pip=False)  # Border in fg color
        self.lbltim = Label(self.wri, 200, 2, 35)
        self.hrs = Pointer(self.dial)
        self.mins = Pointer(self.dial)
        self.secs = Pointer(self.dial)

        self.hstart =  0 + 0.7j  # Pointer lengths and position at top
        self.mstart = 0 + 0.92j
        self.sstart = 0 + 0.92j
        print("Clock init done...")        

    def run(self):
        print("Clock running...")
        
        while True:
            t = utime.localtime()
            self.hrs.value(self.hstart * self.uv(-t[3]*self.pi/6 - t[4]*self.pi/360), YELLOW)
            self.mins.value(self.mstart * self.uv(-t[4] * self.pi/30), YELLOW)
            self.secs.value(self.sstart * self.uv(-t[5] * self.pi/30), RED)
            self.lbltim.value('{:02d}.{:02d}.{:02d}'.format(t[3], t[4], t[5]))
            self.dial.text('{} {} {} {}'.format(self.days[t[6]], t[2], self.months[t[1] - 1], t[0]))
            refresh(ssd)
            utime.sleep(1)
