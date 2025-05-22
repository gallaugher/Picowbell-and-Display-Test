# SPDX-FileCopyrightText: Copyright (c) 2023 Limor Fried for Adafruit Industries
# SPDX-License-Identifier: Unlicense

"""
Demo for Raspberry Pi Pico W + PiCowbell Camera + ILI9341 320x240 SPI Display
Shows a live feed from the OV5640 camera on the display
"""

import time
import board
import busio
import digitalio
import displayio
import pwmio

import adafruit_ov5640
import adafruit_ili9341

displayio.release_displays()

# === SPI and Display Setup for ILI9341 ===
backlight = pwmio.PWMOut(board.GP16, frequency=5000, duty_cycle=65535)

# Rewire your EYESPI to these pins instead:
spi = busio.SPI(clock=board.GP18, MOSI=board.GP19)
display_bus = displayio.FourWire( 
    spi,
    command=board.GP21,      # DC (move from GP6)
    chip_select=board.GP17,  # CS (move from GP7)
    reset=board.GP15         # RST (move from GP8)
)

display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240)

# === I2C + Camera Setup ===
i2c = busio.I2C(scl=board.GP5, sda=board.GP4)

reset = digitalio.DigitalInOut(board.GP14)

cam = adafruit_ov5640.OV5640(
    i2c,
    data_pins=(
        board.GP6,
        board.GP7,
        board.GP8,
        board.GP9,
        board.GP10,
        board.GP11,
        board.GP12,
        board.GP13,
    ),
    clock=board.GP3,      # XCLK / PCLK (external clock pin)
    vsync=board.GP0,
    href=board.GP2,
    mclk=None,
    shutdown=None,
    reset=reset,
    size=adafruit_ov5640.OV5640_SIZE_QVGA,  # 320x240
)

print("Camera ID:", cam.chip_id)

# === Camera Settings ===
cam.colorspace = adafruit_ov5640.OV5640_COLOR_RGB
cam.flip_y = False
cam.flip_x = False
cam.test_pattern = False

# === Create Bitmap Buffer to Hold Camera Output ===
try:
    bitmap = displayio.Bitmap(cam.width, cam.height, 65535)
except MemoryError:
    print("MemoryError: falling back to smaller camera size")
    cam.size = adafruit_ov5640.OV5640_SIZE_QCIF  # 176x144
    bitmap = displayio.Bitmap(cam.width, cam.height, 65535)

# === Prepare Display Group ===
g = displayio.Group(scale=1, x=(display.width - cam.width) // 2, y=(display.height - cam.height) // 2)
tg = displayio.TileGrid(
    bitmap,
    pixel_shader=displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565_SWAPPED)
)
g.append(tg)
display.root_group = g

# === Main Camera Loop ===
display.auto_refresh = False
t0 = time.monotonic_ns()

print("Camera code running!")

while True:
    cam.capture(bitmap)
    bitmap.dirty()
    display.refresh(minimum_frames_per_second=0)
    t1 = time.monotonic_ns()
    print("FPS:", round(1e9 / (t1 - t0), 2))
    t0 = t1
