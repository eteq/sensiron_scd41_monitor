from scd41 import SensirionSCD41

import time
import board

import displayio
displayio.release_displays()

import terminalio
from adafruit_display_text import label
import adafruit_displayio_sh1107

import neopixel

# note that the SCD41 says it needs 1 sec of startup time.  Implicit assumption
# here is that MC + circuitpython needs at least that much too.

i2c = board.I2C()
scd41 = SensirionSCD41(i2c)

scd41.start_measuring()

display_bus = displayio.I2CDisplay(i2c, device_address=0x3c)
display = adafruit_displayio_sh1107.SH1107(display_bus, width=128, height=64)

initial_text = 'CO2:\nTemp:\nRH:'
text_area = label.Label(terminalio.FONT, text=initial_text, color=0xFFFFFF, x=8, y=8)
display.show(text_area)

npx = neopixel.NeoPixel(board.NEOPIXEL, 1)

while True:
    if scd41.measurement_ready():
        co2, tc, rh = scd41.read_measurement()

        # set neopixel
        if co2 < 1000:
            npx.fill((0, 20, 0))
        elif co2 < 2000:
            npx.fill((25, 20, 0))
        else: # co2 >= 2000
            npx.fill((35, 0, 0))

        co2str = 'CO2: {} ppm'.format(co2)
        tempstr = 'Temp: {} deg C'.format(tc)
        rhstr = 'RH: {} %'.format(rh)

        text_area.text = '\n'.join([co2str, tempstr, rhstr])

    time.sleep(1)
