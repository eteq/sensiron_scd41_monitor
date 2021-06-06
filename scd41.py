import time
import board
from adafruit_bus_device.i2c_device import I2CDevice

#SCD41 datasheet is available from: https://www.sensirion.com/en/environmental-sensors/evaluation-kit-sek-environmental-sensing/evaluation-kit-sek-scd41

CRC8_POLYNOMIAL = 0x31
CRC8_INIT = 0xFF
def generate_crc8(bs):
    """
    bs is a `bytes` and the return value is the CRC8 result
    """
    crc = CRC8_INIT
    for b in bs:
        crc ^= b
        for i in range(8):
            if (crc & 0x80):
                crc = (crc << 1) ^ CRC8_POLYNOMIAL
            else:
                crc = (crc << 1)
    return crc & 0xff


def addr_to_bytes(addr):
    msb = (addr >> 8) & 0xff
    lsb = addr & 0xff
    return bytes((msb, lsb))


SCD41_ADDR = 0x62

class SensirionSCD41:
    def __init__(self, i2c=None):
        if i2c is None:
            i2c = board.I2C()
        self.i2c = i2c

        self.i2c_dev = I2CDevice(self.i2c, SCD41_ADDR)

    def send_command(self, addr):
        barr = addr_to_bytes(addr)
        with self.i2c_dev:
            self.i2c_dev.write(barr)

    def write(self, addr, towrite):
        barr = addr_to_bytes(addr)

        towrite = bytes(towrite)
        if len(towrite) != 2:
            raise ValueError('only accepts 2-byte writes!')
        crcb = chr(generate_crc8(towrite))

        with self.i2c_dev:
            self.i2c_dev.write(barr + towrite + crcb)

    def read(self, addr, nwords=1):
        barr = addr_to_bytes(addr)
        btoread = bytearray(nwords * 3)

        with self.i2c_dev:
            self.i2c_dev.write_then_readinto(barr, btoread)

        words = []
        for i in range(nwords):
            crc = generate_crc8(btoread[i*3 : (i*3+2)])
            if crc != btoread[i*3 + 2]:
                raise ValueError('read failure! CRCs do not match.')

            words.append((btoread[i*3] << 8) + btoread[i*3 + 1])

        return words

    def start_measuring(self):
        self.send_command(0x21b1)

    def stop_measuring(self):
        self.send_command(0x3f86)
        time.sleep(.5)

    def measure_one_shot(self):
        self.send_command(0x219d)
        time.sleep(5)

    def read_measurement(self):
        words = self.read(0xec05, 3)
        co2 = words[0]
        tc = 175 * words[1] / 0x10000 - 45
        rh = 100 * words[2] / 0x10000

        return co2, tc, rh

    def measurement_ready(self):
        w = self.read(0xe4b8, 1)[0]
        return bool(w & 0x7ff)  #0x7ff = 2**11 - 1
