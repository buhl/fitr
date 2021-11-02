# -*- coding: utf-8 -*-

import copy
import struct


class FitFileMemory():
    CRC_TABLE = (
        0x0000, 0xcc01, 0xd801, 0x1400, 0xf001, 0x3c00, 0x2800, 0xe401,
        0xa001, 0x6c00, 0x7800, 0xb401, 0x5000, 0x9c01, 0x8801, 0x4400
    )

    def __init__(self, fitfile):
        self._at = 0
        self._last_read = 0
        with open(fitfile, "rb") as fp:
            self._memory = memoryview(fp.read()).toreadonly()

    def __len__(self):
        return len(self._memory)

    def read(self, fmt, start=None, endian=0):
        endian_fmt = f"{'>' if endian else '<'}{fmt}"
        readsize = struct.calcsize(endian_fmt)
        if start is None:
            end = self._at + readsize
        else:
            end = start + readsize
        assert end <= len(self), "Trying to read out of bounds"
        chunk = self._memory[self._at if start is None else start:end]
        if start is None:
            self._at = end
            self._last_read = readsize
        return struct.unpack(endian_fmt, chunk)

    @property
    def readsize(self):
        return self._last_read

    def slice(self, *args):
        self._memory = self._memory[slice(*args)]

    def seek(self, at):
        assert 0 <= at <= len(self), "Out of bound seek"
        self._at = at

    def tell(self):
        return self._at

    def copy(self):
        new = copy.copy(self)
        new._memory = new._memory[0:]
        return new

    def crc(self, start, end):
        crc = 0
        for byte in self._memory[start:end]:
            tmp = self.CRC_TABLE[crc & 0xf]
            crc = (crc >> 4) & 0x0fff
            crc = crc ^ tmp ^ self.CRC_TABLE[byte & 0xf]

            tmp = self.CRC_TABLE[crc & 0xf]
            crc = (crc >> 4) & 0x0fff
            crc = crc ^ tmp ^ self.CRC_TABLE[(byte >> 4) & 0xf]
            #print(f"{crc}")

        return crc
