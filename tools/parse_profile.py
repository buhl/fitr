#!/usr/bin/env python
import re
import sys
import json
import struct
import inspect
import datetime
import functools

import openpyxl


class Base():
    def __str__(self):
        return f"<{__name__}.{self.__class__.__name__}:{getattr(self, 'name', '')} at {hex(id(self))}>"

    def pack(self):
        raise NotImplementedError

    @classmethod
    def unpack(self, stream):
        raise NotImplementedError

    def __repr__(self):
        def render(v):
            if isinstance(v, Base):
                return f"{repr(v)}"
            elif isinstance(v, type):
                if issubclass(v, Base):
                    return v.__name__
                return v.__name__
            elif isinstance(v, type(lambda x: x)) and "TypeParsers." in v.__qualname__:
                return v.__qualname__
            elif isinstance(v, str):
                return repr(v)
            elif isinstance(v, int):
                return str(v)
            elif isinstance(v, type(None)):
                return "None"
            else:
                return v

        out = []
        out.append(f"{self.__class__.__name__}(")
        out.extend(
            f"    {k[1:] if k.startswith('_') else k}={render(v)}," for k, v in self.__dict__.items() if (
                (isinstance(v, Map) and v)
                or (not isinstance(v, Map) and v is not None)
            )
        )
        out.append(f")")
        return "\n".join(out)


class Map(Base):
    def __init__(self, value_type, map_type=list, key_type=str, map=None):
        self._map = map_type() if map_type in [list, dict, set] else list()
        self._map_type = type(self._map)
        self._value_type = value_type
        self._key_type = key_type if map_type == dict else int

        if map:
            self._uptend(map)

    def __len__(self):
        return len(self._map)

    def __bool__(self):
        return bool(self._map)

    def __getitem__(self, key):
        return self._map[key]

    def __setitem__(self, key, value):
        if isinstance(self._map, set):
            raise TypeError(f"{self.__class.__name__} of 'set' type does not support item assignment")

        if not isinstance(key, self._key_type):
            raise IndexError(f"'{self.__class__.__name__}' index must be of type '{self._key_type}'")

        if not isinstance(value, self._value_type):
            raise ValueError(f"'{self.__class__.__name__}' value can only be '{self._value_type.__class__.__name__}'")
        self._map[key] = value

    def __iter__(self):
        return iter(self._map)

    def __delitem__(self, key):
        if isinstance(self._map, set):
            raise TypeError(f"{self.__class.__name__} of 'set' type does not support item deletion")
        del self._map[key]

    def __getattr__(self, attr):
        if not (method := getattr(self._map, attr, False)):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr}'")

        def check_value(value):
            if not isinstance(value, self._value_type):
                raise ValueError(f"'{self.__class__.__name__}' can only contain '{self._value_type.__class__.__name__}'")
 

        if isinstance(self._map, list):
            if attr == "append":
                def append(value):
                    check_value(value)
                    method(value)
                return append
                
            elif attr ==  "extend":
                def extend(values):
                    for value in values:
                        check_value(value)
                    method(values)
                return extend

        elif isinstance(self._map, dict):
            if attr == "update":
                def check_key(key):
                    if not isinstance(key, self._key_type):
                        raise KeyError(f"'{self.__class__.__name__}' can only contain '{self._key_type.__class__.__name__}'")

                def update(*args, **kwargs):
                    for map in args:
                        if hasattr(map, 'keys'):
                            for k in map:
                                check_key(k)
                                check_value(map[k])
                        else:
                            for k, v in map:
                                check_key(k)
                                check_value(v)
                    for k in kwargs:
                        check_key(k)
                        check_value(kwargs[k])

                    return method(*args, **kwargs)
                return update

        elif isinstance(self._map, set):
            if attr == "add":
                def add(value):
                    check_value(value)
                    return method(value)
                return add

            elif attr == "symmetric_difference_update":
                def symmetric_difference_update(value):
                    [check_value(v) for v in value]
                    return method(value)
                return symmetric_difference_update
                
            elif attr.endswith("update"):
                def updates(*values):
                    for set_value in values:
                        [check_value(v) for v in set_value]
                    return method(*values)
                return updates

        else: 
            raise AttributeError(f"'{self.__class__.__name__}' object does not support attribute '{attr}'")

        return method

    def _uptend(self, values):
        attr = "update" if isinstance(self._map, (dict, set)) else "extend"
        getattr(self, attr)(values)

    def pick(self, key=..., **kwargs):
        match = any if kwargs.pop("_match", None) == any else all 
        ellipsis = type(...)
        for k, v in enumerate(self._map) if isinstance(self._map, (list, set)) else self._map.items():
            if not kwargs and key == k:
                return v
            if kwargs and match(getattr(v,a, ...) == kwargs[a] for a in kwargs):
                if isinstance(key, bool) and key:
                    return v
                return k


class Type(Base):
    def __init__(self, name, base_type, parser=None, values=None, comment=None):
        assert isinstance(name, str)
        assert isinstance(base_type, str)
        self.name = name
        self._base_type = base_type
        self._parser = parser
        self.values = values or Map(TypeValue, dict, int)
        self.comment = comment

    @property
    def parser(self):
        return functools.partial(self._parser, self) if self._parser else lambda x: x

    @property
    def base_type(self):
        return base_types.pick(True, name=self._base_type) or self._base_type


class TypeValue(Base):
    def __init__(self, name, value, comment=None):
        self.name = name
        self.value = value
        self.comment = comment


class Message(Base):
    def __init__(self, name, global_number, group_name, fields=None, comment=None):
        self.name = name
        self.global_number = global_number
        self.group_name = group_name
        self.fields = fields or Map(Field, dict, int)
        self.comment = comment


class Component(Base):
    def __init__(self, name, scale=None, offset=None, units=None, bits=None, accumulate=None, num=None, bit_offset=None):
        self.name = name
        self.scale = scale
        self.offset = offset
        self.units = units
        self.bits = bits
        self.accumulate = accumulate
        self.num = num
        self.bit_offset = bit_offset

    def parser(self, raw_value):
        if raw_value is None:
            return None

        if isinstance(raw_value, type):
            if self.bit_offset and self.bit_offset >= len(raw_value) << 3:
                raise ValueError()
            unpacked_num = 0
            for value in reversed(raw_value):
                unpacked_num = (unpacked_num << 8) + value

            raw_value = unpacked_num

        if isinstance(raw_value, int):
            raw_value = (raw_value >> self.bit_offset) & ((1 << self.bits) - 1)

        return raw_value


class FieldBase(Base):
    def __init__(self, name, type, def_num=None, scale=None, offset=None, units=None, components=None, comment=None):
        self.name = name
        self._type = type
        self.def_num = def_num

        self.components = components or Map(Component, list)
 
        if components and not str(scale).isdigit():
            self.scale = self.offset = self.units = None
        else:
            self.scale = scale
            self.offset = offset
            self.units = units
        self.comment = comment

    @property
    def type(self):
        return types.pick(True, name=self._type) or base_types.pick(True, name=self._type) or self._type


class Field(FieldBase):
    def __init__(self, subfields=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subfields = subfields or Map(SubField, list)


class SubField(FieldBase):
    def __init__(self, reference_fields=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reference_fields = reference_fields or Map(ReferenceField, list)


class ReferenceField(Base):
    def __init__(self, name, value, def_num=None, raw_value=None):
        self.name = name
        self.value = value
        self.def_num = def_num
        self.raw_value = raw_value


class BaseType(Base):
    def __init__(self, name, fmt, parser=lambda x: x, size=None, byte=None, type_num=None):
        self.name = name
        self.fmt = fmt
        self.parser = parser
        self.byte = byte
        self.type_num = type_num
        self.size = size if size is not None else struct.calcsize(self.fmt)


class BaseTypeParsers():
    def enum(v):
        return None if v == 0xFF else v

    def sint8(v):
        return None if v == 0x7F else v

    def uint8(v):
        return None if v == 0xFF else v

    def string(v):
        if v is None:
            return None
        elif isinstance(v, bytes):
            v = v.decode('utf-8', errors="replace")
        try:
            s = v[:v.index('\x00')]
        except ValueError:
            s = v
        return s or None

    def uint8z(v):
        return None if v == 0x0 else v

    def byte(v):
        if v is None:
            return None
        if isinstance(v, int):
            return None if v == 0xFF else v
        return None if all(b == 0xFF for b in v) else v

    def sint16(v):
        return None if v == 0x7FFF else v

    def uint16(v):
        return None if v == 0xFFFF else v

    def sint32(v):
        return None if v == 0x7FFFFFFF else v

    def uint32(v):
        return None if v == 0xFFFFFFFF else v

    def float32(v):
        return None if math.isnan(v) else v

    def float64(v):
        return None if math.isnan(v) else v

    def uint16z(v):
        return None if v == 0x0 else v

    def uint32z(v):
        return None if v == 0x0 else v

    def sint64(v):
        return None if v == 0x7FFFFFFFFFFFFFFF else v

    def uint64(v):
        return None if v == 0xFFFFFFFFFFFFFFFF else v

    def uint64z(v):
        return None if v == 0 else v

    def bool(v):
        return True if v else False

class TypeParsers():
    def date_time(self, value):
        max_offset_value = self.values.pick(name="min")
        if value < max_offset_value:
            return value
        return datetime.datetime.fromtimestamp(value + GARMIN_EPOC_OFFSET) 
    local_date_time = date_time

base_types = Map(BaseType, dict, int)
base_type_list = [
    {"fmt":'B', "size":struct.calcsize('B'), "parser":BaseTypeParsers.enum,    "name":'enum'},
    {"fmt":'b', "size":struct.calcsize('b'), "parser":BaseTypeParsers.sint8,   "name":'sint8'},
    {"fmt":'B', "size":struct.calcsize('B'), "parser":BaseTypeParsers.uint8,   "name":'uint8'},
    {"fmt":'s', "size":struct.calcsize('s'), "parser":BaseTypeParsers.string,  "name":'string'},
    {"fmt":'B', "size":struct.calcsize('B'), "parser":BaseTypeParsers.uint8z,  "name":'uint8z'},
    {"fmt":'B', "size":struct.calcsize('B'), "parser":BaseTypeParsers.byte,    "name":'byte'},
    {"fmt":'h', "size":struct.calcsize('h'), "parser":BaseTypeParsers.sint16,  "name":'sint16'},
    {"fmt":'H', "size":struct.calcsize('H'), "parser":BaseTypeParsers.uint16,  "name":'uint16'},
    {"fmt":'i', "size":struct.calcsize('i'), "parser":BaseTypeParsers.sint32,  "name":'sint32'},
    {"fmt":'I', "size":struct.calcsize('I'), "parser":BaseTypeParsers.uint32,  "name":'uint32'},
    {"fmt":'f', "size":struct.calcsize('f'), "parser":BaseTypeParsers.float32, "name":'float32'},
    {"fmt":'d', "size":struct.calcsize('d'), "parser":BaseTypeParsers.float64, "name":'float64'},
    {"fmt":'H', "size":struct.calcsize('H'), "parser":BaseTypeParsers.uint16z, "name":'uint16z'},
    {"fmt":'I', "size":struct.calcsize('I'), "parser":BaseTypeParsers.uint32z, "name":'uint32z'},
    {"fmt":'q', "size":struct.calcsize('q'), "parser":BaseTypeParsers.sint64,  "name":'sint64'},
    {"fmt":'Q', "size":struct.calcsize('Q'), "parser":BaseTypeParsers.uint64,  "name":'uint64'},
    {"fmt":'Q', "size":struct.calcsize('Q'), "parser":BaseTypeParsers.uint64z, "name":'uint64z'},
    {"fmt":'B', "size":struct.calcsize('B'), "parser":BaseTypeParsers.bool,    "name":'bool'},
]

def parse_csv_field(field, items=0, func=lambda x: x):
    if not field:
        return [func(None)] * items
    if isinstance(field, (str, bytes)):
        array = [func(int(striped)) if striped.isdigit() else func(striped) for raw in field.split(',') if (striped := raw.strip())]
    else:
        array = [func(field)]

    array_lenght = len(array)
    if array_lenght < items:
        assert array_lenght == 1
        return array * items
    return array

fix_scale = lambda x: None if x == 1 else x
fix_units = lambda x: x.replace(' / ', '/').replace(' * ', '*').replace('(steps)', 'or steps') if x else None

#
## TYPES
#
#headers = [n.lower().replace(" ", "_") if n else n for n in next(ws_types.iter_rows(max_row=1, values_only=True))]

types = Map(Type, dict, str)
def parse_types_sheet(sheet):
    for row in sheet.iter_rows(min_row=2, values_only=True):
        type_name, base_type, value_name, value, comment = row
        if type_name:
            type_parser = getattr(TypeParsers, type_name, None)
            current_type = types[type_name] = Type(type_name, base_type, parser=type_parser)
            
        elif value is not None:
            try:
                int_value = int(value)
            except ValueError as e:
                int_value = int(value, 16)

            current_type.values[int_value] = TypeValue(name=value_name, value=int_value, comment=comment)

            if not comment:
                continue

            if not comment.startswith(f"0x{hex(int_value).upper()[2:]}"):  # doing range values
                continue

            start = int_value + 1
            end = int(comment.split()[2], 16)
            name = "_".join(value_name.split("_")[:-1])
            for n in range(start, end):
                current_type.values[n] = TypeValue(name=f"{name}_{n}", value=n, comment=comment)

        else:
            assert not any(row), "We should not get here"


def format_base_types():
    base_type_map = {v.name:k for k, v in types['fit_base_type'].values.items()}
    base_type_map["bool"] = 0
    for base_type_kwargs in base_type_list: 
        byte = base_type_map.get(base_type_kwargs["name"], {})
        base_types[byte] = BaseType(**{**base_type_kwargs, **{"byte": byte, "type_num": byte & 0x1F}})


def get_type(type):
    if not isinstance(type, str):
        return type
    return base_types.get(type) or types.get(type)


#
## MESSAGES
#
messages = Map(Message, dict, str)
def parse_message_sheet(sheet):
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not any(bool(v) for i, v in enumerate(row) if i != 3):  # empty line or message group header
            if row[3] and len(row[3]):  # message group header
                group_name = row[3].title()
            continue

        (
            message_name, field_def_num, field_name, field_type, array,
            components, scale, offset, units, bits, accumulate,
            ref_field_name, ref_field_value, comment, products, example
        ) = row[:-3]

        if message_name:
            current_message = messages[message_name] = Message(
                    name=message_name,
                    global_number=types["mesg_num"].values.pick(name=message_name),
                    group_name=group_name,
                    fields=None,
                    comment=comment
            )
            continue


        component_fields = Map(Component, list)
        if components and (component_names := [c.strip() for c in components.split(",") if c.strip()]):

            num_components = len(component_names)

            component_fields.extend(
                [Component(
                    name=component_name,
                    scale=component_scale,
                    offset=component_offset,
                    units=component_units,
                    bits=component_bits,
                    accumulate=component_accumulate
                ) 
                for component_name, component_scale, component_offset, component_units, component_bits, component_accumulate in zip(
                    component_names,
                    parse_csv_field(scale, num_components, fix_scale),
                    parse_csv_field(offset, num_components),
                    parse_csv_field(units, num_components, fix_units),
                    parse_csv_field(bits, num_components),
                    parse_csv_field(accumulate, num_components, bool)
                )]
            )

            
            assert len(component_fields) == num_components
            assert all(c.name and c.bits for c in component_fields)



        if field_def_num is not None:
            current_field = current_message.fields[field_def_num] = Field(
                name=field_name,
                type=field_type,
                def_num=field_def_num,
                scale=fix_scale(scale),
                offset=offset,
                units=fix_units(units),
                components=component_fields,
                comment=comment
            )
            continue

        elif field_name is not None:
            subfield = SubField(
                name=field_name,
                type=field_type,
                scale=fix_scale(scale),
                offset=offset,
                units=fix_units(units),
                components=component_fields,
                comment=comment
            )

            ref_field_names = parse_csv_field(ref_field_name)
            assert ref_field_names, f"{ref_field_name} {ref_field_names} {row}"

            subfield.reference_fields.extend(
                [ReferenceField(
                    name=name,
                    value=value,
                    def_num=None,
                    raw_value=None
                ) for name, value in zip(ref_field_names, parse_csv_field(ref_field_value))
                ]
            )

            assert len(subfield.reference_fields) == len(ref_field_names)
            if "alert_type" not in ref_field_names:
                current_field.subfields.append(subfield)

            continue

    messages._map = {k:v for k ,v in sorted(messages._map.items(), key=lambda item: item[1].global_number)}

    for message_name, message in messages.items():
        for _, field in message.fields.items():
            for subfield in field.subfields:
                for sub_ref_field in subfield.reference_fields:
                    ref_field = message.fields.pick(True,  name=sub_ref_field.name)
                    sub_ref_field.def_num = ref_field.def_num 
                    sub_ref_field.raw_value = get_type(ref_field.type).values.pick(name=sub_ref_field.value) 

                bit_offset = 0
                for component in subfield.components:
                    component.num = message.fields.pick(name=component.name)
                    component.bit_offset = bit_offset
                    bit_offset += component.bits
            bit_offset = 0
            for component in field.components:
                component.num = message.fields.pick(name=component.name)
                component.bit_offset = bit_offset
                bit_offset += component.bits


GARMIN_EPOC_OFFSET = datetime.datetime.fromisoformat('1989-12-31T00:00:00').timestamp()

obj2render = [
    BaseTypeParsers,
    TypeParsers,
    Base,
    Map,
    BaseType,
    Type,
    TypeValue,
    Message,
    Component,
    FieldBase,
    Field,
    SubField,
    ReferenceField
]

def print_rendered():
    print("# -*- coding: utf-8 -*-\n")
    print("import math")
    print("import struct")
    print("import datetime")
    print("import functools")
    print("")
    print(f"{GARMIN_EPOC_OFFSET=}")
    print("")
    for obj in obj2render:
        print(inspect.getsource(obj))
        print("\n")
    print(f"base_types =", repr(base_types))
    print(f"types =", repr(types))
    print(f"messages =", repr(messages))

def dofile(file):
    wb = openpyxl.load_workbook(file)
    ws_types = wb['Types']
    ws_messages = wb['Messages']
    parse_types_sheet(ws_types)
    format_base_types()
    parse_message_sheet(ws_messages)
    print_rendered()



if __name__ == "__main__":
    dofile(sys.argv[-1])
