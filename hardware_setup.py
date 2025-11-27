# color_setup.py Customise for your hardware config

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

# As written, supports:
# Adafruit 1.5" 128*128 OLED display: https://www.adafruit.com/product/1431
# Adafruit 1.27" 128*96 display https://www.adafruit.com/product/1673
# Edit the driver import for other displays.

# Demo of initialisation procedure designed to minimise risk of memory fail
# when instantiating the frame buffer. The aim is to do this as early as
# possible before importing other modules.

# WIRING (Adafruit pin nos and names).
# Pyb   SSD
# 3v3   Vin (10)
# Gnd   Gnd (11)
# Y1    DC (3 DC)
# Y2    CS (5 OC OLEDCS)
# Y3    Rst (4 R RESET)
# Y6    CLK (2 CL SCK)
# Y8    DATA (1 SI MOSI)

from machine import Pin, SPI
import gc

# *** Choose your color display driver here ***
# Driver supporting non-STM platforms
# from drivers.ssd1351.ssd1351_generic import SSD1351 as SSD

from ili94xx.ili9486 import ILI9486 as SSD
SSD.COLOR_INVERT = 0xFFFF  # Fix color inversion

LCD_DC   = 8
LCD_CS   = 9
LCD_SCK  = 10
LCD_MOSI = 11
LCD_MISO = 12
LCD_BL   = 13
LCD_RST  = 15
TP_CS    = 16
TP_IRQ   = 17

#dc = Pin(8, Pin.OUT, value=0)
#rst = Pin(9, Pin.OUT, value=1)
#cs = Pin(10, Pin.OUT, value=1)

dc = Pin(LCD_DC, Pin.OUT, value=0)
rst = Pin(LCD_RST, Pin.OUT, value=1)
cs = Pin(LCD_CS, Pin.OUT, value=1)

#spi = SPI(0, sck=Pin(6), mosi=Pin(7), miso=Pin(4), baudrate=30_000_000)
spi = SPI(1,30_000_000,sck=Pin(LCD_SCK),mosi=Pin(LCD_MOSI),miso=Pin(LCD_MISO))
gc.collect()  # Precaution before instantiating framebuf
ssd = SSD(spi, cs, dc, rst)
