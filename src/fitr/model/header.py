# -*- coding: utf-8 -*-

class RecordHeader():
    def __init__(self, bit):
        if bit & 0x80 and isinstance(self, CompressedTimestampHeader):
            self._local_message_type = (bit >> 5) & 0x3
            assert self._local_message_type in range(0,4), "Invalid local message type"
        elif not bit & 0x80 and isinstance(self, NormalHeader):
            self._local_message_type = bit & 0xF
            assert self._local_message_type in range(0,16), "Invalid local message type"
        else:
            raise ValueError("Invalid header bit")

        self._bit = bit

    def __format__(self, spec):
        if not spec:
            return str(self)
        if spec == "r":
            return repr(self)
        if spec == "b":
            spec = "08b"

        return f"{format(self.bit, f'{spec}')}"

    def __str__(self):
        return str(self.bit)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.bit})"

    @property
    def bit(self):
        return self._bit

    @property
    def local_message_type(self):
        return self._local_message_type

    def create(reader):
        bit = reader('B')[0]
        cls = CompressedTimestampHeader if bit & 0x80 else NormalHeader
        return cls(bit)

class NormalHeader(RecordHeader):
    def __init__(self, bit):
        super().__init__(bit)
        self._definition = bool(self.bit & 0x40)
        self._developer_data = bool(self.bit & 0x20)

    @property
    def definition(self):
        return self._definition 

    @property
    def developer_data(self):
        return self._developer_data

    def create(definition, data, local_message_type):
        assert local_message_type in range(0, 16)
        return RecordHeader.create(int(f"0{int(bool(definition))}{int(bool(data))}0{local_message_type:04b}", 2))

class CompressedTimestampHeader(RecordHeader):
    def __init__(self, bit):
        super().__init__(bit)
        self._time_offset = self.bit & 0x1F

    @property
    def time_offset(self):
        return self._time_offset

    def create(local_message_type, time_offset):
        assert local_message_type in range(0, 4)
        assert time_offset in range(0, 32)
        return RecordHeader.create(int(f"1{local_message_type:02b}{time_offset:05b}", 2))

