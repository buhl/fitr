# -*- coding: utf-8 -*-
import functools

from ..profile import Map, base_types, messages, types


class Accumulator(Map):
    def __init__(self):
        super().__init__(self, int, dict, int)


class FieldDefinition():
    def __init__(self, field_type, definition_number, base_type, size):
        self.field_type = field_type
        self.definition_number = definition_number
        self.base_type = base_type
        self.size = size

    @classmethod
    def unpack(cls, message_type, reader):
        field_def_num, field_size, base_type_num = reader('3B')
        field_type = message_type.fields[field_def_num] if message_type else None
        base_type = base_types[base_type_num]

        if field_type and field_type.components:
            for component in field_type.component:
                if component.accumulate:
                    if message_type.global_number in Ctx.accumulators:
                        accumulator = Ctx.accumulators[message_type.global_number]
                    else:
                        accumulator = Ctx.accumulators[message_type.global_number] = Accumulator()
                    accumulator[compnent.def_num] = 0

        return cls(
            field_type = field_type,
            definition_number = field_def_num,
            base_type = base_type,
            size = field_size
        )


class DeveloperFieldDefinition():
    def __init__(self, field, dev_data_index, def_num, size):
        self._field = field
        self._dev_data_index = dev_data_index,
        self._def_num = def_num
        self._size = size

    @classmethod
    def unpack(cls, reader):
        field_def_num, field_size, dev_data_index = reader('3B')
        field = None
        return cls(
                field = field,
                dev_data_index = dev_data_index,
                def_num = field_def_num,
                size = field_size
        )


class MessageDefinition():
    def __init__(self, header, type, endian, field_definitions, developer_field_definitions):
        self.header = header
        self.type = type
        self.endian = endian
        self.field_definitions = field_definitions
        self.developer_field_definitions = developer_field_definitions

    @classmethod
    def unpack(cls, header, reader):
        endian = reader('xB')[0]
        reader = functools.partial(reader, endian='>' if endian else '<')
        global_message_number, num_fields = reader('HB')
        message_type = messages.pick(True, global_number=global_message_number)
        field_defs = Map(FieldDefinition, list)

        for n in range(num_fields):
            field_defs.append(FieldDefinition.unpack(message_type, reader))

        dev_field_defs = Map(DeveloperFieldDefinition, list)
        if header.developer_data:
            num_dev_fields = reader('B')[0]
            for n in range(num_dev_fields):
                def_field_defs.append(DeveloperFieldDefinition.unpack(reader))


        return cls(
                header=header,
                type=message_type,
                endian=endian,
                field_definitions=field_defs,
                developer_field_definitions=dev_field_defs
        )
