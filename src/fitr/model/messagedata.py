# -*- coding: utf-8 -*-
import sys
import functools

from .message import Message
from ..context import Ctx
from ..profile import types


def read_field_def(field_def, reader):
    base_type = field_def.base_type
    count = int(field_def.size / base_type.size)
    fmt = f"{count}{base_type.fmt}"
    raw_value = reader(fmt)

    if isinstance(raw_value, tuple) and base_type.name != "byte":
        out = tuple(base_type.parser(v) for v in raw_value)
    else:
        out = base_type.parser(raw_value)
    if count < 2 and out:
        return out[0]
    return out


def find_parent_field(field, message_type, raw_values):
    if hasattr(field, "subfield"):
        for sub_field in field.subfields:
            for ref_field in sub_field.reference_fields:
                for field_def, raw_value in zip(message_type.type.fields.values(), raw_values):
                    if (field_def.def_num == ref_field.def_num and ref_field.raw_value == raw_value):
                        return sub_field, field

    return field, None

def apply_scale_offset(field, raw_value):
    if isinstance(raw_value, tuple):
        return tuple(apply_scale_offset(field, rv) for rv in raw_value)
    if hasattr(field, "type") and field.type:
        raw_value = field.type.parser(raw_value)
    if isinstance(raw_value, (float, int)):
        if hasattr(field, "scale") and field.scale:
            raw_value = float(raw_value) / field.scale
        if hasattr(field, "offset") and field.offset:
            raw_value = raw_value - field.offset
    return raw_value


class FieldData():
    def __init__(self, fdef, field, parent_field, value, raw_value):
        self.fdef = fdef
        self.field = field
        self.parent_field = parent_field
        self.value = value
        self.raw_value = raw_value

    @property
    def name(self):
        return self.field.name if self.field else f"unknown_{self.definition_number}"

class MessageData(Message):
    def __init__(self, definition, fields, **kwargs):
        super().__init__(**kwargs)
        self.definition = definition
        self.fields = fields

    @classmethod
    def unpack(cls, header, reader):
        def_mesg = Ctx.message_definitions.pick(header.local_message_type)

        timestamp_type = types.pick("date_time")
        assert def_mesg


        fields = list(def_mesg.field_definitions) + list(def_mesg.developer_field_definitions)
        field_raw_values = {field: read_field_def(field, functools.partial(reader, endian=def_mesg.endian)) for field in fields}

        data_fields = []
        for field_def, raw_value in field_raw_values.items():
            field, parent_field = field_def.field, None

            if not field:
                value = raw_value
            else:
                field, parent_field = find_parent_field(field, def_mesg, field_raw_values.values())
                if hasattr(field, "components"):
                    for component in field.components:
                        component_raw_value = component.parser(raw_value)
                        if component.accumulate and component_raw_value is not None:
                            accumulator = Ctx.accumulators[def_mesg.global_number]
                            print("OHNO!", file=sys.stderr)
                            sys.exit(1)
                        component_field = def_mesg.type.fields.pick(component.num)
                        component_raw_value = apply_scale_offset(component_field, component_raw_value)

                        component_field, component_parent_field = find_parent_field(component_field, def_mesg, field_raw_values.values())
                        component_value = component_field.type.parser(component_raw_value)

                        data_fields.append(
                            FieldData(
                                fdef = None,
                                field = component_field,
                                parent_field = component_parent_field,
                                value = component_value,
                                raw_value = component_raw_value
                            )
                        )

                value = apply_scale_offset(field, raw_value) 

            if field_def.definition_number == 253 and raw_value is not None:
                Ctx.compressed_ts_accumulator = raw_value

            data_fields.append(
                FieldData(
                    fdef = field_def,
                    field = field,
                    parent_field = parent_field,
                    value = value,
                    raw_value = raw_value
                )
            )

        if time_offset := getattr(header, "time_offset", None):
            print("OHNO!!", file=sys.stderr)
            sys.exit(1)


        return cls(
            header = header,
            definition = def_mesg,
            fields = data_fields
        )
    
