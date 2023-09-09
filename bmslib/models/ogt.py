"""
BMS implementation for Offgridtec LiFePo4 Smart Pro Batteries
"""
__author__ = "patman15"
__license__ = "LGPL"
import asyncio

from bmslib.bms import BmsSample
from bmslib.bt import BtBms
from .conv import OgtResp

class OgtBt(BtBms):
    UUID_RX = '0000fff4-0000-1000-8000-00805f9b34fb'
    UUID_TX = '0000fff6-0000-1000-8000-00805f9b34fb'
    OGT_REGISTERS = {
         8: dict(name = "mos_temperature", len = 2, func = lambda x: round(float(x)*0.1-273.15, 1)),
         9: dict(name = "voltage", len = 2, func = lambda x: float(x)/1000),
        10: dict(name = "current", len = 3,
                 func = lambda x: float(x & 0x00FFFF)/100 if (x & 0x00FFFF) < 32768 else float((x & 0x00FFFF)-65535)/100),
        13: dict(name = "soc", len = 1, func = lambda x: x),
        15: dict(name = "cycle_capacity", len = 3, func = lambda x: float(x & 0x00FFFF)*0.01),
        23: dict(name = "num_cycles", len = 2, func = lambda x: x),
        24: dict(name = "capacity", len = 3, func = lambda x: float(x & 0x00FFFF)*0.01)
    }
    TIMEOUT = 20

    def __init__(self, address, **kwargs):
        super().__init__(address, **kwargs)
        self._values = {}
        self._voltages = {}

    def _notification_handler(self, sender, data):
        self.logger.debug("ble data frame %s", data.hex())
        resp = OgtResp.from_bytearray(data)
        if resp.reg > 48:
          self.logger.debug("reg: #%i, raw: %i, valid: %s", resp.reg, resp.value, resp.valid)
          if resp.valid:
            self._voltages[resp.reg-49] = resp.value
        else:
          self.logger.debug("reg: %s (#%i), raw: %i, value: %i", self.OGT_REGISTERS[resp.reg]['name'],
                                                        resp.reg, resp.value,
                                                        self.OGT_REGISTERS[resp.reg]['func'](resp.value))
          self._values[self.OGT_REGISTERS[resp.reg]['name']] = self.OGT_REGISTERS[resp.reg]['func'](resp.value)

    async def connect(self, timeout=20):
        #try:
            await super().connect(timeout=timeout)
            await self.client.start_notify(self.UUID_RX, self._notification_handler)
        #except:
        #    self.logger.info("connect failed")

    async def disconnect(self):
        await self.client.stop_notify(self.UUID_RX)
        await super().disconnect()

    def _ogt_command(self, command: int):
      tail = OgtResp.from_int(2) if command > 48 else OgtResp.from_int(self.OGT_REGISTERS[command]['len'])
      cmd = OgtResp.from_int(command)
      return bytes([0x32, 0x4B, 0x28, 0x2f, cmd[0], cmd[1], tail[0], tail[1]])

    async def _q(self, cmd):
#        try:

        await self.client.write_gatt_char(self.UUID_TX, data=self._ogt_command(cmd))
        self.logger.debug("ble cmd frame %.10s", self._ogt_command(cmd))
#        except:
#          self.logger.debug("failed to send ble frame")

    async def fetch(self) -> BmsSample:
        for key in self.OGT_REGISTERS.keys():
            await self._q(key)
            await asyncio.sleep(0.1)

        values = self._values
        sample = BmsSample(**values)
        return sample

    async def fetch_voltages(self):
        for x in range(15):
          await self._q(63-x)
          await asyncio.sleep(0.1)
        return list(self._voltages.values())

    async def fetch_temperatures(self):
        return []


async def main():
    mac_address = '12:34:56:78:9A:BC' # for CLI tests enter MAC address of battery here

    bms = OgtBt(mac_address, name='ogt')
    await bms.connect()
    #voltages = await bms.fetch_voltages()
    #print(voltages)
    while True:
      sample = await bms.fetch()
      print(sample)
      await asyncio.sleep(5)

    await bms.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
