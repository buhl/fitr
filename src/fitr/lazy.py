import sys
import functools
from typing import Any, Union
from dataclasses import dataclass
from collections import defaultdict

from . import profile

from .readers import FitFileMemory
from .fitfile import FitFile

message_definitions = {}
data_messages = []
developer_data = {}

def add_developer_data(message):
    data = {k: None for k in ["developer_data_index", "application_id"]}
    for field in message.fields:
        if field.definition.global_message_number ==  207:
            if field.definition.definition_number == 1:
                data["application_id"] = field.data
            if field.definition.definition_number == 3:
                data["developer_data_index"] = field.data

    if data["developer_data_index"] is not None:
        developer_data[data["developer_data_index"]] = {**data, **{"fields": {}}}

def add_developer_field_description(message):
    data = {k: None for k in ["developer_data_index", "field_definition_number", "fit_base_type_id", "field_name" ]}
    for field in message.fields:
        if field.definition.global_message_number ==  206:
            if field.definition.definition_number == 0:
                data["developer_data_index"] = field.data
            if field.definition.definition_number == 1:
                data["definition_number"] = field.data
            if field.definition.definition_number == 2:
                data["type"] = field.data
            if field.definition.definition_number == 3:
                data["name"] = field.data
            if field.definition.definition_number == 8:
                data["units"] = field.data
            if field.definition.definition_number == 15:
                data["native_field_num"] = field.data

    if data["developer_data_index"] is not None:
        developer_data[data["developer_data_index"]][data["definition_number"]] = data

@dataclass
class RecordHeader():
    bit: int

    def unpack(reader):
        bit = reader('B')
        cls = CompressedTimestampHeader if bit & 0x80 else NormalHeader
        return cls(bit)

@dataclass
class NormalHeader(RecordHeader):

    @property
    def definition(self):
        return bool(self.bit & 0x40)

    @property
    def developer_data(self):
        return bool(self.bit & 0x20)


    @property
    def local_message_type(self):
        local_message_type = self.bit & 0xF
        assert local_message_type in range(0,16)
        return local_message_type

@dataclass
class CompressedTimestampHeader(RecordHeader):
    @property
    def local_message_type(self):
        local_message_type = (self.bit >> 5) & 0x3
        assert local_message_type in range(0,4)
        return local_message_type

    @property
    def time_offset(self):
        return self.bit & 0x1F

@dataclass
class Record():
    header: RecordHeader

    def unpack(header, reader):
        if hasattr(header, "definition") and header.definition:
            message = DefinitionRecord.unpack(header, reader)
            message_definitions[header.local_message_type] = message
        else:
            message = DataRecord.unpack(header, reader)
            data_messages.append(message)
            if message.definition.profile:
                if message.definition.profile["name"] == "developer_data_id":
                    add_developer_data(message)
                elif message.definition.profile["name"] == "field_description":
                    add_developer_field_description(message)

        return message

   
@dataclass
class FieldBase():
    definition_number: int
    size: int

    @property
    def record(self):
        return profile.messages[self.global_message_number]


@dataclass
class FieldDefinition(FieldBase):
    _base_type: int
    global_message_number: int

    @property
    def profile(self):
        try:
            return profile.messages[self.global_message_number]["fields"][self.definition_number]
        except KeyError:
            return None

    @property
    def base_type(self):
        return profile.picker(profile.base_types, profile.dict(byte=self._base_type))[1]

    @property
    def type(self):
        if profile := self.profile:
            return profile["type"]
        return self.base_type


    @classmethod
    def unpack(cls, global_message_number, reader):
        field_definition_number, field_size, base_type_id = reader('3B')

        # TODO: why?
        bt = profile.picker(profile.base_types, profile.dict(byte=base_type_id))[1] 
        if field_size % bt["size"] != 0:
            base_type_id = profile.base_types['byte']['byte']

        return cls(field_definition_number, field_size, base_type_id, global_message_number)




@dataclass
class DeveloperFieldDefinition(FieldBase):
    developer_data_index: int
    profile: Any

    @property
    def base_type(self):
        return profile.base_types[self.profile['type']]

    @property
    def type(self):
        return self.base_type

    @classmethod
    def unpack(cls, global_message_number, reader):
        field_definition_number, field_size, developer_data_index = reader('3B')
        field = developer_data[developer_data_index][field_definition_number]
        return cls(field_definition_number, field_size, developer_data_index, field)


@dataclass
class DefinitionRecord(Record):
    global_message_number: int
    fields: list
    developer_fields: list
    _endian: int

    @property
    def profile(self):
        return profile.messages.get(self.global_message_number, None)

    @property
    def endian(self):
        return '>' if self._endian else '<'

    @classmethod
    def unpack(cls, header, reader):
        endian = reader('xB')
        reader = functools.partial(reader, endian='>' if endian else '<') 
        global_message_number, fields = reader('HB')
        field_definitions = [FieldDefinition.unpack(global_message_number, reader) for _ in range(fields)]
        developer_fields = []
        if header.developer_data:
            developer_fields = [DeveloperFieldDefinition.unpack(global_message_number, reader) for _ in range(reader('B'))]

        message = cls(header, global_message_number, field_definitions, developer_fields, endian)
        return message

@dataclass
class DataField():
    definition: Union[FieldDefinition, DeveloperFieldDefinition]
    raw: Any

    @property
    def type(self):
        type = self.definition.type
        if isinstance(type, str):
            type = profile.types.get(type, profile.base_types.get(type))
        return type

    @property
    def name(self):
        return self.definition.profile["name"] if self.definition.profile else f"unknown_{self.definition.definition_number}"

    @property
    def profile(self):
        return self.definition.profile

    @property
    def parser(self):
        return self.type["parser"]

    @property
    def values(self):
        return self.type.get("values", None)

    @property
    def data(self):
        base_type_parser = self.definition.base_type['parser']
        if isinstance(self.raw, tuple):
            data = tuple(self.parser(base_type_parser(_), self.values) for _ in self.raw)
            return data if any(data) else None
        return self.parser(base_type_parser(self.raw), self.values)


def field_reader(field, reader):
    base_type = field.base_type
    count = int(field.size/base_type["size"])
    fmt = f"{count}{base_type['fmt']}"
    raw_value = reader(fmt)
    return DataField(field, raw_value)

@dataclass
class DataRecord(Record):
    definition: DefinitionRecord
    fields: list

    @classmethod
    def unpack(cls, header, reader):
        definition = message_definitions[header.local_message_type]

        definition_fields = definition.fields + definition.developer_fields
        fields = [
            field_reader(field, functools.partial(reader, endian=definition.endian))
            for field in definition_fields
        ]

        return cls(header, definition, fields)


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



accs = defaultdict(lambda: defaultdict(int))

def accumulate(raw_value, message_definition, component):
    acc = accs[message_definition.global_message_number][component["num"]]
    max_value = (1 << component["bits"])
    max_mask = max_value - 1
    base_value = raw_value + (accs[message_definition.global_message_number][component["num"]] & ~max_mask)

    if raw_value < (accs[message_definition.global_message_number][component["num"]] & max_mask):
        base_value += max_value

    accs[message_definition.global_message_number][component["num"]] = base_value
    return base_value
 
def resolve_subfield(field_profile, message_profile, values):
    for subfield in field_profile.get("subfields", []):
        for reference_field in subfield.get("reference_fields", []):
            for fd in message_profile["fields"].values():
                for rv in values:
                    if fd["def_num"] == reference_field["def_num"] and reference_field["raw_value"] == rv:
                        return subfield, field_profile
    return field_profile, None

def print_fitr():
    out = []
    for idx, message in enumerate(data_messages, start=1):
        message_definition = message.definition
        try:
            message_profile = profile.messages[message_definition.global_message_number] if message_definition else None
        except KeyError:
            message_profile = {
                "name": f"unknown_{message_definition.global_message_number}",
                "fields": {}
            }

        raw_values = [field.raw for field in message.fields]
        out.append(f"{idx}. {message_profile['name']}")
        fields = {}
        for field in message.fields:
            field_profile = field.profile or {  # Make a fake field_profile
                    "name": f"unknown_{field.definition.definition_number}",
                    "units": None,
                    "type": "byte",
                    "subfields": [],
                    "components": []
            }
            field_profile, parent_field_profile = resolve_subfield(field_profile, message_profile, raw_values)
            if "components" in field_profile and field_profile["components"]:
                fields[f"{field_profile['name']}"] = ""
                for component in field_profile['components']:
                    try:
                        component_field_data = profile.parse_component_value(component, field.raw)
                    except ValueError:
                        continue
                    if component["accumulate"] and component_field_data is not None:
                        component_field_data = accumulate(component_field_data, message_definition, component)

                    component_field_profile = message_profile["fields"][component["num"]]
                    component_field_data = apply_scale_offset(component_field_profile, component_field_data)

                    component_field, component_parent_field = resolve_subfield(component_field_profile, message_profile, raw_values)

                    unit = f" [{component_field_profile['units']}]" if component_field_profile['units'] else ""
                    fields[f"{component_field_profile['name']}"] = f"{apply_scale_offset(component_field_profile, component_field_data)}{unit}"

            unit = f" [{field_profile['units']}]" if field_profile['units'] else ""
            if field_profile["type"] in profile.types:
                value = profile.types.get(field_profile["type"])["parser"](
                    apply_scale_offset(field_profile, field.data),
                    profile.types.get(field_profile["type"])["values"]
                )
            else:
                value = apply_scale_offset(field_profile, field.data)
            fields[f"{field_profile['name']}"] = f"{value}{unit}"
        for k in sorted(fields.keys()):
            out.append(f" * {k}: {fields[k]}")
        out.append("")

    print("\n".join(out))


class NewFitFile(FitFile):
    def _read_message(self):
        header = RecordHeader.unpack(self._fitfile.read)
        return Record.unpack(header, self._fitfile.read)

class LFitR():
    def __init__(self, fitfile):
        self._memory = FitFileMemory(fitfile)

    def get_fitfiles(self):
        while self._memory.tell() < len(self._memory):
            ff = NewFitFile(self._memory.copy())
            for message in ff.messages():
                #print(f"{message!r}")
                ...

            print_fitr()
            self._memory.seek(self._memory.tell() + ff.file_size)


def run():
    fitr = LFitR(sys.argv[-1])
    fitr.get_fitfiles()


