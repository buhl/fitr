# -*- coding: utf-8 -*-
import functools

from .message import Message
from ..profile import base_types, messages, types
from ..context import Ctx


class Accumulator():
    def __init__(self):
        super().__init__(int, dict, int)


class FieldDefinition():
    def __init__(self, field, definition_number, base_type, size):
        self.field = field
        self.definition_number = definition_number
        self.base_type = base_type
        self.size = size

    @property
    def name(self):
        return self.field.name if self.field else f"unknown_{self.definition_number}"

    @classmethod
    def unpack(cls, message_type, reader):
        field_def_num, field_size, base_type_num = reader('3B')
        field_type = message_type.fields.pick(field_def_num) if message_type else None
        base_type = base_types[base_type_num] or base_types.pick(name="byte")

        if field_type and field_type.components:
            for component in field_type.components:
                if component.accumulate:
                    if message_type.global_number in Ctx.accumulators:
                        accumulator = Ctx.accumulators[message_type.global_number]
                    else:
                        accumulator = Ctx.accumulators[message_type.global_number] = Accumulator()
                    accumulator[component.num] = 0

        return cls(
            field = field_type,
            definition_number = field_def_num,
            base_type = base_type,
            size = field_size
        )


class DeveloperFieldDefinition():
    def __init__(self, dev_data_index, definition_number, size, field=None):
        self.dev_data_index = dev_data_index
        self.definition_number = definition_number
        self.size = size
        self.field = field or Ctx.developer_data_types.pick(dev_data_index).fields.pick(definition_number)

    @property
    def base_type(self):
        return self.field.type

    @classmethod
    def unpack(cls, reader):
        field_def_num, field_size, dev_data_index = reader('3B')
        field = None
        return cls(
                field = field,
                dev_data_index = dev_data_index,
                definition_number = field_def_num,
                size = field_size
        )


class MessageDefinition(Message):
    def __init__(self, global_number, type, endian, field_definitions, developer_field_definitions, **kwargs):
        super().__init__(**kwargs)
        self.global_number = global_number
        self.type = type
        self._endian = 1 if bool(endian) else 0
        self.field_definitions = field_definitions
        self.developer_field_definitions = developer_field_definitions

    @property
    def endian(self):
        return '>' if self._endian else '<'

    @property
    def name(self):
        return self.type.name if self.type else f"unknown_{self.global_number}"

    @classmethod
    def unpack(cls, header, reader):
        endian = reader('xB')[0]
        import sys
        reader = functools.partial(reader, endian='>' if endian else '<')
        global_message_number, num_fields = reader('HB')
        message_type = messages.pick(True, global_number=global_message_number)
        field_defs = []

        for n in range(num_fields):
            field_defs.append(FieldDefinition.unpack(message_type, reader))

        dev_field_defs = []
        if header.developer_data:
            num_dev_fields = reader('B')[0]
            for n in range(num_dev_fields):
                dev_field_def = DeveloperFieldDefinition.unpack(reader)
                dev_field_defs.append(dev_field_def)

        return cls(
                header=header,
                global_number = global_message_number,
                type=message_type,
                endian=endian,
                field_definitions=field_defs,
                developer_field_definitions=dev_field_defs
        )
