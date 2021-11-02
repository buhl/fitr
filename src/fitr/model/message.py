# -*- coding: utf-8 -*-
from .. import model
from ..context import Ctx


class Message():
    def __init__(self, header, endian, message_type):
        self.header = header
        self.endian = 1 if bool(endian) else 0
        self.message_type

    @property
    def endian(self):
        return '>' if self._endian else '<'

    @classmethod
    def unpack(cls, header, reader):
        if isinstance(header, model.NormalHeader) and header.definition:
            message = model.MessageDefinition.unpack(header, reader)
            Ctx.message_definitions[header.local_message_type] = message
        else:
            message = model.MessageData.unpack(header, reader)
        return message
