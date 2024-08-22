import asyncio
from bleak import BleakScanner, BleakClient
import numpy as np

class Corsense:
    def __init__(self):
        self.running = True
        self.device = None
        self.device_info = None
        self.hrm_uuid = "00002a37-0000-1000-8000-00805f9b34fb"  # Heart Rate Measurement characteristic UUID
        self.ccc_uuid = "00002902-0000-1000-8000-00805f9b34fb"  # Client Characteristic Configuration descriptor UUID
# 2A37 2A38 2A39
# FEE8 
        #("00001822-0000-1000-8000-00805f9b34fb", "Pulse Oximeter Service")
#("00002a62-0000-1000-8000-00805f9b34fb", "Pulse Oximetry Control Point")
        self.vals = [0, 0]

    async def scan(self):
        devices = await BleakScanner.discover()
        for dev in devices:
            if dev.name and "CorSense" in dev.name:
                self.device_info = dev
                print("CorSense has been found!")
                return True
        return False

    async def connect(self):
        if self.device_info is None:
            print("No CorSense device found. Please scan first.")
            return False

        try:
            self.device = BleakClient(self.device_info.address)
            await self.device.connect()
            print('CorSense has been connected')
            return True
        except Exception as e:
            print(f"Error connecting to CorSense: {e}")
            return False

    async def enable_notifications(self):
        await self.device.start_notify(self.hrm_uuid, self.notification_handler)

    def notification_handler(self, sender, data):
        self.set_vals(data)

    async def initialize(self):
        if self.device is None:
            while True:
                if await self.scan():
                    break
            
            if not await self.connect():
                return

        await self.enable_notifications()
        await self.run()

    async def run(self):
        while self.running:
            await asyncio.sleep(1)

    def stop(self):
        self.running = False

    def rr(self):
        return self.vals

    @staticmethod
    def get_rr(index, data):
        rr_list = []
        while index < len(data):
            rr_cur = data[index] + (data[index + 1] << 8)
            rr_cur = (float(rr_cur) / 1024) * 1000  # convert to ms
            index += 2
            rr_list.append(rr_cur)
            print('RR List: ' + str(rr_list), index)
        return rr_list

    def set_vals(self, data):
        flag = data[0]
        uint8_bit = 0
        rr_bit = 16  # in decimal - 00010000 (5th bit)
        ee_bit = 8  # in decimal - 00001000 (4th bit)
        index = 1

        # HR format
        if flag & uint8_bit == 0:
            index += 1

        # ee_exit availability
        if flag & ee_bit != 0:
            index += 2

        # rr_exit availability
        if flag & rr_bit != 0:
            self.vals = self.get_rr(index, data)

if __name__ == "__main__":
    cs = Corsense()
    asyncio.run(cs.initialize())