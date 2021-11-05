# -*- coding: utf-8 -*-

from .context import ctxmng
from .model import RecordHeader, Message


class FitFile():
    def __init__(self, fitfile):
        self._fitfile = fitfile
        self._start = self._fitfile.tell()
        self._read_file_header()

        crc, *_ = self._fitfile.read("H", self.header_size + self.data_size)
        calc_crc = self._fitfile.crc(0, self.file_size - 2)
        assert crc == calc_crc, f"{crc} == {calc_crc}"

    @property
    def header_size(self):
        return self._header_size

    @property
    def data_size(self):
        return self._data_size

    @property
    def file_size(self):
        return self._header_size + self._data_size + 2

    @property
    def protocol_version(self):
        return float(f"{self._protocol_version >> 4}.{self._protocol_version & ((1 << 4) - 1)}")

    @property
    def profile_version(self):
        return float(f"{self._profile_version // 100}.{self._profile_version % 100}")

    def _read_file_header(self):
        ( self._header_size, 
          self._protocol_version,
          self._profile_version,
          self._data_size,
          *fit
        ) = self._fitfile.read('2BHI4c')
        readsize = self._fitfile.readsize

        assert ".FIT" == b"".join(fit).decode(), "Invalid FitFile header"
        self._fitfile.slice(self._start, self._start + self.file_size)
        assert self.file_size <= len(self._fitfile), "Invalid FitFile header file size"
        self._fitfile.seek(readsize)

        if readsize < self._header_size:
            crc, *_ = self._fitfile.read('H')
            calculated_crc = self._fitfile.crc(0, readsize)
            assert crc == calculated_crc, "Invalid FitFile header crc"
            readsize += self._fitfile.readsize
            assert readsize == self._header_size, "Invalid Fiffile header size"

    def _read_message(self):
        header = RecordHeader.create(self._fitfile.read)
        return Message.unpack(header, self._fitfile.read)

    def messages(self):
        with ctxmng() as context:
            while self._fitfile.tell() < self.file_size - 2:
                message = self._read_message()
                yield message

            crc, *_ = self._fitfile.read("H")
            calc_crc = self._fitfile.crc(0, self.file_size - 2)
            assert crc == calc_crc, f"{crc} == {calc_crc}"
        return
