# -*- coding: utf-8 -*-
import sys
import functools

from .message import Message
from ..context import Ctx

class MessageData(Message):
    def __init__(self, fields, *args, **kwargs):
        self.fields = fields
        super().__init__(*args, **kwargs)

    @classmethod
    def unpack(cls, header, reader):
        #509 _parse_data_message
        def_mesg = Ctx.message_definitions[header.local_message_type]
        print(def_mesg)
        assert def_mesg
        def read_field_def(field_def, reader):
            base_type = field_def.base_type
            count = int(field_def.size / base_type.size)
            fmt = f"{count}{base_type.fmt}"
            out = tuple(base_type.parse(v) for v in reader(fmt))
            if count < 2:
                return out[0]
            return out

        def find_parent_field(field, message_type, raw_values):
            for sub_field in field.subfields:
                for ref_field in sub_field.reference_fields:
                    for field_def, raw_value in zip(message_type.type.fields.values(), raw_values):
                        if (field_def.def_num == ref_field.def_num and
                            ref_field.raw_value == raw_value):
                            return sub_field, field

            else:
                return field, None

        def field_value(field, raw_value):
            if not field.field:
                return raw_value, []
            field, parent_field, field.field, field.sub


        fields = list(def_mesg.field_definitions) + list(def_mesg.developer_field_definitions)
        field_raw_values = {field: read_field_def(field, functools.partial(reader, endian=def_mesg.endian)) for field in fields}

        for field, raw_value in field_raw_values.items():
            field, parent_field = find_parent_field(field.field_type, def_mesg, field_raw_values.values())

            for component in field.components:
                print(component)

        sys.exit()
        #return cls(
        #    header = header
        #)
