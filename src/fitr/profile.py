# -*- coding: utf-8 -*-

import struct

class BaseTypeParsers():
    def enum(v):
        return None if v == 0xFF else v

    def sint8(v):
        return None if v == 0x7F else v

    def uint8(v):
        return None if v == 0xFF else v

    def string(v):
        try:
            s = v[:v.index('\0x00')]
        except ValueError:
            s = v
        return s.decode('utf-8', errors=replace) or None

    def uint8z(v):
        return None if v == 0x0 else v

    def byte(v):
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
            elif isinstance(v, type(lambda x: x)) and v.__qualname__.startswith("BaseTypeParsers."):
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
        out.append(f"{self.__class__.__name__}("),
        out.extend(
            f"    {k[1:] if k.startswith('_') else k}={render(v)}," for k, v in self.__dict__.items() if (
                (isinstance(v, Map) and v)
                or (not isinstance(v, Map) and v is not None)
            )
        )
        out.append(f")"),
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



class BaseType(Base):
    def __init__(self, name, fmt, parse=lambda x: x, size=None, byte=None, type_num=None):
        self.name = name
        self.fmt = fmt
        self.parse = parse
        self.byte = byte
        self.type_num = type_num
        self.size = size if size is not None else struct.calcsize(self.fmt)



class Type(Base):
    def __init__(self, name, base_type, values=None, comment=None):
        assert isinstance(name, str)
        assert isinstance(base_type, str)
        self.name = name
        self.base_type = base_type
        self.values = values or Map(TypeValue, dict, int)
        self.comment = comment



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



class FieldBase(Base):
    def __init__(self, name, type, def_num=None, scale=None, offset=None, units=None, components=None, comment=None):
        self.name = name
        self.type = type
        self.def_num = def_num

        self.components = components or Map(Component, list)
 
        if components and not str(scale).isdigit():
            self.scale = self.offset = self.units = None
        else:
            self.scale = scale
            self.offset = offset
            self.units = units
        self.comment = comment



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



base_types = Map(
    map={0: BaseType(
    name='enum',
    fmt='B',
    parse=BaseTypeParsers.enum,
    byte=0,
    type_num=0,
    size=1,
), 1: BaseType(
    name='sint8',
    fmt='b',
    parse=BaseTypeParsers.sint8,
    byte=1,
    type_num=1,
    size=1,
), 2: BaseType(
    name='uint8',
    fmt='B',
    parse=BaseTypeParsers.uint8,
    byte=2,
    type_num=2,
    size=1,
), 7: BaseType(
    name='string',
    fmt='s',
    parse=BaseTypeParsers.string,
    byte=7,
    type_num=7,
    size=1,
), 10: BaseType(
    name='uint8z',
    fmt='B',
    parse=BaseTypeParsers.uint8z,
    byte=10,
    type_num=10,
    size=1,
), 13: BaseType(
    name='byte',
    fmt='B',
    parse=BaseTypeParsers.byte,
    byte=13,
    type_num=13,
    size=1,
), 131: BaseType(
    name='sint16',
    fmt='h',
    parse=BaseTypeParsers.sint16,
    byte=131,
    type_num=3,
    size=2,
), 132: BaseType(
    name='uint16',
    fmt='H',
    parse=BaseTypeParsers.uint16,
    byte=132,
    type_num=4,
    size=2,
), 133: BaseType(
    name='sint32',
    fmt='i',
    parse=BaseTypeParsers.sint32,
    byte=133,
    type_num=5,
    size=4,
), 134: BaseType(
    name='uint32',
    fmt='I',
    parse=BaseTypeParsers.uint32,
    byte=134,
    type_num=6,
    size=4,
), 136: BaseType(
    name='float32',
    fmt='f',
    parse=BaseTypeParsers.float32,
    byte=136,
    type_num=8,
    size=4,
), 137: BaseType(
    name='float64',
    fmt='d',
    parse=BaseTypeParsers.float64,
    byte=137,
    type_num=9,
    size=8,
), 139: BaseType(
    name='uint16z',
    fmt='H',
    parse=BaseTypeParsers.uint16z,
    byte=139,
    type_num=11,
    size=2,
), 140: BaseType(
    name='uint32z',
    fmt='I',
    parse=BaseTypeParsers.uint32z,
    byte=140,
    type_num=12,
    size=4,
), 142: BaseType(
    name='sint64',
    fmt='q',
    parse=BaseTypeParsers.sint64,
    byte=142,
    type_num=14,
    size=8,
), 143: BaseType(
    name='uint64',
    fmt='Q',
    parse=BaseTypeParsers.uint64,
    byte=143,
    type_num=15,
    size=8,
), 144: BaseType(
    name='uint64z',
    fmt='Q',
    parse=BaseTypeParsers.uint64z,
    byte=144,
    type_num=16,
    size=8,
)},
    map_type=dict,
    value_type=BaseType,
    key_type=int,
)
types = Map(
    map={'file': Type(
    name='file',
    base_type='enum',
    values=Map(
    map={1: TypeValue(
    name='device',
    value=1,
    comment='Read only, single file. Must be in root directory.',
), 2: TypeValue(
    name='settings',
    value=2,
    comment='Read/write, single file. Directory=Settings',
), 3: TypeValue(
    name='sport',
    value=3,
    comment='Read/write, multiple files, file number = sport type. Directory=Sports',
), 4: TypeValue(
    name='activity',
    value=4,
    comment='Read/erase, multiple files. Directory=Activities',
), 5: TypeValue(
    name='workout',
    value=5,
    comment='Read/write/erase, multiple files. Directory=Workouts',
), 6: TypeValue(
    name='course',
    value=6,
    comment='Read/write/erase, multiple files. Directory=Courses',
), 7: TypeValue(
    name='schedules',
    value=7,
    comment='Read/write, single file. Directory=Schedules',
), 9: TypeValue(
    name='weight',
    value=9,
    comment='Read only, single file. Circular buffer. All message definitions at start of file. Directory=Weight',
), 10: TypeValue(
    name='totals',
    value=10,
    comment='Read only, single file. Directory=Totals',
), 11: TypeValue(
    name='goals',
    value=11,
    comment='Read/write, single file. Directory=Goals',
), 14: TypeValue(
    name='blood_pressure',
    value=14,
    comment='Read only. Directory=Blood Pressure',
), 15: TypeValue(
    name='monitoring_a',
    value=15,
    comment='Read only. Directory=Monitoring. File number=sub type.',
), 20: TypeValue(
    name='activity_summary',
    value=20,
    comment='Read/erase, multiple files. Directory=Activities',
), 28: TypeValue(
    name='monitoring_daily',
    value=28,
), 32: TypeValue(
    name='monitoring_b',
    value=32,
    comment='Read only. Directory=Monitoring. File number=identifier',
), 34: TypeValue(
    name='segment',
    value=34,
    comment='Read/write/erase. Multiple Files.  Directory=Segments',
), 35: TypeValue(
    name='segment_list',
    value=35,
    comment='Read/write/erase. Single File.  Directory=Segments',
), 40: TypeValue(
    name='exd_configuration',
    value=40,
    comment='Read/write/erase. Single File. Directory=Settings',
), 247: TypeValue(
    name='mfg_range_min',
    value=247,
    comment='0xF7 - 0xFE reserved for manufacturer specific file types',
), 248: TypeValue(
    name='mfg_range_248',
    value=248,
    comment='0xF7 - 0xFE reserved for manufacturer specific file types',
), 249: TypeValue(
    name='mfg_range_249',
    value=249,
    comment='0xF7 - 0xFE reserved for manufacturer specific file types',
), 250: TypeValue(
    name='mfg_range_250',
    value=250,
    comment='0xF7 - 0xFE reserved for manufacturer specific file types',
), 251: TypeValue(
    name='mfg_range_251',
    value=251,
    comment='0xF7 - 0xFE reserved for manufacturer specific file types',
), 252: TypeValue(
    name='mfg_range_252',
    value=252,
    comment='0xF7 - 0xFE reserved for manufacturer specific file types',
), 253: TypeValue(
    name='mfg_range_253',
    value=253,
    comment='0xF7 - 0xFE reserved for manufacturer specific file types',
), 254: TypeValue(
    name='mfg_range_max',
    value=254,
    comment='0xF7 - 0xFE reserved for manufacturer specific file types',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'mesg_num': Type(
    name='mesg_num',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='file_id',
    value=0,
), 1: TypeValue(
    name='capabilities',
    value=1,
), 2: TypeValue(
    name='device_settings',
    value=2,
), 3: TypeValue(
    name='user_profile',
    value=3,
), 4: TypeValue(
    name='hrm_profile',
    value=4,
), 5: TypeValue(
    name='sdm_profile',
    value=5,
), 6: TypeValue(
    name='bike_profile',
    value=6,
), 7: TypeValue(
    name='zones_target',
    value=7,
), 8: TypeValue(
    name='hr_zone',
    value=8,
), 9: TypeValue(
    name='power_zone',
    value=9,
), 10: TypeValue(
    name='met_zone',
    value=10,
), 12: TypeValue(
    name='sport',
    value=12,
), 15: TypeValue(
    name='goal',
    value=15,
), 18: TypeValue(
    name='session',
    value=18,
), 19: TypeValue(
    name='lap',
    value=19,
), 20: TypeValue(
    name='record',
    value=20,
), 21: TypeValue(
    name='event',
    value=21,
), 23: TypeValue(
    name='device_info',
    value=23,
), 26: TypeValue(
    name='workout',
    value=26,
), 27: TypeValue(
    name='workout_step',
    value=27,
), 28: TypeValue(
    name='schedule',
    value=28,
), 30: TypeValue(
    name='weight_scale',
    value=30,
), 31: TypeValue(
    name='course',
    value=31,
), 32: TypeValue(
    name='course_point',
    value=32,
), 33: TypeValue(
    name='totals',
    value=33,
), 34: TypeValue(
    name='activity',
    value=34,
), 35: TypeValue(
    name='software',
    value=35,
), 37: TypeValue(
    name='file_capabilities',
    value=37,
), 38: TypeValue(
    name='mesg_capabilities',
    value=38,
), 39: TypeValue(
    name='field_capabilities',
    value=39,
), 49: TypeValue(
    name='file_creator',
    value=49,
), 51: TypeValue(
    name='blood_pressure',
    value=51,
), 53: TypeValue(
    name='speed_zone',
    value=53,
), 55: TypeValue(
    name='monitoring',
    value=55,
), 72: TypeValue(
    name='training_file',
    value=72,
), 78: TypeValue(
    name='hrv',
    value=78,
), 80: TypeValue(
    name='ant_rx',
    value=80,
), 81: TypeValue(
    name='ant_tx',
    value=81,
), 82: TypeValue(
    name='ant_channel_id',
    value=82,
), 101: TypeValue(
    name='length',
    value=101,
), 103: TypeValue(
    name='monitoring_info',
    value=103,
), 105: TypeValue(
    name='pad',
    value=105,
), 106: TypeValue(
    name='slave_device',
    value=106,
), 127: TypeValue(
    name='connectivity',
    value=127,
), 128: TypeValue(
    name='weather_conditions',
    value=128,
), 129: TypeValue(
    name='weather_alert',
    value=129,
), 131: TypeValue(
    name='cadence_zone',
    value=131,
), 132: TypeValue(
    name='hr',
    value=132,
), 142: TypeValue(
    name='segment_lap',
    value=142,
), 145: TypeValue(
    name='memo_glob',
    value=145,
), 148: TypeValue(
    name='segment_id',
    value=148,
), 149: TypeValue(
    name='segment_leaderboard_entry',
    value=149,
), 150: TypeValue(
    name='segment_point',
    value=150,
), 151: TypeValue(
    name='segment_file',
    value=151,
), 158: TypeValue(
    name='workout_session',
    value=158,
), 159: TypeValue(
    name='watchface_settings',
    value=159,
), 160: TypeValue(
    name='gps_metadata',
    value=160,
), 161: TypeValue(
    name='camera_event',
    value=161,
), 162: TypeValue(
    name='timestamp_correlation',
    value=162,
), 164: TypeValue(
    name='gyroscope_data',
    value=164,
), 165: TypeValue(
    name='accelerometer_data',
    value=165,
), 167: TypeValue(
    name='three_d_sensor_calibration',
    value=167,
), 169: TypeValue(
    name='video_frame',
    value=169,
), 174: TypeValue(
    name='obdii_data',
    value=174,
), 177: TypeValue(
    name='nmea_sentence',
    value=177,
), 178: TypeValue(
    name='aviation_attitude',
    value=178,
), 184: TypeValue(
    name='video',
    value=184,
), 185: TypeValue(
    name='video_title',
    value=185,
), 186: TypeValue(
    name='video_description',
    value=186,
), 187: TypeValue(
    name='video_clip',
    value=187,
), 188: TypeValue(
    name='ohr_settings',
    value=188,
), 200: TypeValue(
    name='exd_screen_configuration',
    value=200,
), 201: TypeValue(
    name='exd_data_field_configuration',
    value=201,
), 202: TypeValue(
    name='exd_data_concept_configuration',
    value=202,
), 206: TypeValue(
    name='field_description',
    value=206,
), 207: TypeValue(
    name='developer_data_id',
    value=207,
), 208: TypeValue(
    name='magnetometer_data',
    value=208,
), 209: TypeValue(
    name='barometer_data',
    value=209,
), 210: TypeValue(
    name='one_d_sensor_calibration',
    value=210,
), 225: TypeValue(
    name='set',
    value=225,
), 227: TypeValue(
    name='stress_level',
    value=227,
), 258: TypeValue(
    name='dive_settings',
    value=258,
), 259: TypeValue(
    name='dive_gas',
    value=259,
), 262: TypeValue(
    name='dive_alarm',
    value=262,
), 264: TypeValue(
    name='exercise_title',
    value=264,
), 268: TypeValue(
    name='dive_summary',
    value=268,
), 285: TypeValue(
    name='jump',
    value=285,
), 317: TypeValue(
    name='climb_pro',
    value=317,
), 65280: TypeValue(
    name='mfg_range_min',
    value=65280,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65281: TypeValue(
    name='mfg_range_65281',
    value=65281,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65282: TypeValue(
    name='mfg_range_65282',
    value=65282,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65283: TypeValue(
    name='mfg_range_65283',
    value=65283,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65284: TypeValue(
    name='mfg_range_65284',
    value=65284,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65285: TypeValue(
    name='mfg_range_65285',
    value=65285,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65286: TypeValue(
    name='mfg_range_65286',
    value=65286,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65287: TypeValue(
    name='mfg_range_65287',
    value=65287,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65288: TypeValue(
    name='mfg_range_65288',
    value=65288,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65289: TypeValue(
    name='mfg_range_65289',
    value=65289,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65290: TypeValue(
    name='mfg_range_65290',
    value=65290,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65291: TypeValue(
    name='mfg_range_65291',
    value=65291,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65292: TypeValue(
    name='mfg_range_65292',
    value=65292,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65293: TypeValue(
    name='mfg_range_65293',
    value=65293,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65294: TypeValue(
    name='mfg_range_65294',
    value=65294,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65295: TypeValue(
    name='mfg_range_65295',
    value=65295,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65296: TypeValue(
    name='mfg_range_65296',
    value=65296,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65297: TypeValue(
    name='mfg_range_65297',
    value=65297,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65298: TypeValue(
    name='mfg_range_65298',
    value=65298,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65299: TypeValue(
    name='mfg_range_65299',
    value=65299,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65300: TypeValue(
    name='mfg_range_65300',
    value=65300,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65301: TypeValue(
    name='mfg_range_65301',
    value=65301,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65302: TypeValue(
    name='mfg_range_65302',
    value=65302,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65303: TypeValue(
    name='mfg_range_65303',
    value=65303,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65304: TypeValue(
    name='mfg_range_65304',
    value=65304,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65305: TypeValue(
    name='mfg_range_65305',
    value=65305,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65306: TypeValue(
    name='mfg_range_65306',
    value=65306,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65307: TypeValue(
    name='mfg_range_65307',
    value=65307,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65308: TypeValue(
    name='mfg_range_65308',
    value=65308,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65309: TypeValue(
    name='mfg_range_65309',
    value=65309,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65310: TypeValue(
    name='mfg_range_65310',
    value=65310,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65311: TypeValue(
    name='mfg_range_65311',
    value=65311,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65312: TypeValue(
    name='mfg_range_65312',
    value=65312,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65313: TypeValue(
    name='mfg_range_65313',
    value=65313,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65314: TypeValue(
    name='mfg_range_65314',
    value=65314,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65315: TypeValue(
    name='mfg_range_65315',
    value=65315,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65316: TypeValue(
    name='mfg_range_65316',
    value=65316,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65317: TypeValue(
    name='mfg_range_65317',
    value=65317,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65318: TypeValue(
    name='mfg_range_65318',
    value=65318,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65319: TypeValue(
    name='mfg_range_65319',
    value=65319,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65320: TypeValue(
    name='mfg_range_65320',
    value=65320,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65321: TypeValue(
    name='mfg_range_65321',
    value=65321,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65322: TypeValue(
    name='mfg_range_65322',
    value=65322,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65323: TypeValue(
    name='mfg_range_65323',
    value=65323,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65324: TypeValue(
    name='mfg_range_65324',
    value=65324,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65325: TypeValue(
    name='mfg_range_65325',
    value=65325,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65326: TypeValue(
    name='mfg_range_65326',
    value=65326,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65327: TypeValue(
    name='mfg_range_65327',
    value=65327,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65328: TypeValue(
    name='mfg_range_65328',
    value=65328,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65329: TypeValue(
    name='mfg_range_65329',
    value=65329,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65330: TypeValue(
    name='mfg_range_65330',
    value=65330,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65331: TypeValue(
    name='mfg_range_65331',
    value=65331,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65332: TypeValue(
    name='mfg_range_65332',
    value=65332,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65333: TypeValue(
    name='mfg_range_65333',
    value=65333,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65334: TypeValue(
    name='mfg_range_65334',
    value=65334,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65335: TypeValue(
    name='mfg_range_65335',
    value=65335,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65336: TypeValue(
    name='mfg_range_65336',
    value=65336,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65337: TypeValue(
    name='mfg_range_65337',
    value=65337,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65338: TypeValue(
    name='mfg_range_65338',
    value=65338,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65339: TypeValue(
    name='mfg_range_65339',
    value=65339,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65340: TypeValue(
    name='mfg_range_65340',
    value=65340,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65341: TypeValue(
    name='mfg_range_65341',
    value=65341,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65342: TypeValue(
    name='mfg_range_65342',
    value=65342,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65343: TypeValue(
    name='mfg_range_65343',
    value=65343,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65344: TypeValue(
    name='mfg_range_65344',
    value=65344,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65345: TypeValue(
    name='mfg_range_65345',
    value=65345,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65346: TypeValue(
    name='mfg_range_65346',
    value=65346,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65347: TypeValue(
    name='mfg_range_65347',
    value=65347,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65348: TypeValue(
    name='mfg_range_65348',
    value=65348,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65349: TypeValue(
    name='mfg_range_65349',
    value=65349,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65350: TypeValue(
    name='mfg_range_65350',
    value=65350,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65351: TypeValue(
    name='mfg_range_65351',
    value=65351,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65352: TypeValue(
    name='mfg_range_65352',
    value=65352,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65353: TypeValue(
    name='mfg_range_65353',
    value=65353,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65354: TypeValue(
    name='mfg_range_65354',
    value=65354,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65355: TypeValue(
    name='mfg_range_65355',
    value=65355,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65356: TypeValue(
    name='mfg_range_65356',
    value=65356,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65357: TypeValue(
    name='mfg_range_65357',
    value=65357,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65358: TypeValue(
    name='mfg_range_65358',
    value=65358,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65359: TypeValue(
    name='mfg_range_65359',
    value=65359,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65360: TypeValue(
    name='mfg_range_65360',
    value=65360,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65361: TypeValue(
    name='mfg_range_65361',
    value=65361,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65362: TypeValue(
    name='mfg_range_65362',
    value=65362,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65363: TypeValue(
    name='mfg_range_65363',
    value=65363,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65364: TypeValue(
    name='mfg_range_65364',
    value=65364,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65365: TypeValue(
    name='mfg_range_65365',
    value=65365,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65366: TypeValue(
    name='mfg_range_65366',
    value=65366,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65367: TypeValue(
    name='mfg_range_65367',
    value=65367,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65368: TypeValue(
    name='mfg_range_65368',
    value=65368,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65369: TypeValue(
    name='mfg_range_65369',
    value=65369,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65370: TypeValue(
    name='mfg_range_65370',
    value=65370,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65371: TypeValue(
    name='mfg_range_65371',
    value=65371,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65372: TypeValue(
    name='mfg_range_65372',
    value=65372,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65373: TypeValue(
    name='mfg_range_65373',
    value=65373,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65374: TypeValue(
    name='mfg_range_65374',
    value=65374,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65375: TypeValue(
    name='mfg_range_65375',
    value=65375,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65376: TypeValue(
    name='mfg_range_65376',
    value=65376,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65377: TypeValue(
    name='mfg_range_65377',
    value=65377,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65378: TypeValue(
    name='mfg_range_65378',
    value=65378,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65379: TypeValue(
    name='mfg_range_65379',
    value=65379,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65380: TypeValue(
    name='mfg_range_65380',
    value=65380,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65381: TypeValue(
    name='mfg_range_65381',
    value=65381,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65382: TypeValue(
    name='mfg_range_65382',
    value=65382,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65383: TypeValue(
    name='mfg_range_65383',
    value=65383,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65384: TypeValue(
    name='mfg_range_65384',
    value=65384,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65385: TypeValue(
    name='mfg_range_65385',
    value=65385,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65386: TypeValue(
    name='mfg_range_65386',
    value=65386,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65387: TypeValue(
    name='mfg_range_65387',
    value=65387,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65388: TypeValue(
    name='mfg_range_65388',
    value=65388,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65389: TypeValue(
    name='mfg_range_65389',
    value=65389,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65390: TypeValue(
    name='mfg_range_65390',
    value=65390,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65391: TypeValue(
    name='mfg_range_65391',
    value=65391,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65392: TypeValue(
    name='mfg_range_65392',
    value=65392,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65393: TypeValue(
    name='mfg_range_65393',
    value=65393,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65394: TypeValue(
    name='mfg_range_65394',
    value=65394,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65395: TypeValue(
    name='mfg_range_65395',
    value=65395,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65396: TypeValue(
    name='mfg_range_65396',
    value=65396,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65397: TypeValue(
    name='mfg_range_65397',
    value=65397,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65398: TypeValue(
    name='mfg_range_65398',
    value=65398,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65399: TypeValue(
    name='mfg_range_65399',
    value=65399,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65400: TypeValue(
    name='mfg_range_65400',
    value=65400,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65401: TypeValue(
    name='mfg_range_65401',
    value=65401,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65402: TypeValue(
    name='mfg_range_65402',
    value=65402,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65403: TypeValue(
    name='mfg_range_65403',
    value=65403,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65404: TypeValue(
    name='mfg_range_65404',
    value=65404,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65405: TypeValue(
    name='mfg_range_65405',
    value=65405,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65406: TypeValue(
    name='mfg_range_65406',
    value=65406,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65407: TypeValue(
    name='mfg_range_65407',
    value=65407,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65408: TypeValue(
    name='mfg_range_65408',
    value=65408,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65409: TypeValue(
    name='mfg_range_65409',
    value=65409,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65410: TypeValue(
    name='mfg_range_65410',
    value=65410,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65411: TypeValue(
    name='mfg_range_65411',
    value=65411,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65412: TypeValue(
    name='mfg_range_65412',
    value=65412,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65413: TypeValue(
    name='mfg_range_65413',
    value=65413,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65414: TypeValue(
    name='mfg_range_65414',
    value=65414,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65415: TypeValue(
    name='mfg_range_65415',
    value=65415,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65416: TypeValue(
    name='mfg_range_65416',
    value=65416,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65417: TypeValue(
    name='mfg_range_65417',
    value=65417,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65418: TypeValue(
    name='mfg_range_65418',
    value=65418,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65419: TypeValue(
    name='mfg_range_65419',
    value=65419,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65420: TypeValue(
    name='mfg_range_65420',
    value=65420,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65421: TypeValue(
    name='mfg_range_65421',
    value=65421,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65422: TypeValue(
    name='mfg_range_65422',
    value=65422,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65423: TypeValue(
    name='mfg_range_65423',
    value=65423,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65424: TypeValue(
    name='mfg_range_65424',
    value=65424,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65425: TypeValue(
    name='mfg_range_65425',
    value=65425,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65426: TypeValue(
    name='mfg_range_65426',
    value=65426,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65427: TypeValue(
    name='mfg_range_65427',
    value=65427,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65428: TypeValue(
    name='mfg_range_65428',
    value=65428,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65429: TypeValue(
    name='mfg_range_65429',
    value=65429,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65430: TypeValue(
    name='mfg_range_65430',
    value=65430,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65431: TypeValue(
    name='mfg_range_65431',
    value=65431,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65432: TypeValue(
    name='mfg_range_65432',
    value=65432,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65433: TypeValue(
    name='mfg_range_65433',
    value=65433,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65434: TypeValue(
    name='mfg_range_65434',
    value=65434,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65435: TypeValue(
    name='mfg_range_65435',
    value=65435,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65436: TypeValue(
    name='mfg_range_65436',
    value=65436,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65437: TypeValue(
    name='mfg_range_65437',
    value=65437,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65438: TypeValue(
    name='mfg_range_65438',
    value=65438,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65439: TypeValue(
    name='mfg_range_65439',
    value=65439,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65440: TypeValue(
    name='mfg_range_65440',
    value=65440,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65441: TypeValue(
    name='mfg_range_65441',
    value=65441,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65442: TypeValue(
    name='mfg_range_65442',
    value=65442,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65443: TypeValue(
    name='mfg_range_65443',
    value=65443,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65444: TypeValue(
    name='mfg_range_65444',
    value=65444,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65445: TypeValue(
    name='mfg_range_65445',
    value=65445,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65446: TypeValue(
    name='mfg_range_65446',
    value=65446,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65447: TypeValue(
    name='mfg_range_65447',
    value=65447,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65448: TypeValue(
    name='mfg_range_65448',
    value=65448,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65449: TypeValue(
    name='mfg_range_65449',
    value=65449,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65450: TypeValue(
    name='mfg_range_65450',
    value=65450,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65451: TypeValue(
    name='mfg_range_65451',
    value=65451,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65452: TypeValue(
    name='mfg_range_65452',
    value=65452,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65453: TypeValue(
    name='mfg_range_65453',
    value=65453,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65454: TypeValue(
    name='mfg_range_65454',
    value=65454,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65455: TypeValue(
    name='mfg_range_65455',
    value=65455,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65456: TypeValue(
    name='mfg_range_65456',
    value=65456,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65457: TypeValue(
    name='mfg_range_65457',
    value=65457,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65458: TypeValue(
    name='mfg_range_65458',
    value=65458,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65459: TypeValue(
    name='mfg_range_65459',
    value=65459,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65460: TypeValue(
    name='mfg_range_65460',
    value=65460,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65461: TypeValue(
    name='mfg_range_65461',
    value=65461,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65462: TypeValue(
    name='mfg_range_65462',
    value=65462,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65463: TypeValue(
    name='mfg_range_65463',
    value=65463,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65464: TypeValue(
    name='mfg_range_65464',
    value=65464,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65465: TypeValue(
    name='mfg_range_65465',
    value=65465,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65466: TypeValue(
    name='mfg_range_65466',
    value=65466,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65467: TypeValue(
    name='mfg_range_65467',
    value=65467,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65468: TypeValue(
    name='mfg_range_65468',
    value=65468,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65469: TypeValue(
    name='mfg_range_65469',
    value=65469,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65470: TypeValue(
    name='mfg_range_65470',
    value=65470,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65471: TypeValue(
    name='mfg_range_65471',
    value=65471,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65472: TypeValue(
    name='mfg_range_65472',
    value=65472,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65473: TypeValue(
    name='mfg_range_65473',
    value=65473,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65474: TypeValue(
    name='mfg_range_65474',
    value=65474,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65475: TypeValue(
    name='mfg_range_65475',
    value=65475,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65476: TypeValue(
    name='mfg_range_65476',
    value=65476,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65477: TypeValue(
    name='mfg_range_65477',
    value=65477,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65478: TypeValue(
    name='mfg_range_65478',
    value=65478,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65479: TypeValue(
    name='mfg_range_65479',
    value=65479,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65480: TypeValue(
    name='mfg_range_65480',
    value=65480,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65481: TypeValue(
    name='mfg_range_65481',
    value=65481,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65482: TypeValue(
    name='mfg_range_65482',
    value=65482,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65483: TypeValue(
    name='mfg_range_65483',
    value=65483,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65484: TypeValue(
    name='mfg_range_65484',
    value=65484,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65485: TypeValue(
    name='mfg_range_65485',
    value=65485,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65486: TypeValue(
    name='mfg_range_65486',
    value=65486,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65487: TypeValue(
    name='mfg_range_65487',
    value=65487,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65488: TypeValue(
    name='mfg_range_65488',
    value=65488,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65489: TypeValue(
    name='mfg_range_65489',
    value=65489,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65490: TypeValue(
    name='mfg_range_65490',
    value=65490,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65491: TypeValue(
    name='mfg_range_65491',
    value=65491,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65492: TypeValue(
    name='mfg_range_65492',
    value=65492,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65493: TypeValue(
    name='mfg_range_65493',
    value=65493,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65494: TypeValue(
    name='mfg_range_65494',
    value=65494,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65495: TypeValue(
    name='mfg_range_65495',
    value=65495,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65496: TypeValue(
    name='mfg_range_65496',
    value=65496,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65497: TypeValue(
    name='mfg_range_65497',
    value=65497,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65498: TypeValue(
    name='mfg_range_65498',
    value=65498,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65499: TypeValue(
    name='mfg_range_65499',
    value=65499,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65500: TypeValue(
    name='mfg_range_65500',
    value=65500,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65501: TypeValue(
    name='mfg_range_65501',
    value=65501,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65502: TypeValue(
    name='mfg_range_65502',
    value=65502,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65503: TypeValue(
    name='mfg_range_65503',
    value=65503,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65504: TypeValue(
    name='mfg_range_65504',
    value=65504,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65505: TypeValue(
    name='mfg_range_65505',
    value=65505,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65506: TypeValue(
    name='mfg_range_65506',
    value=65506,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65507: TypeValue(
    name='mfg_range_65507',
    value=65507,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65508: TypeValue(
    name='mfg_range_65508',
    value=65508,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65509: TypeValue(
    name='mfg_range_65509',
    value=65509,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65510: TypeValue(
    name='mfg_range_65510',
    value=65510,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65511: TypeValue(
    name='mfg_range_65511',
    value=65511,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65512: TypeValue(
    name='mfg_range_65512',
    value=65512,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65513: TypeValue(
    name='mfg_range_65513',
    value=65513,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65514: TypeValue(
    name='mfg_range_65514',
    value=65514,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65515: TypeValue(
    name='mfg_range_65515',
    value=65515,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65516: TypeValue(
    name='mfg_range_65516',
    value=65516,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65517: TypeValue(
    name='mfg_range_65517',
    value=65517,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65518: TypeValue(
    name='mfg_range_65518',
    value=65518,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65519: TypeValue(
    name='mfg_range_65519',
    value=65519,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65520: TypeValue(
    name='mfg_range_65520',
    value=65520,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65521: TypeValue(
    name='mfg_range_65521',
    value=65521,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65522: TypeValue(
    name='mfg_range_65522',
    value=65522,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65523: TypeValue(
    name='mfg_range_65523',
    value=65523,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65524: TypeValue(
    name='mfg_range_65524',
    value=65524,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65525: TypeValue(
    name='mfg_range_65525',
    value=65525,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65526: TypeValue(
    name='mfg_range_65526',
    value=65526,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65527: TypeValue(
    name='mfg_range_65527',
    value=65527,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65528: TypeValue(
    name='mfg_range_65528',
    value=65528,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65529: TypeValue(
    name='mfg_range_65529',
    value=65529,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65530: TypeValue(
    name='mfg_range_65530',
    value=65530,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65531: TypeValue(
    name='mfg_range_65531',
    value=65531,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65532: TypeValue(
    name='mfg_range_65532',
    value=65532,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65533: TypeValue(
    name='mfg_range_65533',
    value=65533,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
), 65534: TypeValue(
    name='mfg_range_max',
    value=65534,
    comment='0xFF00 - 0xFFFE reserved for manufacturer specific messages',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'checksum': Type(
    name='checksum',
    base_type='uint8',
    values=Map(
    map={0: TypeValue(
    name='clear',
    value=0,
    comment='Allows clear of checksum for flash memory where can only write 1 to 0 without erasing sector.',
), 1: TypeValue(
    name='ok',
    value=1,
    comment='Set to mark checksum as valid if computes to invalid values 0 or 0xFF.  Checksum can also be set to ok to save encoding computation time.',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'file_flags': Type(
    name='file_flags',
    base_type='uint8z',
    values=Map(
    map={2: TypeValue(
    name='read',
    value=2,
), 4: TypeValue(
    name='write',
    value=4,
), 8: TypeValue(
    name='erase',
    value=8,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'mesg_count': Type(
    name='mesg_count',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='num_per_file',
    value=0,
), 1: TypeValue(
    name='max_per_file',
    value=1,
), 2: TypeValue(
    name='max_per_file_type',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'date_time': Type(
    name='date_time',
    base_type='uint32',
    values=Map(
    map={268435456: TypeValue(
    name='min',
    value=268435456,
    comment='if date_time is < 0x10000000 then it is system time (seconds from device power on)',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'local_date_time': Type(
    name='local_date_time',
    base_type='uint32',
    values=Map(
    map={268435456: TypeValue(
    name='min',
    value=268435456,
    comment='if date_time is < 0x10000000 then it is system time (seconds from device power on)',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'message_index': Type(
    name='message_index',
    base_type='uint16',
    values=Map(
    map={32768: TypeValue(
    name='selected',
    value=32768,
    comment='message is selected if set',
), 28672: TypeValue(
    name='reserved',
    value=28672,
    comment='reserved (default 0)',
), 4095: TypeValue(
    name='mask',
    value=4095,
    comment='index',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'device_index': Type(
    name='device_index',
    base_type='uint8',
    values=Map(
    map={0: TypeValue(
    name='creator',
    value=0,
    comment='Creator of the file is always device index 0.',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'gender': Type(
    name='gender',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='female',
    value=0,
), 1: TypeValue(
    name='male',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'language': Type(
    name='language',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='english',
    value=0,
), 1: TypeValue(
    name='french',
    value=1,
), 2: TypeValue(
    name='italian',
    value=2,
), 3: TypeValue(
    name='german',
    value=3,
), 4: TypeValue(
    name='spanish',
    value=4,
), 5: TypeValue(
    name='croatian',
    value=5,
), 6: TypeValue(
    name='czech',
    value=6,
), 7: TypeValue(
    name='danish',
    value=7,
), 8: TypeValue(
    name='dutch',
    value=8,
), 9: TypeValue(
    name='finnish',
    value=9,
), 10: TypeValue(
    name='greek',
    value=10,
), 11: TypeValue(
    name='hungarian',
    value=11,
), 12: TypeValue(
    name='norwegian',
    value=12,
), 13: TypeValue(
    name='polish',
    value=13,
), 14: TypeValue(
    name='portuguese',
    value=14,
), 15: TypeValue(
    name='slovakian',
    value=15,
), 16: TypeValue(
    name='slovenian',
    value=16,
), 17: TypeValue(
    name='swedish',
    value=17,
), 18: TypeValue(
    name='russian',
    value=18,
), 19: TypeValue(
    name='turkish',
    value=19,
), 20: TypeValue(
    name='latvian',
    value=20,
), 21: TypeValue(
    name='ukrainian',
    value=21,
), 22: TypeValue(
    name='arabic',
    value=22,
), 23: TypeValue(
    name='farsi',
    value=23,
), 24: TypeValue(
    name='bulgarian',
    value=24,
), 25: TypeValue(
    name='romanian',
    value=25,
), 26: TypeValue(
    name='chinese',
    value=26,
), 27: TypeValue(
    name='japanese',
    value=27,
), 28: TypeValue(
    name='korean',
    value=28,
), 29: TypeValue(
    name='taiwanese',
    value=29,
), 30: TypeValue(
    name='thai',
    value=30,
), 31: TypeValue(
    name='hebrew',
    value=31,
), 32: TypeValue(
    name='brazilian_portuguese',
    value=32,
), 33: TypeValue(
    name='indonesian',
    value=33,
), 34: TypeValue(
    name='malaysian',
    value=34,
), 35: TypeValue(
    name='vietnamese',
    value=35,
), 36: TypeValue(
    name='burmese',
    value=36,
), 37: TypeValue(
    name='mongolian',
    value=37,
), 254: TypeValue(
    name='custom',
    value=254,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'language_bits_0': Type(
    name='language_bits_0',
    base_type='uint8z',
    values=Map(
    map={1: TypeValue(
    name='english',
    value=1,
), 2: TypeValue(
    name='french',
    value=2,
), 4: TypeValue(
    name='italian',
    value=4,
), 8: TypeValue(
    name='german',
    value=8,
), 16: TypeValue(
    name='spanish',
    value=16,
), 32: TypeValue(
    name='croatian',
    value=32,
), 64: TypeValue(
    name='czech',
    value=64,
), 128: TypeValue(
    name='danish',
    value=128,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'language_bits_1': Type(
    name='language_bits_1',
    base_type='uint8z',
    values=Map(
    map={1: TypeValue(
    name='dutch',
    value=1,
), 2: TypeValue(
    name='finnish',
    value=2,
), 4: TypeValue(
    name='greek',
    value=4,
), 8: TypeValue(
    name='hungarian',
    value=8,
), 16: TypeValue(
    name='norwegian',
    value=16,
), 32: TypeValue(
    name='polish',
    value=32,
), 64: TypeValue(
    name='portuguese',
    value=64,
), 128: TypeValue(
    name='slovakian',
    value=128,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'language_bits_2': Type(
    name='language_bits_2',
    base_type='uint8z',
    values=Map(
    map={1: TypeValue(
    name='slovenian',
    value=1,
), 2: TypeValue(
    name='swedish',
    value=2,
), 4: TypeValue(
    name='russian',
    value=4,
), 8: TypeValue(
    name='turkish',
    value=8,
), 16: TypeValue(
    name='latvian',
    value=16,
), 32: TypeValue(
    name='ukrainian',
    value=32,
), 64: TypeValue(
    name='arabic',
    value=64,
), 128: TypeValue(
    name='farsi',
    value=128,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'language_bits_3': Type(
    name='language_bits_3',
    base_type='uint8z',
    values=Map(
    map={1: TypeValue(
    name='bulgarian',
    value=1,
), 2: TypeValue(
    name='romanian',
    value=2,
), 4: TypeValue(
    name='chinese',
    value=4,
), 8: TypeValue(
    name='japanese',
    value=8,
), 16: TypeValue(
    name='korean',
    value=16,
), 32: TypeValue(
    name='taiwanese',
    value=32,
), 64: TypeValue(
    name='thai',
    value=64,
), 128: TypeValue(
    name='hebrew',
    value=128,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'language_bits_4': Type(
    name='language_bits_4',
    base_type='uint8z',
    values=Map(
    map={1: TypeValue(
    name='brazilian_portuguese',
    value=1,
), 2: TypeValue(
    name='indonesian',
    value=2,
), 4: TypeValue(
    name='malaysian',
    value=4,
), 8: TypeValue(
    name='vietnamese',
    value=8,
), 16: TypeValue(
    name='burmese',
    value=16,
), 32: TypeValue(
    name='mongolian',
    value=32,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'time_zone': Type(
    name='time_zone',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='almaty',
    value=0,
), 1: TypeValue(
    name='bangkok',
    value=1,
), 2: TypeValue(
    name='bombay',
    value=2,
), 3: TypeValue(
    name='brasilia',
    value=3,
), 4: TypeValue(
    name='cairo',
    value=4,
), 5: TypeValue(
    name='cape_verde_is',
    value=5,
), 6: TypeValue(
    name='darwin',
    value=6,
), 7: TypeValue(
    name='eniwetok',
    value=7,
), 8: TypeValue(
    name='fiji',
    value=8,
), 9: TypeValue(
    name='hong_kong',
    value=9,
), 10: TypeValue(
    name='islamabad',
    value=10,
), 11: TypeValue(
    name='kabul',
    value=11,
), 12: TypeValue(
    name='magadan',
    value=12,
), 13: TypeValue(
    name='mid_atlantic',
    value=13,
), 14: TypeValue(
    name='moscow',
    value=14,
), 15: TypeValue(
    name='muscat',
    value=15,
), 16: TypeValue(
    name='newfoundland',
    value=16,
), 17: TypeValue(
    name='samoa',
    value=17,
), 18: TypeValue(
    name='sydney',
    value=18,
), 19: TypeValue(
    name='tehran',
    value=19,
), 20: TypeValue(
    name='tokyo',
    value=20,
), 21: TypeValue(
    name='us_alaska',
    value=21,
), 22: TypeValue(
    name='us_atlantic',
    value=22,
), 23: TypeValue(
    name='us_central',
    value=23,
), 24: TypeValue(
    name='us_eastern',
    value=24,
), 25: TypeValue(
    name='us_hawaii',
    value=25,
), 26: TypeValue(
    name='us_mountain',
    value=26,
), 27: TypeValue(
    name='us_pacific',
    value=27,
), 28: TypeValue(
    name='other',
    value=28,
), 29: TypeValue(
    name='auckland',
    value=29,
), 30: TypeValue(
    name='kathmandu',
    value=30,
), 31: TypeValue(
    name='europe_western_wet',
    value=31,
), 32: TypeValue(
    name='europe_central_cet',
    value=32,
), 33: TypeValue(
    name='europe_eastern_eet',
    value=33,
), 34: TypeValue(
    name='jakarta',
    value=34,
), 35: TypeValue(
    name='perth',
    value=35,
), 36: TypeValue(
    name='adelaide',
    value=36,
), 37: TypeValue(
    name='brisbane',
    value=37,
), 38: TypeValue(
    name='tasmania',
    value=38,
), 39: TypeValue(
    name='iceland',
    value=39,
), 40: TypeValue(
    name='amsterdam',
    value=40,
), 41: TypeValue(
    name='athens',
    value=41,
), 42: TypeValue(
    name='barcelona',
    value=42,
), 43: TypeValue(
    name='berlin',
    value=43,
), 44: TypeValue(
    name='brussels',
    value=44,
), 45: TypeValue(
    name='budapest',
    value=45,
), 46: TypeValue(
    name='copenhagen',
    value=46,
), 47: TypeValue(
    name='dublin',
    value=47,
), 48: TypeValue(
    name='helsinki',
    value=48,
), 49: TypeValue(
    name='lisbon',
    value=49,
), 50: TypeValue(
    name='london',
    value=50,
), 51: TypeValue(
    name='madrid',
    value=51,
), 52: TypeValue(
    name='munich',
    value=52,
), 53: TypeValue(
    name='oslo',
    value=53,
), 54: TypeValue(
    name='paris',
    value=54,
), 55: TypeValue(
    name='prague',
    value=55,
), 56: TypeValue(
    name='reykjavik',
    value=56,
), 57: TypeValue(
    name='rome',
    value=57,
), 58: TypeValue(
    name='stockholm',
    value=58,
), 59: TypeValue(
    name='vienna',
    value=59,
), 60: TypeValue(
    name='warsaw',
    value=60,
), 61: TypeValue(
    name='zurich',
    value=61,
), 62: TypeValue(
    name='quebec',
    value=62,
), 63: TypeValue(
    name='ontario',
    value=63,
), 64: TypeValue(
    name='manitoba',
    value=64,
), 65: TypeValue(
    name='saskatchewan',
    value=65,
), 66: TypeValue(
    name='alberta',
    value=66,
), 67: TypeValue(
    name='british_columbia',
    value=67,
), 68: TypeValue(
    name='boise',
    value=68,
), 69: TypeValue(
    name='boston',
    value=69,
), 70: TypeValue(
    name='chicago',
    value=70,
), 71: TypeValue(
    name='dallas',
    value=71,
), 72: TypeValue(
    name='denver',
    value=72,
), 73: TypeValue(
    name='kansas_city',
    value=73,
), 74: TypeValue(
    name='las_vegas',
    value=74,
), 75: TypeValue(
    name='los_angeles',
    value=75,
), 76: TypeValue(
    name='miami',
    value=76,
), 77: TypeValue(
    name='minneapolis',
    value=77,
), 78: TypeValue(
    name='new_york',
    value=78,
), 79: TypeValue(
    name='new_orleans',
    value=79,
), 80: TypeValue(
    name='phoenix',
    value=80,
), 81: TypeValue(
    name='santa_fe',
    value=81,
), 82: TypeValue(
    name='seattle',
    value=82,
), 83: TypeValue(
    name='washington_dc',
    value=83,
), 84: TypeValue(
    name='us_arizona',
    value=84,
), 85: TypeValue(
    name='chita',
    value=85,
), 86: TypeValue(
    name='ekaterinburg',
    value=86,
), 87: TypeValue(
    name='irkutsk',
    value=87,
), 88: TypeValue(
    name='kaliningrad',
    value=88,
), 89: TypeValue(
    name='krasnoyarsk',
    value=89,
), 90: TypeValue(
    name='novosibirsk',
    value=90,
), 91: TypeValue(
    name='petropavlovsk_kamchatskiy',
    value=91,
), 92: TypeValue(
    name='samara',
    value=92,
), 93: TypeValue(
    name='vladivostok',
    value=93,
), 94: TypeValue(
    name='mexico_central',
    value=94,
), 95: TypeValue(
    name='mexico_mountain',
    value=95,
), 96: TypeValue(
    name='mexico_pacific',
    value=96,
), 97: TypeValue(
    name='cape_town',
    value=97,
), 98: TypeValue(
    name='winkhoek',
    value=98,
), 99: TypeValue(
    name='lagos',
    value=99,
), 100: TypeValue(
    name='riyahd',
    value=100,
), 101: TypeValue(
    name='venezuela',
    value=101,
), 102: TypeValue(
    name='australia_lh',
    value=102,
), 103: TypeValue(
    name='santiago',
    value=103,
), 253: TypeValue(
    name='manual',
    value=253,
), 254: TypeValue(
    name='automatic',
    value=254,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'display_measure': Type(
    name='display_measure',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='metric',
    value=0,
), 1: TypeValue(
    name='statute',
    value=1,
), 2: TypeValue(
    name='nautical',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'display_heart': Type(
    name='display_heart',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='bpm',
    value=0,
), 1: TypeValue(
    name='max',
    value=1,
), 2: TypeValue(
    name='reserve',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'display_power': Type(
    name='display_power',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='watts',
    value=0,
), 1: TypeValue(
    name='percent_ftp',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'display_position': Type(
    name='display_position',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='degree',
    value=0,
    comment='dd.dddddd',
), 1: TypeValue(
    name='degree_minute',
    value=1,
    comment='dddmm.mmm',
), 2: TypeValue(
    name='degree_minute_second',
    value=2,
    comment='dddmmss',
), 3: TypeValue(
    name='austrian_grid',
    value=3,
    comment='Austrian Grid (BMN)',
), 4: TypeValue(
    name='british_grid',
    value=4,
    comment='British National Grid',
), 5: TypeValue(
    name='dutch_grid',
    value=5,
    comment='Dutch grid system',
), 6: TypeValue(
    name='hungarian_grid',
    value=6,
    comment='Hungarian grid system',
), 7: TypeValue(
    name='finnish_grid',
    value=7,
    comment='Finnish grid system Zone3 KKJ27',
), 8: TypeValue(
    name='german_grid',
    value=8,
    comment='Gausss Krueger (German)',
), 9: TypeValue(
    name='icelandic_grid',
    value=9,
    comment='Icelandic Grid',
), 10: TypeValue(
    name='indonesian_equatorial',
    value=10,
    comment='Indonesian Equatorial LCO',
), 11: TypeValue(
    name='indonesian_irian',
    value=11,
    comment='Indonesian Irian LCO',
), 12: TypeValue(
    name='indonesian_southern',
    value=12,
    comment='Indonesian Southern LCO',
), 13: TypeValue(
    name='india_zone_0',
    value=13,
    comment='India zone 0',
), 14: TypeValue(
    name='india_zone_IA',
    value=14,
    comment='India zone IA',
), 15: TypeValue(
    name='india_zone_IB',
    value=15,
    comment='India zone IB',
), 16: TypeValue(
    name='india_zone_IIA',
    value=16,
    comment='India zone IIA',
), 17: TypeValue(
    name='india_zone_IIB',
    value=17,
    comment='India zone IIB',
), 18: TypeValue(
    name='india_zone_IIIA',
    value=18,
    comment='India zone IIIA',
), 19: TypeValue(
    name='india_zone_IIIB',
    value=19,
    comment='India zone IIIB',
), 20: TypeValue(
    name='india_zone_IVA',
    value=20,
    comment='India zone IVA',
), 21: TypeValue(
    name='india_zone_IVB',
    value=21,
    comment='India zone IVB',
), 22: TypeValue(
    name='irish_transverse',
    value=22,
    comment='Irish Transverse Mercator',
), 23: TypeValue(
    name='irish_grid',
    value=23,
    comment='Irish Grid',
), 24: TypeValue(
    name='loran',
    value=24,
    comment='Loran TD',
), 25: TypeValue(
    name='maidenhead_grid',
    value=25,
    comment='Maidenhead grid system',
), 26: TypeValue(
    name='mgrs_grid',
    value=26,
    comment='MGRS grid system',
), 27: TypeValue(
    name='new_zealand_grid',
    value=27,
    comment='New Zealand grid system',
), 28: TypeValue(
    name='new_zealand_transverse',
    value=28,
    comment='New Zealand Transverse Mercator',
), 29: TypeValue(
    name='qatar_grid',
    value=29,
    comment='Qatar National Grid',
), 30: TypeValue(
    name='modified_swedish_grid',
    value=30,
    comment='Modified RT-90 (Sweden)',
), 31: TypeValue(
    name='swedish_grid',
    value=31,
    comment='RT-90 (Sweden)',
), 32: TypeValue(
    name='south_african_grid',
    value=32,
    comment='South African Grid',
), 33: TypeValue(
    name='swiss_grid',
    value=33,
    comment='Swiss CH-1903 grid',
), 34: TypeValue(
    name='taiwan_grid',
    value=34,
    comment='Taiwan Grid',
), 35: TypeValue(
    name='united_states_grid',
    value=35,
    comment='United States National Grid',
), 36: TypeValue(
    name='utm_ups_grid',
    value=36,
    comment='UTM/UPS grid system',
), 37: TypeValue(
    name='west_malayan',
    value=37,
    comment='West Malayan RSO',
), 38: TypeValue(
    name='borneo_rso',
    value=38,
    comment='Borneo RSO',
), 39: TypeValue(
    name='estonian_grid',
    value=39,
    comment='Estonian grid system',
), 40: TypeValue(
    name='latvian_grid',
    value=40,
    comment='Latvian Transverse Mercator',
), 41: TypeValue(
    name='swedish_ref_99_grid',
    value=41,
    comment='Reference Grid 99 TM (Swedish)',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'switch': Type(
    name='switch',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='off',
    value=0,
), 1: TypeValue(
    name='on',
    value=1,
), 2: TypeValue(
    name='auto',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'sport': Type(
    name='sport',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='generic',
    value=0,
), 1: TypeValue(
    name='running',
    value=1,
), 2: TypeValue(
    name='cycling',
    value=2,
), 3: TypeValue(
    name='transition',
    value=3,
    comment='Mulitsport transition',
), 4: TypeValue(
    name='fitness_equipment',
    value=4,
), 5: TypeValue(
    name='swimming',
    value=5,
), 6: TypeValue(
    name='basketball',
    value=6,
), 7: TypeValue(
    name='soccer',
    value=7,
), 8: TypeValue(
    name='tennis',
    value=8,
), 9: TypeValue(
    name='american_football',
    value=9,
), 10: TypeValue(
    name='training',
    value=10,
), 11: TypeValue(
    name='walking',
    value=11,
), 12: TypeValue(
    name='cross_country_skiing',
    value=12,
), 13: TypeValue(
    name='alpine_skiing',
    value=13,
), 14: TypeValue(
    name='snowboarding',
    value=14,
), 15: TypeValue(
    name='rowing',
    value=15,
), 16: TypeValue(
    name='mountaineering',
    value=16,
), 17: TypeValue(
    name='hiking',
    value=17,
), 18: TypeValue(
    name='multisport',
    value=18,
), 19: TypeValue(
    name='paddling',
    value=19,
), 20: TypeValue(
    name='flying',
    value=20,
), 21: TypeValue(
    name='e_biking',
    value=21,
), 22: TypeValue(
    name='motorcycling',
    value=22,
), 23: TypeValue(
    name='boating',
    value=23,
), 24: TypeValue(
    name='driving',
    value=24,
), 25: TypeValue(
    name='golf',
    value=25,
), 26: TypeValue(
    name='hang_gliding',
    value=26,
), 27: TypeValue(
    name='horseback_riding',
    value=27,
), 28: TypeValue(
    name='hunting',
    value=28,
), 29: TypeValue(
    name='fishing',
    value=29,
), 30: TypeValue(
    name='inline_skating',
    value=30,
), 31: TypeValue(
    name='rock_climbing',
    value=31,
), 32: TypeValue(
    name='sailing',
    value=32,
), 33: TypeValue(
    name='ice_skating',
    value=33,
), 34: TypeValue(
    name='sky_diving',
    value=34,
), 35: TypeValue(
    name='snowshoeing',
    value=35,
), 36: TypeValue(
    name='snowmobiling',
    value=36,
), 37: TypeValue(
    name='stand_up_paddleboarding',
    value=37,
), 38: TypeValue(
    name='surfing',
    value=38,
), 39: TypeValue(
    name='wakeboarding',
    value=39,
), 40: TypeValue(
    name='water_skiing',
    value=40,
), 41: TypeValue(
    name='kayaking',
    value=41,
), 42: TypeValue(
    name='rafting',
    value=42,
), 43: TypeValue(
    name='windsurfing',
    value=43,
), 44: TypeValue(
    name='kitesurfing',
    value=44,
), 45: TypeValue(
    name='tactical',
    value=45,
), 46: TypeValue(
    name='jumpmaster',
    value=46,
), 47: TypeValue(
    name='boxing',
    value=47,
), 48: TypeValue(
    name='floor_climbing',
    value=48,
), 53: TypeValue(
    name='diving',
    value=53,
), 254: TypeValue(
    name='all',
    value=254,
    comment='All is for goals only to include all sports.',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'sport_bits_0': Type(
    name='sport_bits_0',
    base_type='uint8z',
    values=Map(
    map={1: TypeValue(
    name='generic',
    value=1,
), 2: TypeValue(
    name='running',
    value=2,
), 4: TypeValue(
    name='cycling',
    value=4,
), 8: TypeValue(
    name='transition',
    value=8,
    comment='Mulitsport transition',
), 16: TypeValue(
    name='fitness_equipment',
    value=16,
), 32: TypeValue(
    name='swimming',
    value=32,
), 64: TypeValue(
    name='basketball',
    value=64,
), 128: TypeValue(
    name='soccer',
    value=128,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'sport_bits_1': Type(
    name='sport_bits_1',
    base_type='uint8z',
    values=Map(
    map={1: TypeValue(
    name='tennis',
    value=1,
), 2: TypeValue(
    name='american_football',
    value=2,
), 4: TypeValue(
    name='training',
    value=4,
), 8: TypeValue(
    name='walking',
    value=8,
), 16: TypeValue(
    name='cross_country_skiing',
    value=16,
), 32: TypeValue(
    name='alpine_skiing',
    value=32,
), 64: TypeValue(
    name='snowboarding',
    value=64,
), 128: TypeValue(
    name='rowing',
    value=128,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'sport_bits_2': Type(
    name='sport_bits_2',
    base_type='uint8z',
    values=Map(
    map={1: TypeValue(
    name='mountaineering',
    value=1,
), 2: TypeValue(
    name='hiking',
    value=2,
), 4: TypeValue(
    name='multisport',
    value=4,
), 8: TypeValue(
    name='paddling',
    value=8,
), 16: TypeValue(
    name='flying',
    value=16,
), 32: TypeValue(
    name='e_biking',
    value=32,
), 64: TypeValue(
    name='motorcycling',
    value=64,
), 128: TypeValue(
    name='boating',
    value=128,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'sport_bits_3': Type(
    name='sport_bits_3',
    base_type='uint8z',
    values=Map(
    map={1: TypeValue(
    name='driving',
    value=1,
), 2: TypeValue(
    name='golf',
    value=2,
), 4: TypeValue(
    name='hang_gliding',
    value=4,
), 8: TypeValue(
    name='horseback_riding',
    value=8,
), 16: TypeValue(
    name='hunting',
    value=16,
), 32: TypeValue(
    name='fishing',
    value=32,
), 64: TypeValue(
    name='inline_skating',
    value=64,
), 128: TypeValue(
    name='rock_climbing',
    value=128,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'sport_bits_4': Type(
    name='sport_bits_4',
    base_type='uint8z',
    values=Map(
    map={1: TypeValue(
    name='sailing',
    value=1,
), 2: TypeValue(
    name='ice_skating',
    value=2,
), 4: TypeValue(
    name='sky_diving',
    value=4,
), 8: TypeValue(
    name='snowshoeing',
    value=8,
), 16: TypeValue(
    name='snowmobiling',
    value=16,
), 32: TypeValue(
    name='stand_up_paddleboarding',
    value=32,
), 64: TypeValue(
    name='surfing',
    value=64,
), 128: TypeValue(
    name='wakeboarding',
    value=128,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'sport_bits_5': Type(
    name='sport_bits_5',
    base_type='uint8z',
    values=Map(
    map={1: TypeValue(
    name='water_skiing',
    value=1,
), 2: TypeValue(
    name='kayaking',
    value=2,
), 4: TypeValue(
    name='rafting',
    value=4,
), 8: TypeValue(
    name='windsurfing',
    value=8,
), 16: TypeValue(
    name='kitesurfing',
    value=16,
), 32: TypeValue(
    name='tactical',
    value=32,
), 64: TypeValue(
    name='jumpmaster',
    value=64,
), 128: TypeValue(
    name='boxing',
    value=128,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'sport_bits_6': Type(
    name='sport_bits_6',
    base_type='uint8z',
    values=Map(
    map={1: TypeValue(
    name='floor_climbing',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'sub_sport': Type(
    name='sub_sport',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='generic',
    value=0,
), 1: TypeValue(
    name='treadmill',
    value=1,
    comment='Run/Fitness Equipment',
), 2: TypeValue(
    name='street',
    value=2,
    comment='Run',
), 3: TypeValue(
    name='trail',
    value=3,
    comment='Run',
), 4: TypeValue(
    name='track',
    value=4,
    comment='Run',
), 5: TypeValue(
    name='spin',
    value=5,
    comment='Cycling',
), 6: TypeValue(
    name='indoor_cycling',
    value=6,
    comment='Cycling/Fitness Equipment',
), 7: TypeValue(
    name='road',
    value=7,
    comment='Cycling',
), 8: TypeValue(
    name='mountain',
    value=8,
    comment='Cycling',
), 9: TypeValue(
    name='downhill',
    value=9,
    comment='Cycling',
), 10: TypeValue(
    name='recumbent',
    value=10,
    comment='Cycling',
), 11: TypeValue(
    name='cyclocross',
    value=11,
    comment='Cycling',
), 12: TypeValue(
    name='hand_cycling',
    value=12,
    comment='Cycling',
), 13: TypeValue(
    name='track_cycling',
    value=13,
    comment='Cycling',
), 14: TypeValue(
    name='indoor_rowing',
    value=14,
    comment='Fitness Equipment',
), 15: TypeValue(
    name='elliptical',
    value=15,
    comment='Fitness Equipment',
), 16: TypeValue(
    name='stair_climbing',
    value=16,
    comment='Fitness Equipment',
), 17: TypeValue(
    name='lap_swimming',
    value=17,
    comment='Swimming',
), 18: TypeValue(
    name='open_water',
    value=18,
    comment='Swimming',
), 19: TypeValue(
    name='flexibility_training',
    value=19,
    comment='Training',
), 20: TypeValue(
    name='strength_training',
    value=20,
    comment='Training',
), 21: TypeValue(
    name='warm_up',
    value=21,
    comment='Tennis',
), 22: TypeValue(
    name='match',
    value=22,
    comment='Tennis',
), 23: TypeValue(
    name='exercise',
    value=23,
    comment='Tennis',
), 24: TypeValue(
    name='challenge',
    value=24,
), 25: TypeValue(
    name='indoor_skiing',
    value=25,
    comment='Fitness Equipment',
), 26: TypeValue(
    name='cardio_training',
    value=26,
    comment='Training',
), 27: TypeValue(
    name='indoor_walking',
    value=27,
    comment='Walking/Fitness Equipment',
), 28: TypeValue(
    name='e_bike_fitness',
    value=28,
    comment='E-Biking',
), 29: TypeValue(
    name='bmx',
    value=29,
    comment='Cycling',
), 30: TypeValue(
    name='casual_walking',
    value=30,
    comment='Walking',
), 31: TypeValue(
    name='speed_walking',
    value=31,
    comment='Walking',
), 32: TypeValue(
    name='bike_to_run_transition',
    value=32,
    comment='Transition',
), 33: TypeValue(
    name='run_to_bike_transition',
    value=33,
    comment='Transition',
), 34: TypeValue(
    name='swim_to_bike_transition',
    value=34,
    comment='Transition',
), 35: TypeValue(
    name='atv',
    value=35,
    comment='Motorcycling',
), 36: TypeValue(
    name='motocross',
    value=36,
    comment='Motorcycling',
), 37: TypeValue(
    name='backcountry',
    value=37,
    comment='Alpine Skiing/Snowboarding',
), 38: TypeValue(
    name='resort',
    value=38,
    comment='Alpine Skiing/Snowboarding',
), 39: TypeValue(
    name='rc_drone',
    value=39,
    comment='Flying',
), 40: TypeValue(
    name='wingsuit',
    value=40,
    comment='Flying',
), 41: TypeValue(
    name='whitewater',
    value=41,
    comment='Kayaking/Rafting',
), 42: TypeValue(
    name='skate_skiing',
    value=42,
    comment='Cross Country Skiing',
), 43: TypeValue(
    name='yoga',
    value=43,
    comment='Training',
), 44: TypeValue(
    name='pilates',
    value=44,
    comment='Fitness Equipment',
), 45: TypeValue(
    name='indoor_running',
    value=45,
    comment='Run',
), 46: TypeValue(
    name='gravel_cycling',
    value=46,
    comment='Cycling',
), 47: TypeValue(
    name='e_bike_mountain',
    value=47,
    comment='Cycling',
), 48: TypeValue(
    name='commuting',
    value=48,
    comment='Cycling',
), 49: TypeValue(
    name='mixed_surface',
    value=49,
    comment='Cycling',
), 50: TypeValue(
    name='navigate',
    value=50,
), 51: TypeValue(
    name='track_me',
    value=51,
), 52: TypeValue(
    name='map',
    value=52,
), 53: TypeValue(
    name='single_gas_diving',
    value=53,
    comment='Diving',
), 54: TypeValue(
    name='multi_gas_diving',
    value=54,
    comment='Diving',
), 55: TypeValue(
    name='gauge_diving',
    value=55,
    comment='Diving',
), 56: TypeValue(
    name='apnea_diving',
    value=56,
    comment='Diving',
), 57: TypeValue(
    name='apnea_hunting',
    value=57,
    comment='Diving',
), 58: TypeValue(
    name='virtual_activity',
    value=58,
), 59: TypeValue(
    name='obstacle',
    value=59,
    comment='Used for events where participants run, crawl through mud, climb over walls, etc.',
), 62: TypeValue(
    name='breathing',
    value=62,
), 65: TypeValue(
    name='sail_race',
    value=65,
    comment='Sailing',
), 67: TypeValue(
    name='ultra',
    value=67,
    comment='Ultramarathon',
), 68: TypeValue(
    name='indoor_climbing',
    value=68,
    comment='Climbing',
), 69: TypeValue(
    name='bouldering',
    value=69,
    comment='Climbing',
), 254: TypeValue(
    name='all',
    value=254,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'sport_event': Type(
    name='sport_event',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='uncategorized',
    value=0,
), 1: TypeValue(
    name='geocaching',
    value=1,
), 2: TypeValue(
    name='fitness',
    value=2,
), 3: TypeValue(
    name='recreation',
    value=3,
), 4: TypeValue(
    name='race',
    value=4,
), 5: TypeValue(
    name='special_event',
    value=5,
), 6: TypeValue(
    name='training',
    value=6,
), 7: TypeValue(
    name='transportation',
    value=7,
), 8: TypeValue(
    name='touring',
    value=8,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'activity': Type(
    name='activity',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='manual',
    value=0,
), 1: TypeValue(
    name='auto_multi_sport',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'intensity': Type(
    name='intensity',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='active',
    value=0,
), 1: TypeValue(
    name='rest',
    value=1,
), 2: TypeValue(
    name='warmup',
    value=2,
), 3: TypeValue(
    name='cooldown',
    value=3,
), 4: TypeValue(
    name='recovery',
    value=4,
), 5: TypeValue(
    name='interval',
    value=5,
), 6: TypeValue(
    name='other',
    value=6,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'session_trigger': Type(
    name='session_trigger',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='activity_end',
    value=0,
), 1: TypeValue(
    name='manual',
    value=1,
    comment='User changed sport.',
), 2: TypeValue(
    name='auto_multi_sport',
    value=2,
    comment='Auto multi-sport feature is enabled and user pressed lap button to advance session.',
), 3: TypeValue(
    name='fitness_equipment',
    value=3,
    comment='Auto sport change caused by user linking to fitness equipment.',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'autolap_trigger': Type(
    name='autolap_trigger',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='time',
    value=0,
), 1: TypeValue(
    name='distance',
    value=1,
), 2: TypeValue(
    name='position_start',
    value=2,
), 3: TypeValue(
    name='position_lap',
    value=3,
), 4: TypeValue(
    name='position_waypoint',
    value=4,
), 5: TypeValue(
    name='position_marked',
    value=5,
), 6: TypeValue(
    name='off',
    value=6,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'lap_trigger': Type(
    name='lap_trigger',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='manual',
    value=0,
), 1: TypeValue(
    name='time',
    value=1,
), 2: TypeValue(
    name='distance',
    value=2,
), 3: TypeValue(
    name='position_start',
    value=3,
), 4: TypeValue(
    name='position_lap',
    value=4,
), 5: TypeValue(
    name='position_waypoint',
    value=5,
), 6: TypeValue(
    name='position_marked',
    value=6,
), 7: TypeValue(
    name='session_end',
    value=7,
), 8: TypeValue(
    name='fitness_equipment',
    value=8,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'time_mode': Type(
    name='time_mode',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='hour12',
    value=0,
), 1: TypeValue(
    name='hour24',
    value=1,
    comment='Does not use a leading zero and has a colon',
), 2: TypeValue(
    name='military',
    value=2,
    comment='Uses a leading zero and does not have a colon',
), 3: TypeValue(
    name='hour_12_with_seconds',
    value=3,
), 4: TypeValue(
    name='hour_24_with_seconds',
    value=4,
), 5: TypeValue(
    name='utc',
    value=5,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'backlight_mode': Type(
    name='backlight_mode',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='off',
    value=0,
), 1: TypeValue(
    name='manual',
    value=1,
), 2: TypeValue(
    name='key_and_messages',
    value=2,
), 3: TypeValue(
    name='auto_brightness',
    value=3,
), 4: TypeValue(
    name='smart_notifications',
    value=4,
), 5: TypeValue(
    name='key_and_messages_night',
    value=5,
), 6: TypeValue(
    name='key_and_messages_and_smart_notifications',
    value=6,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'date_mode': Type(
    name='date_mode',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='day_month',
    value=0,
), 1: TypeValue(
    name='month_day',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'backlight_timeout': Type(
    name='backlight_timeout',
    base_type='uint8',
    values=Map(
    map={0: TypeValue(
    name='infinite',
    value=0,
    comment='Backlight stays on forever.',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'event': Type(
    name='event',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='timer',
    value=0,
    comment='Group 0.  Start / stop_all',
), 3: TypeValue(
    name='workout',
    value=3,
    comment='start / stop',
), 4: TypeValue(
    name='workout_step',
    value=4,
    comment='Start at beginning of workout.  Stop at end of each step.',
), 5: TypeValue(
    name='power_down',
    value=5,
    comment='stop_all group 0',
), 6: TypeValue(
    name='power_up',
    value=6,
    comment='stop_all group 0',
), 7: TypeValue(
    name='off_course',
    value=7,
    comment='start / stop group 0',
), 8: TypeValue(
    name='session',
    value=8,
    comment='Stop at end of each session.',
), 9: TypeValue(
    name='lap',
    value=9,
    comment='Stop at end of each lap.',
), 10: TypeValue(
    name='course_point',
    value=10,
    comment='marker',
), 11: TypeValue(
    name='battery',
    value=11,
    comment='marker',
), 12: TypeValue(
    name='virtual_partner_pace',
    value=12,
    comment='Group 1. Start at beginning of activity if VP enabled, when VP pace is changed during activity or VP enabled mid activity.  stop_disable when VP disabled.',
), 13: TypeValue(
    name='hr_high_alert',
    value=13,
    comment='Group 0.  Start / stop when in alert condition.',
), 14: TypeValue(
    name='hr_low_alert',
    value=14,
    comment='Group 0.  Start / stop when in alert condition.',
), 15: TypeValue(
    name='speed_high_alert',
    value=15,
    comment='Group 0.  Start / stop when in alert condition.',
), 16: TypeValue(
    name='speed_low_alert',
    value=16,
    comment='Group 0.  Start / stop when in alert condition.',
), 17: TypeValue(
    name='cad_high_alert',
    value=17,
    comment='Group 0.  Start / stop when in alert condition.',
), 18: TypeValue(
    name='cad_low_alert',
    value=18,
    comment='Group 0.  Start / stop when in alert condition.',
), 19: TypeValue(
    name='power_high_alert',
    value=19,
    comment='Group 0.  Start / stop when in alert condition.',
), 20: TypeValue(
    name='power_low_alert',
    value=20,
    comment='Group 0.  Start / stop when in alert condition.',
), 21: TypeValue(
    name='recovery_hr',
    value=21,
    comment='marker',
), 22: TypeValue(
    name='battery_low',
    value=22,
    comment='marker',
), 23: TypeValue(
    name='time_duration_alert',
    value=23,
    comment='Group 1.  Start if enabled mid activity (not required at start of activity). Stop when duration is reached.  stop_disable if disabled.',
), 24: TypeValue(
    name='distance_duration_alert',
    value=24,
    comment='Group 1.  Start if enabled mid activity (not required at start of activity). Stop when duration is reached.  stop_disable if disabled.',
), 25: TypeValue(
    name='calorie_duration_alert',
    value=25,
    comment='Group 1.  Start if enabled mid activity (not required at start of activity). Stop when duration is reached.  stop_disable if disabled.',
), 26: TypeValue(
    name='activity',
    value=26,
    comment='Group 1..  Stop at end of activity.',
), 27: TypeValue(
    name='fitness_equipment',
    value=27,
    comment='marker',
), 28: TypeValue(
    name='length',
    value=28,
    comment='Stop at end of each length.',
), 32: TypeValue(
    name='user_marker',
    value=32,
    comment='marker',
), 33: TypeValue(
    name='sport_point',
    value=33,
    comment='marker',
), 36: TypeValue(
    name='calibration',
    value=36,
    comment='start/stop/marker',
), 42: TypeValue(
    name='front_gear_change',
    value=42,
    comment='marker',
), 43: TypeValue(
    name='rear_gear_change',
    value=43,
    comment='marker',
), 44: TypeValue(
    name='rider_position_change',
    value=44,
    comment='marker',
), 45: TypeValue(
    name='elev_high_alert',
    value=45,
    comment='Group 0.  Start / stop when in alert condition.',
), 46: TypeValue(
    name='elev_low_alert',
    value=46,
    comment='Group 0.  Start / stop when in alert condition.',
), 47: TypeValue(
    name='comm_timeout',
    value=47,
    comment='marker',
), 75: TypeValue(
    name='radar_threat_alert',
    value=75,
    comment='start/stop/marker',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'event_type': Type(
    name='event_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='start',
    value=0,
), 1: TypeValue(
    name='stop',
    value=1,
), 2: TypeValue(
    name='consecutive_depreciated',
    value=2,
), 3: TypeValue(
    name='marker',
    value=3,
), 4: TypeValue(
    name='stop_all',
    value=4,
), 5: TypeValue(
    name='begin_depreciated',
    value=5,
), 6: TypeValue(
    name='end_depreciated',
    value=6,
), 7: TypeValue(
    name='end_all_depreciated',
    value=7,
), 8: TypeValue(
    name='stop_disable',
    value=8,
), 9: TypeValue(
    name='stop_disable_all',
    value=9,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'timer_trigger': Type(
    name='timer_trigger',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='manual',
    value=0,
), 1: TypeValue(
    name='auto',
    value=1,
), 2: TypeValue(
    name='fitness_equipment',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'fitness_equipment_state': Type(
    name='fitness_equipment_state',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='ready',
    value=0,
), 1: TypeValue(
    name='in_use',
    value=1,
), 2: TypeValue(
    name='paused',
    value=2,
), 3: TypeValue(
    name='unknown',
    value=3,
    comment='lost connection to fitness equipment',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'tone': Type(
    name='tone',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='off',
    value=0,
), 1: TypeValue(
    name='tone',
    value=1,
), 2: TypeValue(
    name='vibrate',
    value=2,
), 3: TypeValue(
    name='tone_and_vibrate',
    value=3,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'autoscroll': Type(
    name='autoscroll',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='none',
    value=0,
), 1: TypeValue(
    name='slow',
    value=1,
), 2: TypeValue(
    name='medium',
    value=2,
), 3: TypeValue(
    name='fast',
    value=3,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'activity_class': Type(
    name='activity_class',
    base_type='enum',
    values=Map(
    map={127: TypeValue(
    name='level',
    value=127,
    comment='0 to 100',
), 100: TypeValue(
    name='level_max',
    value=100,
), 128: TypeValue(
    name='athlete',
    value=128,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'hr_zone_calc': Type(
    name='hr_zone_calc',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='custom',
    value=0,
), 1: TypeValue(
    name='percent_max_hr',
    value=1,
), 2: TypeValue(
    name='percent_hrr',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'pwr_zone_calc': Type(
    name='pwr_zone_calc',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='custom',
    value=0,
), 1: TypeValue(
    name='percent_ftp',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'wkt_step_duration': Type(
    name='wkt_step_duration',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='time',
    value=0,
), 1: TypeValue(
    name='distance',
    value=1,
), 2: TypeValue(
    name='hr_less_than',
    value=2,
), 3: TypeValue(
    name='hr_greater_than',
    value=3,
), 4: TypeValue(
    name='calories',
    value=4,
), 5: TypeValue(
    name='open',
    value=5,
), 6: TypeValue(
    name='repeat_until_steps_cmplt',
    value=6,
), 7: TypeValue(
    name='repeat_until_time',
    value=7,
), 8: TypeValue(
    name='repeat_until_distance',
    value=8,
), 9: TypeValue(
    name='repeat_until_calories',
    value=9,
), 10: TypeValue(
    name='repeat_until_hr_less_than',
    value=10,
), 11: TypeValue(
    name='repeat_until_hr_greater_than',
    value=11,
), 12: TypeValue(
    name='repeat_until_power_less_than',
    value=12,
), 13: TypeValue(
    name='repeat_until_power_greater_than',
    value=13,
), 14: TypeValue(
    name='power_less_than',
    value=14,
), 15: TypeValue(
    name='power_greater_than',
    value=15,
), 16: TypeValue(
    name='training_peaks_tss',
    value=16,
), 17: TypeValue(
    name='repeat_until_power_last_lap_less_than',
    value=17,
), 18: TypeValue(
    name='repeat_until_max_power_last_lap_less_than',
    value=18,
), 19: TypeValue(
    name='power_3s_less_than',
    value=19,
), 20: TypeValue(
    name='power_10s_less_than',
    value=20,
), 21: TypeValue(
    name='power_30s_less_than',
    value=21,
), 22: TypeValue(
    name='power_3s_greater_than',
    value=22,
), 23: TypeValue(
    name='power_10s_greater_than',
    value=23,
), 24: TypeValue(
    name='power_30s_greater_than',
    value=24,
), 25: TypeValue(
    name='power_lap_less_than',
    value=25,
), 26: TypeValue(
    name='power_lap_greater_than',
    value=26,
), 27: TypeValue(
    name='repeat_until_training_peaks_tss',
    value=27,
), 28: TypeValue(
    name='repetition_time',
    value=28,
), 29: TypeValue(
    name='reps',
    value=29,
), 31: TypeValue(
    name='time_only',
    value=31,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'wkt_step_target': Type(
    name='wkt_step_target',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='speed',
    value=0,
), 1: TypeValue(
    name='heart_rate',
    value=1,
), 2: TypeValue(
    name='open',
    value=2,
), 3: TypeValue(
    name='cadence',
    value=3,
), 4: TypeValue(
    name='power',
    value=4,
), 5: TypeValue(
    name='grade',
    value=5,
), 6: TypeValue(
    name='resistance',
    value=6,
), 7: TypeValue(
    name='power_3s',
    value=7,
), 8: TypeValue(
    name='power_10s',
    value=8,
), 9: TypeValue(
    name='power_30s',
    value=9,
), 10: TypeValue(
    name='power_lap',
    value=10,
), 11: TypeValue(
    name='swim_stroke',
    value=11,
), 12: TypeValue(
    name='speed_lap',
    value=12,
), 13: TypeValue(
    name='heart_rate_lap',
    value=13,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'goal': Type(
    name='goal',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='time',
    value=0,
), 1: TypeValue(
    name='distance',
    value=1,
), 2: TypeValue(
    name='calories',
    value=2,
), 3: TypeValue(
    name='frequency',
    value=3,
), 4: TypeValue(
    name='steps',
    value=4,
), 5: TypeValue(
    name='ascent',
    value=5,
), 6: TypeValue(
    name='active_minutes',
    value=6,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'goal_recurrence': Type(
    name='goal_recurrence',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='off',
    value=0,
), 1: TypeValue(
    name='daily',
    value=1,
), 2: TypeValue(
    name='weekly',
    value=2,
), 3: TypeValue(
    name='monthly',
    value=3,
), 4: TypeValue(
    name='yearly',
    value=4,
), 5: TypeValue(
    name='custom',
    value=5,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'goal_source': Type(
    name='goal_source',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='auto',
    value=0,
    comment='Device generated',
), 1: TypeValue(
    name='community',
    value=1,
    comment='Social network sourced goal',
), 2: TypeValue(
    name='user',
    value=2,
    comment='Manually generated',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'schedule': Type(
    name='schedule',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='workout',
    value=0,
), 1: TypeValue(
    name='course',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'course_point': Type(
    name='course_point',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='generic',
    value=0,
), 1: TypeValue(
    name='summit',
    value=1,
), 2: TypeValue(
    name='valley',
    value=2,
), 3: TypeValue(
    name='water',
    value=3,
), 4: TypeValue(
    name='food',
    value=4,
), 5: TypeValue(
    name='danger',
    value=5,
), 6: TypeValue(
    name='left',
    value=6,
), 7: TypeValue(
    name='right',
    value=7,
), 8: TypeValue(
    name='straight',
    value=8,
), 9: TypeValue(
    name='first_aid',
    value=9,
), 10: TypeValue(
    name='fourth_category',
    value=10,
), 11: TypeValue(
    name='third_category',
    value=11,
), 12: TypeValue(
    name='second_category',
    value=12,
), 13: TypeValue(
    name='first_category',
    value=13,
), 14: TypeValue(
    name='hors_category',
    value=14,
), 15: TypeValue(
    name='sprint',
    value=15,
), 16: TypeValue(
    name='left_fork',
    value=16,
), 17: TypeValue(
    name='right_fork',
    value=17,
), 18: TypeValue(
    name='middle_fork',
    value=18,
), 19: TypeValue(
    name='slight_left',
    value=19,
), 20: TypeValue(
    name='sharp_left',
    value=20,
), 21: TypeValue(
    name='slight_right',
    value=21,
), 22: TypeValue(
    name='sharp_right',
    value=22,
), 23: TypeValue(
    name='u_turn',
    value=23,
), 24: TypeValue(
    name='segment_start',
    value=24,
), 25: TypeValue(
    name='segment_end',
    value=25,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'manufacturer': Type(
    name='manufacturer',
    base_type='uint16',
    values=Map(
    map={1: TypeValue(
    name='garmin',
    value=1,
), 2: TypeValue(
    name='garmin_fr405_antfs',
    value=2,
    comment='Do not use.  Used by FR405 for ANTFS man id.',
), 3: TypeValue(
    name='zephyr',
    value=3,
), 4: TypeValue(
    name='dayton',
    value=4,
), 5: TypeValue(
    name='idt',
    value=5,
), 6: TypeValue(
    name='srm',
    value=6,
), 7: TypeValue(
    name='quarq',
    value=7,
), 8: TypeValue(
    name='ibike',
    value=8,
), 9: TypeValue(
    name='saris',
    value=9,
), 10: TypeValue(
    name='spark_hk',
    value=10,
), 11: TypeValue(
    name='tanita',
    value=11,
), 12: TypeValue(
    name='echowell',
    value=12,
), 13: TypeValue(
    name='dynastream_oem',
    value=13,
), 14: TypeValue(
    name='nautilus',
    value=14,
), 15: TypeValue(
    name='dynastream',
    value=15,
), 16: TypeValue(
    name='timex',
    value=16,
), 17: TypeValue(
    name='metrigear',
    value=17,
), 18: TypeValue(
    name='xelic',
    value=18,
), 19: TypeValue(
    name='beurer',
    value=19,
), 20: TypeValue(
    name='cardiosport',
    value=20,
), 21: TypeValue(
    name='a_and_d',
    value=21,
), 22: TypeValue(
    name='hmm',
    value=22,
), 23: TypeValue(
    name='suunto',
    value=23,
), 24: TypeValue(
    name='thita_elektronik',
    value=24,
), 25: TypeValue(
    name='gpulse',
    value=25,
), 26: TypeValue(
    name='clean_mobile',
    value=26,
), 27: TypeValue(
    name='pedal_brain',
    value=27,
), 28: TypeValue(
    name='peaksware',
    value=28,
), 29: TypeValue(
    name='saxonar',
    value=29,
), 30: TypeValue(
    name='lemond_fitness',
    value=30,
), 31: TypeValue(
    name='dexcom',
    value=31,
), 32: TypeValue(
    name='wahoo_fitness',
    value=32,
), 33: TypeValue(
    name='octane_fitness',
    value=33,
), 34: TypeValue(
    name='archinoetics',
    value=34,
), 35: TypeValue(
    name='the_hurt_box',
    value=35,
), 36: TypeValue(
    name='citizen_systems',
    value=36,
), 37: TypeValue(
    name='magellan',
    value=37,
), 38: TypeValue(
    name='osynce',
    value=38,
), 39: TypeValue(
    name='holux',
    value=39,
), 40: TypeValue(
    name='concept2',
    value=40,
), 41: TypeValue(
    name='shimano',
    value=41,
), 42: TypeValue(
    name='one_giant_leap',
    value=42,
), 43: TypeValue(
    name='ace_sensor',
    value=43,
), 44: TypeValue(
    name='brim_brothers',
    value=44,
), 45: TypeValue(
    name='xplova',
    value=45,
), 46: TypeValue(
    name='perception_digital',
    value=46,
), 47: TypeValue(
    name='bf1systems',
    value=47,
), 48: TypeValue(
    name='pioneer',
    value=48,
), 49: TypeValue(
    name='spantec',
    value=49,
), 50: TypeValue(
    name='metalogics',
    value=50,
), 51: TypeValue(
    name='4iiiis',
    value=51,
), 52: TypeValue(
    name='seiko_epson',
    value=52,
), 53: TypeValue(
    name='seiko_epson_oem',
    value=53,
), 54: TypeValue(
    name='ifor_powell',
    value=54,
), 55: TypeValue(
    name='maxwell_guider',
    value=55,
), 56: TypeValue(
    name='star_trac',
    value=56,
), 57: TypeValue(
    name='breakaway',
    value=57,
), 58: TypeValue(
    name='alatech_technology_ltd',
    value=58,
), 59: TypeValue(
    name='mio_technology_europe',
    value=59,
), 60: TypeValue(
    name='rotor',
    value=60,
), 61: TypeValue(
    name='geonaute',
    value=61,
), 62: TypeValue(
    name='id_bike',
    value=62,
), 63: TypeValue(
    name='specialized',
    value=63,
), 64: TypeValue(
    name='wtek',
    value=64,
), 65: TypeValue(
    name='physical_enterprises',
    value=65,
), 66: TypeValue(
    name='north_pole_engineering',
    value=66,
), 67: TypeValue(
    name='bkool',
    value=67,
), 68: TypeValue(
    name='cateye',
    value=68,
), 69: TypeValue(
    name='stages_cycling',
    value=69,
), 70: TypeValue(
    name='sigmasport',
    value=70,
), 71: TypeValue(
    name='tomtom',
    value=71,
), 72: TypeValue(
    name='peripedal',
    value=72,
), 73: TypeValue(
    name='wattbike',
    value=73,
), 76: TypeValue(
    name='moxy',
    value=76,
), 77: TypeValue(
    name='ciclosport',
    value=77,
), 78: TypeValue(
    name='powerbahn',
    value=78,
), 79: TypeValue(
    name='acorn_projects_aps',
    value=79,
), 80: TypeValue(
    name='lifebeam',
    value=80,
), 81: TypeValue(
    name='bontrager',
    value=81,
), 82: TypeValue(
    name='wellgo',
    value=82,
), 83: TypeValue(
    name='scosche',
    value=83,
), 84: TypeValue(
    name='magura',
    value=84,
), 85: TypeValue(
    name='woodway',
    value=85,
), 86: TypeValue(
    name='elite',
    value=86,
), 87: TypeValue(
    name='nielsen_kellerman',
    value=87,
), 88: TypeValue(
    name='dk_city',
    value=88,
), 89: TypeValue(
    name='tacx',
    value=89,
), 90: TypeValue(
    name='direction_technology',
    value=90,
), 91: TypeValue(
    name='magtonic',
    value=91,
), 92: TypeValue(
    name='1partcarbon',
    value=92,
), 93: TypeValue(
    name='inside_ride_technologies',
    value=93,
), 94: TypeValue(
    name='sound_of_motion',
    value=94,
), 95: TypeValue(
    name='stryd',
    value=95,
), 96: TypeValue(
    name='icg',
    value=96,
    comment='Indoorcycling Group',
), 97: TypeValue(
    name='MiPulse',
    value=97,
), 98: TypeValue(
    name='bsx_athletics',
    value=98,
), 99: TypeValue(
    name='look',
    value=99,
), 100: TypeValue(
    name='campagnolo_srl',
    value=100,
), 101: TypeValue(
    name='body_bike_smart',
    value=101,
), 102: TypeValue(
    name='praxisworks',
    value=102,
), 103: TypeValue(
    name='limits_technology',
    value=103,
    comment='Limits Technology Ltd.',
), 104: TypeValue(
    name='topaction_technology',
    value=104,
    comment='TopAction Technology Inc.',
), 105: TypeValue(
    name='cosinuss',
    value=105,
), 106: TypeValue(
    name='fitcare',
    value=106,
), 107: TypeValue(
    name='magene',
    value=107,
), 108: TypeValue(
    name='giant_manufacturing_co',
    value=108,
), 109: TypeValue(
    name='tigrasport',
    value=109,
    comment='Tigrasport',
), 110: TypeValue(
    name='salutron',
    value=110,
), 111: TypeValue(
    name='technogym',
    value=111,
), 112: TypeValue(
    name='bryton_sensors',
    value=112,
), 113: TypeValue(
    name='latitude_limited',
    value=113,
), 114: TypeValue(
    name='soaring_technology',
    value=114,
), 115: TypeValue(
    name='igpsport',
    value=115,
), 116: TypeValue(
    name='thinkrider',
    value=116,
), 117: TypeValue(
    name='gopher_sport',
    value=117,
), 118: TypeValue(
    name='waterrower',
    value=118,
), 119: TypeValue(
    name='orangetheory',
    value=119,
), 120: TypeValue(
    name='inpeak',
    value=120,
), 121: TypeValue(
    name='kinetic',
    value=121,
), 122: TypeValue(
    name='johnson_health_tech',
    value=122,
), 123: TypeValue(
    name='polar_electro',
    value=123,
), 124: TypeValue(
    name='seesense',
    value=124,
), 125: TypeValue(
    name='nci_technology',
    value=125,
), 126: TypeValue(
    name='iqsquare',
    value=126,
), 127: TypeValue(
    name='leomo',
    value=127,
), 128: TypeValue(
    name='ifit_com',
    value=128,
), 129: TypeValue(
    name='coros_byte',
    value=129,
), 130: TypeValue(
    name='versa_design',
    value=130,
), 131: TypeValue(
    name='chileaf',
    value=131,
), 132: TypeValue(
    name='cycplus',
    value=132,
), 133: TypeValue(
    name='gravaa_byte',
    value=133,
), 134: TypeValue(
    name='sigeyi',
    value=134,
), 135: TypeValue(
    name='coospo',
    value=135,
), 136: TypeValue(
    name='geoid',
    value=136,
), 255: TypeValue(
    name='development',
    value=255,
), 257: TypeValue(
    name='healthandlife',
    value=257,
), 258: TypeValue(
    name='lezyne',
    value=258,
), 259: TypeValue(
    name='scribe_labs',
    value=259,
), 260: TypeValue(
    name='zwift',
    value=260,
), 261: TypeValue(
    name='watteam',
    value=261,
), 262: TypeValue(
    name='recon',
    value=262,
), 263: TypeValue(
    name='favero_electronics',
    value=263,
), 264: TypeValue(
    name='dynovelo',
    value=264,
), 265: TypeValue(
    name='strava',
    value=265,
), 266: TypeValue(
    name='precor',
    value=266,
    comment='Amer Sports',
), 267: TypeValue(
    name='bryton',
    value=267,
), 268: TypeValue(
    name='sram',
    value=268,
), 269: TypeValue(
    name='navman',
    value=269,
    comment='MiTAC Global Corporation (Mio Technology)',
), 270: TypeValue(
    name='cobi',
    value=270,
    comment='COBI GmbH',
), 271: TypeValue(
    name='spivi',
    value=271,
), 272: TypeValue(
    name='mio_magellan',
    value=272,
), 273: TypeValue(
    name='evesports',
    value=273,
), 274: TypeValue(
    name='sensitivus_gauge',
    value=274,
), 275: TypeValue(
    name='podoon',
    value=275,
), 276: TypeValue(
    name='life_time_fitness',
    value=276,
), 277: TypeValue(
    name='falco_e_motors',
    value=277,
    comment='Falco eMotors Inc.',
), 278: TypeValue(
    name='minoura',
    value=278,
), 279: TypeValue(
    name='cycliq',
    value=279,
), 280: TypeValue(
    name='luxottica',
    value=280,
), 281: TypeValue(
    name='trainer_road',
    value=281,
), 282: TypeValue(
    name='the_sufferfest',
    value=282,
), 283: TypeValue(
    name='fullspeedahead',
    value=283,
), 284: TypeValue(
    name='virtualtraining',
    value=284,
), 285: TypeValue(
    name='feedbacksports',
    value=285,
), 286: TypeValue(
    name='omata',
    value=286,
), 287: TypeValue(
    name='vdo',
    value=287,
), 288: TypeValue(
    name='magneticdays',
    value=288,
), 289: TypeValue(
    name='hammerhead',
    value=289,
), 290: TypeValue(
    name='kinetic_by_kurt',
    value=290,
), 291: TypeValue(
    name='shapelog',
    value=291,
), 292: TypeValue(
    name='dabuziduo',
    value=292,
), 293: TypeValue(
    name='jetblack',
    value=293,
), 294: TypeValue(
    name='coros',
    value=294,
), 295: TypeValue(
    name='virtugo',
    value=295,
), 296: TypeValue(
    name='velosense',
    value=296,
), 297: TypeValue(
    name='cycligentinc',
    value=297,
), 298: TypeValue(
    name='trailforks',
    value=298,
), 299: TypeValue(
    name='mahle_ebikemotion',
    value=299,
), 300: TypeValue(
    name='nurvv',
    value=300,
), 301: TypeValue(
    name='microprogram',
    value=301,
), 302: TypeValue(
    name='zone5cloud',
    value=302,
), 303: TypeValue(
    name='greenteg',
    value=303,
), 304: TypeValue(
    name='yamaha_motors',
    value=304,
), 305: TypeValue(
    name='whoop',
    value=305,
), 306: TypeValue(
    name='gravaa',
    value=306,
), 307: TypeValue(
    name='onelap',
    value=307,
), 308: TypeValue(
    name='monark_exercise',
    value=308,
), 309: TypeValue(
    name='form',
    value=309,
), 310: TypeValue(
    name='decathlon',
    value=310,
), 311: TypeValue(
    name='syncros',
    value=311,
), 5759: TypeValue(
    name='actigraphcorp',
    value=5759,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'garmin_product': Type(
    name='garmin_product',
    base_type='uint16',
    values=Map(
    map={1: TypeValue(
    name='hrm1',
    value=1,
), 2: TypeValue(
    name='axh01',
    value=2,
    comment='AXH01 HRM chipset',
), 3: TypeValue(
    name='axb01',
    value=3,
), 4: TypeValue(
    name='axb02',
    value=4,
), 5: TypeValue(
    name='hrm2ss',
    value=5,
), 6: TypeValue(
    name='dsi_alf02',
    value=6,
), 7: TypeValue(
    name='hrm3ss',
    value=7,
), 8: TypeValue(
    name='hrm_run_single_byte_product_id',
    value=8,
    comment='hrm_run model for HRM ANT+ messaging',
), 9: TypeValue(
    name='bsm',
    value=9,
    comment='BSM model for ANT+ messaging',
), 10: TypeValue(
    name='bcm',
    value=10,
    comment='BCM model for ANT+ messaging',
), 11: TypeValue(
    name='axs01',
    value=11,
    comment='AXS01 HRM Bike Chipset model for ANT+ messaging',
), 12: TypeValue(
    name='hrm_tri_single_byte_product_id',
    value=12,
    comment='hrm_tri model for HRM ANT+ messaging',
), 13: TypeValue(
    name='hrm4_run_single_byte_product_id',
    value=13,
    comment='hrm4 run model for HRM ANT+ messaging',
), 14: TypeValue(
    name='fr225_single_byte_product_id',
    value=14,
    comment='fr225 model for HRM ANT+ messaging',
), 15: TypeValue(
    name='gen3_bsm_single_byte_product_id',
    value=15,
    comment='gen3_bsm model for Bike Speed ANT+ messaging',
), 16: TypeValue(
    name='gen3_bcm_single_byte_product_id',
    value=16,
    comment='gen3_bcm model for Bike Cadence ANT+ messaging',
), 473: TypeValue(
    name='fr301_china',
    value=473,
), 474: TypeValue(
    name='fr301_japan',
    value=474,
), 475: TypeValue(
    name='fr301_korea',
    value=475,
), 494: TypeValue(
    name='fr301_taiwan',
    value=494,
), 717: TypeValue(
    name='fr405',
    value=717,
    comment='Forerunner 405',
), 782: TypeValue(
    name='fr50',
    value=782,
    comment='Forerunner 50',
), 987: TypeValue(
    name='fr405_japan',
    value=987,
), 988: TypeValue(
    name='fr60',
    value=988,
    comment='Forerunner 60',
), 1011: TypeValue(
    name='dsi_alf01',
    value=1011,
), 1018: TypeValue(
    name='fr310xt',
    value=1018,
    comment='Forerunner 310',
), 1036: TypeValue(
    name='edge500',
    value=1036,
), 1124: TypeValue(
    name='fr110',
    value=1124,
    comment='Forerunner 110',
), 1169: TypeValue(
    name='edge800',
    value=1169,
), 1199: TypeValue(
    name='edge500_taiwan',
    value=1199,
), 1213: TypeValue(
    name='edge500_japan',
    value=1213,
), 1253: TypeValue(
    name='chirp',
    value=1253,
), 1274: TypeValue(
    name='fr110_japan',
    value=1274,
), 1325: TypeValue(
    name='edge200',
    value=1325,
), 1328: TypeValue(
    name='fr910xt',
    value=1328,
), 1333: TypeValue(
    name='edge800_taiwan',
    value=1333,
), 1334: TypeValue(
    name='edge800_japan',
    value=1334,
), 1341: TypeValue(
    name='alf04',
    value=1341,
), 1345: TypeValue(
    name='fr610',
    value=1345,
), 1360: TypeValue(
    name='fr210_japan',
    value=1360,
), 1380: TypeValue(
    name='vector_ss',
    value=1380,
), 1381: TypeValue(
    name='vector_cp',
    value=1381,
), 1386: TypeValue(
    name='edge800_china',
    value=1386,
), 1387: TypeValue(
    name='edge500_china',
    value=1387,
), 1405: TypeValue(
    name='approach_g10',
    value=1405,
), 1410: TypeValue(
    name='fr610_japan',
    value=1410,
), 1422: TypeValue(
    name='edge500_korea',
    value=1422,
), 1436: TypeValue(
    name='fr70',
    value=1436,
), 1446: TypeValue(
    name='fr310xt_4t',
    value=1446,
), 1461: TypeValue(
    name='amx',
    value=1461,
), 1482: TypeValue(
    name='fr10',
    value=1482,
), 1497: TypeValue(
    name='edge800_korea',
    value=1497,
), 1499: TypeValue(
    name='swim',
    value=1499,
), 1537: TypeValue(
    name='fr910xt_china',
    value=1537,
), 1551: TypeValue(
    name='fenix',
    value=1551,
), 1555: TypeValue(
    name='edge200_taiwan',
    value=1555,
), 1561: TypeValue(
    name='edge510',
    value=1561,
), 1567: TypeValue(
    name='edge810',
    value=1567,
), 1570: TypeValue(
    name='tempe',
    value=1570,
), 1600: TypeValue(
    name='fr910xt_japan',
    value=1600,
), 1623: TypeValue(
    name='fr620',
    value=1623,
), 1632: TypeValue(
    name='fr220',
    value=1632,
), 1664: TypeValue(
    name='fr910xt_korea',
    value=1664,
), 1688: TypeValue(
    name='fr10_japan',
    value=1688,
), 1721: TypeValue(
    name='edge810_japan',
    value=1721,
), 1735: TypeValue(
    name='virb_elite',
    value=1735,
), 1736: TypeValue(
    name='edge_touring',
    value=1736,
    comment='Also Edge Touring Plus',
), 1742: TypeValue(
    name='edge510_japan',
    value=1742,
), 1743: TypeValue(
    name='hrm_tri',
    value=1743,
    comment='Also HRM-Swim',
), 1752: TypeValue(
    name='hrm_run',
    value=1752,
), 1765: TypeValue(
    name='fr920xt',
    value=1765,
), 1821: TypeValue(
    name='edge510_asia',
    value=1821,
), 1822: TypeValue(
    name='edge810_china',
    value=1822,
), 1823: TypeValue(
    name='edge810_taiwan',
    value=1823,
), 1836: TypeValue(
    name='edge1000',
    value=1836,
), 1837: TypeValue(
    name='vivo_fit',
    value=1837,
), 1853: TypeValue(
    name='virb_remote',
    value=1853,
), 1885: TypeValue(
    name='vivo_ki',
    value=1885,
), 1903: TypeValue(
    name='fr15',
    value=1903,
), 1907: TypeValue(
    name='vivo_active',
    value=1907,
), 1918: TypeValue(
    name='edge510_korea',
    value=1918,
), 1928: TypeValue(
    name='fr620_japan',
    value=1928,
), 1929: TypeValue(
    name='fr620_china',
    value=1929,
), 1930: TypeValue(
    name='fr220_japan',
    value=1930,
), 1931: TypeValue(
    name='fr220_china',
    value=1931,
), 1936: TypeValue(
    name='approach_s6',
    value=1936,
), 1956: TypeValue(
    name='vivo_smart',
    value=1956,
), 1967: TypeValue(
    name='fenix2',
    value=1967,
), 1988: TypeValue(
    name='epix',
    value=1988,
), 2050: TypeValue(
    name='fenix3',
    value=2050,
), 2052: TypeValue(
    name='edge1000_taiwan',
    value=2052,
), 2053: TypeValue(
    name='edge1000_japan',
    value=2053,
), 2061: TypeValue(
    name='fr15_japan',
    value=2061,
), 2067: TypeValue(
    name='edge520',
    value=2067,
), 2070: TypeValue(
    name='edge1000_china',
    value=2070,
), 2072: TypeValue(
    name='fr620_russia',
    value=2072,
), 2073: TypeValue(
    name='fr220_russia',
    value=2073,
), 2079: TypeValue(
    name='vector_s',
    value=2079,
), 2100: TypeValue(
    name='edge1000_korea',
    value=2100,
), 2130: TypeValue(
    name='fr920xt_taiwan',
    value=2130,
), 2131: TypeValue(
    name='fr920xt_china',
    value=2131,
), 2132: TypeValue(
    name='fr920xt_japan',
    value=2132,
), 2134: TypeValue(
    name='virbx',
    value=2134,
), 2135: TypeValue(
    name='vivo_smart_apac',
    value=2135,
), 2140: TypeValue(
    name='etrex_touch',
    value=2140,
), 2147: TypeValue(
    name='edge25',
    value=2147,
), 2148: TypeValue(
    name='fr25',
    value=2148,
), 2150: TypeValue(
    name='vivo_fit2',
    value=2150,
), 2153: TypeValue(
    name='fr225',
    value=2153,
), 2156: TypeValue(
    name='fr630',
    value=2156,
), 2157: TypeValue(
    name='fr230',
    value=2157,
), 2158: TypeValue(
    name='fr735xt',
    value=2158,
), 2160: TypeValue(
    name='vivo_active_apac',
    value=2160,
), 2161: TypeValue(
    name='vector_2',
    value=2161,
), 2162: TypeValue(
    name='vector_2s',
    value=2162,
), 2172: TypeValue(
    name='virbxe',
    value=2172,
), 2173: TypeValue(
    name='fr620_taiwan',
    value=2173,
), 2174: TypeValue(
    name='fr220_taiwan',
    value=2174,
), 2175: TypeValue(
    name='truswing',
    value=2175,
), 2187: TypeValue(
    name='d2airvenu',
    value=2187,
), 2188: TypeValue(
    name='fenix3_china',
    value=2188,
), 2189: TypeValue(
    name='fenix3_twn',
    value=2189,
), 2192: TypeValue(
    name='varia_headlight',
    value=2192,
), 2193: TypeValue(
    name='varia_taillight_old',
    value=2193,
), 2204: TypeValue(
    name='edge_explore_1000',
    value=2204,
), 2219: TypeValue(
    name='fr225_asia',
    value=2219,
), 2225: TypeValue(
    name='varia_radar_taillight',
    value=2225,
), 2226: TypeValue(
    name='varia_radar_display',
    value=2226,
), 2238: TypeValue(
    name='edge20',
    value=2238,
), 2260: TypeValue(
    name='edge520_asia',
    value=2260,
), 2261: TypeValue(
    name='edge520_japan',
    value=2261,
), 2262: TypeValue(
    name='d2_bravo',
    value=2262,
), 2266: TypeValue(
    name='approach_s20',
    value=2266,
), 2271: TypeValue(
    name='vivo_smart2',
    value=2271,
), 2274: TypeValue(
    name='edge1000_thai',
    value=2274,
), 2276: TypeValue(
    name='varia_remote',
    value=2276,
), 2288: TypeValue(
    name='edge25_asia',
    value=2288,
), 2289: TypeValue(
    name='edge25_jpn',
    value=2289,
), 2290: TypeValue(
    name='edge20_asia',
    value=2290,
), 2292: TypeValue(
    name='approach_x40',
    value=2292,
), 2293: TypeValue(
    name='fenix3_japan',
    value=2293,
), 2294: TypeValue(
    name='vivo_smart_emea',
    value=2294,
), 2310: TypeValue(
    name='fr630_asia',
    value=2310,
), 2311: TypeValue(
    name='fr630_jpn',
    value=2311,
), 2313: TypeValue(
    name='fr230_jpn',
    value=2313,
), 2327: TypeValue(
    name='hrm4_run',
    value=2327,
), 2332: TypeValue(
    name='epix_japan',
    value=2332,
), 2337: TypeValue(
    name='vivo_active_hr',
    value=2337,
), 2347: TypeValue(
    name='vivo_smart_gps_hr',
    value=2347,
), 2348: TypeValue(
    name='vivo_smart_hr',
    value=2348,
), 2361: TypeValue(
    name='vivo_smart_hr_asia',
    value=2361,
), 2362: TypeValue(
    name='vivo_smart_gps_hr_asia',
    value=2362,
), 2368: TypeValue(
    name='vivo_move',
    value=2368,
), 2379: TypeValue(
    name='varia_taillight',
    value=2379,
), 2396: TypeValue(
    name='fr235_asia',
    value=2396,
), 2397: TypeValue(
    name='fr235_japan',
    value=2397,
), 2398: TypeValue(
    name='varia_vision',
    value=2398,
), 2406: TypeValue(
    name='vivo_fit3',
    value=2406,
), 2407: TypeValue(
    name='fenix3_korea',
    value=2407,
), 2408: TypeValue(
    name='fenix3_sea',
    value=2408,
), 2413: TypeValue(
    name='fenix3_hr',
    value=2413,
), 2417: TypeValue(
    name='virb_ultra_30',
    value=2417,
), 2429: TypeValue(
    name='index_smart_scale',
    value=2429,
), 2431: TypeValue(
    name='fr235',
    value=2431,
), 2432: TypeValue(
    name='fenix3_chronos',
    value=2432,
), 2441: TypeValue(
    name='oregon7xx',
    value=2441,
), 2444: TypeValue(
    name='rino7xx',
    value=2444,
), 2457: TypeValue(
    name='epix_korea',
    value=2457,
), 2473: TypeValue(
    name='fenix3_hr_chn',
    value=2473,
), 2474: TypeValue(
    name='fenix3_hr_twn',
    value=2474,
), 2475: TypeValue(
    name='fenix3_hr_jpn',
    value=2475,
), 2476: TypeValue(
    name='fenix3_hr_sea',
    value=2476,
), 2477: TypeValue(
    name='fenix3_hr_kor',
    value=2477,
), 2496: TypeValue(
    name='nautix',
    value=2496,
), 2497: TypeValue(
    name='vivo_active_hr_apac',
    value=2497,
), 2512: TypeValue(
    name='oregon7xx_ww',
    value=2512,
), 2530: TypeValue(
    name='edge_820',
    value=2530,
), 2531: TypeValue(
    name='edge_explore_820',
    value=2531,
), 2533: TypeValue(
    name='fr735xt_apac',
    value=2533,
), 2534: TypeValue(
    name='fr735xt_japan',
    value=2534,
), 2544: TypeValue(
    name='fenix5s',
    value=2544,
), 2547: TypeValue(
    name='d2_bravo_titanium',
    value=2547,
), 2567: TypeValue(
    name='varia_ut800',
    value=2567,
    comment='Varia UT 800 SW',
), 2593: TypeValue(
    name='running_dynamics_pod',
    value=2593,
), 2599: TypeValue(
    name='edge_820_china',
    value=2599,
), 2600: TypeValue(
    name='edge_820_japan',
    value=2600,
), 2604: TypeValue(
    name='fenix5x',
    value=2604,
), 2606: TypeValue(
    name='vivo_fit_jr',
    value=2606,
), 2622: TypeValue(
    name='vivo_smart3',
    value=2622,
), 2623: TypeValue(
    name='vivo_sport',
    value=2623,
), 2628: TypeValue(
    name='edge_820_taiwan',
    value=2628,
), 2629: TypeValue(
    name='edge_820_korea',
    value=2629,
), 2630: TypeValue(
    name='edge_820_sea',
    value=2630,
), 2650: TypeValue(
    name='fr35_hebrew',
    value=2650,
), 2656: TypeValue(
    name='approach_s60',
    value=2656,
), 2667: TypeValue(
    name='fr35_apac',
    value=2667,
), 2668: TypeValue(
    name='fr35_japan',
    value=2668,
), 2675: TypeValue(
    name='fenix3_chronos_asia',
    value=2675,
), 2687: TypeValue(
    name='virb_360',
    value=2687,
), 2691: TypeValue(
    name='fr935',
    value=2691,
), 2697: TypeValue(
    name='fenix5',
    value=2697,
), 2700: TypeValue(
    name='vivoactive3',
    value=2700,
), 2733: TypeValue(
    name='fr235_china_nfc',
    value=2733,
), 2769: TypeValue(
    name='foretrex_601_701',
    value=2769,
), 2772: TypeValue(
    name='vivo_move_hr',
    value=2772,
), 2713: TypeValue(
    name='edge_1030',
    value=2713,
), 2787: TypeValue(
    name='vector_3',
    value=2787,
), 2796: TypeValue(
    name='fenix5_asia',
    value=2796,
), 2797: TypeValue(
    name='fenix5s_asia',
    value=2797,
), 2798: TypeValue(
    name='fenix5x_asia',
    value=2798,
), 2806: TypeValue(
    name='approach_z80',
    value=2806,
), 2814: TypeValue(
    name='fr35_korea',
    value=2814,
), 2819: TypeValue(
    name='d2charlie',
    value=2819,
), 2831: TypeValue(
    name='vivo_smart3_apac',
    value=2831,
), 2832: TypeValue(
    name='vivo_sport_apac',
    value=2832,
), 2833: TypeValue(
    name='fr935_asia',
    value=2833,
), 2859: TypeValue(
    name='descent',
    value=2859,
), 2878: TypeValue(
    name='vivo_fit4',
    value=2878,
), 2886: TypeValue(
    name='fr645',
    value=2886,
), 2888: TypeValue(
    name='fr645m',
    value=2888,
), 2891: TypeValue(
    name='fr30',
    value=2891,
), 2900: TypeValue(
    name='fenix5s_plus',
    value=2900,
), 2909: TypeValue(
    name='Edge_130',
    value=2909,
), 2924: TypeValue(
    name='edge_1030_asia',
    value=2924,
), 2927: TypeValue(
    name='vivosmart_4',
    value=2927,
), 2945: TypeValue(
    name='vivo_move_hr_asia',
    value=2945,
), 2962: TypeValue(
    name='approach_x10',
    value=2962,
), 2977: TypeValue(
    name='fr30_asia',
    value=2977,
), 2988: TypeValue(
    name='vivoactive3m_w',
    value=2988,
), 3003: TypeValue(
    name='fr645_asia',
    value=3003,
), 3004: TypeValue(
    name='fr645m_asia',
    value=3004,
), 3011: TypeValue(
    name='edge_explore',
    value=3011,
), 3028: TypeValue(
    name='gpsmap66',
    value=3028,
), 3049: TypeValue(
    name='approach_s10',
    value=3049,
), 3066: TypeValue(
    name='vivoactive3m_l',
    value=3066,
), 3085: TypeValue(
    name='approach_g80',
    value=3085,
), 3092: TypeValue(
    name='edge_130_asia',
    value=3092,
), 3095: TypeValue(
    name='edge_1030_bontrager',
    value=3095,
), 3110: TypeValue(
    name='fenix5_plus',
    value=3110,
), 3111: TypeValue(
    name='fenix5x_plus',
    value=3111,
), 3112: TypeValue(
    name='edge_520_plus',
    value=3112,
), 3113: TypeValue(
    name='fr945',
    value=3113,
), 3121: TypeValue(
    name='edge_530',
    value=3121,
), 3122: TypeValue(
    name='edge_830',
    value=3122,
), 3126: TypeValue(
    name='instinct_esports',
    value=3126,
), 3134: TypeValue(
    name='fenix5s_plus_apac',
    value=3134,
), 3135: TypeValue(
    name='fenix5x_plus_apac',
    value=3135,
), 3142: TypeValue(
    name='edge_520_plus_apac',
    value=3142,
), 3144: TypeValue(
    name='fr235l_asia',
    value=3144,
), 3145: TypeValue(
    name='fr245_asia',
    value=3145,
), 3163: TypeValue(
    name='vivo_active3m_apac',
    value=3163,
), 3192: TypeValue(
    name='gen3_bsm',
    value=3192,
    comment='gen3 bike speed sensor',
), 3193: TypeValue(
    name='gen3_bcm',
    value=3193,
    comment='gen3 bike cadence sensor',
), 3218: TypeValue(
    name='vivo_smart4_asia',
    value=3218,
), 3224: TypeValue(
    name='vivoactive4_small',
    value=3224,
), 3225: TypeValue(
    name='vivoactive4_large',
    value=3225,
), 3226: TypeValue(
    name='venu',
    value=3226,
), 3246: TypeValue(
    name='marq_driver',
    value=3246,
), 3247: TypeValue(
    name='marq_aviator',
    value=3247,
), 3248: TypeValue(
    name='marq_captain',
    value=3248,
), 3249: TypeValue(
    name='marq_commander',
    value=3249,
), 3250: TypeValue(
    name='marq_expedition',
    value=3250,
), 3251: TypeValue(
    name='marq_athlete',
    value=3251,
), 3258: TypeValue(
    name='descent_mk2',
    value=3258,
), 3284: TypeValue(
    name='gpsmap66i',
    value=3284,
), 3287: TypeValue(
    name='fenix6S_sport',
    value=3287,
), 3288: TypeValue(
    name='fenix6S',
    value=3288,
), 3289: TypeValue(
    name='fenix6_sport',
    value=3289,
), 3290: TypeValue(
    name='fenix6',
    value=3290,
), 3291: TypeValue(
    name='fenix6x',
    value=3291,
), 3299: TypeValue(
    name='hrm_dual',
    value=3299,
    comment='HRM-Dual',
), 3300: TypeValue(
    name='hrm_pro',
    value=3300,
    comment='HRM-Pro',
), 3308: TypeValue(
    name='vivo_move3_premium',
    value=3308,
), 3314: TypeValue(
    name='approach_s40',
    value=3314,
), 3321: TypeValue(
    name='fr245m_asia',
    value=3321,
), 3349: TypeValue(
    name='edge_530_apac',
    value=3349,
), 3350: TypeValue(
    name='edge_830_apac',
    value=3350,
), 3378: TypeValue(
    name='vivo_move3',
    value=3378,
), 3387: TypeValue(
    name='vivo_active4_small_asia',
    value=3387,
), 3388: TypeValue(
    name='vivo_active4_large_asia',
    value=3388,
), 3389: TypeValue(
    name='vivo_active4_oled_asia',
    value=3389,
), 3405: TypeValue(
    name='swim2',
    value=3405,
), 3420: TypeValue(
    name='marq_driver_asia',
    value=3420,
), 3421: TypeValue(
    name='marq_aviator_asia',
    value=3421,
), 3422: TypeValue(
    name='vivo_move3_asia',
    value=3422,
), 3441: TypeValue(
    name='fr945_asia',
    value=3441,
), 3446: TypeValue(
    name='vivo_active3t_chn',
    value=3446,
), 3448: TypeValue(
    name='marq_captain_asia',
    value=3448,
), 3449: TypeValue(
    name='marq_commander_asia',
    value=3449,
), 3450: TypeValue(
    name='marq_expedition_asia',
    value=3450,
), 3451: TypeValue(
    name='marq_athlete_asia',
    value=3451,
), 3469: TypeValue(
    name='fr45_asia',
    value=3469,
), 3473: TypeValue(
    name='vivoactive3_daimler',
    value=3473,
), 3498: TypeValue(
    name='legacy_rey',
    value=3498,
), 3499: TypeValue(
    name='legacy_darth_vader',
    value=3499,
), 3500: TypeValue(
    name='legacy_captain_marvel',
    value=3500,
), 3501: TypeValue(
    name='legacy_first_avenger',
    value=3501,
), 3512: TypeValue(
    name='fenix6s_sport_asia',
    value=3512,
), 3513: TypeValue(
    name='fenix6s_asia',
    value=3513,
), 3514: TypeValue(
    name='fenix6_sport_asia',
    value=3514,
), 3515: TypeValue(
    name='fenix6_asia',
    value=3515,
), 3516: TypeValue(
    name='fenix6x_asia',
    value=3516,
), 3535: TypeValue(
    name='legacy_captain_marvel_asia',
    value=3535,
), 3536: TypeValue(
    name='legacy_first_avenger_asia',
    value=3536,
), 3537: TypeValue(
    name='legacy_rey_asia',
    value=3537,
), 3538: TypeValue(
    name='legacy_darth_vader_asia',
    value=3538,
), 3542: TypeValue(
    name='descent_mk2s',
    value=3542,
), 3558: TypeValue(
    name='edge_130_plus',
    value=3558,
), 3570: TypeValue(
    name='edge_1030_plus',
    value=3570,
), 3578: TypeValue(
    name='rally_200',
    value=3578,
    comment='Rally 100/200 Power Meter Series',
), 3589: TypeValue(
    name='fr745',
    value=3589,
), 3600: TypeValue(
    name='venusq',
    value=3600,
), 3615: TypeValue(
    name='lily',
    value=3615,
), 3624: TypeValue(
    name='marq_adventurer',
    value=3624,
), 3638: TypeValue(
    name='enduro',
    value=3638,
), 3639: TypeValue(
    name='swim2_apac',
    value=3639,
), 3648: TypeValue(
    name='marq_adventurer_asia',
    value=3648,
), 3652: TypeValue(
    name='fr945_lte',
    value=3652,
), 3702: TypeValue(
    name='descent_mk2_asia',
    value=3702,
    comment='Mk2 and Mk2i',
), 3703: TypeValue(
    name='venu2',
    value=3703,
), 3704: TypeValue(
    name='venu2s',
    value=3704,
), 3737: TypeValue(
    name='venu_daimler_asia',
    value=3737,
), 3739: TypeValue(
    name='marq_golfer',
    value=3739,
), 3740: TypeValue(
    name='venu_daimler',
    value=3740,
), 3794: TypeValue(
    name='fr745_asia',
    value=3794,
), 3809: TypeValue(
    name='lily_asia',
    value=3809,
), 3812: TypeValue(
    name='edge_1030_plus_asia',
    value=3812,
), 3813: TypeValue(
    name='edge_130_plus_asia',
    value=3813,
), 3823: TypeValue(
    name='approach_s12',
    value=3823,
), 3872: TypeValue(
    name='enduro_asia',
    value=3872,
), 3837: TypeValue(
    name='venusq_asia',
    value=3837,
), 3850: TypeValue(
    name='marq_golfer_asia',
    value=3850,
), 3869: TypeValue(
    name='fr55',
    value=3869,
), 3927: TypeValue(
    name='approach_g12',
    value=3927,
), 3930: TypeValue(
    name='descent_mk2s_asia',
    value=3930,
), 3934: TypeValue(
    name='approach_s42',
    value=3934,
), 3949: TypeValue(
    name='venu2s_asia',
    value=3949,
), 3950: TypeValue(
    name='venu2_asia',
    value=3950,
), 3978: TypeValue(
    name='fr945_lte_asia',
    value=3978,
), 3986: TypeValue(
    name='approach_S12_asia',
    value=3986,
), 4001: TypeValue(
    name='approach_g12_asia',
    value=4001,
), 4002: TypeValue(
    name='approach_s42_asia',
    value=4002,
), 4033: TypeValue(
    name='fr55_asia',
    value=4033,
), 10007: TypeValue(
    name='sdm4',
    value=10007,
    comment='SDM4 footpod',
), 10014: TypeValue(
    name='edge_remote',
    value=10014,
), 20533: TypeValue(
    name='tacx_training_app_win',
    value=20533,
), 20534: TypeValue(
    name='tacx_training_app_mac',
    value=20534,
), 20119: TypeValue(
    name='training_center',
    value=20119,
), 30045: TypeValue(
    name='tacx_training_app_android',
    value=30045,
), 30046: TypeValue(
    name='tacx_training_app_ios',
    value=30046,
), 30047: TypeValue(
    name='tacx_training_app_legacy',
    value=30047,
), 65531: TypeValue(
    name='connectiq_simulator',
    value=65531,
), 65532: TypeValue(
    name='android_antplus_plugin',
    value=65532,
), 65534: TypeValue(
    name='connect',
    value=65534,
    comment='Garmin Connect website',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'antplus_device_type': Type(
    name='antplus_device_type',
    base_type='uint8',
    values=Map(
    map={1: TypeValue(
    name='antfs',
    value=1,
), 11: TypeValue(
    name='bike_power',
    value=11,
), 12: TypeValue(
    name='environment_sensor_legacy',
    value=12,
), 15: TypeValue(
    name='multi_sport_speed_distance',
    value=15,
), 16: TypeValue(
    name='control',
    value=16,
), 17: TypeValue(
    name='fitness_equipment',
    value=17,
), 18: TypeValue(
    name='blood_pressure',
    value=18,
), 19: TypeValue(
    name='geocache_node',
    value=19,
), 20: TypeValue(
    name='light_electric_vehicle',
    value=20,
), 25: TypeValue(
    name='env_sensor',
    value=25,
), 26: TypeValue(
    name='racquet',
    value=26,
), 27: TypeValue(
    name='control_hub',
    value=27,
), 31: TypeValue(
    name='muscle_oxygen',
    value=31,
), 34: TypeValue(
    name='shifting',
    value=34,
), 35: TypeValue(
    name='bike_light_main',
    value=35,
), 36: TypeValue(
    name='bike_light_shared',
    value=36,
), 38: TypeValue(
    name='exd',
    value=38,
), 40: TypeValue(
    name='bike_radar',
    value=40,
), 46: TypeValue(
    name='bike_aero',
    value=46,
), 119: TypeValue(
    name='weight_scale',
    value=119,
), 120: TypeValue(
    name='heart_rate',
    value=120,
), 121: TypeValue(
    name='bike_speed_cadence',
    value=121,
), 122: TypeValue(
    name='bike_cadence',
    value=122,
), 123: TypeValue(
    name='bike_speed',
    value=123,
), 124: TypeValue(
    name='stride_speed_distance',
    value=124,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'ant_network': Type(
    name='ant_network',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='public',
    value=0,
), 1: TypeValue(
    name='antplus',
    value=1,
), 2: TypeValue(
    name='antfs',
    value=2,
), 3: TypeValue(
    name='private',
    value=3,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'workout_capabilities': Type(
    name='workout_capabilities',
    base_type='uint32z',
    values=Map(
    map={1: TypeValue(
    name='interval',
    value=1,
), 2: TypeValue(
    name='custom',
    value=2,
), 4: TypeValue(
    name='fitness_equipment',
    value=4,
), 8: TypeValue(
    name='firstbeat',
    value=8,
), 16: TypeValue(
    name='new_leaf',
    value=16,
), 32: TypeValue(
    name='tcx',
    value=32,
    comment='For backwards compatibility.  Watch should add missing id fields then clear flag.',
), 128: TypeValue(
    name='speed',
    value=128,
    comment='Speed source required for workout step.',
), 256: TypeValue(
    name='heart_rate',
    value=256,
    comment='Heart rate source required for workout step.',
), 512: TypeValue(
    name='distance',
    value=512,
    comment='Distance source required for workout step.',
), 1024: TypeValue(
    name='cadence',
    value=1024,
    comment='Cadence source required for workout step.',
), 2048: TypeValue(
    name='power',
    value=2048,
    comment='Power source required for workout step.',
), 4096: TypeValue(
    name='grade',
    value=4096,
    comment='Grade source required for workout step.',
), 8192: TypeValue(
    name='resistance',
    value=8192,
    comment='Resistance source required for workout step.',
), 16384: TypeValue(
    name='protected',
    value=16384,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'battery_status': Type(
    name='battery_status',
    base_type='uint8',
    values=Map(
    map={1: TypeValue(
    name='new',
    value=1,
), 2: TypeValue(
    name='good',
    value=2,
), 3: TypeValue(
    name='ok',
    value=3,
), 4: TypeValue(
    name='low',
    value=4,
), 5: TypeValue(
    name='critical',
    value=5,
), 6: TypeValue(
    name='charging',
    value=6,
), 7: TypeValue(
    name='unknown',
    value=7,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'hr_type': Type(
    name='hr_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='normal',
    value=0,
), 1: TypeValue(
    name='irregular',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'course_capabilities': Type(
    name='course_capabilities',
    base_type='uint32z',
    values=Map(
    map={1: TypeValue(
    name='processed',
    value=1,
), 2: TypeValue(
    name='valid',
    value=2,
), 4: TypeValue(
    name='time',
    value=4,
), 8: TypeValue(
    name='distance',
    value=8,
), 16: TypeValue(
    name='position',
    value=16,
), 32: TypeValue(
    name='heart_rate',
    value=32,
), 64: TypeValue(
    name='power',
    value=64,
), 128: TypeValue(
    name='cadence',
    value=128,
), 256: TypeValue(
    name='training',
    value=256,
), 512: TypeValue(
    name='navigation',
    value=512,
), 1024: TypeValue(
    name='bikeway',
    value=1024,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'weight': Type(
    name='weight',
    base_type='uint16',
    values=Map(
    map={65534: TypeValue(
    name='calculating',
    value=65534,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'workout_hr': Type(
    name='workout_hr',
    base_type='uint32',
    values=Map(
    map={100: TypeValue(
    name='bpm_offset',
    value=100,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'workout_power': Type(
    name='workout_power',
    base_type='uint32',
    values=Map(
    map={1000: TypeValue(
    name='watts_offset',
    value=1000,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'bp_status': Type(
    name='bp_status',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='no_error',
    value=0,
), 1: TypeValue(
    name='error_incomplete_data',
    value=1,
), 2: TypeValue(
    name='error_no_measurement',
    value=2,
), 3: TypeValue(
    name='error_data_out_of_range',
    value=3,
), 4: TypeValue(
    name='error_irregular_heart_rate',
    value=4,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'user_local_id': Type(
    name='user_local_id',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='local_min',
    value=0,
), 15: TypeValue(
    name='local_max',
    value=15,
), 16: TypeValue(
    name='stationary_min',
    value=16,
), 255: TypeValue(
    name='stationary_max',
    value=255,
), 256: TypeValue(
    name='portable_min',
    value=256,
), 65534: TypeValue(
    name='portable_max',
    value=65534,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'swim_stroke': Type(
    name='swim_stroke',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='freestyle',
    value=0,
), 1: TypeValue(
    name='backstroke',
    value=1,
), 2: TypeValue(
    name='breaststroke',
    value=2,
), 3: TypeValue(
    name='butterfly',
    value=3,
), 4: TypeValue(
    name='drill',
    value=4,
), 5: TypeValue(
    name='mixed',
    value=5,
), 6: TypeValue(
    name='im',
    value=6,
    comment='IM is a mixed interval containing the same number of lengths for each of: Butterfly, Backstroke, Breaststroke, Freestyle, swam in that order.',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'activity_type': Type(
    name='activity_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='generic',
    value=0,
), 1: TypeValue(
    name='running',
    value=1,
), 2: TypeValue(
    name='cycling',
    value=2,
), 3: TypeValue(
    name='transition',
    value=3,
    comment='Mulitsport transition',
), 4: TypeValue(
    name='fitness_equipment',
    value=4,
), 5: TypeValue(
    name='swimming',
    value=5,
), 6: TypeValue(
    name='walking',
    value=6,
), 8: TypeValue(
    name='sedentary',
    value=8,
), 254: TypeValue(
    name='all',
    value=254,
    comment='All is for goals only to include all sports.',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'activity_subtype': Type(
    name='activity_subtype',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='generic',
    value=0,
), 1: TypeValue(
    name='treadmill',
    value=1,
    comment='Run',
), 2: TypeValue(
    name='street',
    value=2,
    comment='Run',
), 3: TypeValue(
    name='trail',
    value=3,
    comment='Run',
), 4: TypeValue(
    name='track',
    value=4,
    comment='Run',
), 5: TypeValue(
    name='spin',
    value=5,
    comment='Cycling',
), 6: TypeValue(
    name='indoor_cycling',
    value=6,
    comment='Cycling',
), 7: TypeValue(
    name='road',
    value=7,
    comment='Cycling',
), 8: TypeValue(
    name='mountain',
    value=8,
    comment='Cycling',
), 9: TypeValue(
    name='downhill',
    value=9,
    comment='Cycling',
), 10: TypeValue(
    name='recumbent',
    value=10,
    comment='Cycling',
), 11: TypeValue(
    name='cyclocross',
    value=11,
    comment='Cycling',
), 12: TypeValue(
    name='hand_cycling',
    value=12,
    comment='Cycling',
), 13: TypeValue(
    name='track_cycling',
    value=13,
    comment='Cycling',
), 14: TypeValue(
    name='indoor_rowing',
    value=14,
    comment='Fitness Equipment',
), 15: TypeValue(
    name='elliptical',
    value=15,
    comment='Fitness Equipment',
), 16: TypeValue(
    name='stair_climbing',
    value=16,
    comment='Fitness Equipment',
), 17: TypeValue(
    name='lap_swimming',
    value=17,
    comment='Swimming',
), 18: TypeValue(
    name='open_water',
    value=18,
    comment='Swimming',
), 254: TypeValue(
    name='all',
    value=254,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'activity_level': Type(
    name='activity_level',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='low',
    value=0,
), 1: TypeValue(
    name='medium',
    value=1,
), 2: TypeValue(
    name='high',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'side': Type(
    name='side',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='right',
    value=0,
), 1: TypeValue(
    name='left',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'left_right_balance': Type(
    name='left_right_balance',
    base_type='uint8',
    values=Map(
    map={127: TypeValue(
    name='mask',
    value=127,
    comment='% contribution',
), 128: TypeValue(
    name='right',
    value=128,
    comment='data corresponds to right if set, otherwise unknown',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'left_right_balance_100': Type(
    name='left_right_balance_100',
    base_type='uint16',
    values=Map(
    map={16383: TypeValue(
    name='mask',
    value=16383,
    comment='% contribution scaled by 100',
), 32768: TypeValue(
    name='right',
    value=32768,
    comment='data corresponds to right if set, otherwise unknown',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'length_type': Type(
    name='length_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='idle',
    value=0,
    comment='Rest period. Length with no strokes',
), 1: TypeValue(
    name='active',
    value=1,
    comment='Length with strokes.',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'day_of_week': Type(
    name='day_of_week',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='sunday',
    value=0,
), 1: TypeValue(
    name='monday',
    value=1,
), 2: TypeValue(
    name='tuesday',
    value=2,
), 3: TypeValue(
    name='wednesday',
    value=3,
), 4: TypeValue(
    name='thursday',
    value=4,
), 5: TypeValue(
    name='friday',
    value=5,
), 6: TypeValue(
    name='saturday',
    value=6,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'connectivity_capabilities': Type(
    name='connectivity_capabilities',
    base_type='uint32z',
    values=Map(
    map={1: TypeValue(
    name='bluetooth',
    value=1,
), 2: TypeValue(
    name='bluetooth_le',
    value=2,
), 4: TypeValue(
    name='ant',
    value=4,
), 8: TypeValue(
    name='activity_upload',
    value=8,
), 16: TypeValue(
    name='course_download',
    value=16,
), 32: TypeValue(
    name='workout_download',
    value=32,
), 64: TypeValue(
    name='live_track',
    value=64,
), 128: TypeValue(
    name='weather_conditions',
    value=128,
), 256: TypeValue(
    name='weather_alerts',
    value=256,
), 512: TypeValue(
    name='gps_ephemeris_download',
    value=512,
), 1024: TypeValue(
    name='explicit_archive',
    value=1024,
), 2048: TypeValue(
    name='setup_incomplete',
    value=2048,
), 4096: TypeValue(
    name='continue_sync_after_software_update',
    value=4096,
), 8192: TypeValue(
    name='connect_iq_app_download',
    value=8192,
), 16384: TypeValue(
    name='golf_course_download',
    value=16384,
), 32768: TypeValue(
    name='device_initiates_sync',
    value=32768,
    comment='Indicates device is in control of initiating all syncs',
), 65536: TypeValue(
    name='connect_iq_watch_app_download',
    value=65536,
), 131072: TypeValue(
    name='connect_iq_widget_download',
    value=131072,
), 262144: TypeValue(
    name='connect_iq_watch_face_download',
    value=262144,
), 524288: TypeValue(
    name='connect_iq_data_field_download',
    value=524288,
), 1048576: TypeValue(
    name='connect_iq_app_managment',
    value=1048576,
    comment='Device supports delete and reorder of apps via GCM',
), 2097152: TypeValue(
    name='swing_sensor',
    value=2097152,
), 4194304: TypeValue(
    name='swing_sensor_remote',
    value=4194304,
), 8388608: TypeValue(
    name='incident_detection',
    value=8388608,
    comment='Device supports incident detection',
), 16777216: TypeValue(
    name='audio_prompts',
    value=16777216,
), 33554432: TypeValue(
    name='wifi_verification',
    value=33554432,
    comment='Device supports reporting wifi verification via GCM',
), 67108864: TypeValue(
    name='true_up',
    value=67108864,
    comment='Device supports True Up',
), 134217728: TypeValue(
    name='find_my_watch',
    value=134217728,
    comment='Device supports Find My Watch',
), 268435456: TypeValue(
    name='remote_manual_sync',
    value=268435456,
), 536870912: TypeValue(
    name='live_track_auto_start',
    value=536870912,
    comment='Device supports LiveTrack auto start',
), 1073741824: TypeValue(
    name='live_track_messaging',
    value=1073741824,
    comment='Device supports LiveTrack Messaging',
), 2147483648: TypeValue(
    name='instant_input',
    value=2147483648,
    comment='Device supports instant input feature',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'weather_report': Type(
    name='weather_report',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='current',
    value=0,
), 1: TypeValue(
    name='hourly_forecast',
    value=1,
), 2: TypeValue(
    name='daily_forecast',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'weather_status': Type(
    name='weather_status',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='clear',
    value=0,
), 1: TypeValue(
    name='partly_cloudy',
    value=1,
), 2: TypeValue(
    name='mostly_cloudy',
    value=2,
), 3: TypeValue(
    name='rain',
    value=3,
), 4: TypeValue(
    name='snow',
    value=4,
), 5: TypeValue(
    name='windy',
    value=5,
), 6: TypeValue(
    name='thunderstorms',
    value=6,
), 7: TypeValue(
    name='wintry_mix',
    value=7,
), 8: TypeValue(
    name='fog',
    value=8,
), 11: TypeValue(
    name='hazy',
    value=11,
), 12: TypeValue(
    name='hail',
    value=12,
), 13: TypeValue(
    name='scattered_showers',
    value=13,
), 14: TypeValue(
    name='scattered_thunderstorms',
    value=14,
), 15: TypeValue(
    name='unknown_precipitation',
    value=15,
), 16: TypeValue(
    name='light_rain',
    value=16,
), 17: TypeValue(
    name='heavy_rain',
    value=17,
), 18: TypeValue(
    name='light_snow',
    value=18,
), 19: TypeValue(
    name='heavy_snow',
    value=19,
), 20: TypeValue(
    name='light_rain_snow',
    value=20,
), 21: TypeValue(
    name='heavy_rain_snow',
    value=21,
), 22: TypeValue(
    name='cloudy',
    value=22,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'weather_severity': Type(
    name='weather_severity',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='unknown',
    value=0,
), 1: TypeValue(
    name='warning',
    value=1,
), 2: TypeValue(
    name='watch',
    value=2,
), 3: TypeValue(
    name='advisory',
    value=3,
), 4: TypeValue(
    name='statement',
    value=4,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'weather_severe_type': Type(
    name='weather_severe_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='unspecified',
    value=0,
), 1: TypeValue(
    name='tornado',
    value=1,
), 2: TypeValue(
    name='tsunami',
    value=2,
), 3: TypeValue(
    name='hurricane',
    value=3,
), 4: TypeValue(
    name='extreme_wind',
    value=4,
), 5: TypeValue(
    name='typhoon',
    value=5,
), 6: TypeValue(
    name='inland_hurricane',
    value=6,
), 7: TypeValue(
    name='hurricane_force_wind',
    value=7,
), 8: TypeValue(
    name='waterspout',
    value=8,
), 9: TypeValue(
    name='severe_thunderstorm',
    value=9,
), 10: TypeValue(
    name='wreckhouse_winds',
    value=10,
), 11: TypeValue(
    name='les_suetes_wind',
    value=11,
), 12: TypeValue(
    name='avalanche',
    value=12,
), 13: TypeValue(
    name='flash_flood',
    value=13,
), 14: TypeValue(
    name='tropical_storm',
    value=14,
), 15: TypeValue(
    name='inland_tropical_storm',
    value=15,
), 16: TypeValue(
    name='blizzard',
    value=16,
), 17: TypeValue(
    name='ice_storm',
    value=17,
), 18: TypeValue(
    name='freezing_rain',
    value=18,
), 19: TypeValue(
    name='debris_flow',
    value=19,
), 20: TypeValue(
    name='flash_freeze',
    value=20,
), 21: TypeValue(
    name='dust_storm',
    value=21,
), 22: TypeValue(
    name='high_wind',
    value=22,
), 23: TypeValue(
    name='winter_storm',
    value=23,
), 24: TypeValue(
    name='heavy_freezing_spray',
    value=24,
), 25: TypeValue(
    name='extreme_cold',
    value=25,
), 26: TypeValue(
    name='wind_chill',
    value=26,
), 27: TypeValue(
    name='cold_wave',
    value=27,
), 28: TypeValue(
    name='heavy_snow_alert',
    value=28,
), 29: TypeValue(
    name='lake_effect_blowing_snow',
    value=29,
), 30: TypeValue(
    name='snow_squall',
    value=30,
), 31: TypeValue(
    name='lake_effect_snow',
    value=31,
), 32: TypeValue(
    name='winter_weather',
    value=32,
), 33: TypeValue(
    name='sleet',
    value=33,
), 34: TypeValue(
    name='snowfall',
    value=34,
), 35: TypeValue(
    name='snow_and_blowing_snow',
    value=35,
), 36: TypeValue(
    name='blowing_snow',
    value=36,
), 37: TypeValue(
    name='snow_alert',
    value=37,
), 38: TypeValue(
    name='arctic_outflow',
    value=38,
), 39: TypeValue(
    name='freezing_drizzle',
    value=39,
), 40: TypeValue(
    name='storm',
    value=40,
), 41: TypeValue(
    name='storm_surge',
    value=41,
), 42: TypeValue(
    name='rainfall',
    value=42,
), 43: TypeValue(
    name='areal_flood',
    value=43,
), 44: TypeValue(
    name='coastal_flood',
    value=44,
), 45: TypeValue(
    name='lakeshore_flood',
    value=45,
), 46: TypeValue(
    name='excessive_heat',
    value=46,
), 47: TypeValue(
    name='heat',
    value=47,
), 48: TypeValue(
    name='weather',
    value=48,
), 49: TypeValue(
    name='high_heat_and_humidity',
    value=49,
), 50: TypeValue(
    name='humidex_and_health',
    value=50,
), 51: TypeValue(
    name='humidex',
    value=51,
), 52: TypeValue(
    name='gale',
    value=52,
), 53: TypeValue(
    name='freezing_spray',
    value=53,
), 54: TypeValue(
    name='special_marine',
    value=54,
), 55: TypeValue(
    name='squall',
    value=55,
), 56: TypeValue(
    name='strong_wind',
    value=56,
), 57: TypeValue(
    name='lake_wind',
    value=57,
), 58: TypeValue(
    name='marine_weather',
    value=58,
), 59: TypeValue(
    name='wind',
    value=59,
), 60: TypeValue(
    name='small_craft_hazardous_seas',
    value=60,
), 61: TypeValue(
    name='hazardous_seas',
    value=61,
), 62: TypeValue(
    name='small_craft',
    value=62,
), 63: TypeValue(
    name='small_craft_winds',
    value=63,
), 64: TypeValue(
    name='small_craft_rough_bar',
    value=64,
), 65: TypeValue(
    name='high_water_level',
    value=65,
), 66: TypeValue(
    name='ashfall',
    value=66,
), 67: TypeValue(
    name='freezing_fog',
    value=67,
), 68: TypeValue(
    name='dense_fog',
    value=68,
), 69: TypeValue(
    name='dense_smoke',
    value=69,
), 70: TypeValue(
    name='blowing_dust',
    value=70,
), 71: TypeValue(
    name='hard_freeze',
    value=71,
), 72: TypeValue(
    name='freeze',
    value=72,
), 73: TypeValue(
    name='frost',
    value=73,
), 74: TypeValue(
    name='fire_weather',
    value=74,
), 75: TypeValue(
    name='flood',
    value=75,
), 76: TypeValue(
    name='rip_tide',
    value=76,
), 77: TypeValue(
    name='high_surf',
    value=77,
), 78: TypeValue(
    name='smog',
    value=78,
), 79: TypeValue(
    name='air_quality',
    value=79,
), 80: TypeValue(
    name='brisk_wind',
    value=80,
), 81: TypeValue(
    name='air_stagnation',
    value=81,
), 82: TypeValue(
    name='low_water',
    value=82,
), 83: TypeValue(
    name='hydrological',
    value=83,
), 84: TypeValue(
    name='special_weather',
    value=84,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'time_into_day': Type(
    name='time_into_day',
    base_type='uint32',
), 'localtime_into_day': Type(
    name='localtime_into_day',
    base_type='uint32',
), 'stroke_type': Type(
    name='stroke_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='no_event',
    value=0,
), 1: TypeValue(
    name='other',
    value=1,
    comment='stroke was detected but cannot be identified',
), 2: TypeValue(
    name='serve',
    value=2,
), 3: TypeValue(
    name='forehand',
    value=3,
), 4: TypeValue(
    name='backhand',
    value=4,
), 5: TypeValue(
    name='smash',
    value=5,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'body_location': Type(
    name='body_location',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='left_leg',
    value=0,
), 1: TypeValue(
    name='left_calf',
    value=1,
), 2: TypeValue(
    name='left_shin',
    value=2,
), 3: TypeValue(
    name='left_hamstring',
    value=3,
), 4: TypeValue(
    name='left_quad',
    value=4,
), 5: TypeValue(
    name='left_glute',
    value=5,
), 6: TypeValue(
    name='right_leg',
    value=6,
), 7: TypeValue(
    name='right_calf',
    value=7,
), 8: TypeValue(
    name='right_shin',
    value=8,
), 9: TypeValue(
    name='right_hamstring',
    value=9,
), 10: TypeValue(
    name='right_quad',
    value=10,
), 11: TypeValue(
    name='right_glute',
    value=11,
), 12: TypeValue(
    name='torso_back',
    value=12,
), 13: TypeValue(
    name='left_lower_back',
    value=13,
), 14: TypeValue(
    name='left_upper_back',
    value=14,
), 15: TypeValue(
    name='right_lower_back',
    value=15,
), 16: TypeValue(
    name='right_upper_back',
    value=16,
), 17: TypeValue(
    name='torso_front',
    value=17,
), 18: TypeValue(
    name='left_abdomen',
    value=18,
), 19: TypeValue(
    name='left_chest',
    value=19,
), 20: TypeValue(
    name='right_abdomen',
    value=20,
), 21: TypeValue(
    name='right_chest',
    value=21,
), 22: TypeValue(
    name='left_arm',
    value=22,
), 23: TypeValue(
    name='left_shoulder',
    value=23,
), 24: TypeValue(
    name='left_bicep',
    value=24,
), 25: TypeValue(
    name='left_tricep',
    value=25,
), 26: TypeValue(
    name='left_brachioradialis',
    value=26,
    comment='Left anterior forearm',
), 27: TypeValue(
    name='left_forearm_extensors',
    value=27,
    comment='Left posterior forearm',
), 28: TypeValue(
    name='right_arm',
    value=28,
), 29: TypeValue(
    name='right_shoulder',
    value=29,
), 30: TypeValue(
    name='right_bicep',
    value=30,
), 31: TypeValue(
    name='right_tricep',
    value=31,
), 32: TypeValue(
    name='right_brachioradialis',
    value=32,
    comment='Right anterior forearm',
), 33: TypeValue(
    name='right_forearm_extensors',
    value=33,
    comment='Right posterior forearm',
), 34: TypeValue(
    name='neck',
    value=34,
), 35: TypeValue(
    name='throat',
    value=35,
), 36: TypeValue(
    name='waist_mid_back',
    value=36,
), 37: TypeValue(
    name='waist_front',
    value=37,
), 38: TypeValue(
    name='waist_left',
    value=38,
), 39: TypeValue(
    name='waist_right',
    value=39,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'segment_lap_status': Type(
    name='segment_lap_status',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='end',
    value=0,
), 1: TypeValue(
    name='fail',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'segment_leaderboard_type': Type(
    name='segment_leaderboard_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='overall',
    value=0,
), 1: TypeValue(
    name='personal_best',
    value=1,
), 2: TypeValue(
    name='connections',
    value=2,
), 3: TypeValue(
    name='group',
    value=3,
), 4: TypeValue(
    name='challenger',
    value=4,
), 5: TypeValue(
    name='kom',
    value=5,
), 6: TypeValue(
    name='qom',
    value=6,
), 7: TypeValue(
    name='pr',
    value=7,
), 8: TypeValue(
    name='goal',
    value=8,
), 9: TypeValue(
    name='rival',
    value=9,
), 10: TypeValue(
    name='club_leader',
    value=10,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'segment_delete_status': Type(
    name='segment_delete_status',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='do_not_delete',
    value=0,
), 1: TypeValue(
    name='delete_one',
    value=1,
), 2: TypeValue(
    name='delete_all',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'segment_selection_type': Type(
    name='segment_selection_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='starred',
    value=0,
), 1: TypeValue(
    name='suggested',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'source_type': Type(
    name='source_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='ant',
    value=0,
    comment='External device connected with ANT',
), 1: TypeValue(
    name='antplus',
    value=1,
    comment='External device connected with ANT+',
), 2: TypeValue(
    name='bluetooth',
    value=2,
    comment='External device connected with BT',
), 3: TypeValue(
    name='bluetooth_low_energy',
    value=3,
    comment='External device connected with BLE',
), 4: TypeValue(
    name='wifi',
    value=4,
    comment='External device connected with Wifi',
), 5: TypeValue(
    name='local',
    value=5,
    comment='Onboard device',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'local_device_type': Type(
    name='local_device_type',
    base_type='uint8',
), 'display_orientation': Type(
    name='display_orientation',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='auto',
    value=0,
    comment='automatic if the device supports it',
), 1: TypeValue(
    name='portrait',
    value=1,
), 2: TypeValue(
    name='landscape',
    value=2,
), 3: TypeValue(
    name='portrait_flipped',
    value=3,
    comment='portrait mode but rotated 180 degrees',
), 4: TypeValue(
    name='landscape_flipped',
    value=4,
    comment='landscape mode but rotated 180 degrees',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'workout_equipment': Type(
    name='workout_equipment',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='none',
    value=0,
), 1: TypeValue(
    name='swim_fins',
    value=1,
), 2: TypeValue(
    name='swim_kickboard',
    value=2,
), 3: TypeValue(
    name='swim_paddles',
    value=3,
), 4: TypeValue(
    name='swim_pull_buoy',
    value=4,
), 5: TypeValue(
    name='swim_snorkel',
    value=5,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'watchface_mode': Type(
    name='watchface_mode',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='digital',
    value=0,
), 1: TypeValue(
    name='analog',
    value=1,
), 2: TypeValue(
    name='connect_iq',
    value=2,
), 3: TypeValue(
    name='disabled',
    value=3,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'digital_watchface_layout': Type(
    name='digital_watchface_layout',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='traditional',
    value=0,
), 1: TypeValue(
    name='modern',
    value=1,
), 2: TypeValue(
    name='bold',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'analog_watchface_layout': Type(
    name='analog_watchface_layout',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='minimal',
    value=0,
), 1: TypeValue(
    name='traditional',
    value=1,
), 2: TypeValue(
    name='modern',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'rider_position_type': Type(
    name='rider_position_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='seated',
    value=0,
), 1: TypeValue(
    name='standing',
    value=1,
), 2: TypeValue(
    name='transition_to_seated',
    value=2,
), 3: TypeValue(
    name='transition_to_standing',
    value=3,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'power_phase_type': Type(
    name='power_phase_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='power_phase_start_angle',
    value=0,
), 1: TypeValue(
    name='power_phase_end_angle',
    value=1,
), 2: TypeValue(
    name='power_phase_arc_length',
    value=2,
), 3: TypeValue(
    name='power_phase_center',
    value=3,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'camera_event_type': Type(
    name='camera_event_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='video_start',
    value=0,
    comment='Start of video recording',
), 1: TypeValue(
    name='video_split',
    value=1,
    comment='Mark of video file split (end of one file, beginning of the other)',
), 2: TypeValue(
    name='video_end',
    value=2,
    comment='End of video recording',
), 3: TypeValue(
    name='photo_taken',
    value=3,
    comment='Still photo taken',
), 4: TypeValue(
    name='video_second_stream_start',
    value=4,
), 5: TypeValue(
    name='video_second_stream_split',
    value=5,
), 6: TypeValue(
    name='video_second_stream_end',
    value=6,
), 7: TypeValue(
    name='video_split_start',
    value=7,
    comment='Mark of video file split start',
), 8: TypeValue(
    name='video_second_stream_split_start',
    value=8,
), 11: TypeValue(
    name='video_pause',
    value=11,
    comment='Mark when a video recording has been paused',
), 12: TypeValue(
    name='video_second_stream_pause',
    value=12,
), 13: TypeValue(
    name='video_resume',
    value=13,
    comment='Mark when a video recording has been resumed',
), 14: TypeValue(
    name='video_second_stream_resume',
    value=14,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'sensor_type': Type(
    name='sensor_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='accelerometer',
    value=0,
), 1: TypeValue(
    name='gyroscope',
    value=1,
), 2: TypeValue(
    name='compass',
    value=2,
    comment='Magnetometer',
), 3: TypeValue(
    name='barometer',
    value=3,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'bike_light_network_config_type': Type(
    name='bike_light_network_config_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='auto',
    value=0,
), 4: TypeValue(
    name='individual',
    value=4,
), 5: TypeValue(
    name='high_visibility',
    value=5,
), 6: TypeValue(
    name='trail',
    value=6,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'comm_timeout_type': Type(
    name='comm_timeout_type',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='wildcard_pairing_timeout',
    value=0,
    comment='Timeout pairing to any device',
), 1: TypeValue(
    name='pairing_timeout',
    value=1,
    comment='Timeout pairing to previously paired device',
), 2: TypeValue(
    name='connection_lost',
    value=2,
    comment='Temporary loss of communications',
), 3: TypeValue(
    name='connection_timeout',
    value=3,
    comment='Connection closed due to extended bad communications',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'camera_orientation_type': Type(
    name='camera_orientation_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='camera_orientation_0',
    value=0,
), 1: TypeValue(
    name='camera_orientation_90',
    value=1,
), 2: TypeValue(
    name='camera_orientation_180',
    value=2,
), 3: TypeValue(
    name='camera_orientation_270',
    value=3,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'attitude_stage': Type(
    name='attitude_stage',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='failed',
    value=0,
), 1: TypeValue(
    name='aligning',
    value=1,
), 2: TypeValue(
    name='degraded',
    value=2,
), 3: TypeValue(
    name='valid',
    value=3,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'attitude_validity': Type(
    name='attitude_validity',
    base_type='uint16',
    values=Map(
    map={1: TypeValue(
    name='track_angle_heading_valid',
    value=1,
), 2: TypeValue(
    name='pitch_valid',
    value=2,
), 4: TypeValue(
    name='roll_valid',
    value=4,
), 8: TypeValue(
    name='lateral_body_accel_valid',
    value=8,
), 16: TypeValue(
    name='normal_body_accel_valid',
    value=16,
), 32: TypeValue(
    name='turn_rate_valid',
    value=32,
), 64: TypeValue(
    name='hw_fail',
    value=64,
), 128: TypeValue(
    name='mag_invalid',
    value=128,
), 256: TypeValue(
    name='no_gps',
    value=256,
), 512: TypeValue(
    name='gps_invalid',
    value=512,
), 1024: TypeValue(
    name='solution_coasting',
    value=1024,
), 2048: TypeValue(
    name='true_track_angle',
    value=2048,
), 4096: TypeValue(
    name='magnetic_heading',
    value=4096,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'auto_sync_frequency': Type(
    name='auto_sync_frequency',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='never',
    value=0,
), 1: TypeValue(
    name='occasionally',
    value=1,
), 2: TypeValue(
    name='frequent',
    value=2,
), 3: TypeValue(
    name='once_a_day',
    value=3,
), 4: TypeValue(
    name='remote',
    value=4,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'exd_layout': Type(
    name='exd_layout',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='full_screen',
    value=0,
), 1: TypeValue(
    name='half_vertical',
    value=1,
), 2: TypeValue(
    name='half_horizontal',
    value=2,
), 3: TypeValue(
    name='half_vertical_right_split',
    value=3,
), 4: TypeValue(
    name='half_horizontal_bottom_split',
    value=4,
), 5: TypeValue(
    name='full_quarter_split',
    value=5,
), 6: TypeValue(
    name='half_vertical_left_split',
    value=6,
), 7: TypeValue(
    name='half_horizontal_top_split',
    value=7,
), 8: TypeValue(
    name='dynamic',
    value=8,
    comment='The EXD may display the configured concepts in any layout it sees fit.',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'exd_display_type': Type(
    name='exd_display_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='numerical',
    value=0,
), 1: TypeValue(
    name='simple',
    value=1,
), 2: TypeValue(
    name='graph',
    value=2,
), 3: TypeValue(
    name='bar',
    value=3,
), 4: TypeValue(
    name='circle_graph',
    value=4,
), 5: TypeValue(
    name='virtual_partner',
    value=5,
), 6: TypeValue(
    name='balance',
    value=6,
), 7: TypeValue(
    name='string_list',
    value=7,
), 8: TypeValue(
    name='string',
    value=8,
), 9: TypeValue(
    name='simple_dynamic_icon',
    value=9,
), 10: TypeValue(
    name='gauge',
    value=10,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'exd_data_units': Type(
    name='exd_data_units',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='no_units',
    value=0,
), 1: TypeValue(
    name='laps',
    value=1,
), 2: TypeValue(
    name='miles_per_hour',
    value=2,
), 3: TypeValue(
    name='kilometers_per_hour',
    value=3,
), 4: TypeValue(
    name='feet_per_hour',
    value=4,
), 5: TypeValue(
    name='meters_per_hour',
    value=5,
), 6: TypeValue(
    name='degrees_celsius',
    value=6,
), 7: TypeValue(
    name='degrees_farenheit',
    value=7,
), 8: TypeValue(
    name='zone',
    value=8,
), 9: TypeValue(
    name='gear',
    value=9,
), 10: TypeValue(
    name='rpm',
    value=10,
), 11: TypeValue(
    name='bpm',
    value=11,
), 12: TypeValue(
    name='degrees',
    value=12,
), 13: TypeValue(
    name='millimeters',
    value=13,
), 14: TypeValue(
    name='meters',
    value=14,
), 15: TypeValue(
    name='kilometers',
    value=15,
), 16: TypeValue(
    name='feet',
    value=16,
), 17: TypeValue(
    name='yards',
    value=17,
), 18: TypeValue(
    name='kilofeet',
    value=18,
), 19: TypeValue(
    name='miles',
    value=19,
), 20: TypeValue(
    name='time',
    value=20,
), 21: TypeValue(
    name='enum_turn_type',
    value=21,
), 22: TypeValue(
    name='percent',
    value=22,
), 23: TypeValue(
    name='watts',
    value=23,
), 24: TypeValue(
    name='watts_per_kilogram',
    value=24,
), 25: TypeValue(
    name='enum_battery_status',
    value=25,
), 26: TypeValue(
    name='enum_bike_light_beam_angle_mode',
    value=26,
), 27: TypeValue(
    name='enum_bike_light_battery_status',
    value=27,
), 28: TypeValue(
    name='enum_bike_light_network_config_type',
    value=28,
), 29: TypeValue(
    name='lights',
    value=29,
), 30: TypeValue(
    name='seconds',
    value=30,
), 31: TypeValue(
    name='minutes',
    value=31,
), 32: TypeValue(
    name='hours',
    value=32,
), 33: TypeValue(
    name='calories',
    value=33,
), 34: TypeValue(
    name='kilojoules',
    value=34,
), 35: TypeValue(
    name='milliseconds',
    value=35,
), 36: TypeValue(
    name='second_per_mile',
    value=36,
), 37: TypeValue(
    name='second_per_kilometer',
    value=37,
), 38: TypeValue(
    name='centimeter',
    value=38,
), 39: TypeValue(
    name='enum_course_point',
    value=39,
), 40: TypeValue(
    name='bradians',
    value=40,
), 41: TypeValue(
    name='enum_sport',
    value=41,
), 42: TypeValue(
    name='inches_hg',
    value=42,
), 43: TypeValue(
    name='mm_hg',
    value=43,
), 44: TypeValue(
    name='mbars',
    value=44,
), 45: TypeValue(
    name='hecto_pascals',
    value=45,
), 46: TypeValue(
    name='feet_per_min',
    value=46,
), 47: TypeValue(
    name='meters_per_min',
    value=47,
), 48: TypeValue(
    name='meters_per_sec',
    value=48,
), 49: TypeValue(
    name='eight_cardinal',
    value=49,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'exd_qualifiers': Type(
    name='exd_qualifiers',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='no_qualifier',
    value=0,
), 1: TypeValue(
    name='instantaneous',
    value=1,
), 2: TypeValue(
    name='average',
    value=2,
), 3: TypeValue(
    name='lap',
    value=3,
), 4: TypeValue(
    name='maximum',
    value=4,
), 5: TypeValue(
    name='maximum_average',
    value=5,
), 6: TypeValue(
    name='maximum_lap',
    value=6,
), 7: TypeValue(
    name='last_lap',
    value=7,
), 8: TypeValue(
    name='average_lap',
    value=8,
), 9: TypeValue(
    name='to_destination',
    value=9,
), 10: TypeValue(
    name='to_go',
    value=10,
), 11: TypeValue(
    name='to_next',
    value=11,
), 12: TypeValue(
    name='next_course_point',
    value=12,
), 13: TypeValue(
    name='total',
    value=13,
), 14: TypeValue(
    name='three_second_average',
    value=14,
), 15: TypeValue(
    name='ten_second_average',
    value=15,
), 16: TypeValue(
    name='thirty_second_average',
    value=16,
), 17: TypeValue(
    name='percent_maximum',
    value=17,
), 18: TypeValue(
    name='percent_maximum_average',
    value=18,
), 19: TypeValue(
    name='lap_percent_maximum',
    value=19,
), 20: TypeValue(
    name='elapsed',
    value=20,
), 21: TypeValue(
    name='sunrise',
    value=21,
), 22: TypeValue(
    name='sunset',
    value=22,
), 23: TypeValue(
    name='compared_to_virtual_partner',
    value=23,
), 24: TypeValue(
    name='maximum_24h',
    value=24,
), 25: TypeValue(
    name='minimum_24h',
    value=25,
), 26: TypeValue(
    name='minimum',
    value=26,
), 27: TypeValue(
    name='first',
    value=27,
), 28: TypeValue(
    name='second',
    value=28,
), 29: TypeValue(
    name='third',
    value=29,
), 30: TypeValue(
    name='shifter',
    value=30,
), 31: TypeValue(
    name='last_sport',
    value=31,
), 32: TypeValue(
    name='moving',
    value=32,
), 33: TypeValue(
    name='stopped',
    value=33,
), 34: TypeValue(
    name='estimated_total',
    value=34,
), 242: TypeValue(
    name='zone_9',
    value=242,
), 243: TypeValue(
    name='zone_8',
    value=243,
), 244: TypeValue(
    name='zone_7',
    value=244,
), 245: TypeValue(
    name='zone_6',
    value=245,
), 246: TypeValue(
    name='zone_5',
    value=246,
), 247: TypeValue(
    name='zone_4',
    value=247,
), 248: TypeValue(
    name='zone_3',
    value=248,
), 249: TypeValue(
    name='zone_2',
    value=249,
), 250: TypeValue(
    name='zone_1',
    value=250,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'exd_descriptors': Type(
    name='exd_descriptors',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='bike_light_battery_status',
    value=0,
), 1: TypeValue(
    name='beam_angle_status',
    value=1,
), 2: TypeValue(
    name='batery_level',
    value=2,
), 3: TypeValue(
    name='light_network_mode',
    value=3,
), 4: TypeValue(
    name='number_lights_connected',
    value=4,
), 5: TypeValue(
    name='cadence',
    value=5,
), 6: TypeValue(
    name='distance',
    value=6,
), 7: TypeValue(
    name='estimated_time_of_arrival',
    value=7,
), 8: TypeValue(
    name='heading',
    value=8,
), 9: TypeValue(
    name='time',
    value=9,
), 10: TypeValue(
    name='battery_level',
    value=10,
), 11: TypeValue(
    name='trainer_resistance',
    value=11,
), 12: TypeValue(
    name='trainer_target_power',
    value=12,
), 13: TypeValue(
    name='time_seated',
    value=13,
), 14: TypeValue(
    name='time_standing',
    value=14,
), 15: TypeValue(
    name='elevation',
    value=15,
), 16: TypeValue(
    name='grade',
    value=16,
), 17: TypeValue(
    name='ascent',
    value=17,
), 18: TypeValue(
    name='descent',
    value=18,
), 19: TypeValue(
    name='vertical_speed',
    value=19,
), 20: TypeValue(
    name='di2_battery_level',
    value=20,
), 21: TypeValue(
    name='front_gear',
    value=21,
), 22: TypeValue(
    name='rear_gear',
    value=22,
), 23: TypeValue(
    name='gear_ratio',
    value=23,
), 24: TypeValue(
    name='heart_rate',
    value=24,
), 25: TypeValue(
    name='heart_rate_zone',
    value=25,
), 26: TypeValue(
    name='time_in_heart_rate_zone',
    value=26,
), 27: TypeValue(
    name='heart_rate_reserve',
    value=27,
), 28: TypeValue(
    name='calories',
    value=28,
), 29: TypeValue(
    name='gps_accuracy',
    value=29,
), 30: TypeValue(
    name='gps_signal_strength',
    value=30,
), 31: TypeValue(
    name='temperature',
    value=31,
), 32: TypeValue(
    name='time_of_day',
    value=32,
), 33: TypeValue(
    name='balance',
    value=33,
), 34: TypeValue(
    name='pedal_smoothness',
    value=34,
), 35: TypeValue(
    name='power',
    value=35,
), 36: TypeValue(
    name='functional_threshold_power',
    value=36,
), 37: TypeValue(
    name='intensity_factor',
    value=37,
), 38: TypeValue(
    name='work',
    value=38,
), 39: TypeValue(
    name='power_ratio',
    value=39,
), 40: TypeValue(
    name='normalized_power',
    value=40,
), 41: TypeValue(
    name='training_stress_Score',
    value=41,
), 42: TypeValue(
    name='time_on_zone',
    value=42,
), 43: TypeValue(
    name='speed',
    value=43,
), 44: TypeValue(
    name='laps',
    value=44,
), 45: TypeValue(
    name='reps',
    value=45,
), 46: TypeValue(
    name='workout_step',
    value=46,
), 47: TypeValue(
    name='course_distance',
    value=47,
), 48: TypeValue(
    name='navigation_distance',
    value=48,
), 49: TypeValue(
    name='course_estimated_time_of_arrival',
    value=49,
), 50: TypeValue(
    name='navigation_estimated_time_of_arrival',
    value=50,
), 51: TypeValue(
    name='course_time',
    value=51,
), 52: TypeValue(
    name='navigation_time',
    value=52,
), 53: TypeValue(
    name='course_heading',
    value=53,
), 54: TypeValue(
    name='navigation_heading',
    value=54,
), 55: TypeValue(
    name='power_zone',
    value=55,
), 56: TypeValue(
    name='torque_effectiveness',
    value=56,
), 57: TypeValue(
    name='timer_time',
    value=57,
), 58: TypeValue(
    name='power_weight_ratio',
    value=58,
), 59: TypeValue(
    name='left_platform_center_offset',
    value=59,
), 60: TypeValue(
    name='right_platform_center_offset',
    value=60,
), 61: TypeValue(
    name='left_power_phase_start_angle',
    value=61,
), 62: TypeValue(
    name='right_power_phase_start_angle',
    value=62,
), 63: TypeValue(
    name='left_power_phase_finish_angle',
    value=63,
), 64: TypeValue(
    name='right_power_phase_finish_angle',
    value=64,
), 65: TypeValue(
    name='gears',
    value=65,
    comment='Combined gear information',
), 66: TypeValue(
    name='pace',
    value=66,
), 67: TypeValue(
    name='training_effect',
    value=67,
), 68: TypeValue(
    name='vertical_oscillation',
    value=68,
), 69: TypeValue(
    name='vertical_ratio',
    value=69,
), 70: TypeValue(
    name='ground_contact_time',
    value=70,
), 71: TypeValue(
    name='left_ground_contact_time_balance',
    value=71,
), 72: TypeValue(
    name='right_ground_contact_time_balance',
    value=72,
), 73: TypeValue(
    name='stride_length',
    value=73,
), 74: TypeValue(
    name='running_cadence',
    value=74,
), 75: TypeValue(
    name='performance_condition',
    value=75,
), 76: TypeValue(
    name='course_type',
    value=76,
), 77: TypeValue(
    name='time_in_power_zone',
    value=77,
), 78: TypeValue(
    name='navigation_turn',
    value=78,
), 79: TypeValue(
    name='course_location',
    value=79,
), 80: TypeValue(
    name='navigation_location',
    value=80,
), 81: TypeValue(
    name='compass',
    value=81,
), 82: TypeValue(
    name='gear_combo',
    value=82,
), 83: TypeValue(
    name='muscle_oxygen',
    value=83,
), 84: TypeValue(
    name='icon',
    value=84,
), 85: TypeValue(
    name='compass_heading',
    value=85,
), 86: TypeValue(
    name='gps_heading',
    value=86,
), 87: TypeValue(
    name='gps_elevation',
    value=87,
), 88: TypeValue(
    name='anaerobic_training_effect',
    value=88,
), 89: TypeValue(
    name='course',
    value=89,
), 90: TypeValue(
    name='off_course',
    value=90,
), 91: TypeValue(
    name='glide_ratio',
    value=91,
), 92: TypeValue(
    name='vertical_distance',
    value=92,
), 93: TypeValue(
    name='vmg',
    value=93,
), 94: TypeValue(
    name='ambient_pressure',
    value=94,
), 95: TypeValue(
    name='pressure',
    value=95,
), 96: TypeValue(
    name='vam',
    value=96,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'auto_activity_detect': Type(
    name='auto_activity_detect',
    base_type='uint32',
    values=Map(
    map={0: TypeValue(
    name='none',
    value=0,
), 1: TypeValue(
    name='running',
    value=1,
), 2: TypeValue(
    name='cycling',
    value=2,
), 4: TypeValue(
    name='swimming',
    value=4,
), 8: TypeValue(
    name='walking',
    value=8,
), 32: TypeValue(
    name='elliptical',
    value=32,
), 1024: TypeValue(
    name='sedentary',
    value=1024,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'supported_exd_screen_layouts': Type(
    name='supported_exd_screen_layouts',
    base_type='uint32z',
    values=Map(
    map={1: TypeValue(
    name='full_screen',
    value=1,
), 2: TypeValue(
    name='half_vertical',
    value=2,
), 4: TypeValue(
    name='half_horizontal',
    value=4,
), 8: TypeValue(
    name='half_vertical_right_split',
    value=8,
), 16: TypeValue(
    name='half_horizontal_bottom_split',
    value=16,
), 32: TypeValue(
    name='full_quarter_split',
    value=32,
), 64: TypeValue(
    name='half_vertical_left_split',
    value=64,
), 128: TypeValue(
    name='half_horizontal_top_split',
    value=128,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'fit_base_type': Type(
    name='fit_base_type',
    base_type='uint8',
    values=Map(
    map={0: TypeValue(
    name='enum',
    value=0,
), 1: TypeValue(
    name='sint8',
    value=1,
), 2: TypeValue(
    name='uint8',
    value=2,
), 131: TypeValue(
    name='sint16',
    value=131,
), 132: TypeValue(
    name='uint16',
    value=132,
), 133: TypeValue(
    name='sint32',
    value=133,
), 134: TypeValue(
    name='uint32',
    value=134,
), 7: TypeValue(
    name='string',
    value=7,
), 136: TypeValue(
    name='float32',
    value=136,
), 137: TypeValue(
    name='float64',
    value=137,
), 10: TypeValue(
    name='uint8z',
    value=10,
), 139: TypeValue(
    name='uint16z',
    value=139,
), 140: TypeValue(
    name='uint32z',
    value=140,
), 13: TypeValue(
    name='byte',
    value=13,
), 142: TypeValue(
    name='sint64',
    value=142,
), 143: TypeValue(
    name='uint64',
    value=143,
), 144: TypeValue(
    name='uint64z',
    value=144,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'turn_type': Type(
    name='turn_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='arriving_idx',
    value=0,
), 1: TypeValue(
    name='arriving_left_idx',
    value=1,
), 2: TypeValue(
    name='arriving_right_idx',
    value=2,
), 3: TypeValue(
    name='arriving_via_idx',
    value=3,
), 4: TypeValue(
    name='arriving_via_left_idx',
    value=4,
), 5: TypeValue(
    name='arriving_via_right_idx',
    value=5,
), 6: TypeValue(
    name='bear_keep_left_idx',
    value=6,
), 7: TypeValue(
    name='bear_keep_right_idx',
    value=7,
), 8: TypeValue(
    name='continue_idx',
    value=8,
), 9: TypeValue(
    name='exit_left_idx',
    value=9,
), 10: TypeValue(
    name='exit_right_idx',
    value=10,
), 11: TypeValue(
    name='ferry_idx',
    value=11,
), 12: TypeValue(
    name='roundabout_45_idx',
    value=12,
), 13: TypeValue(
    name='roundabout_90_idx',
    value=13,
), 14: TypeValue(
    name='roundabout_135_idx',
    value=14,
), 15: TypeValue(
    name='roundabout_180_idx',
    value=15,
), 16: TypeValue(
    name='roundabout_225_idx',
    value=16,
), 17: TypeValue(
    name='roundabout_270_idx',
    value=17,
), 18: TypeValue(
    name='roundabout_315_idx',
    value=18,
), 19: TypeValue(
    name='roundabout_360_idx',
    value=19,
), 20: TypeValue(
    name='roundabout_neg_45_idx',
    value=20,
), 21: TypeValue(
    name='roundabout_neg_90_idx',
    value=21,
), 22: TypeValue(
    name='roundabout_neg_135_idx',
    value=22,
), 23: TypeValue(
    name='roundabout_neg_180_idx',
    value=23,
), 24: TypeValue(
    name='roundabout_neg_225_idx',
    value=24,
), 25: TypeValue(
    name='roundabout_neg_270_idx',
    value=25,
), 26: TypeValue(
    name='roundabout_neg_315_idx',
    value=26,
), 27: TypeValue(
    name='roundabout_neg_360_idx',
    value=27,
), 28: TypeValue(
    name='roundabout_generic_idx',
    value=28,
), 29: TypeValue(
    name='roundabout_neg_generic_idx',
    value=29,
), 30: TypeValue(
    name='sharp_turn_left_idx',
    value=30,
), 31: TypeValue(
    name='sharp_turn_right_idx',
    value=31,
), 32: TypeValue(
    name='turn_left_idx',
    value=32,
), 33: TypeValue(
    name='turn_right_idx',
    value=33,
), 34: TypeValue(
    name='uturn_left_idx',
    value=34,
), 35: TypeValue(
    name='uturn_right_idx',
    value=35,
), 36: TypeValue(
    name='icon_inv_idx',
    value=36,
), 37: TypeValue(
    name='icon_idx_cnt',
    value=37,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'bike_light_beam_angle_mode': Type(
    name='bike_light_beam_angle_mode',
    base_type='uint8',
    values=Map(
    map={0: TypeValue(
    name='manual',
    value=0,
), 1: TypeValue(
    name='auto',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'fit_base_unit': Type(
    name='fit_base_unit',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='other',
    value=0,
), 1: TypeValue(
    name='kilogram',
    value=1,
), 2: TypeValue(
    name='pound',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'set_type': Type(
    name='set_type',
    base_type='uint8',
    values=Map(
    map={0: TypeValue(
    name='rest',
    value=0,
), 1: TypeValue(
    name='active',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'exercise_category': Type(
    name='exercise_category',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='bench_press',
    value=0,
), 1: TypeValue(
    name='calf_raise',
    value=1,
), 2: TypeValue(
    name='cardio',
    value=2,
), 3: TypeValue(
    name='carry',
    value=3,
), 4: TypeValue(
    name='chop',
    value=4,
), 5: TypeValue(
    name='core',
    value=5,
), 6: TypeValue(
    name='crunch',
    value=6,
), 7: TypeValue(
    name='curl',
    value=7,
), 8: TypeValue(
    name='deadlift',
    value=8,
), 9: TypeValue(
    name='flye',
    value=9,
), 10: TypeValue(
    name='hip_raise',
    value=10,
), 11: TypeValue(
    name='hip_stability',
    value=11,
), 12: TypeValue(
    name='hip_swing',
    value=12,
), 13: TypeValue(
    name='hyperextension',
    value=13,
), 14: TypeValue(
    name='lateral_raise',
    value=14,
), 15: TypeValue(
    name='leg_curl',
    value=15,
), 16: TypeValue(
    name='leg_raise',
    value=16,
), 17: TypeValue(
    name='lunge',
    value=17,
), 18: TypeValue(
    name='olympic_lift',
    value=18,
), 19: TypeValue(
    name='plank',
    value=19,
), 20: TypeValue(
    name='plyo',
    value=20,
), 21: TypeValue(
    name='pull_up',
    value=21,
), 22: TypeValue(
    name='push_up',
    value=22,
), 23: TypeValue(
    name='row',
    value=23,
), 24: TypeValue(
    name='shoulder_press',
    value=24,
), 25: TypeValue(
    name='shoulder_stability',
    value=25,
), 26: TypeValue(
    name='shrug',
    value=26,
), 27: TypeValue(
    name='sit_up',
    value=27,
), 28: TypeValue(
    name='squat',
    value=28,
), 29: TypeValue(
    name='total_body',
    value=29,
), 30: TypeValue(
    name='triceps_extension',
    value=30,
), 31: TypeValue(
    name='warm_up',
    value=31,
), 32: TypeValue(
    name='run',
    value=32,
), 65534: TypeValue(
    name='unknown',
    value=65534,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'bench_press_exercise_name': Type(
    name='bench_press_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='alternating_dumbbell_chest_press_on_swiss_ball',
    value=0,
), 1: TypeValue(
    name='barbell_bench_press',
    value=1,
), 2: TypeValue(
    name='barbell_board_bench_press',
    value=2,
), 3: TypeValue(
    name='barbell_floor_press',
    value=3,
), 4: TypeValue(
    name='close_grip_barbell_bench_press',
    value=4,
), 5: TypeValue(
    name='decline_dumbbell_bench_press',
    value=5,
), 6: TypeValue(
    name='dumbbell_bench_press',
    value=6,
), 7: TypeValue(
    name='dumbbell_floor_press',
    value=7,
), 8: TypeValue(
    name='incline_barbell_bench_press',
    value=8,
), 9: TypeValue(
    name='incline_dumbbell_bench_press',
    value=9,
), 10: TypeValue(
    name='incline_smith_machine_bench_press',
    value=10,
), 11: TypeValue(
    name='isometric_barbell_bench_press',
    value=11,
), 12: TypeValue(
    name='kettlebell_chest_press',
    value=12,
), 13: TypeValue(
    name='neutral_grip_dumbbell_bench_press',
    value=13,
), 14: TypeValue(
    name='neutral_grip_dumbbell_incline_bench_press',
    value=14,
), 15: TypeValue(
    name='one_arm_floor_press',
    value=15,
), 16: TypeValue(
    name='weighted_one_arm_floor_press',
    value=16,
), 17: TypeValue(
    name='partial_lockout',
    value=17,
), 18: TypeValue(
    name='reverse_grip_barbell_bench_press',
    value=18,
), 19: TypeValue(
    name='reverse_grip_incline_bench_press',
    value=19,
), 20: TypeValue(
    name='single_arm_cable_chest_press',
    value=20,
), 21: TypeValue(
    name='single_arm_dumbbell_bench_press',
    value=21,
), 22: TypeValue(
    name='smith_machine_bench_press',
    value=22,
), 23: TypeValue(
    name='swiss_ball_dumbbell_chest_press',
    value=23,
), 24: TypeValue(
    name='triple_stop_barbell_bench_press',
    value=24,
), 25: TypeValue(
    name='wide_grip_barbell_bench_press',
    value=25,
), 26: TypeValue(
    name='alternating_dumbbell_chest_press',
    value=26,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'calf_raise_exercise_name': Type(
    name='calf_raise_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='3_way_calf_raise',
    value=0,
), 1: TypeValue(
    name='3_way_weighted_calf_raise',
    value=1,
), 2: TypeValue(
    name='3_way_single_leg_calf_raise',
    value=2,
), 3: TypeValue(
    name='3_way_weighted_single_leg_calf_raise',
    value=3,
), 4: TypeValue(
    name='donkey_calf_raise',
    value=4,
), 5: TypeValue(
    name='weighted_donkey_calf_raise',
    value=5,
), 6: TypeValue(
    name='seated_calf_raise',
    value=6,
), 7: TypeValue(
    name='weighted_seated_calf_raise',
    value=7,
), 8: TypeValue(
    name='seated_dumbbell_toe_raise',
    value=8,
), 9: TypeValue(
    name='single_leg_bent_knee_calf_raise',
    value=9,
), 10: TypeValue(
    name='weighted_single_leg_bent_knee_calf_raise',
    value=10,
), 11: TypeValue(
    name='single_leg_decline_push_up',
    value=11,
), 12: TypeValue(
    name='single_leg_donkey_calf_raise',
    value=12,
), 13: TypeValue(
    name='weighted_single_leg_donkey_calf_raise',
    value=13,
), 14: TypeValue(
    name='single_leg_hip_raise_with_knee_hold',
    value=14,
), 15: TypeValue(
    name='single_leg_standing_calf_raise',
    value=15,
), 16: TypeValue(
    name='single_leg_standing_dumbbell_calf_raise',
    value=16,
), 17: TypeValue(
    name='standing_barbell_calf_raise',
    value=17,
), 18: TypeValue(
    name='standing_calf_raise',
    value=18,
), 19: TypeValue(
    name='weighted_standing_calf_raise',
    value=19,
), 20: TypeValue(
    name='standing_dumbbell_calf_raise',
    value=20,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'cardio_exercise_name': Type(
    name='cardio_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='bob_and_weave_circle',
    value=0,
), 1: TypeValue(
    name='weighted_bob_and_weave_circle',
    value=1,
), 2: TypeValue(
    name='cardio_core_crawl',
    value=2,
), 3: TypeValue(
    name='weighted_cardio_core_crawl',
    value=3,
), 4: TypeValue(
    name='double_under',
    value=4,
), 5: TypeValue(
    name='weighted_double_under',
    value=5,
), 6: TypeValue(
    name='jump_rope',
    value=6,
), 7: TypeValue(
    name='weighted_jump_rope',
    value=7,
), 8: TypeValue(
    name='jump_rope_crossover',
    value=8,
), 9: TypeValue(
    name='weighted_jump_rope_crossover',
    value=9,
), 10: TypeValue(
    name='jump_rope_jog',
    value=10,
), 11: TypeValue(
    name='weighted_jump_rope_jog',
    value=11,
), 12: TypeValue(
    name='jumping_jacks',
    value=12,
), 13: TypeValue(
    name='weighted_jumping_jacks',
    value=13,
), 14: TypeValue(
    name='ski_moguls',
    value=14,
), 15: TypeValue(
    name='weighted_ski_moguls',
    value=15,
), 16: TypeValue(
    name='split_jacks',
    value=16,
), 17: TypeValue(
    name='weighted_split_jacks',
    value=17,
), 18: TypeValue(
    name='squat_jacks',
    value=18,
), 19: TypeValue(
    name='weighted_squat_jacks',
    value=19,
), 20: TypeValue(
    name='triple_under',
    value=20,
), 21: TypeValue(
    name='weighted_triple_under',
    value=21,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'carry_exercise_name': Type(
    name='carry_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='bar_holds',
    value=0,
), 1: TypeValue(
    name='farmers_walk',
    value=1,
), 2: TypeValue(
    name='farmers_walk_on_toes',
    value=2,
), 3: TypeValue(
    name='hex_dumbbell_hold',
    value=3,
), 4: TypeValue(
    name='overhead_carry',
    value=4,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'chop_exercise_name': Type(
    name='chop_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='cable_pull_through',
    value=0,
), 1: TypeValue(
    name='cable_rotational_lift',
    value=1,
), 2: TypeValue(
    name='cable_woodchop',
    value=2,
), 3: TypeValue(
    name='cross_chop_to_knee',
    value=3,
), 4: TypeValue(
    name='weighted_cross_chop_to_knee',
    value=4,
), 5: TypeValue(
    name='dumbbell_chop',
    value=5,
), 6: TypeValue(
    name='half_kneeling_rotation',
    value=6,
), 7: TypeValue(
    name='weighted_half_kneeling_rotation',
    value=7,
), 8: TypeValue(
    name='half_kneeling_rotational_chop',
    value=8,
), 9: TypeValue(
    name='half_kneeling_rotational_reverse_chop',
    value=9,
), 10: TypeValue(
    name='half_kneeling_stability_chop',
    value=10,
), 11: TypeValue(
    name='half_kneeling_stability_reverse_chop',
    value=11,
), 12: TypeValue(
    name='kneeling_rotational_chop',
    value=12,
), 13: TypeValue(
    name='kneeling_rotational_reverse_chop',
    value=13,
), 14: TypeValue(
    name='kneeling_stability_chop',
    value=14,
), 15: TypeValue(
    name='kneeling_woodchopper',
    value=15,
), 16: TypeValue(
    name='medicine_ball_wood_chops',
    value=16,
), 17: TypeValue(
    name='power_squat_chops',
    value=17,
), 18: TypeValue(
    name='weighted_power_squat_chops',
    value=18,
), 19: TypeValue(
    name='standing_rotational_chop',
    value=19,
), 20: TypeValue(
    name='standing_split_rotational_chop',
    value=20,
), 21: TypeValue(
    name='standing_split_rotational_reverse_chop',
    value=21,
), 22: TypeValue(
    name='standing_stability_reverse_chop',
    value=22,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'core_exercise_name': Type(
    name='core_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='abs_jabs',
    value=0,
), 1: TypeValue(
    name='weighted_abs_jabs',
    value=1,
), 2: TypeValue(
    name='alternating_plate_reach',
    value=2,
), 3: TypeValue(
    name='barbell_rollout',
    value=3,
), 4: TypeValue(
    name='weighted_barbell_rollout',
    value=4,
), 5: TypeValue(
    name='body_bar_oblique_twist',
    value=5,
), 6: TypeValue(
    name='cable_core_press',
    value=6,
), 7: TypeValue(
    name='cable_side_bend',
    value=7,
), 8: TypeValue(
    name='side_bend',
    value=8,
), 9: TypeValue(
    name='weighted_side_bend',
    value=9,
), 10: TypeValue(
    name='crescent_circle',
    value=10,
), 11: TypeValue(
    name='weighted_crescent_circle',
    value=11,
), 12: TypeValue(
    name='cycling_russian_twist',
    value=12,
), 13: TypeValue(
    name='weighted_cycling_russian_twist',
    value=13,
), 14: TypeValue(
    name='elevated_feet_russian_twist',
    value=14,
), 15: TypeValue(
    name='weighted_elevated_feet_russian_twist',
    value=15,
), 16: TypeValue(
    name='half_turkish_get_up',
    value=16,
), 17: TypeValue(
    name='kettlebell_windmill',
    value=17,
), 18: TypeValue(
    name='kneeling_ab_wheel',
    value=18,
), 19: TypeValue(
    name='weighted_kneeling_ab_wheel',
    value=19,
), 20: TypeValue(
    name='modified_front_lever',
    value=20,
), 21: TypeValue(
    name='open_knee_tucks',
    value=21,
), 22: TypeValue(
    name='weighted_open_knee_tucks',
    value=22,
), 23: TypeValue(
    name='side_abs_leg_lift',
    value=23,
), 24: TypeValue(
    name='weighted_side_abs_leg_lift',
    value=24,
), 25: TypeValue(
    name='swiss_ball_jackknife',
    value=25,
), 26: TypeValue(
    name='weighted_swiss_ball_jackknife',
    value=26,
), 27: TypeValue(
    name='swiss_ball_pike',
    value=27,
), 28: TypeValue(
    name='weighted_swiss_ball_pike',
    value=28,
), 29: TypeValue(
    name='swiss_ball_rollout',
    value=29,
), 30: TypeValue(
    name='weighted_swiss_ball_rollout',
    value=30,
), 31: TypeValue(
    name='triangle_hip_press',
    value=31,
), 32: TypeValue(
    name='weighted_triangle_hip_press',
    value=32,
), 33: TypeValue(
    name='trx_suspended_jackknife',
    value=33,
), 34: TypeValue(
    name='weighted_trx_suspended_jackknife',
    value=34,
), 35: TypeValue(
    name='u_boat',
    value=35,
), 36: TypeValue(
    name='weighted_u_boat',
    value=36,
), 37: TypeValue(
    name='windmill_switches',
    value=37,
), 38: TypeValue(
    name='weighted_windmill_switches',
    value=38,
), 39: TypeValue(
    name='alternating_slide_out',
    value=39,
), 40: TypeValue(
    name='weighted_alternating_slide_out',
    value=40,
), 41: TypeValue(
    name='ghd_back_extensions',
    value=41,
), 42: TypeValue(
    name='weighted_ghd_back_extensions',
    value=42,
), 43: TypeValue(
    name='overhead_walk',
    value=43,
), 44: TypeValue(
    name='inchworm',
    value=44,
), 45: TypeValue(
    name='weighted_modified_front_lever',
    value=45,
), 46: TypeValue(
    name='russian_twist',
    value=46,
), 47: TypeValue(
    name='abdominal_leg_rotations',
    value=47,
    comment='Deprecated do not use',
), 48: TypeValue(
    name='arm_and_leg_extension_on_knees',
    value=48,
), 49: TypeValue(
    name='bicycle',
    value=49,
), 50: TypeValue(
    name='bicep_curl_with_leg_extension',
    value=50,
), 51: TypeValue(
    name='cat_cow',
    value=51,
), 52: TypeValue(
    name='corkscrew',
    value=52,
), 53: TypeValue(
    name='criss_cross',
    value=53,
), 54: TypeValue(
    name='criss_cross_with_ball',
    value=54,
    comment='Deprecated do not use',
), 55: TypeValue(
    name='double_leg_stretch',
    value=55,
), 56: TypeValue(
    name='knee_folds',
    value=56,
), 57: TypeValue(
    name='lower_lift',
    value=57,
), 58: TypeValue(
    name='neck_pull',
    value=58,
), 59: TypeValue(
    name='pelvic_clocks',
    value=59,
), 60: TypeValue(
    name='roll_over',
    value=60,
), 61: TypeValue(
    name='roll_up',
    value=61,
), 62: TypeValue(
    name='rolling',
    value=62,
), 63: TypeValue(
    name='rowing_1',
    value=63,
), 64: TypeValue(
    name='rowing_2',
    value=64,
), 65: TypeValue(
    name='scissors',
    value=65,
), 66: TypeValue(
    name='single_leg_circles',
    value=66,
), 67: TypeValue(
    name='single_leg_stretch',
    value=67,
), 68: TypeValue(
    name='snake_twist_1_and_2',
    value=68,
    comment='Deprecated do not use',
), 69: TypeValue(
    name='swan',
    value=69,
), 70: TypeValue(
    name='swimming',
    value=70,
), 71: TypeValue(
    name='teaser',
    value=71,
), 72: TypeValue(
    name='the_hundred',
    value=72,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'crunch_exercise_name': Type(
    name='crunch_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='bicycle_crunch',
    value=0,
), 1: TypeValue(
    name='cable_crunch',
    value=1,
), 2: TypeValue(
    name='circular_arm_crunch',
    value=2,
), 3: TypeValue(
    name='crossed_arms_crunch',
    value=3,
), 4: TypeValue(
    name='weighted_crossed_arms_crunch',
    value=4,
), 5: TypeValue(
    name='cross_leg_reverse_crunch',
    value=5,
), 6: TypeValue(
    name='weighted_cross_leg_reverse_crunch',
    value=6,
), 7: TypeValue(
    name='crunch_chop',
    value=7,
), 8: TypeValue(
    name='weighted_crunch_chop',
    value=8,
), 9: TypeValue(
    name='double_crunch',
    value=9,
), 10: TypeValue(
    name='weighted_double_crunch',
    value=10,
), 11: TypeValue(
    name='elbow_to_knee_crunch',
    value=11,
), 12: TypeValue(
    name='weighted_elbow_to_knee_crunch',
    value=12,
), 13: TypeValue(
    name='flutter_kicks',
    value=13,
), 14: TypeValue(
    name='weighted_flutter_kicks',
    value=14,
), 15: TypeValue(
    name='foam_roller_reverse_crunch_on_bench',
    value=15,
), 16: TypeValue(
    name='weighted_foam_roller_reverse_crunch_on_bench',
    value=16,
), 17: TypeValue(
    name='foam_roller_reverse_crunch_with_dumbbell',
    value=17,
), 18: TypeValue(
    name='foam_roller_reverse_crunch_with_medicine_ball',
    value=18,
), 19: TypeValue(
    name='frog_press',
    value=19,
), 20: TypeValue(
    name='hanging_knee_raise_oblique_crunch',
    value=20,
), 21: TypeValue(
    name='weighted_hanging_knee_raise_oblique_crunch',
    value=21,
), 22: TypeValue(
    name='hip_crossover',
    value=22,
), 23: TypeValue(
    name='weighted_hip_crossover',
    value=23,
), 24: TypeValue(
    name='hollow_rock',
    value=24,
), 25: TypeValue(
    name='weighted_hollow_rock',
    value=25,
), 26: TypeValue(
    name='incline_reverse_crunch',
    value=26,
), 27: TypeValue(
    name='weighted_incline_reverse_crunch',
    value=27,
), 28: TypeValue(
    name='kneeling_cable_crunch',
    value=28,
), 29: TypeValue(
    name='kneeling_cross_crunch',
    value=29,
), 30: TypeValue(
    name='weighted_kneeling_cross_crunch',
    value=30,
), 31: TypeValue(
    name='kneeling_oblique_cable_crunch',
    value=31,
), 32: TypeValue(
    name='knees_to_elbow',
    value=32,
), 33: TypeValue(
    name='leg_extensions',
    value=33,
), 34: TypeValue(
    name='weighted_leg_extensions',
    value=34,
), 35: TypeValue(
    name='leg_levers',
    value=35,
), 36: TypeValue(
    name='mcgill_curl_up',
    value=36,
), 37: TypeValue(
    name='weighted_mcgill_curl_up',
    value=37,
), 38: TypeValue(
    name='modified_pilates_roll_up_with_ball',
    value=38,
), 39: TypeValue(
    name='weighted_modified_pilates_roll_up_with_ball',
    value=39,
), 40: TypeValue(
    name='pilates_crunch',
    value=40,
), 41: TypeValue(
    name='weighted_pilates_crunch',
    value=41,
), 42: TypeValue(
    name='pilates_roll_up_with_ball',
    value=42,
), 43: TypeValue(
    name='weighted_pilates_roll_up_with_ball',
    value=43,
), 44: TypeValue(
    name='raised_legs_crunch',
    value=44,
), 45: TypeValue(
    name='weighted_raised_legs_crunch',
    value=45,
), 46: TypeValue(
    name='reverse_crunch',
    value=46,
), 47: TypeValue(
    name='weighted_reverse_crunch',
    value=47,
), 48: TypeValue(
    name='reverse_crunch_on_a_bench',
    value=48,
), 49: TypeValue(
    name='weighted_reverse_crunch_on_a_bench',
    value=49,
), 50: TypeValue(
    name='reverse_curl_and_lift',
    value=50,
), 51: TypeValue(
    name='weighted_reverse_curl_and_lift',
    value=51,
), 52: TypeValue(
    name='rotational_lift',
    value=52,
), 53: TypeValue(
    name='weighted_rotational_lift',
    value=53,
), 54: TypeValue(
    name='seated_alternating_reverse_crunch',
    value=54,
), 55: TypeValue(
    name='weighted_seated_alternating_reverse_crunch',
    value=55,
), 56: TypeValue(
    name='seated_leg_u',
    value=56,
), 57: TypeValue(
    name='weighted_seated_leg_u',
    value=57,
), 58: TypeValue(
    name='side_to_side_crunch_and_weave',
    value=58,
), 59: TypeValue(
    name='weighted_side_to_side_crunch_and_weave',
    value=59,
), 60: TypeValue(
    name='single_leg_reverse_crunch',
    value=60,
), 61: TypeValue(
    name='weighted_single_leg_reverse_crunch',
    value=61,
), 62: TypeValue(
    name='skater_crunch_cross',
    value=62,
), 63: TypeValue(
    name='weighted_skater_crunch_cross',
    value=63,
), 64: TypeValue(
    name='standing_cable_crunch',
    value=64,
), 65: TypeValue(
    name='standing_side_crunch',
    value=65,
), 66: TypeValue(
    name='step_climb',
    value=66,
), 67: TypeValue(
    name='weighted_step_climb',
    value=67,
), 68: TypeValue(
    name='swiss_ball_crunch',
    value=68,
), 69: TypeValue(
    name='swiss_ball_reverse_crunch',
    value=69,
), 70: TypeValue(
    name='weighted_swiss_ball_reverse_crunch',
    value=70,
), 71: TypeValue(
    name='swiss_ball_russian_twist',
    value=71,
), 72: TypeValue(
    name='weighted_swiss_ball_russian_twist',
    value=72,
), 73: TypeValue(
    name='swiss_ball_side_crunch',
    value=73,
), 74: TypeValue(
    name='weighted_swiss_ball_side_crunch',
    value=74,
), 75: TypeValue(
    name='thoracic_crunches_on_foam_roller',
    value=75,
), 76: TypeValue(
    name='weighted_thoracic_crunches_on_foam_roller',
    value=76,
), 77: TypeValue(
    name='triceps_crunch',
    value=77,
), 78: TypeValue(
    name='weighted_bicycle_crunch',
    value=78,
), 79: TypeValue(
    name='weighted_crunch',
    value=79,
), 80: TypeValue(
    name='weighted_swiss_ball_crunch',
    value=80,
), 81: TypeValue(
    name='toes_to_bar',
    value=81,
), 82: TypeValue(
    name='weighted_toes_to_bar',
    value=82,
), 83: TypeValue(
    name='crunch',
    value=83,
), 84: TypeValue(
    name='straight_leg_crunch_with_ball',
    value=84,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'curl_exercise_name': Type(
    name='curl_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='alternating_dumbbell_biceps_curl',
    value=0,
), 1: TypeValue(
    name='alternating_dumbbell_biceps_curl_on_swiss_ball',
    value=1,
), 2: TypeValue(
    name='alternating_incline_dumbbell_biceps_curl',
    value=2,
), 3: TypeValue(
    name='barbell_biceps_curl',
    value=3,
), 4: TypeValue(
    name='barbell_reverse_wrist_curl',
    value=4,
), 5: TypeValue(
    name='barbell_wrist_curl',
    value=5,
), 6: TypeValue(
    name='behind_the_back_barbell_reverse_wrist_curl',
    value=6,
), 7: TypeValue(
    name='behind_the_back_one_arm_cable_curl',
    value=7,
), 8: TypeValue(
    name='cable_biceps_curl',
    value=8,
), 9: TypeValue(
    name='cable_hammer_curl',
    value=9,
), 10: TypeValue(
    name='cheating_barbell_biceps_curl',
    value=10,
), 11: TypeValue(
    name='close_grip_ez_bar_biceps_curl',
    value=11,
), 12: TypeValue(
    name='cross_body_dumbbell_hammer_curl',
    value=12,
), 13: TypeValue(
    name='dead_hang_biceps_curl',
    value=13,
), 14: TypeValue(
    name='decline_hammer_curl',
    value=14,
), 15: TypeValue(
    name='dumbbell_biceps_curl_with_static_hold',
    value=15,
), 16: TypeValue(
    name='dumbbell_hammer_curl',
    value=16,
), 17: TypeValue(
    name='dumbbell_reverse_wrist_curl',
    value=17,
), 18: TypeValue(
    name='dumbbell_wrist_curl',
    value=18,
), 19: TypeValue(
    name='ez_bar_preacher_curl',
    value=19,
), 20: TypeValue(
    name='forward_bend_biceps_curl',
    value=20,
), 21: TypeValue(
    name='hammer_curl_to_press',
    value=21,
), 22: TypeValue(
    name='incline_dumbbell_biceps_curl',
    value=22,
), 23: TypeValue(
    name='incline_offset_thumb_dumbbell_curl',
    value=23,
), 24: TypeValue(
    name='kettlebell_biceps_curl',
    value=24,
), 25: TypeValue(
    name='lying_concentration_cable_curl',
    value=25,
), 26: TypeValue(
    name='one_arm_preacher_curl',
    value=26,
), 27: TypeValue(
    name='plate_pinch_curl',
    value=27,
), 28: TypeValue(
    name='preacher_curl_with_cable',
    value=28,
), 29: TypeValue(
    name='reverse_ez_bar_curl',
    value=29,
), 30: TypeValue(
    name='reverse_grip_wrist_curl',
    value=30,
), 31: TypeValue(
    name='reverse_grip_barbell_biceps_curl',
    value=31,
), 32: TypeValue(
    name='seated_alternating_dumbbell_biceps_curl',
    value=32,
), 33: TypeValue(
    name='seated_dumbbell_biceps_curl',
    value=33,
), 34: TypeValue(
    name='seated_reverse_dumbbell_curl',
    value=34,
), 35: TypeValue(
    name='split_stance_offset_pinky_dumbbell_curl',
    value=35,
), 36: TypeValue(
    name='standing_alternating_dumbbell_curls',
    value=36,
), 37: TypeValue(
    name='standing_dumbbell_biceps_curl',
    value=37,
), 38: TypeValue(
    name='standing_ez_bar_biceps_curl',
    value=38,
), 39: TypeValue(
    name='static_curl',
    value=39,
), 40: TypeValue(
    name='swiss_ball_dumbbell_overhead_triceps_extension',
    value=40,
), 41: TypeValue(
    name='swiss_ball_ez_bar_preacher_curl',
    value=41,
), 42: TypeValue(
    name='twisting_standing_dumbbell_biceps_curl',
    value=42,
), 43: TypeValue(
    name='wide_grip_ez_bar_biceps_curl',
    value=43,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'deadlift_exercise_name': Type(
    name='deadlift_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='barbell_deadlift',
    value=0,
), 1: TypeValue(
    name='barbell_straight_leg_deadlift',
    value=1,
), 2: TypeValue(
    name='dumbbell_deadlift',
    value=2,
), 3: TypeValue(
    name='dumbbell_single_leg_deadlift_to_row',
    value=3,
), 4: TypeValue(
    name='dumbbell_straight_leg_deadlift',
    value=4,
), 5: TypeValue(
    name='kettlebell_floor_to_shelf',
    value=5,
), 6: TypeValue(
    name='one_arm_one_leg_deadlift',
    value=6,
), 7: TypeValue(
    name='rack_pull',
    value=7,
), 8: TypeValue(
    name='rotational_dumbbell_straight_leg_deadlift',
    value=8,
), 9: TypeValue(
    name='single_arm_deadlift',
    value=9,
), 10: TypeValue(
    name='single_leg_barbell_deadlift',
    value=10,
), 11: TypeValue(
    name='single_leg_barbell_straight_leg_deadlift',
    value=11,
), 12: TypeValue(
    name='single_leg_deadlift_with_barbell',
    value=12,
), 13: TypeValue(
    name='single_leg_rdl_circuit',
    value=13,
), 14: TypeValue(
    name='single_leg_romanian_deadlift_with_dumbbell',
    value=14,
), 15: TypeValue(
    name='sumo_deadlift',
    value=15,
), 16: TypeValue(
    name='sumo_deadlift_high_pull',
    value=16,
), 17: TypeValue(
    name='trap_bar_deadlift',
    value=17,
), 18: TypeValue(
    name='wide_grip_barbell_deadlift',
    value=18,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'flye_exercise_name': Type(
    name='flye_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='cable_crossover',
    value=0,
), 1: TypeValue(
    name='decline_dumbbell_flye',
    value=1,
), 2: TypeValue(
    name='dumbbell_flye',
    value=2,
), 3: TypeValue(
    name='incline_dumbbell_flye',
    value=3,
), 4: TypeValue(
    name='kettlebell_flye',
    value=4,
), 5: TypeValue(
    name='kneeling_rear_flye',
    value=5,
), 6: TypeValue(
    name='single_arm_standing_cable_reverse_flye',
    value=6,
), 7: TypeValue(
    name='swiss_ball_dumbbell_flye',
    value=7,
), 8: TypeValue(
    name='arm_rotations',
    value=8,
), 9: TypeValue(
    name='hug_a_tree',
    value=9,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'hip_raise_exercise_name': Type(
    name='hip_raise_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='barbell_hip_thrust_on_floor',
    value=0,
), 1: TypeValue(
    name='barbell_hip_thrust_with_bench',
    value=1,
), 2: TypeValue(
    name='bent_knee_swiss_ball_reverse_hip_raise',
    value=2,
), 3: TypeValue(
    name='weighted_bent_knee_swiss_ball_reverse_hip_raise',
    value=3,
), 4: TypeValue(
    name='bridge_with_leg_extension',
    value=4,
), 5: TypeValue(
    name='weighted_bridge_with_leg_extension',
    value=5,
), 6: TypeValue(
    name='clam_bridge',
    value=6,
), 7: TypeValue(
    name='front_kick_tabletop',
    value=7,
), 8: TypeValue(
    name='weighted_front_kick_tabletop',
    value=8,
), 9: TypeValue(
    name='hip_extension_and_cross',
    value=9,
), 10: TypeValue(
    name='weighted_hip_extension_and_cross',
    value=10,
), 11: TypeValue(
    name='hip_raise',
    value=11,
), 12: TypeValue(
    name='weighted_hip_raise',
    value=12,
), 13: TypeValue(
    name='hip_raise_with_feet_on_swiss_ball',
    value=13,
), 14: TypeValue(
    name='weighted_hip_raise_with_feet_on_swiss_ball',
    value=14,
), 15: TypeValue(
    name='hip_raise_with_head_on_bosu_ball',
    value=15,
), 16: TypeValue(
    name='weighted_hip_raise_with_head_on_bosu_ball',
    value=16,
), 17: TypeValue(
    name='hip_raise_with_head_on_swiss_ball',
    value=17,
), 18: TypeValue(
    name='weighted_hip_raise_with_head_on_swiss_ball',
    value=18,
), 19: TypeValue(
    name='hip_raise_with_knee_squeeze',
    value=19,
), 20: TypeValue(
    name='weighted_hip_raise_with_knee_squeeze',
    value=20,
), 21: TypeValue(
    name='incline_rear_leg_extension',
    value=21,
), 22: TypeValue(
    name='weighted_incline_rear_leg_extension',
    value=22,
), 23: TypeValue(
    name='kettlebell_swing',
    value=23,
), 24: TypeValue(
    name='marching_hip_raise',
    value=24,
), 25: TypeValue(
    name='weighted_marching_hip_raise',
    value=25,
), 26: TypeValue(
    name='marching_hip_raise_with_feet_on_a_swiss_ball',
    value=26,
), 27: TypeValue(
    name='weighted_marching_hip_raise_with_feet_on_a_swiss_ball',
    value=27,
), 28: TypeValue(
    name='reverse_hip_raise',
    value=28,
), 29: TypeValue(
    name='weighted_reverse_hip_raise',
    value=29,
), 30: TypeValue(
    name='single_leg_hip_raise',
    value=30,
), 31: TypeValue(
    name='weighted_single_leg_hip_raise',
    value=31,
), 32: TypeValue(
    name='single_leg_hip_raise_with_foot_on_bench',
    value=32,
), 33: TypeValue(
    name='weighted_single_leg_hip_raise_with_foot_on_bench',
    value=33,
), 34: TypeValue(
    name='single_leg_hip_raise_with_foot_on_bosu_ball',
    value=34,
), 35: TypeValue(
    name='weighted_single_leg_hip_raise_with_foot_on_bosu_ball',
    value=35,
), 36: TypeValue(
    name='single_leg_hip_raise_with_foot_on_foam_roller',
    value=36,
), 37: TypeValue(
    name='weighted_single_leg_hip_raise_with_foot_on_foam_roller',
    value=37,
), 38: TypeValue(
    name='single_leg_hip_raise_with_foot_on_medicine_ball',
    value=38,
), 39: TypeValue(
    name='weighted_single_leg_hip_raise_with_foot_on_medicine_ball',
    value=39,
), 40: TypeValue(
    name='single_leg_hip_raise_with_head_on_bosu_ball',
    value=40,
), 41: TypeValue(
    name='weighted_single_leg_hip_raise_with_head_on_bosu_ball',
    value=41,
), 42: TypeValue(
    name='weighted_clam_bridge',
    value=42,
), 43: TypeValue(
    name='single_leg_swiss_ball_hip_raise_and_leg_curl',
    value=43,
), 44: TypeValue(
    name='clams',
    value=44,
), 45: TypeValue(
    name='inner_thigh_circles',
    value=45,
    comment='Deprecated do not use',
), 46: TypeValue(
    name='inner_thigh_side_lift',
    value=46,
    comment='Deprecated do not use',
), 47: TypeValue(
    name='leg_circles',
    value=47,
), 48: TypeValue(
    name='leg_lift',
    value=48,
), 49: TypeValue(
    name='leg_lift_in_external_rotation',
    value=49,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'hip_stability_exercise_name': Type(
    name='hip_stability_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='band_side_lying_leg_raise',
    value=0,
), 1: TypeValue(
    name='dead_bug',
    value=1,
), 2: TypeValue(
    name='weighted_dead_bug',
    value=2,
), 3: TypeValue(
    name='external_hip_raise',
    value=3,
), 4: TypeValue(
    name='weighted_external_hip_raise',
    value=4,
), 5: TypeValue(
    name='fire_hydrant_kicks',
    value=5,
), 6: TypeValue(
    name='weighted_fire_hydrant_kicks',
    value=6,
), 7: TypeValue(
    name='hip_circles',
    value=7,
), 8: TypeValue(
    name='weighted_hip_circles',
    value=8,
), 9: TypeValue(
    name='inner_thigh_lift',
    value=9,
), 10: TypeValue(
    name='weighted_inner_thigh_lift',
    value=10,
), 11: TypeValue(
    name='lateral_walks_with_band_at_ankles',
    value=11,
), 12: TypeValue(
    name='pretzel_side_kick',
    value=12,
), 13: TypeValue(
    name='weighted_pretzel_side_kick',
    value=13,
), 14: TypeValue(
    name='prone_hip_internal_rotation',
    value=14,
), 15: TypeValue(
    name='weighted_prone_hip_internal_rotation',
    value=15,
), 16: TypeValue(
    name='quadruped',
    value=16,
), 17: TypeValue(
    name='quadruped_hip_extension',
    value=17,
), 18: TypeValue(
    name='weighted_quadruped_hip_extension',
    value=18,
), 19: TypeValue(
    name='quadruped_with_leg_lift',
    value=19,
), 20: TypeValue(
    name='weighted_quadruped_with_leg_lift',
    value=20,
), 21: TypeValue(
    name='side_lying_leg_raise',
    value=21,
), 22: TypeValue(
    name='weighted_side_lying_leg_raise',
    value=22,
), 23: TypeValue(
    name='sliding_hip_adduction',
    value=23,
), 24: TypeValue(
    name='weighted_sliding_hip_adduction',
    value=24,
), 25: TypeValue(
    name='standing_adduction',
    value=25,
), 26: TypeValue(
    name='weighted_standing_adduction',
    value=26,
), 27: TypeValue(
    name='standing_cable_hip_abduction',
    value=27,
), 28: TypeValue(
    name='standing_hip_abduction',
    value=28,
), 29: TypeValue(
    name='weighted_standing_hip_abduction',
    value=29,
), 30: TypeValue(
    name='standing_rear_leg_raise',
    value=30,
), 31: TypeValue(
    name='weighted_standing_rear_leg_raise',
    value=31,
), 32: TypeValue(
    name='supine_hip_internal_rotation',
    value=32,
), 33: TypeValue(
    name='weighted_supine_hip_internal_rotation',
    value=33,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'hip_swing_exercise_name': Type(
    name='hip_swing_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='single_arm_kettlebell_swing',
    value=0,
), 1: TypeValue(
    name='single_arm_dumbbell_swing',
    value=1,
), 2: TypeValue(
    name='step_out_swing',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'hyperextension_exercise_name': Type(
    name='hyperextension_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='back_extension_with_opposite_arm_and_leg_reach',
    value=0,
), 1: TypeValue(
    name='weighted_back_extension_with_opposite_arm_and_leg_reach',
    value=1,
), 2: TypeValue(
    name='base_rotations',
    value=2,
), 3: TypeValue(
    name='weighted_base_rotations',
    value=3,
), 4: TypeValue(
    name='bent_knee_reverse_hyperextension',
    value=4,
), 5: TypeValue(
    name='weighted_bent_knee_reverse_hyperextension',
    value=5,
), 6: TypeValue(
    name='hollow_hold_and_roll',
    value=6,
), 7: TypeValue(
    name='weighted_hollow_hold_and_roll',
    value=7,
), 8: TypeValue(
    name='kicks',
    value=8,
), 9: TypeValue(
    name='weighted_kicks',
    value=9,
), 10: TypeValue(
    name='knee_raises',
    value=10,
), 11: TypeValue(
    name='weighted_knee_raises',
    value=11,
), 12: TypeValue(
    name='kneeling_superman',
    value=12,
), 13: TypeValue(
    name='weighted_kneeling_superman',
    value=13,
), 14: TypeValue(
    name='lat_pull_down_with_row',
    value=14,
), 15: TypeValue(
    name='medicine_ball_deadlift_to_reach',
    value=15,
), 16: TypeValue(
    name='one_arm_one_leg_row',
    value=16,
), 17: TypeValue(
    name='one_arm_row_with_band',
    value=17,
), 18: TypeValue(
    name='overhead_lunge_with_medicine_ball',
    value=18,
), 19: TypeValue(
    name='plank_knee_tucks',
    value=19,
), 20: TypeValue(
    name='weighted_plank_knee_tucks',
    value=20,
), 21: TypeValue(
    name='side_step',
    value=21,
), 22: TypeValue(
    name='weighted_side_step',
    value=22,
), 23: TypeValue(
    name='single_leg_back_extension',
    value=23,
), 24: TypeValue(
    name='weighted_single_leg_back_extension',
    value=24,
), 25: TypeValue(
    name='spine_extension',
    value=25,
), 26: TypeValue(
    name='weighted_spine_extension',
    value=26,
), 27: TypeValue(
    name='static_back_extension',
    value=27,
), 28: TypeValue(
    name='weighted_static_back_extension',
    value=28,
), 29: TypeValue(
    name='superman_from_floor',
    value=29,
), 30: TypeValue(
    name='weighted_superman_from_floor',
    value=30,
), 31: TypeValue(
    name='swiss_ball_back_extension',
    value=31,
), 32: TypeValue(
    name='weighted_swiss_ball_back_extension',
    value=32,
), 33: TypeValue(
    name='swiss_ball_hyperextension',
    value=33,
), 34: TypeValue(
    name='weighted_swiss_ball_hyperextension',
    value=34,
), 35: TypeValue(
    name='swiss_ball_opposite_arm_and_leg_lift',
    value=35,
), 36: TypeValue(
    name='weighted_swiss_ball_opposite_arm_and_leg_lift',
    value=36,
), 37: TypeValue(
    name='superman_on_swiss_ball',
    value=37,
), 38: TypeValue(
    name='cobra',
    value=38,
), 39: TypeValue(
    name='supine_floor_barre',
    value=39,
    comment='Deprecated do not use',
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'lateral_raise_exercise_name': Type(
    name='lateral_raise_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='45_degree_cable_external_rotation',
    value=0,
), 1: TypeValue(
    name='alternating_lateral_raise_with_static_hold',
    value=1,
), 2: TypeValue(
    name='bar_muscle_up',
    value=2,
), 3: TypeValue(
    name='bent_over_lateral_raise',
    value=3,
), 4: TypeValue(
    name='cable_diagonal_raise',
    value=4,
), 5: TypeValue(
    name='cable_front_raise',
    value=5,
), 6: TypeValue(
    name='calorie_row',
    value=6,
), 7: TypeValue(
    name='combo_shoulder_raise',
    value=7,
), 8: TypeValue(
    name='dumbbell_diagonal_raise',
    value=8,
), 9: TypeValue(
    name='dumbbell_v_raise',
    value=9,
), 10: TypeValue(
    name='front_raise',
    value=10,
), 11: TypeValue(
    name='leaning_dumbbell_lateral_raise',
    value=11,
), 12: TypeValue(
    name='lying_dumbbell_raise',
    value=12,
), 13: TypeValue(
    name='muscle_up',
    value=13,
), 14: TypeValue(
    name='one_arm_cable_lateral_raise',
    value=14,
), 15: TypeValue(
    name='overhand_grip_rear_lateral_raise',
    value=15,
), 16: TypeValue(
    name='plate_raises',
    value=16,
), 17: TypeValue(
    name='ring_dip',
    value=17,
), 18: TypeValue(
    name='weighted_ring_dip',
    value=18,
), 19: TypeValue(
    name='ring_muscle_up',
    value=19,
), 20: TypeValue(
    name='weighted_ring_muscle_up',
    value=20,
), 21: TypeValue(
    name='rope_climb',
    value=21,
), 22: TypeValue(
    name='weighted_rope_climb',
    value=22,
), 23: TypeValue(
    name='scaption',
    value=23,
), 24: TypeValue(
    name='seated_lateral_raise',
    value=24,
), 25: TypeValue(
    name='seated_rear_lateral_raise',
    value=25,
), 26: TypeValue(
    name='side_lying_lateral_raise',
    value=26,
), 27: TypeValue(
    name='standing_lift',
    value=27,
), 28: TypeValue(
    name='suspended_row',
    value=28,
), 29: TypeValue(
    name='underhand_grip_rear_lateral_raise',
    value=29,
), 30: TypeValue(
    name='wall_slide',
    value=30,
), 31: TypeValue(
    name='weighted_wall_slide',
    value=31,
), 32: TypeValue(
    name='arm_circles',
    value=32,
), 33: TypeValue(
    name='shaving_the_head',
    value=33,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'leg_curl_exercise_name': Type(
    name='leg_curl_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='leg_curl',
    value=0,
), 1: TypeValue(
    name='weighted_leg_curl',
    value=1,
), 2: TypeValue(
    name='good_morning',
    value=2,
), 3: TypeValue(
    name='seated_barbell_good_morning',
    value=3,
), 4: TypeValue(
    name='single_leg_barbell_good_morning',
    value=4,
), 5: TypeValue(
    name='single_leg_sliding_leg_curl',
    value=5,
), 6: TypeValue(
    name='sliding_leg_curl',
    value=6,
), 7: TypeValue(
    name='split_barbell_good_morning',
    value=7,
), 8: TypeValue(
    name='split_stance_extension',
    value=8,
), 9: TypeValue(
    name='staggered_stance_good_morning',
    value=9,
), 10: TypeValue(
    name='swiss_ball_hip_raise_and_leg_curl',
    value=10,
), 11: TypeValue(
    name='zercher_good_morning',
    value=11,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'leg_raise_exercise_name': Type(
    name='leg_raise_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='hanging_knee_raise',
    value=0,
), 1: TypeValue(
    name='hanging_leg_raise',
    value=1,
), 2: TypeValue(
    name='weighted_hanging_leg_raise',
    value=2,
), 3: TypeValue(
    name='hanging_single_leg_raise',
    value=3,
), 4: TypeValue(
    name='weighted_hanging_single_leg_raise',
    value=4,
), 5: TypeValue(
    name='kettlebell_leg_raises',
    value=5,
), 6: TypeValue(
    name='leg_lowering_drill',
    value=6,
), 7: TypeValue(
    name='weighted_leg_lowering_drill',
    value=7,
), 8: TypeValue(
    name='lying_straight_leg_raise',
    value=8,
), 9: TypeValue(
    name='weighted_lying_straight_leg_raise',
    value=9,
), 10: TypeValue(
    name='medicine_ball_leg_drops',
    value=10,
), 11: TypeValue(
    name='quadruped_leg_raise',
    value=11,
), 12: TypeValue(
    name='weighted_quadruped_leg_raise',
    value=12,
), 13: TypeValue(
    name='reverse_leg_raise',
    value=13,
), 14: TypeValue(
    name='weighted_reverse_leg_raise',
    value=14,
), 15: TypeValue(
    name='reverse_leg_raise_on_swiss_ball',
    value=15,
), 16: TypeValue(
    name='weighted_reverse_leg_raise_on_swiss_ball',
    value=16,
), 17: TypeValue(
    name='single_leg_lowering_drill',
    value=17,
), 18: TypeValue(
    name='weighted_single_leg_lowering_drill',
    value=18,
), 19: TypeValue(
    name='weighted_hanging_knee_raise',
    value=19,
), 20: TypeValue(
    name='lateral_stepover',
    value=20,
), 21: TypeValue(
    name='weighted_lateral_stepover',
    value=21,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'lunge_exercise_name': Type(
    name='lunge_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='overhead_lunge',
    value=0,
), 1: TypeValue(
    name='lunge_matrix',
    value=1,
), 2: TypeValue(
    name='weighted_lunge_matrix',
    value=2,
), 3: TypeValue(
    name='alternating_barbell_forward_lunge',
    value=3,
), 4: TypeValue(
    name='alternating_dumbbell_lunge_with_reach',
    value=4,
), 5: TypeValue(
    name='back_foot_elevated_dumbbell_split_squat',
    value=5,
), 6: TypeValue(
    name='barbell_box_lunge',
    value=6,
), 7: TypeValue(
    name='barbell_bulgarian_split_squat',
    value=7,
), 8: TypeValue(
    name='barbell_crossover_lunge',
    value=8,
), 9: TypeValue(
    name='barbell_front_split_squat',
    value=9,
), 10: TypeValue(
    name='barbell_lunge',
    value=10,
), 11: TypeValue(
    name='barbell_reverse_lunge',
    value=11,
), 12: TypeValue(
    name='barbell_side_lunge',
    value=12,
), 13: TypeValue(
    name='barbell_split_squat',
    value=13,
), 14: TypeValue(
    name='core_control_rear_lunge',
    value=14,
), 15: TypeValue(
    name='diagonal_lunge',
    value=15,
), 16: TypeValue(
    name='drop_lunge',
    value=16,
), 17: TypeValue(
    name='dumbbell_box_lunge',
    value=17,
), 18: TypeValue(
    name='dumbbell_bulgarian_split_squat',
    value=18,
), 19: TypeValue(
    name='dumbbell_crossover_lunge',
    value=19,
), 20: TypeValue(
    name='dumbbell_diagonal_lunge',
    value=20,
), 21: TypeValue(
    name='dumbbell_lunge',
    value=21,
), 22: TypeValue(
    name='dumbbell_lunge_and_rotation',
    value=22,
), 23: TypeValue(
    name='dumbbell_overhead_bulgarian_split_squat',
    value=23,
), 24: TypeValue(
    name='dumbbell_reverse_lunge_to_high_knee_and_press',
    value=24,
), 25: TypeValue(
    name='dumbbell_side_lunge',
    value=25,
), 26: TypeValue(
    name='elevated_front_foot_barbell_split_squat',
    value=26,
), 27: TypeValue(
    name='front_foot_elevated_dumbbell_split_squat',
    value=27,
), 28: TypeValue(
    name='gunslinger_lunge',
    value=28,
), 29: TypeValue(
    name='lawnmower_lunge',
    value=29,
), 30: TypeValue(
    name='low_lunge_with_isometric_adduction',
    value=30,
), 31: TypeValue(
    name='low_side_to_side_lunge',
    value=31,
), 32: TypeValue(
    name='lunge',
    value=32,
), 33: TypeValue(
    name='weighted_lunge',
    value=33,
), 34: TypeValue(
    name='lunge_with_arm_reach',
    value=34,
), 35: TypeValue(
    name='lunge_with_diagonal_reach',
    value=35,
), 36: TypeValue(
    name='lunge_with_side_bend',
    value=36,
), 37: TypeValue(
    name='offset_dumbbell_lunge',
    value=37,
), 38: TypeValue(
    name='offset_dumbbell_reverse_lunge',
    value=38,
), 39: TypeValue(
    name='overhead_bulgarian_split_squat',
    value=39,
), 40: TypeValue(
    name='overhead_dumbbell_reverse_lunge',
    value=40,
), 41: TypeValue(
    name='overhead_dumbbell_split_squat',
    value=41,
), 42: TypeValue(
    name='overhead_lunge_with_rotation',
    value=42,
), 43: TypeValue(
    name='reverse_barbell_box_lunge',
    value=43,
), 44: TypeValue(
    name='reverse_box_lunge',
    value=44,
), 45: TypeValue(
    name='reverse_dumbbell_box_lunge',
    value=45,
), 46: TypeValue(
    name='reverse_dumbbell_crossover_lunge',
    value=46,
), 47: TypeValue(
    name='reverse_dumbbell_diagonal_lunge',
    value=47,
), 48: TypeValue(
    name='reverse_lunge_with_reach_back',
    value=48,
), 49: TypeValue(
    name='weighted_reverse_lunge_with_reach_back',
    value=49,
), 50: TypeValue(
    name='reverse_lunge_with_twist_and_overhead_reach',
    value=50,
), 51: TypeValue(
    name='weighted_reverse_lunge_with_twist_and_overhead_reach',
    value=51,
), 52: TypeValue(
    name='reverse_sliding_box_lunge',
    value=52,
), 53: TypeValue(
    name='weighted_reverse_sliding_box_lunge',
    value=53,
), 54: TypeValue(
    name='reverse_sliding_lunge',
    value=54,
), 55: TypeValue(
    name='weighted_reverse_sliding_lunge',
    value=55,
), 56: TypeValue(
    name='runners_lunge_to_balance',
    value=56,
), 57: TypeValue(
    name='weighted_runners_lunge_to_balance',
    value=57,
), 58: TypeValue(
    name='shifting_side_lunge',
    value=58,
), 59: TypeValue(
    name='side_and_crossover_lunge',
    value=59,
), 60: TypeValue(
    name='weighted_side_and_crossover_lunge',
    value=60,
), 61: TypeValue(
    name='side_lunge',
    value=61,
), 62: TypeValue(
    name='weighted_side_lunge',
    value=62,
), 63: TypeValue(
    name='side_lunge_and_press',
    value=63,
), 64: TypeValue(
    name='side_lunge_jump_off',
    value=64,
), 65: TypeValue(
    name='side_lunge_sweep',
    value=65,
), 66: TypeValue(
    name='weighted_side_lunge_sweep',
    value=66,
), 67: TypeValue(
    name='side_lunge_to_crossover_tap',
    value=67,
), 68: TypeValue(
    name='weighted_side_lunge_to_crossover_tap',
    value=68,
), 69: TypeValue(
    name='side_to_side_lunge_chops',
    value=69,
), 70: TypeValue(
    name='weighted_side_to_side_lunge_chops',
    value=70,
), 71: TypeValue(
    name='siff_jump_lunge',
    value=71,
), 72: TypeValue(
    name='weighted_siff_jump_lunge',
    value=72,
), 73: TypeValue(
    name='single_arm_reverse_lunge_and_press',
    value=73,
), 74: TypeValue(
    name='sliding_lateral_lunge',
    value=74,
), 75: TypeValue(
    name='weighted_sliding_lateral_lunge',
    value=75,
), 76: TypeValue(
    name='walking_barbell_lunge',
    value=76,
), 77: TypeValue(
    name='walking_dumbbell_lunge',
    value=77,
), 78: TypeValue(
    name='walking_lunge',
    value=78,
), 79: TypeValue(
    name='weighted_walking_lunge',
    value=79,
), 80: TypeValue(
    name='wide_grip_overhead_barbell_split_squat',
    value=80,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'olympic_lift_exercise_name': Type(
    name='olympic_lift_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='barbell_hang_power_clean',
    value=0,
), 1: TypeValue(
    name='barbell_hang_squat_clean',
    value=1,
), 2: TypeValue(
    name='barbell_power_clean',
    value=2,
), 3: TypeValue(
    name='barbell_power_snatch',
    value=3,
), 4: TypeValue(
    name='barbell_squat_clean',
    value=4,
), 5: TypeValue(
    name='clean_and_jerk',
    value=5,
), 6: TypeValue(
    name='barbell_hang_power_snatch',
    value=6,
), 7: TypeValue(
    name='barbell_hang_pull',
    value=7,
), 8: TypeValue(
    name='barbell_high_pull',
    value=8,
), 9: TypeValue(
    name='barbell_snatch',
    value=9,
), 10: TypeValue(
    name='barbell_split_jerk',
    value=10,
), 11: TypeValue(
    name='clean',
    value=11,
), 12: TypeValue(
    name='dumbbell_clean',
    value=12,
), 13: TypeValue(
    name='dumbbell_hang_pull',
    value=13,
), 14: TypeValue(
    name='one_hand_dumbbell_split_snatch',
    value=14,
), 15: TypeValue(
    name='push_jerk',
    value=15,
), 16: TypeValue(
    name='single_arm_dumbbell_snatch',
    value=16,
), 17: TypeValue(
    name='single_arm_hang_snatch',
    value=17,
), 18: TypeValue(
    name='single_arm_kettlebell_snatch',
    value=18,
), 19: TypeValue(
    name='split_jerk',
    value=19,
), 20: TypeValue(
    name='squat_clean_and_jerk',
    value=20,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'plank_exercise_name': Type(
    name='plank_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='45_degree_plank',
    value=0,
), 1: TypeValue(
    name='weighted_45_degree_plank',
    value=1,
), 2: TypeValue(
    name='90_degree_static_hold',
    value=2,
), 3: TypeValue(
    name='weighted_90_degree_static_hold',
    value=3,
), 4: TypeValue(
    name='bear_crawl',
    value=4,
), 5: TypeValue(
    name='weighted_bear_crawl',
    value=5,
), 6: TypeValue(
    name='cross_body_mountain_climber',
    value=6,
), 7: TypeValue(
    name='weighted_cross_body_mountain_climber',
    value=7,
), 8: TypeValue(
    name='elbow_plank_pike_jacks',
    value=8,
), 9: TypeValue(
    name='weighted_elbow_plank_pike_jacks',
    value=9,
), 10: TypeValue(
    name='elevated_feet_plank',
    value=10,
), 11: TypeValue(
    name='weighted_elevated_feet_plank',
    value=11,
), 12: TypeValue(
    name='elevator_abs',
    value=12,
), 13: TypeValue(
    name='weighted_elevator_abs',
    value=13,
), 14: TypeValue(
    name='extended_plank',
    value=14,
), 15: TypeValue(
    name='weighted_extended_plank',
    value=15,
), 16: TypeValue(
    name='full_plank_passe_twist',
    value=16,
), 17: TypeValue(
    name='weighted_full_plank_passe_twist',
    value=17,
), 18: TypeValue(
    name='inching_elbow_plank',
    value=18,
), 19: TypeValue(
    name='weighted_inching_elbow_plank',
    value=19,
), 20: TypeValue(
    name='inchworm_to_side_plank',
    value=20,
), 21: TypeValue(
    name='weighted_inchworm_to_side_plank',
    value=21,
), 22: TypeValue(
    name='kneeling_plank',
    value=22,
), 23: TypeValue(
    name='weighted_kneeling_plank',
    value=23,
), 24: TypeValue(
    name='kneeling_side_plank_with_leg_lift',
    value=24,
), 25: TypeValue(
    name='weighted_kneeling_side_plank_with_leg_lift',
    value=25,
), 26: TypeValue(
    name='lateral_roll',
    value=26,
), 27: TypeValue(
    name='weighted_lateral_roll',
    value=27,
), 28: TypeValue(
    name='lying_reverse_plank',
    value=28,
), 29: TypeValue(
    name='weighted_lying_reverse_plank',
    value=29,
), 30: TypeValue(
    name='medicine_ball_mountain_climber',
    value=30,
), 31: TypeValue(
    name='weighted_medicine_ball_mountain_climber',
    value=31,
), 32: TypeValue(
    name='modified_mountain_climber_and_extension',
    value=32,
), 33: TypeValue(
    name='weighted_modified_mountain_climber_and_extension',
    value=33,
), 34: TypeValue(
    name='mountain_climber',
    value=34,
), 35: TypeValue(
    name='weighted_mountain_climber',
    value=35,
), 36: TypeValue(
    name='mountain_climber_on_sliding_discs',
    value=36,
), 37: TypeValue(
    name='weighted_mountain_climber_on_sliding_discs',
    value=37,
), 38: TypeValue(
    name='mountain_climber_with_feet_on_bosu_ball',
    value=38,
), 39: TypeValue(
    name='weighted_mountain_climber_with_feet_on_bosu_ball',
    value=39,
), 40: TypeValue(
    name='mountain_climber_with_hands_on_bench',
    value=40,
), 41: TypeValue(
    name='mountain_climber_with_hands_on_swiss_ball',
    value=41,
), 42: TypeValue(
    name='weighted_mountain_climber_with_hands_on_swiss_ball',
    value=42,
), 43: TypeValue(
    name='plank',
    value=43,
), 44: TypeValue(
    name='plank_jacks_with_feet_on_sliding_discs',
    value=44,
), 45: TypeValue(
    name='weighted_plank_jacks_with_feet_on_sliding_discs',
    value=45,
), 46: TypeValue(
    name='plank_knee_twist',
    value=46,
), 47: TypeValue(
    name='weighted_plank_knee_twist',
    value=47,
), 48: TypeValue(
    name='plank_pike_jumps',
    value=48,
), 49: TypeValue(
    name='weighted_plank_pike_jumps',
    value=49,
), 50: TypeValue(
    name='plank_pikes',
    value=50,
), 51: TypeValue(
    name='weighted_plank_pikes',
    value=51,
), 52: TypeValue(
    name='plank_to_stand_up',
    value=52,
), 53: TypeValue(
    name='weighted_plank_to_stand_up',
    value=53,
), 54: TypeValue(
    name='plank_with_arm_raise',
    value=54,
), 55: TypeValue(
    name='weighted_plank_with_arm_raise',
    value=55,
), 56: TypeValue(
    name='plank_with_knee_to_elbow',
    value=56,
), 57: TypeValue(
    name='weighted_plank_with_knee_to_elbow',
    value=57,
), 58: TypeValue(
    name='plank_with_oblique_crunch',
    value=58,
), 59: TypeValue(
    name='weighted_plank_with_oblique_crunch',
    value=59,
), 60: TypeValue(
    name='plyometric_side_plank',
    value=60,
), 61: TypeValue(
    name='weighted_plyometric_side_plank',
    value=61,
), 62: TypeValue(
    name='rolling_side_plank',
    value=62,
), 63: TypeValue(
    name='weighted_rolling_side_plank',
    value=63,
), 64: TypeValue(
    name='side_kick_plank',
    value=64,
), 65: TypeValue(
    name='weighted_side_kick_plank',
    value=65,
), 66: TypeValue(
    name='side_plank',
    value=66,
), 67: TypeValue(
    name='weighted_side_plank',
    value=67,
), 68: TypeValue(
    name='side_plank_and_row',
    value=68,
), 69: TypeValue(
    name='weighted_side_plank_and_row',
    value=69,
), 70: TypeValue(
    name='side_plank_lift',
    value=70,
), 71: TypeValue(
    name='weighted_side_plank_lift',
    value=71,
), 72: TypeValue(
    name='side_plank_with_elbow_on_bosu_ball',
    value=72,
), 73: TypeValue(
    name='weighted_side_plank_with_elbow_on_bosu_ball',
    value=73,
), 74: TypeValue(
    name='side_plank_with_feet_on_bench',
    value=74,
), 75: TypeValue(
    name='weighted_side_plank_with_feet_on_bench',
    value=75,
), 76: TypeValue(
    name='side_plank_with_knee_circle',
    value=76,
), 77: TypeValue(
    name='weighted_side_plank_with_knee_circle',
    value=77,
), 78: TypeValue(
    name='side_plank_with_knee_tuck',
    value=78,
), 79: TypeValue(
    name='weighted_side_plank_with_knee_tuck',
    value=79,
), 80: TypeValue(
    name='side_plank_with_leg_lift',
    value=80,
), 81: TypeValue(
    name='weighted_side_plank_with_leg_lift',
    value=81,
), 82: TypeValue(
    name='side_plank_with_reach_under',
    value=82,
), 83: TypeValue(
    name='weighted_side_plank_with_reach_under',
    value=83,
), 84: TypeValue(
    name='single_leg_elevated_feet_plank',
    value=84,
), 85: TypeValue(
    name='weighted_single_leg_elevated_feet_plank',
    value=85,
), 86: TypeValue(
    name='single_leg_flex_and_extend',
    value=86,
), 87: TypeValue(
    name='weighted_single_leg_flex_and_extend',
    value=87,
), 88: TypeValue(
    name='single_leg_side_plank',
    value=88,
), 89: TypeValue(
    name='weighted_single_leg_side_plank',
    value=89,
), 90: TypeValue(
    name='spiderman_plank',
    value=90,
), 91: TypeValue(
    name='weighted_spiderman_plank',
    value=91,
), 92: TypeValue(
    name='straight_arm_plank',
    value=92,
), 93: TypeValue(
    name='weighted_straight_arm_plank',
    value=93,
), 94: TypeValue(
    name='straight_arm_plank_with_shoulder_touch',
    value=94,
), 95: TypeValue(
    name='weighted_straight_arm_plank_with_shoulder_touch',
    value=95,
), 96: TypeValue(
    name='swiss_ball_plank',
    value=96,
), 97: TypeValue(
    name='weighted_swiss_ball_plank',
    value=97,
), 98: TypeValue(
    name='swiss_ball_plank_leg_lift',
    value=98,
), 99: TypeValue(
    name='weighted_swiss_ball_plank_leg_lift',
    value=99,
), 100: TypeValue(
    name='swiss_ball_plank_leg_lift_and_hold',
    value=100,
), 101: TypeValue(
    name='swiss_ball_plank_with_feet_on_bench',
    value=101,
), 102: TypeValue(
    name='weighted_swiss_ball_plank_with_feet_on_bench',
    value=102,
), 103: TypeValue(
    name='swiss_ball_prone_jackknife',
    value=103,
), 104: TypeValue(
    name='weighted_swiss_ball_prone_jackknife',
    value=104,
), 105: TypeValue(
    name='swiss_ball_side_plank',
    value=105,
), 106: TypeValue(
    name='weighted_swiss_ball_side_plank',
    value=106,
), 107: TypeValue(
    name='three_way_plank',
    value=107,
), 108: TypeValue(
    name='weighted_three_way_plank',
    value=108,
), 109: TypeValue(
    name='towel_plank_and_knee_in',
    value=109,
), 110: TypeValue(
    name='weighted_towel_plank_and_knee_in',
    value=110,
), 111: TypeValue(
    name='t_stabilization',
    value=111,
), 112: TypeValue(
    name='weighted_t_stabilization',
    value=112,
), 113: TypeValue(
    name='turkish_get_up_to_side_plank',
    value=113,
), 114: TypeValue(
    name='weighted_turkish_get_up_to_side_plank',
    value=114,
), 115: TypeValue(
    name='two_point_plank',
    value=115,
), 116: TypeValue(
    name='weighted_two_point_plank',
    value=116,
), 117: TypeValue(
    name='weighted_plank',
    value=117,
), 118: TypeValue(
    name='wide_stance_plank_with_diagonal_arm_lift',
    value=118,
), 119: TypeValue(
    name='weighted_wide_stance_plank_with_diagonal_arm_lift',
    value=119,
), 120: TypeValue(
    name='wide_stance_plank_with_diagonal_leg_lift',
    value=120,
), 121: TypeValue(
    name='weighted_wide_stance_plank_with_diagonal_leg_lift',
    value=121,
), 122: TypeValue(
    name='wide_stance_plank_with_leg_lift',
    value=122,
), 123: TypeValue(
    name='weighted_wide_stance_plank_with_leg_lift',
    value=123,
), 124: TypeValue(
    name='wide_stance_plank_with_opposite_arm_and_leg_lift',
    value=124,
), 125: TypeValue(
    name='weighted_mountain_climber_with_hands_on_bench',
    value=125,
), 126: TypeValue(
    name='weighted_swiss_ball_plank_leg_lift_and_hold',
    value=126,
), 127: TypeValue(
    name='weighted_wide_stance_plank_with_opposite_arm_and_leg_lift',
    value=127,
), 128: TypeValue(
    name='plank_with_feet_on_swiss_ball',
    value=128,
), 129: TypeValue(
    name='side_plank_to_plank_with_reach_under',
    value=129,
), 130: TypeValue(
    name='bridge_with_glute_lower_lift',
    value=130,
), 131: TypeValue(
    name='bridge_one_leg_bridge',
    value=131,
), 132: TypeValue(
    name='plank_with_arm_variations',
    value=132,
), 133: TypeValue(
    name='plank_with_leg_lift',
    value=133,
), 134: TypeValue(
    name='reverse_plank_with_leg_pull',
    value=134,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'plyo_exercise_name': Type(
    name='plyo_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='alternating_jump_lunge',
    value=0,
), 1: TypeValue(
    name='weighted_alternating_jump_lunge',
    value=1,
), 2: TypeValue(
    name='barbell_jump_squat',
    value=2,
), 3: TypeValue(
    name='body_weight_jump_squat',
    value=3,
), 4: TypeValue(
    name='weighted_jump_squat',
    value=4,
), 5: TypeValue(
    name='cross_knee_strike',
    value=5,
), 6: TypeValue(
    name='weighted_cross_knee_strike',
    value=6,
), 7: TypeValue(
    name='depth_jump',
    value=7,
), 8: TypeValue(
    name='weighted_depth_jump',
    value=8,
), 9: TypeValue(
    name='dumbbell_jump_squat',
    value=9,
), 10: TypeValue(
    name='dumbbell_split_jump',
    value=10,
), 11: TypeValue(
    name='front_knee_strike',
    value=11,
), 12: TypeValue(
    name='weighted_front_knee_strike',
    value=12,
), 13: TypeValue(
    name='high_box_jump',
    value=13,
), 14: TypeValue(
    name='weighted_high_box_jump',
    value=14,
), 15: TypeValue(
    name='isometric_explosive_body_weight_jump_squat',
    value=15,
), 16: TypeValue(
    name='weighted_isometric_explosive_jump_squat',
    value=16,
), 17: TypeValue(
    name='lateral_leap_and_hop',
    value=17,
), 18: TypeValue(
    name='weighted_lateral_leap_and_hop',
    value=18,
), 19: TypeValue(
    name='lateral_plyo_squats',
    value=19,
), 20: TypeValue(
    name='weighted_lateral_plyo_squats',
    value=20,
), 21: TypeValue(
    name='lateral_slide',
    value=21,
), 22: TypeValue(
    name='weighted_lateral_slide',
    value=22,
), 23: TypeValue(
    name='medicine_ball_overhead_throws',
    value=23,
), 24: TypeValue(
    name='medicine_ball_side_throw',
    value=24,
), 25: TypeValue(
    name='medicine_ball_slam',
    value=25,
), 26: TypeValue(
    name='side_to_side_medicine_ball_throws',
    value=26,
), 27: TypeValue(
    name='side_to_side_shuffle_jump',
    value=27,
), 28: TypeValue(
    name='weighted_side_to_side_shuffle_jump',
    value=28,
), 29: TypeValue(
    name='squat_jump_onto_box',
    value=29,
), 30: TypeValue(
    name='weighted_squat_jump_onto_box',
    value=30,
), 31: TypeValue(
    name='squat_jumps_in_and_out',
    value=31,
), 32: TypeValue(
    name='weighted_squat_jumps_in_and_out',
    value=32,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'pull_up_exercise_name': Type(
    name='pull_up_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='banded_pull_ups',
    value=0,
), 1: TypeValue(
    name='30_degree_lat_pulldown',
    value=1,
), 2: TypeValue(
    name='band_assisted_chin_up',
    value=2,
), 3: TypeValue(
    name='close_grip_chin_up',
    value=3,
), 4: TypeValue(
    name='weighted_close_grip_chin_up',
    value=4,
), 5: TypeValue(
    name='close_grip_lat_pulldown',
    value=5,
), 6: TypeValue(
    name='crossover_chin_up',
    value=6,
), 7: TypeValue(
    name='weighted_crossover_chin_up',
    value=7,
), 8: TypeValue(
    name='ez_bar_pullover',
    value=8,
), 9: TypeValue(
    name='hanging_hurdle',
    value=9,
), 10: TypeValue(
    name='weighted_hanging_hurdle',
    value=10,
), 11: TypeValue(
    name='kneeling_lat_pulldown',
    value=11,
), 12: TypeValue(
    name='kneeling_underhand_grip_lat_pulldown',
    value=12,
), 13: TypeValue(
    name='lat_pulldown',
    value=13,
), 14: TypeValue(
    name='mixed_grip_chin_up',
    value=14,
), 15: TypeValue(
    name='weighted_mixed_grip_chin_up',
    value=15,
), 16: TypeValue(
    name='mixed_grip_pull_up',
    value=16,
), 17: TypeValue(
    name='weighted_mixed_grip_pull_up',
    value=17,
), 18: TypeValue(
    name='reverse_grip_pulldown',
    value=18,
), 19: TypeValue(
    name='standing_cable_pullover',
    value=19,
), 20: TypeValue(
    name='straight_arm_pulldown',
    value=20,
), 21: TypeValue(
    name='swiss_ball_ez_bar_pullover',
    value=21,
), 22: TypeValue(
    name='towel_pull_up',
    value=22,
), 23: TypeValue(
    name='weighted_towel_pull_up',
    value=23,
), 24: TypeValue(
    name='weighted_pull_up',
    value=24,
), 25: TypeValue(
    name='wide_grip_lat_pulldown',
    value=25,
), 26: TypeValue(
    name='wide_grip_pull_up',
    value=26,
), 27: TypeValue(
    name='weighted_wide_grip_pull_up',
    value=27,
), 28: TypeValue(
    name='burpee_pull_up',
    value=28,
), 29: TypeValue(
    name='weighted_burpee_pull_up',
    value=29,
), 30: TypeValue(
    name='jumping_pull_ups',
    value=30,
), 31: TypeValue(
    name='weighted_jumping_pull_ups',
    value=31,
), 32: TypeValue(
    name='kipping_pull_up',
    value=32,
), 33: TypeValue(
    name='weighted_kipping_pull_up',
    value=33,
), 34: TypeValue(
    name='l_pull_up',
    value=34,
), 35: TypeValue(
    name='weighted_l_pull_up',
    value=35,
), 36: TypeValue(
    name='suspended_chin_up',
    value=36,
), 37: TypeValue(
    name='weighted_suspended_chin_up',
    value=37,
), 38: TypeValue(
    name='pull_up',
    value=38,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'push_up_exercise_name': Type(
    name='push_up_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='chest_press_with_band',
    value=0,
), 1: TypeValue(
    name='alternating_staggered_push_up',
    value=1,
), 2: TypeValue(
    name='weighted_alternating_staggered_push_up',
    value=2,
), 3: TypeValue(
    name='alternating_hands_medicine_ball_push_up',
    value=3,
), 4: TypeValue(
    name='weighted_alternating_hands_medicine_ball_push_up',
    value=4,
), 5: TypeValue(
    name='bosu_ball_push_up',
    value=5,
), 6: TypeValue(
    name='weighted_bosu_ball_push_up',
    value=6,
), 7: TypeValue(
    name='clapping_push_up',
    value=7,
), 8: TypeValue(
    name='weighted_clapping_push_up',
    value=8,
), 9: TypeValue(
    name='close_grip_medicine_ball_push_up',
    value=9,
), 10: TypeValue(
    name='weighted_close_grip_medicine_ball_push_up',
    value=10,
), 11: TypeValue(
    name='close_hands_push_up',
    value=11,
), 12: TypeValue(
    name='weighted_close_hands_push_up',
    value=12,
), 13: TypeValue(
    name='decline_push_up',
    value=13,
), 14: TypeValue(
    name='weighted_decline_push_up',
    value=14,
), 15: TypeValue(
    name='diamond_push_up',
    value=15,
), 16: TypeValue(
    name='weighted_diamond_push_up',
    value=16,
), 17: TypeValue(
    name='explosive_crossover_push_up',
    value=17,
), 18: TypeValue(
    name='weighted_explosive_crossover_push_up',
    value=18,
), 19: TypeValue(
    name='explosive_push_up',
    value=19,
), 20: TypeValue(
    name='weighted_explosive_push_up',
    value=20,
), 21: TypeValue(
    name='feet_elevated_side_to_side_push_up',
    value=21,
), 22: TypeValue(
    name='weighted_feet_elevated_side_to_side_push_up',
    value=22,
), 23: TypeValue(
    name='hand_release_push_up',
    value=23,
), 24: TypeValue(
    name='weighted_hand_release_push_up',
    value=24,
), 25: TypeValue(
    name='handstand_push_up',
    value=25,
), 26: TypeValue(
    name='weighted_handstand_push_up',
    value=26,
), 27: TypeValue(
    name='incline_push_up',
    value=27,
), 28: TypeValue(
    name='weighted_incline_push_up',
    value=28,
), 29: TypeValue(
    name='isometric_explosive_push_up',
    value=29,
), 30: TypeValue(
    name='weighted_isometric_explosive_push_up',
    value=30,
), 31: TypeValue(
    name='judo_push_up',
    value=31,
), 32: TypeValue(
    name='weighted_judo_push_up',
    value=32,
), 33: TypeValue(
    name='kneeling_push_up',
    value=33,
), 34: TypeValue(
    name='weighted_kneeling_push_up',
    value=34,
), 35: TypeValue(
    name='medicine_ball_chest_pass',
    value=35,
), 36: TypeValue(
    name='medicine_ball_push_up',
    value=36,
), 37: TypeValue(
    name='weighted_medicine_ball_push_up',
    value=37,
), 38: TypeValue(
    name='one_arm_push_up',
    value=38,
), 39: TypeValue(
    name='weighted_one_arm_push_up',
    value=39,
), 40: TypeValue(
    name='weighted_push_up',
    value=40,
), 41: TypeValue(
    name='push_up_and_row',
    value=41,
), 42: TypeValue(
    name='weighted_push_up_and_row',
    value=42,
), 43: TypeValue(
    name='push_up_plus',
    value=43,
), 44: TypeValue(
    name='weighted_push_up_plus',
    value=44,
), 45: TypeValue(
    name='push_up_with_feet_on_swiss_ball',
    value=45,
), 46: TypeValue(
    name='weighted_push_up_with_feet_on_swiss_ball',
    value=46,
), 47: TypeValue(
    name='push_up_with_one_hand_on_medicine_ball',
    value=47,
), 48: TypeValue(
    name='weighted_push_up_with_one_hand_on_medicine_ball',
    value=48,
), 49: TypeValue(
    name='shoulder_push_up',
    value=49,
), 50: TypeValue(
    name='weighted_shoulder_push_up',
    value=50,
), 51: TypeValue(
    name='single_arm_medicine_ball_push_up',
    value=51,
), 52: TypeValue(
    name='weighted_single_arm_medicine_ball_push_up',
    value=52,
), 53: TypeValue(
    name='spiderman_push_up',
    value=53,
), 54: TypeValue(
    name='weighted_spiderman_push_up',
    value=54,
), 55: TypeValue(
    name='stacked_feet_push_up',
    value=55,
), 56: TypeValue(
    name='weighted_stacked_feet_push_up',
    value=56,
), 57: TypeValue(
    name='staggered_hands_push_up',
    value=57,
), 58: TypeValue(
    name='weighted_staggered_hands_push_up',
    value=58,
), 59: TypeValue(
    name='suspended_push_up',
    value=59,
), 60: TypeValue(
    name='weighted_suspended_push_up',
    value=60,
), 61: TypeValue(
    name='swiss_ball_push_up',
    value=61,
), 62: TypeValue(
    name='weighted_swiss_ball_push_up',
    value=62,
), 63: TypeValue(
    name='swiss_ball_push_up_plus',
    value=63,
), 64: TypeValue(
    name='weighted_swiss_ball_push_up_plus',
    value=64,
), 65: TypeValue(
    name='t_push_up',
    value=65,
), 66: TypeValue(
    name='weighted_t_push_up',
    value=66,
), 67: TypeValue(
    name='triple_stop_push_up',
    value=67,
), 68: TypeValue(
    name='weighted_triple_stop_push_up',
    value=68,
), 69: TypeValue(
    name='wide_hands_push_up',
    value=69,
), 70: TypeValue(
    name='weighted_wide_hands_push_up',
    value=70,
), 71: TypeValue(
    name='parallette_handstand_push_up',
    value=71,
), 72: TypeValue(
    name='weighted_parallette_handstand_push_up',
    value=72,
), 73: TypeValue(
    name='ring_handstand_push_up',
    value=73,
), 74: TypeValue(
    name='weighted_ring_handstand_push_up',
    value=74,
), 75: TypeValue(
    name='ring_push_up',
    value=75,
), 76: TypeValue(
    name='weighted_ring_push_up',
    value=76,
), 77: TypeValue(
    name='push_up',
    value=77,
), 78: TypeValue(
    name='pilates_pushup',
    value=78,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'row_exercise_name': Type(
    name='row_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='barbell_straight_leg_deadlift_to_row',
    value=0,
), 1: TypeValue(
    name='cable_row_standing',
    value=1,
), 2: TypeValue(
    name='dumbbell_row',
    value=2,
), 3: TypeValue(
    name='elevated_feet_inverted_row',
    value=3,
), 4: TypeValue(
    name='weighted_elevated_feet_inverted_row',
    value=4,
), 5: TypeValue(
    name='face_pull',
    value=5,
), 6: TypeValue(
    name='face_pull_with_external_rotation',
    value=6,
), 7: TypeValue(
    name='inverted_row_with_feet_on_swiss_ball',
    value=7,
), 8: TypeValue(
    name='weighted_inverted_row_with_feet_on_swiss_ball',
    value=8,
), 9: TypeValue(
    name='kettlebell_row',
    value=9,
), 10: TypeValue(
    name='modified_inverted_row',
    value=10,
), 11: TypeValue(
    name='weighted_modified_inverted_row',
    value=11,
), 12: TypeValue(
    name='neutral_grip_alternating_dumbbell_row',
    value=12,
), 13: TypeValue(
    name='one_arm_bent_over_row',
    value=13,
), 14: TypeValue(
    name='one_legged_dumbbell_row',
    value=14,
), 15: TypeValue(
    name='renegade_row',
    value=15,
), 16: TypeValue(
    name='reverse_grip_barbell_row',
    value=16,
), 17: TypeValue(
    name='rope_handle_cable_row',
    value=17,
), 18: TypeValue(
    name='seated_cable_row',
    value=18,
), 19: TypeValue(
    name='seated_dumbbell_row',
    value=19,
), 20: TypeValue(
    name='single_arm_cable_row',
    value=20,
), 21: TypeValue(
    name='single_arm_cable_row_and_rotation',
    value=21,
), 22: TypeValue(
    name='single_arm_inverted_row',
    value=22,
), 23: TypeValue(
    name='weighted_single_arm_inverted_row',
    value=23,
), 24: TypeValue(
    name='single_arm_neutral_grip_dumbbell_row',
    value=24,
), 25: TypeValue(
    name='single_arm_neutral_grip_dumbbell_row_and_rotation',
    value=25,
), 26: TypeValue(
    name='suspended_inverted_row',
    value=26,
), 27: TypeValue(
    name='weighted_suspended_inverted_row',
    value=27,
), 28: TypeValue(
    name='t_bar_row',
    value=28,
), 29: TypeValue(
    name='towel_grip_inverted_row',
    value=29,
), 30: TypeValue(
    name='weighted_towel_grip_inverted_row',
    value=30,
), 31: TypeValue(
    name='underhand_grip_cable_row',
    value=31,
), 32: TypeValue(
    name='v_grip_cable_row',
    value=32,
), 33: TypeValue(
    name='wide_grip_seated_cable_row',
    value=33,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'shoulder_press_exercise_name': Type(
    name='shoulder_press_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='alternating_dumbbell_shoulder_press',
    value=0,
), 1: TypeValue(
    name='arnold_press',
    value=1,
), 2: TypeValue(
    name='barbell_front_squat_to_push_press',
    value=2,
), 3: TypeValue(
    name='barbell_push_press',
    value=3,
), 4: TypeValue(
    name='barbell_shoulder_press',
    value=4,
), 5: TypeValue(
    name='dead_curl_press',
    value=5,
), 6: TypeValue(
    name='dumbbell_alternating_shoulder_press_and_twist',
    value=6,
), 7: TypeValue(
    name='dumbbell_hammer_curl_to_lunge_to_press',
    value=7,
), 8: TypeValue(
    name='dumbbell_push_press',
    value=8,
), 9: TypeValue(
    name='floor_inverted_shoulder_press',
    value=9,
), 10: TypeValue(
    name='weighted_floor_inverted_shoulder_press',
    value=10,
), 11: TypeValue(
    name='inverted_shoulder_press',
    value=11,
), 12: TypeValue(
    name='weighted_inverted_shoulder_press',
    value=12,
), 13: TypeValue(
    name='one_arm_push_press',
    value=13,
), 14: TypeValue(
    name='overhead_barbell_press',
    value=14,
), 15: TypeValue(
    name='overhead_dumbbell_press',
    value=15,
), 16: TypeValue(
    name='seated_barbell_shoulder_press',
    value=16,
), 17: TypeValue(
    name='seated_dumbbell_shoulder_press',
    value=17,
), 18: TypeValue(
    name='single_arm_dumbbell_shoulder_press',
    value=18,
), 19: TypeValue(
    name='single_arm_step_up_and_press',
    value=19,
), 20: TypeValue(
    name='smith_machine_overhead_press',
    value=20,
), 21: TypeValue(
    name='split_stance_hammer_curl_to_press',
    value=21,
), 22: TypeValue(
    name='swiss_ball_dumbbell_shoulder_press',
    value=22,
), 23: TypeValue(
    name='weight_plate_front_raise',
    value=23,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'shoulder_stability_exercise_name': Type(
    name='shoulder_stability_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='90_degree_cable_external_rotation',
    value=0,
), 1: TypeValue(
    name='band_external_rotation',
    value=1,
), 2: TypeValue(
    name='band_internal_rotation',
    value=2,
), 3: TypeValue(
    name='bent_arm_lateral_raise_and_external_rotation',
    value=3,
), 4: TypeValue(
    name='cable_external_rotation',
    value=4,
), 5: TypeValue(
    name='dumbbell_face_pull_with_external_rotation',
    value=5,
), 6: TypeValue(
    name='floor_i_raise',
    value=6,
), 7: TypeValue(
    name='weighted_floor_i_raise',
    value=7,
), 8: TypeValue(
    name='floor_t_raise',
    value=8,
), 9: TypeValue(
    name='weighted_floor_t_raise',
    value=9,
), 10: TypeValue(
    name='floor_y_raise',
    value=10,
), 11: TypeValue(
    name='weighted_floor_y_raise',
    value=11,
), 12: TypeValue(
    name='incline_i_raise',
    value=12,
), 13: TypeValue(
    name='weighted_incline_i_raise',
    value=13,
), 14: TypeValue(
    name='incline_l_raise',
    value=14,
), 15: TypeValue(
    name='weighted_incline_l_raise',
    value=15,
), 16: TypeValue(
    name='incline_t_raise',
    value=16,
), 17: TypeValue(
    name='weighted_incline_t_raise',
    value=17,
), 18: TypeValue(
    name='incline_w_raise',
    value=18,
), 19: TypeValue(
    name='weighted_incline_w_raise',
    value=19,
), 20: TypeValue(
    name='incline_y_raise',
    value=20,
), 21: TypeValue(
    name='weighted_incline_y_raise',
    value=21,
), 22: TypeValue(
    name='lying_external_rotation',
    value=22,
), 23: TypeValue(
    name='seated_dumbbell_external_rotation',
    value=23,
), 24: TypeValue(
    name='standing_l_raise',
    value=24,
), 25: TypeValue(
    name='swiss_ball_i_raise',
    value=25,
), 26: TypeValue(
    name='weighted_swiss_ball_i_raise',
    value=26,
), 27: TypeValue(
    name='swiss_ball_t_raise',
    value=27,
), 28: TypeValue(
    name='weighted_swiss_ball_t_raise',
    value=28,
), 29: TypeValue(
    name='swiss_ball_w_raise',
    value=29,
), 30: TypeValue(
    name='weighted_swiss_ball_w_raise',
    value=30,
), 31: TypeValue(
    name='swiss_ball_y_raise',
    value=31,
), 32: TypeValue(
    name='weighted_swiss_ball_y_raise',
    value=32,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'shrug_exercise_name': Type(
    name='shrug_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='barbell_jump_shrug',
    value=0,
), 1: TypeValue(
    name='barbell_shrug',
    value=1,
), 2: TypeValue(
    name='barbell_upright_row',
    value=2,
), 3: TypeValue(
    name='behind_the_back_smith_machine_shrug',
    value=3,
), 4: TypeValue(
    name='dumbbell_jump_shrug',
    value=4,
), 5: TypeValue(
    name='dumbbell_shrug',
    value=5,
), 6: TypeValue(
    name='dumbbell_upright_row',
    value=6,
), 7: TypeValue(
    name='incline_dumbbell_shrug',
    value=7,
), 8: TypeValue(
    name='overhead_barbell_shrug',
    value=8,
), 9: TypeValue(
    name='overhead_dumbbell_shrug',
    value=9,
), 10: TypeValue(
    name='scaption_and_shrug',
    value=10,
), 11: TypeValue(
    name='scapular_retraction',
    value=11,
), 12: TypeValue(
    name='serratus_chair_shrug',
    value=12,
), 13: TypeValue(
    name='weighted_serratus_chair_shrug',
    value=13,
), 14: TypeValue(
    name='serratus_shrug',
    value=14,
), 15: TypeValue(
    name='weighted_serratus_shrug',
    value=15,
), 16: TypeValue(
    name='wide_grip_jump_shrug',
    value=16,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'sit_up_exercise_name': Type(
    name='sit_up_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='alternating_sit_up',
    value=0,
), 1: TypeValue(
    name='weighted_alternating_sit_up',
    value=1,
), 2: TypeValue(
    name='bent_knee_v_up',
    value=2,
), 3: TypeValue(
    name='weighted_bent_knee_v_up',
    value=3,
), 4: TypeValue(
    name='butterfly_sit_up',
    value=4,
), 5: TypeValue(
    name='weighted_butterfly_situp',
    value=5,
), 6: TypeValue(
    name='cross_punch_roll_up',
    value=6,
), 7: TypeValue(
    name='weighted_cross_punch_roll_up',
    value=7,
), 8: TypeValue(
    name='crossed_arms_sit_up',
    value=8,
), 9: TypeValue(
    name='weighted_crossed_arms_sit_up',
    value=9,
), 10: TypeValue(
    name='get_up_sit_up',
    value=10,
), 11: TypeValue(
    name='weighted_get_up_sit_up',
    value=11,
), 12: TypeValue(
    name='hovering_sit_up',
    value=12,
), 13: TypeValue(
    name='weighted_hovering_sit_up',
    value=13,
), 14: TypeValue(
    name='kettlebell_sit_up',
    value=14,
), 15: TypeValue(
    name='medicine_ball_alternating_v_up',
    value=15,
), 16: TypeValue(
    name='medicine_ball_sit_up',
    value=16,
), 17: TypeValue(
    name='medicine_ball_v_up',
    value=17,
), 18: TypeValue(
    name='modified_sit_up',
    value=18,
), 19: TypeValue(
    name='negative_sit_up',
    value=19,
), 20: TypeValue(
    name='one_arm_full_sit_up',
    value=20,
), 21: TypeValue(
    name='reclining_circle',
    value=21,
), 22: TypeValue(
    name='weighted_reclining_circle',
    value=22,
), 23: TypeValue(
    name='reverse_curl_up',
    value=23,
), 24: TypeValue(
    name='weighted_reverse_curl_up',
    value=24,
), 25: TypeValue(
    name='single_leg_swiss_ball_jackknife',
    value=25,
), 26: TypeValue(
    name='weighted_single_leg_swiss_ball_jackknife',
    value=26,
), 27: TypeValue(
    name='the_teaser',
    value=27,
), 28: TypeValue(
    name='the_teaser_weighted',
    value=28,
), 29: TypeValue(
    name='three_part_roll_down',
    value=29,
), 30: TypeValue(
    name='weighted_three_part_roll_down',
    value=30,
), 31: TypeValue(
    name='v_up',
    value=31,
), 32: TypeValue(
    name='weighted_v_up',
    value=32,
), 33: TypeValue(
    name='weighted_russian_twist_on_swiss_ball',
    value=33,
), 34: TypeValue(
    name='weighted_sit_up',
    value=34,
), 35: TypeValue(
    name='x_abs',
    value=35,
), 36: TypeValue(
    name='weighted_x_abs',
    value=36,
), 37: TypeValue(
    name='sit_up',
    value=37,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'squat_exercise_name': Type(
    name='squat_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='leg_press',
    value=0,
), 1: TypeValue(
    name='back_squat_with_body_bar',
    value=1,
), 2: TypeValue(
    name='back_squats',
    value=2,
), 3: TypeValue(
    name='weighted_back_squats',
    value=3,
), 4: TypeValue(
    name='balancing_squat',
    value=4,
), 5: TypeValue(
    name='weighted_balancing_squat',
    value=5,
), 6: TypeValue(
    name='barbell_back_squat',
    value=6,
), 7: TypeValue(
    name='barbell_box_squat',
    value=7,
), 8: TypeValue(
    name='barbell_front_squat',
    value=8,
), 9: TypeValue(
    name='barbell_hack_squat',
    value=9,
), 10: TypeValue(
    name='barbell_hang_squat_snatch',
    value=10,
), 11: TypeValue(
    name='barbell_lateral_step_up',
    value=11,
), 12: TypeValue(
    name='barbell_quarter_squat',
    value=12,
), 13: TypeValue(
    name='barbell_siff_squat',
    value=13,
), 14: TypeValue(
    name='barbell_squat_snatch',
    value=14,
), 15: TypeValue(
    name='barbell_squat_with_heels_raised',
    value=15,
), 16: TypeValue(
    name='barbell_stepover',
    value=16,
), 17: TypeValue(
    name='barbell_step_up',
    value=17,
), 18: TypeValue(
    name='bench_squat_with_rotational_chop',
    value=18,
), 19: TypeValue(
    name='weighted_bench_squat_with_rotational_chop',
    value=19,
), 20: TypeValue(
    name='body_weight_wall_squat',
    value=20,
), 21: TypeValue(
    name='weighted_wall_squat',
    value=21,
), 22: TypeValue(
    name='box_step_squat',
    value=22,
), 23: TypeValue(
    name='weighted_box_step_squat',
    value=23,
), 24: TypeValue(
    name='braced_squat',
    value=24,
), 25: TypeValue(
    name='crossed_arm_barbell_front_squat',
    value=25,
), 26: TypeValue(
    name='crossover_dumbbell_step_up',
    value=26,
), 27: TypeValue(
    name='dumbbell_front_squat',
    value=27,
), 28: TypeValue(
    name='dumbbell_split_squat',
    value=28,
), 29: TypeValue(
    name='dumbbell_squat',
    value=29,
), 30: TypeValue(
    name='dumbbell_squat_clean',
    value=30,
), 31: TypeValue(
    name='dumbbell_stepover',
    value=31,
), 32: TypeValue(
    name='dumbbell_step_up',
    value=32,
), 33: TypeValue(
    name='elevated_single_leg_squat',
    value=33,
), 34: TypeValue(
    name='weighted_elevated_single_leg_squat',
    value=34,
), 35: TypeValue(
    name='figure_four_squats',
    value=35,
), 36: TypeValue(
    name='weighted_figure_four_squats',
    value=36,
), 37: TypeValue(
    name='goblet_squat',
    value=37,
), 38: TypeValue(
    name='kettlebell_squat',
    value=38,
), 39: TypeValue(
    name='kettlebell_swing_overhead',
    value=39,
), 40: TypeValue(
    name='kettlebell_swing_with_flip_to_squat',
    value=40,
), 41: TypeValue(
    name='lateral_dumbbell_step_up',
    value=41,
), 42: TypeValue(
    name='one_legged_squat',
    value=42,
), 43: TypeValue(
    name='overhead_dumbbell_squat',
    value=43,
), 44: TypeValue(
    name='overhead_squat',
    value=44,
), 45: TypeValue(
    name='partial_single_leg_squat',
    value=45,
), 46: TypeValue(
    name='weighted_partial_single_leg_squat',
    value=46,
), 47: TypeValue(
    name='pistol_squat',
    value=47,
), 48: TypeValue(
    name='weighted_pistol_squat',
    value=48,
), 49: TypeValue(
    name='plie_slides',
    value=49,
), 50: TypeValue(
    name='weighted_plie_slides',
    value=50,
), 51: TypeValue(
    name='plie_squat',
    value=51,
), 52: TypeValue(
    name='weighted_plie_squat',
    value=52,
), 53: TypeValue(
    name='prisoner_squat',
    value=53,
), 54: TypeValue(
    name='weighted_prisoner_squat',
    value=54,
), 55: TypeValue(
    name='single_leg_bench_get_up',
    value=55,
), 56: TypeValue(
    name='weighted_single_leg_bench_get_up',
    value=56,
), 57: TypeValue(
    name='single_leg_bench_squat',
    value=57,
), 58: TypeValue(
    name='weighted_single_leg_bench_squat',
    value=58,
), 59: TypeValue(
    name='single_leg_squat_on_swiss_ball',
    value=59,
), 60: TypeValue(
    name='weighted_single_leg_squat_on_swiss_ball',
    value=60,
), 61: TypeValue(
    name='squat',
    value=61,
), 62: TypeValue(
    name='weighted_squat',
    value=62,
), 63: TypeValue(
    name='squats_with_band',
    value=63,
), 64: TypeValue(
    name='staggered_squat',
    value=64,
), 65: TypeValue(
    name='weighted_staggered_squat',
    value=65,
), 66: TypeValue(
    name='step_up',
    value=66,
), 67: TypeValue(
    name='weighted_step_up',
    value=67,
), 68: TypeValue(
    name='suitcase_squats',
    value=68,
), 69: TypeValue(
    name='sumo_squat',
    value=69,
), 70: TypeValue(
    name='sumo_squat_slide_in',
    value=70,
), 71: TypeValue(
    name='weighted_sumo_squat_slide_in',
    value=71,
), 72: TypeValue(
    name='sumo_squat_to_high_pull',
    value=72,
), 73: TypeValue(
    name='sumo_squat_to_stand',
    value=73,
), 74: TypeValue(
    name='weighted_sumo_squat_to_stand',
    value=74,
), 75: TypeValue(
    name='sumo_squat_with_rotation',
    value=75,
), 76: TypeValue(
    name='weighted_sumo_squat_with_rotation',
    value=76,
), 77: TypeValue(
    name='swiss_ball_body_weight_wall_squat',
    value=77,
), 78: TypeValue(
    name='weighted_swiss_ball_wall_squat',
    value=78,
), 79: TypeValue(
    name='thrusters',
    value=79,
), 80: TypeValue(
    name='uneven_squat',
    value=80,
), 81: TypeValue(
    name='weighted_uneven_squat',
    value=81,
), 82: TypeValue(
    name='waist_slimming_squat',
    value=82,
), 83: TypeValue(
    name='wall_ball',
    value=83,
), 84: TypeValue(
    name='wide_stance_barbell_squat',
    value=84,
), 85: TypeValue(
    name='wide_stance_goblet_squat',
    value=85,
), 86: TypeValue(
    name='zercher_squat',
    value=86,
), 87: TypeValue(
    name='kbs_overhead',
    value=87,
    comment='Deprecated do not use',
), 88: TypeValue(
    name='squat_and_side_kick',
    value=88,
), 89: TypeValue(
    name='squat_jumps_in_n_out',
    value=89,
), 90: TypeValue(
    name='pilates_plie_squats_parallel_turned_out_flat_and_heels',
    value=90,
), 91: TypeValue(
    name='releve_straight_leg_and_knee_bent_with_one_leg_variation',
    value=91,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'total_body_exercise_name': Type(
    name='total_body_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='burpee',
    value=0,
), 1: TypeValue(
    name='weighted_burpee',
    value=1,
), 2: TypeValue(
    name='burpee_box_jump',
    value=2,
), 3: TypeValue(
    name='weighted_burpee_box_jump',
    value=3,
), 4: TypeValue(
    name='high_pull_burpee',
    value=4,
), 5: TypeValue(
    name='man_makers',
    value=5,
), 6: TypeValue(
    name='one_arm_burpee',
    value=6,
), 7: TypeValue(
    name='squat_thrusts',
    value=7,
), 8: TypeValue(
    name='weighted_squat_thrusts',
    value=8,
), 9: TypeValue(
    name='squat_plank_push_up',
    value=9,
), 10: TypeValue(
    name='weighted_squat_plank_push_up',
    value=10,
), 11: TypeValue(
    name='standing_t_rotation_balance',
    value=11,
), 12: TypeValue(
    name='weighted_standing_t_rotation_balance',
    value=12,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'triceps_extension_exercise_name': Type(
    name='triceps_extension_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='bench_dip',
    value=0,
), 1: TypeValue(
    name='weighted_bench_dip',
    value=1,
), 2: TypeValue(
    name='body_weight_dip',
    value=2,
), 3: TypeValue(
    name='cable_kickback',
    value=3,
), 4: TypeValue(
    name='cable_lying_triceps_extension',
    value=4,
), 5: TypeValue(
    name='cable_overhead_triceps_extension',
    value=5,
), 6: TypeValue(
    name='dumbbell_kickback',
    value=6,
), 7: TypeValue(
    name='dumbbell_lying_triceps_extension',
    value=7,
), 8: TypeValue(
    name='ez_bar_overhead_triceps_extension',
    value=8,
), 9: TypeValue(
    name='incline_dip',
    value=9,
), 10: TypeValue(
    name='weighted_incline_dip',
    value=10,
), 11: TypeValue(
    name='incline_ez_bar_lying_triceps_extension',
    value=11,
), 12: TypeValue(
    name='lying_dumbbell_pullover_to_extension',
    value=12,
), 13: TypeValue(
    name='lying_ez_bar_triceps_extension',
    value=13,
), 14: TypeValue(
    name='lying_triceps_extension_to_close_grip_bench_press',
    value=14,
), 15: TypeValue(
    name='overhead_dumbbell_triceps_extension',
    value=15,
), 16: TypeValue(
    name='reclining_triceps_press',
    value=16,
), 17: TypeValue(
    name='reverse_grip_pressdown',
    value=17,
), 18: TypeValue(
    name='reverse_grip_triceps_pressdown',
    value=18,
), 19: TypeValue(
    name='rope_pressdown',
    value=19,
), 20: TypeValue(
    name='seated_barbell_overhead_triceps_extension',
    value=20,
), 21: TypeValue(
    name='seated_dumbbell_overhead_triceps_extension',
    value=21,
), 22: TypeValue(
    name='seated_ez_bar_overhead_triceps_extension',
    value=22,
), 23: TypeValue(
    name='seated_single_arm_overhead_dumbbell_extension',
    value=23,
), 24: TypeValue(
    name='single_arm_dumbbell_overhead_triceps_extension',
    value=24,
), 25: TypeValue(
    name='single_dumbbell_seated_overhead_triceps_extension',
    value=25,
), 26: TypeValue(
    name='single_leg_bench_dip_and_kick',
    value=26,
), 27: TypeValue(
    name='weighted_single_leg_bench_dip_and_kick',
    value=27,
), 28: TypeValue(
    name='single_leg_dip',
    value=28,
), 29: TypeValue(
    name='weighted_single_leg_dip',
    value=29,
), 30: TypeValue(
    name='static_lying_triceps_extension',
    value=30,
), 31: TypeValue(
    name='suspended_dip',
    value=31,
), 32: TypeValue(
    name='weighted_suspended_dip',
    value=32,
), 33: TypeValue(
    name='swiss_ball_dumbbell_lying_triceps_extension',
    value=33,
), 34: TypeValue(
    name='swiss_ball_ez_bar_lying_triceps_extension',
    value=34,
), 35: TypeValue(
    name='swiss_ball_ez_bar_overhead_triceps_extension',
    value=35,
), 36: TypeValue(
    name='tabletop_dip',
    value=36,
), 37: TypeValue(
    name='weighted_tabletop_dip',
    value=37,
), 38: TypeValue(
    name='triceps_extension_on_floor',
    value=38,
), 39: TypeValue(
    name='triceps_pressdown',
    value=39,
), 40: TypeValue(
    name='weighted_dip',
    value=40,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'warm_up_exercise_name': Type(
    name='warm_up_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='quadruped_rocking',
    value=0,
), 1: TypeValue(
    name='neck_tilts',
    value=1,
), 2: TypeValue(
    name='ankle_circles',
    value=2,
), 3: TypeValue(
    name='ankle_dorsiflexion_with_band',
    value=3,
), 4: TypeValue(
    name='ankle_internal_rotation',
    value=4,
), 5: TypeValue(
    name='arm_circles',
    value=5,
), 6: TypeValue(
    name='bent_over_reach_to_sky',
    value=6,
), 7: TypeValue(
    name='cat_camel',
    value=7,
), 8: TypeValue(
    name='elbow_to_foot_lunge',
    value=8,
), 9: TypeValue(
    name='forward_and_backward_leg_swings',
    value=9,
), 10: TypeValue(
    name='groiners',
    value=10,
), 11: TypeValue(
    name='inverted_hamstring_stretch',
    value=11,
), 12: TypeValue(
    name='lateral_duck_under',
    value=12,
), 13: TypeValue(
    name='neck_rotations',
    value=13,
), 14: TypeValue(
    name='opposite_arm_and_leg_balance',
    value=14,
), 15: TypeValue(
    name='reach_roll_and_lift',
    value=15,
), 16: TypeValue(
    name='scorpion',
    value=16,
    comment='Deprecated do not use',
), 17: TypeValue(
    name='shoulder_circles',
    value=17,
), 18: TypeValue(
    name='side_to_side_leg_swings',
    value=18,
), 19: TypeValue(
    name='sleeper_stretch',
    value=19,
), 20: TypeValue(
    name='slide_out',
    value=20,
), 21: TypeValue(
    name='swiss_ball_hip_crossover',
    value=21,
), 22: TypeValue(
    name='swiss_ball_reach_roll_and_lift',
    value=22,
), 23: TypeValue(
    name='swiss_ball_windshield_wipers',
    value=23,
), 24: TypeValue(
    name='thoracic_rotation',
    value=24,
), 25: TypeValue(
    name='walking_high_kicks',
    value=25,
), 26: TypeValue(
    name='walking_high_knees',
    value=26,
), 27: TypeValue(
    name='walking_knee_hugs',
    value=27,
), 28: TypeValue(
    name='walking_leg_cradles',
    value=28,
), 29: TypeValue(
    name='walkout',
    value=29,
), 30: TypeValue(
    name='walkout_from_push_up_position',
    value=30,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'run_exercise_name': Type(
    name='run_exercise_name',
    base_type='uint16',
    values=Map(
    map={0: TypeValue(
    name='run',
    value=0,
), 1: TypeValue(
    name='walk',
    value=1,
), 2: TypeValue(
    name='jog',
    value=2,
), 3: TypeValue(
    name='sprint',
    value=3,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'water_type': Type(
    name='water_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='fresh',
    value=0,
), 1: TypeValue(
    name='salt',
    value=1,
), 2: TypeValue(
    name='en13319',
    value=2,
), 3: TypeValue(
    name='custom',
    value=3,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'tissue_model_type': Type(
    name='tissue_model_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='zhl_16c',
    value=0,
    comment="Buhlmann's decompression algorithm, version C",
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'dive_gas_status': Type(
    name='dive_gas_status',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='disabled',
    value=0,
), 1: TypeValue(
    name='enabled',
    value=1,
), 2: TypeValue(
    name='backup_only',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'dive_alarm_type': Type(
    name='dive_alarm_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='depth',
    value=0,
), 1: TypeValue(
    name='time',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'dive_backlight_mode': Type(
    name='dive_backlight_mode',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='at_depth',
    value=0,
), 1: TypeValue(
    name='always_on',
    value=1,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'favero_product': Type(
    name='favero_product',
    base_type='uint16',
    values=Map(
    map={10: TypeValue(
    name='assioma_uno',
    value=10,
), 12: TypeValue(
    name='assioma_duo',
    value=12,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'climb_pro_event': Type(
    name='climb_pro_event',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='approach',
    value=0,
), 1: TypeValue(
    name='start',
    value=1,
), 2: TypeValue(
    name='complete',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'tap_sensitivity': Type(
    name='tap_sensitivity',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='high',
    value=0,
), 1: TypeValue(
    name='medium',
    value=1,
), 2: TypeValue(
    name='low',
    value=2,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
), 'radar_threat_level_type': Type(
    name='radar_threat_level_type',
    base_type='enum',
    values=Map(
    map={0: TypeValue(
    name='threat_unknown',
    value=0,
), 1: TypeValue(
    name='threat_none',
    value=1,
), 2: TypeValue(
    name='threat_approaching',
    value=2,
), 3: TypeValue(
    name='threat_approaching_fast',
    value=3,
)},
    map_type=dict,
    value_type=TypeValue,
    key_type=int,
),
)},
    map_type=dict,
    value_type=Type,
    key_type=str,
)
messages = Map(
    map={'file_id': Message(
    name='file_id',
    global_number=0,
    group_name='Common Messages',
    fields=Map(
    map={0: Field(
    name='type',
    type='file',
    def_num=0,
), 1: Field(
    name='manufacturer',
    type='manufacturer',
    def_num=1,
), 2: Field(
    name='product',
    type='uint16',
    def_num=2,
    subfields=Map(
    map=[SubField(
    name='favero_product',
    type='favero_product',
    reference_fields=Map(
    map=[ReferenceField(
    name='manufacturer',
    value='favero_electronics',
    def_num=1,
    raw_value=263,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='garmin_product',
    type='garmin_product',
    reference_fields=Map(
    map=[ReferenceField(
    name='manufacturer',
    value='garmin',
    def_num=1,
    raw_value=1,
), ReferenceField(
    name='manufacturer',
    value='dynastream',
    def_num=1,
    raw_value=15,
), ReferenceField(
    name='manufacturer',
    value='dynastream_oem',
    def_num=1,
    raw_value=13,
), ReferenceField(
    name='manufacturer',
    value='tacx',
    def_num=1,
    raw_value=89,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 3: Field(
    name='serial_number',
    type='uint32z',
    def_num=3,
), 4: Field(
    name='time_created',
    type='date_time',
    def_num=4,
    comment='Only set for files that are can be created/erased.',
), 5: Field(
    name='number',
    type='uint16',
    def_num=5,
    comment='Only set for files that are not created/erased.',
), 8: Field(
    name='product_name',
    type='string',
    def_num=8,
    comment='Optional free form string to indicate the devices name or model',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
    comment='Must be first message in file.',
), 'capabilities': Message(
    name='capabilities',
    global_number=1,
    group_name='Device File Messages',
    fields=Map(
    map={0: Field(
    name='languages',
    type='uint8z',
    def_num=0,
    comment='Use language_bits_x types where x is index of array.',
), 1: Field(
    name='sports',
    type='sport_bits_0',
    def_num=1,
    comment='Use sport_bits_x types where x is index of array.',
), 21: Field(
    name='workouts_supported',
    type='workout_capabilities',
    def_num=21,
), 23: Field(
    name='connectivity_supported',
    type='connectivity_capabilities',
    def_num=23,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'device_settings': Message(
    name='device_settings',
    global_number=2,
    group_name='Settings File Messages',
    fields=Map(
    map={0: Field(
    name='active_time_zone',
    type='uint8',
    def_num=0,
    comment='Index into time zone arrays.',
), 1: Field(
    name='utc_offset',
    type='uint32',
    def_num=1,
    comment='Offset from system time. Required to convert timestamp from system time to UTC.',
), 2: Field(
    name='time_offset',
    type='uint32',
    def_num=2,
    units='s',
    comment='Offset from system time.',
), 4: Field(
    name='time_mode',
    type='time_mode',
    def_num=4,
    comment='Display mode for the time',
), 5: Field(
    name='time_zone_offset',
    type='sint8',
    def_num=5,
    scale=4,
    units='hr',
    comment='timezone offset in 1/4 hour increments',
), 12: Field(
    name='backlight_mode',
    type='backlight_mode',
    def_num=12,
    comment='Mode for backlight',
), 36: Field(
    name='activity_tracker_enabled',
    type='bool',
    def_num=36,
    comment='Enabled state of the activity tracker functionality',
), 39: Field(
    name='clock_time',
    type='date_time',
    def_num=39,
    comment='UTC timestamp used to set the devices clock and date',
), 40: Field(
    name='pages_enabled',
    type='uint16',
    def_num=40,
    comment='Bitfield  to configure enabled screens for each supported loop',
), 46: Field(
    name='move_alert_enabled',
    type='bool',
    def_num=46,
    comment='Enabled state of the move alert',
), 47: Field(
    name='date_mode',
    type='date_mode',
    def_num=47,
    comment='Display mode for the date',
), 55: Field(
    name='display_orientation',
    type='display_orientation',
    def_num=55,
), 56: Field(
    name='mounting_side',
    type='side',
    def_num=56,
), 57: Field(
    name='default_page',
    type='uint16',
    def_num=57,
    comment='Bitfield to indicate one page as default for each supported loop',
), 58: Field(
    name='autosync_min_steps',
    type='uint16',
    def_num=58,
    units='steps',
    comment='Minimum steps before an autosync can occur',
), 59: Field(
    name='autosync_min_time',
    type='uint16',
    def_num=59,
    units='minutes',
    comment='Minimum minutes before an autosync can occur',
), 80: Field(
    name='lactate_threshold_autodetect_enabled',
    type='bool',
    def_num=80,
    comment='Enable auto-detect setting for the lactate threshold feature.',
), 86: Field(
    name='ble_auto_upload_enabled',
    type='bool',
    def_num=86,
    comment='Automatically upload using BLE',
), 89: Field(
    name='auto_sync_frequency',
    type='auto_sync_frequency',
    def_num=89,
    comment='Helps to conserve battery by changing modes',
), 90: Field(
    name='auto_activity_detect',
    type='auto_activity_detect',
    def_num=90,
    comment='Allows setting specific activities auto-activity detect enabled/disabled settings',
), 94: Field(
    name='number_of_screens',
    type='uint8',
    def_num=94,
    comment='Number of screens configured to display',
), 95: Field(
    name='smart_notification_display_orientation',
    type='display_orientation',
    def_num=95,
    comment='Smart Notification display orientation',
), 134: Field(
    name='tap_interface',
    type='switch',
    def_num=134,
), 174: Field(
    name='tap_sensitivity',
    type='tap_sensitivity',
    def_num=174,
    comment='Used to hold the tap threshold setting',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'user_profile': Message(
    name='user_profile',
    global_number=3,
    group_name='Settings File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='friendly_name',
    type='string',
    def_num=0,
), 1: Field(
    name='gender',
    type='gender',
    def_num=1,
), 2: Field(
    name='age',
    type='uint8',
    def_num=2,
    units='years',
), 3: Field(
    name='height',
    type='uint8',
    def_num=3,
    scale=100,
    units='m',
), 4: Field(
    name='weight',
    type='uint16',
    def_num=4,
    scale=10,
    units='kg',
), 5: Field(
    name='language',
    type='language',
    def_num=5,
), 6: Field(
    name='elev_setting',
    type='display_measure',
    def_num=6,
), 7: Field(
    name='weight_setting',
    type='display_measure',
    def_num=7,
), 8: Field(
    name='resting_heart_rate',
    type='uint8',
    def_num=8,
    units='bpm',
), 9: Field(
    name='default_max_running_heart_rate',
    type='uint8',
    def_num=9,
    units='bpm',
), 10: Field(
    name='default_max_biking_heart_rate',
    type='uint8',
    def_num=10,
    units='bpm',
), 11: Field(
    name='default_max_heart_rate',
    type='uint8',
    def_num=11,
    units='bpm',
), 12: Field(
    name='hr_setting',
    type='display_heart',
    def_num=12,
), 13: Field(
    name='speed_setting',
    type='display_measure',
    def_num=13,
), 14: Field(
    name='dist_setting',
    type='display_measure',
    def_num=14,
), 16: Field(
    name='power_setting',
    type='display_power',
    def_num=16,
), 17: Field(
    name='activity_class',
    type='activity_class',
    def_num=17,
), 18: Field(
    name='position_setting',
    type='display_position',
    def_num=18,
), 21: Field(
    name='temperature_setting',
    type='display_measure',
    def_num=21,
), 22: Field(
    name='local_id',
    type='user_local_id',
    def_num=22,
), 23: Field(
    name='global_id',
    type='byte',
    def_num=23,
), 28: Field(
    name='wake_time',
    type='localtime_into_day',
    def_num=28,
    comment='Typical wake time',
), 29: Field(
    name='sleep_time',
    type='localtime_into_day',
    def_num=29,
    comment='Typical bed time',
), 30: Field(
    name='height_setting',
    type='display_measure',
    def_num=30,
), 31: Field(
    name='user_running_step_length',
    type='uint16',
    def_num=31,
    scale=1000,
    units='m',
    comment='User defined running step length set to 0 for auto length',
), 32: Field(
    name='user_walking_step_length',
    type='uint16',
    def_num=32,
    scale=1000,
    units='m',
    comment='User defined walking step length set to 0 for auto length',
), 47: Field(
    name='depth_setting',
    type='display_measure',
    def_num=47,
), 49: Field(
    name='dive_count',
    type='uint32',
    def_num=49,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'hrm_profile': Message(
    name='hrm_profile',
    global_number=4,
    group_name='Settings File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='enabled',
    type='bool',
    def_num=0,
), 1: Field(
    name='hrm_ant_id',
    type='uint16z',
    def_num=1,
), 2: Field(
    name='log_hrv',
    type='bool',
    def_num=2,
), 3: Field(
    name='hrm_ant_id_trans_type',
    type='uint8z',
    def_num=3,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'sdm_profile': Message(
    name='sdm_profile',
    global_number=5,
    group_name='Settings File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='enabled',
    type='bool',
    def_num=0,
), 1: Field(
    name='sdm_ant_id',
    type='uint16z',
    def_num=1,
), 2: Field(
    name='sdm_cal_factor',
    type='uint16',
    def_num=2,
    scale=10,
    units='%',
), 3: Field(
    name='odometer',
    type='uint32',
    def_num=3,
    scale=100,
    units='m',
), 4: Field(
    name='speed_source',
    type='bool',
    def_num=4,
    comment='Use footpod for speed source instead of GPS',
), 5: Field(
    name='sdm_ant_id_trans_type',
    type='uint8z',
    def_num=5,
), 7: Field(
    name='odometer_rollover',
    type='uint8',
    def_num=7,
    comment='Rollover counter that can be used to extend the odometer',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'bike_profile': Message(
    name='bike_profile',
    global_number=6,
    group_name='Settings File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='name',
    type='string',
    def_num=0,
), 1: Field(
    name='sport',
    type='sport',
    def_num=1,
), 2: Field(
    name='sub_sport',
    type='sub_sport',
    def_num=2,
), 3: Field(
    name='odometer',
    type='uint32',
    def_num=3,
    scale=100,
    units='m',
), 4: Field(
    name='bike_spd_ant_id',
    type='uint16z',
    def_num=4,
), 5: Field(
    name='bike_cad_ant_id',
    type='uint16z',
    def_num=5,
), 6: Field(
    name='bike_spdcad_ant_id',
    type='uint16z',
    def_num=6,
), 7: Field(
    name='bike_power_ant_id',
    type='uint16z',
    def_num=7,
), 8: Field(
    name='custom_wheelsize',
    type='uint16',
    def_num=8,
    scale=1000,
    units='m',
), 9: Field(
    name='auto_wheelsize',
    type='uint16',
    def_num=9,
    scale=1000,
    units='m',
), 10: Field(
    name='bike_weight',
    type='uint16',
    def_num=10,
    scale=10,
    units='kg',
), 11: Field(
    name='power_cal_factor',
    type='uint16',
    def_num=11,
    scale=10,
    units='%',
), 12: Field(
    name='auto_wheel_cal',
    type='bool',
    def_num=12,
), 13: Field(
    name='auto_power_zero',
    type='bool',
    def_num=13,
), 14: Field(
    name='id',
    type='uint8',
    def_num=14,
), 15: Field(
    name='spd_enabled',
    type='bool',
    def_num=15,
), 16: Field(
    name='cad_enabled',
    type='bool',
    def_num=16,
), 17: Field(
    name='spdcad_enabled',
    type='bool',
    def_num=17,
), 18: Field(
    name='power_enabled',
    type='bool',
    def_num=18,
), 19: Field(
    name='crank_length',
    type='uint8',
    def_num=19,
    scale=2,
    offset='-110',
    units='mm',
), 20: Field(
    name='enabled',
    type='bool',
    def_num=20,
), 21: Field(
    name='bike_spd_ant_id_trans_type',
    type='uint8z',
    def_num=21,
), 22: Field(
    name='bike_cad_ant_id_trans_type',
    type='uint8z',
    def_num=22,
), 23: Field(
    name='bike_spdcad_ant_id_trans_type',
    type='uint8z',
    def_num=23,
), 24: Field(
    name='bike_power_ant_id_trans_type',
    type='uint8z',
    def_num=24,
), 37: Field(
    name='odometer_rollover',
    type='uint8',
    def_num=37,
    comment='Rollover counter that can be used to extend the odometer',
), 38: Field(
    name='front_gear_num',
    type='uint8z',
    def_num=38,
    comment='Number of front gears',
), 39: Field(
    name='front_gear',
    type='uint8z',
    def_num=39,
    comment='Number of teeth on each gear 0 is innermost',
), 40: Field(
    name='rear_gear_num',
    type='uint8z',
    def_num=40,
    comment='Number of rear gears',
), 41: Field(
    name='rear_gear',
    type='uint8z',
    def_num=41,
    comment='Number of teeth on each gear 0 is innermost',
), 44: Field(
    name='shimano_di2_enabled',
    type='bool',
    def_num=44,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'zones_target': Message(
    name='zones_target',
    global_number=7,
    group_name='Sport Settings File Messages',
    fields=Map(
    map={1: Field(
    name='max_heart_rate',
    type='uint8',
    def_num=1,
), 2: Field(
    name='threshold_heart_rate',
    type='uint8',
    def_num=2,
), 3: Field(
    name='functional_threshold_power',
    type='uint16',
    def_num=3,
), 5: Field(
    name='hr_calc_type',
    type='hr_zone_calc',
    def_num=5,
), 7: Field(
    name='pwr_calc_type',
    type='pwr_zone_calc',
    def_num=7,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'hr_zone': Message(
    name='hr_zone',
    global_number=8,
    group_name='Sport Settings File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 1: Field(
    name='high_bpm',
    type='uint8',
    def_num=1,
    units='bpm',
), 2: Field(
    name='name',
    type='string',
    def_num=2,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'power_zone': Message(
    name='power_zone',
    global_number=9,
    group_name='Sport Settings File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 1: Field(
    name='high_value',
    type='uint16',
    def_num=1,
    units='watts',
), 2: Field(
    name='name',
    type='string',
    def_num=2,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'met_zone': Message(
    name='met_zone',
    global_number=10,
    group_name='Sport Settings File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 1: Field(
    name='high_bpm',
    type='uint8',
    def_num=1,
), 2: Field(
    name='calories',
    type='uint16',
    def_num=2,
    scale=10,
    units='kcal/min',
), 3: Field(
    name='fat_calories',
    type='uint8',
    def_num=3,
    scale=10,
    units='kcal/min',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'sport': Message(
    name='sport',
    global_number=12,
    group_name='Sport Settings File Messages',
    fields=Map(
    map={0: Field(
    name='sport',
    type='sport',
    def_num=0,
), 1: Field(
    name='sub_sport',
    type='sub_sport',
    def_num=1,
), 3: Field(
    name='name',
    type='string',
    def_num=3,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'goal': Message(
    name='goal',
    global_number=15,
    group_name='Goals File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='sport',
    type='sport',
    def_num=0,
), 1: Field(
    name='sub_sport',
    type='sub_sport',
    def_num=1,
), 2: Field(
    name='start_date',
    type='date_time',
    def_num=2,
), 3: Field(
    name='end_date',
    type='date_time',
    def_num=3,
), 4: Field(
    name='type',
    type='goal',
    def_num=4,
), 5: Field(
    name='value',
    type='uint32',
    def_num=5,
), 6: Field(
    name='repeat',
    type='bool',
    def_num=6,
), 7: Field(
    name='target_value',
    type='uint32',
    def_num=7,
), 8: Field(
    name='recurrence',
    type='goal_recurrence',
    def_num=8,
), 9: Field(
    name='recurrence_value',
    type='uint16',
    def_num=9,
), 10: Field(
    name='enabled',
    type='bool',
    def_num=10,
), 11: Field(
    name='source',
    type='goal_source',
    def_num=11,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'session': Message(
    name='session',
    global_number=18,
    group_name='Activity File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
    comment='Selected bit is set for the current session.',
), 253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Sesson end time.',
), 0: Field(
    name='event',
    type='event',
    def_num=0,
    comment='session',
), 1: Field(
    name='event_type',
    type='event_type',
    def_num=1,
    comment='stop',
), 2: Field(
    name='start_time',
    type='date_time',
    def_num=2,
), 3: Field(
    name='start_position_lat',
    type='sint32',
    def_num=3,
    units='semicircles',
), 4: Field(
    name='start_position_long',
    type='sint32',
    def_num=4,
    units='semicircles',
), 5: Field(
    name='sport',
    type='sport',
    def_num=5,
), 6: Field(
    name='sub_sport',
    type='sub_sport',
    def_num=6,
), 7: Field(
    name='total_elapsed_time',
    type='uint32',
    def_num=7,
    scale=1000,
    units='s',
    comment='Time (includes pauses)',
), 8: Field(
    name='total_timer_time',
    type='uint32',
    def_num=8,
    scale=1000,
    units='s',
    comment='Timer Time (excludes pauses)',
), 9: Field(
    name='total_distance',
    type='uint32',
    def_num=9,
    scale=100,
    units='m',
), 10: Field(
    name='total_cycles',
    type='uint32',
    def_num=10,
    units='cycles',
    subfields=Map(
    map=[SubField(
    name='total_strides',
    type='uint32',
    units='strides',
    reference_fields=Map(
    map=[ReferenceField(
    name='sport',
    value='running',
    def_num=5,
    raw_value=1,
), ReferenceField(
    name='sport',
    value='walking',
    def_num=5,
    raw_value=11,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='total_strokes',
    type='uint32',
    units='strokes',
    reference_fields=Map(
    map=[ReferenceField(
    name='sport',
    value='cycling',
    def_num=5,
    raw_value=2,
), ReferenceField(
    name='sport',
    value='swimming',
    def_num=5,
    raw_value=5,
), ReferenceField(
    name='sport',
    value='rowing',
    def_num=5,
    raw_value=15,
), ReferenceField(
    name='sport',
    value='stand_up_paddleboarding',
    def_num=5,
    raw_value=37,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 11: Field(
    name='total_calories',
    type='uint16',
    def_num=11,
    units='kcal',
), 13: Field(
    name='total_fat_calories',
    type='uint16',
    def_num=13,
    units='kcal',
), 14: Field(
    name='avg_speed',
    type='uint16',
    def_num=14,
    components=Map(
    map=[Component(
    name='enhanced_avg_speed',
    scale=1000,
    units='m/s',
    bits=16,
    accumulate=False,
    num=(124,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=1000,
    units='m/s',
    comment='total_distance / total_timer_time',
), 15: Field(
    name='max_speed',
    type='uint16',
    def_num=15,
    components=Map(
    map=[Component(
    name='enhanced_max_speed',
    scale=1000,
    units='m/s',
    bits=16,
    accumulate=False,
    num=(125,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=1000,
    units='m/s',
), 16: Field(
    name='avg_heart_rate',
    type='uint8',
    def_num=16,
    units='bpm',
    comment='average heart rate (excludes pause time)',
), 17: Field(
    name='max_heart_rate',
    type='uint8',
    def_num=17,
    units='bpm',
), 18: Field(
    name='avg_cadence',
    type='uint8',
    def_num=18,
    units='rpm',
    comment='total_cycles / total_timer_time if non_zero_avg_cadence otherwise total_cycles / total_elapsed_time',
    subfields=Map(
    map=[SubField(
    name='avg_running_cadence',
    type='uint8',
    units='strides/min',
    reference_fields=Map(
    map=[ReferenceField(
    name='sport',
    value='running',
    def_num=5,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 19: Field(
    name='max_cadence',
    type='uint8',
    def_num=19,
    units='rpm',
    subfields=Map(
    map=[SubField(
    name='max_running_cadence',
    type='uint8',
    units='strides/min',
    reference_fields=Map(
    map=[ReferenceField(
    name='sport',
    value='running',
    def_num=5,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 20: Field(
    name='avg_power',
    type='uint16',
    def_num=20,
    units='watts',
    comment='total_power / total_timer_time if non_zero_avg_power otherwise total_power / total_elapsed_time',
), 21: Field(
    name='max_power',
    type='uint16',
    def_num=21,
    units='watts',
), 22: Field(
    name='total_ascent',
    type='uint16',
    def_num=22,
    units='m',
), 23: Field(
    name='total_descent',
    type='uint16',
    def_num=23,
    units='m',
), 24: Field(
    name='total_training_effect',
    type='uint8',
    def_num=24,
    scale=10,
), 25: Field(
    name='first_lap_index',
    type='uint16',
    def_num=25,
), 26: Field(
    name='num_laps',
    type='uint16',
    def_num=26,
), 27: Field(
    name='event_group',
    type='uint8',
    def_num=27,
), 28: Field(
    name='trigger',
    type='session_trigger',
    def_num=28,
), 29: Field(
    name='nec_lat',
    type='sint32',
    def_num=29,
    units='semicircles',
    comment='North east corner latitude',
), 30: Field(
    name='nec_long',
    type='sint32',
    def_num=30,
    units='semicircles',
    comment='North east corner longitude',
), 31: Field(
    name='swc_lat',
    type='sint32',
    def_num=31,
    units='semicircles',
    comment='South west corner latitude',
), 32: Field(
    name='swc_long',
    type='sint32',
    def_num=32,
    units='semicircles',
    comment='South west corner longitude',
), 33: Field(
    name='num_lengths',
    type='uint16',
    def_num=33,
    units='lengths',
    comment='# of lengths of swim pool',
), 34: Field(
    name='normalized_power',
    type='uint16',
    def_num=34,
    units='watts',
), 35: Field(
    name='training_stress_score',
    type='uint16',
    def_num=35,
    scale=10,
    units='tss',
), 36: Field(
    name='intensity_factor',
    type='uint16',
    def_num=36,
    scale=1000,
    units='if',
), 37: Field(
    name='left_right_balance',
    type='left_right_balance_100',
    def_num=37,
), 41: Field(
    name='avg_stroke_count',
    type='uint32',
    def_num=41,
    scale=10,
    units='strokes/lap',
), 42: Field(
    name='avg_stroke_distance',
    type='uint16',
    def_num=42,
    scale=100,
    units='m',
), 43: Field(
    name='swim_stroke',
    type='swim_stroke',
    def_num=43,
    units='swim_stroke',
), 44: Field(
    name='pool_length',
    type='uint16',
    def_num=44,
    scale=100,
    units='m',
), 45: Field(
    name='threshold_power',
    type='uint16',
    def_num=45,
    units='watts',
), 46: Field(
    name='pool_length_unit',
    type='display_measure',
    def_num=46,
), 47: Field(
    name='num_active_lengths',
    type='uint16',
    def_num=47,
    units='lengths',
    comment='# of active lengths of swim pool',
), 48: Field(
    name='total_work',
    type='uint32',
    def_num=48,
    units='J',
), 49: Field(
    name='avg_altitude',
    type='uint16',
    def_num=49,
    components=Map(
    map=[Component(
    name='enhanced_avg_altitude',
    scale=5,
    offset=500,
    units='m',
    bits=16,
    accumulate=False,
    num=(126,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=5,
    offset=500,
    units='m',
), 50: Field(
    name='max_altitude',
    type='uint16',
    def_num=50,
    components=Map(
    map=[Component(
    name='enhanced_max_altitude',
    scale=5,
    offset=500,
    units='m',
    bits=16,
    accumulate=False,
    num=(128,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=5,
    offset=500,
    units='m',
), 51: Field(
    name='gps_accuracy',
    type='uint8',
    def_num=51,
    units='m',
), 52: Field(
    name='avg_grade',
    type='sint16',
    def_num=52,
    scale=100,
    units='%',
), 53: Field(
    name='avg_pos_grade',
    type='sint16',
    def_num=53,
    scale=100,
    units='%',
), 54: Field(
    name='avg_neg_grade',
    type='sint16',
    def_num=54,
    scale=100,
    units='%',
), 55: Field(
    name='max_pos_grade',
    type='sint16',
    def_num=55,
    scale=100,
    units='%',
), 56: Field(
    name='max_neg_grade',
    type='sint16',
    def_num=56,
    scale=100,
    units='%',
), 57: Field(
    name='avg_temperature',
    type='sint8',
    def_num=57,
    units='C',
), 58: Field(
    name='max_temperature',
    type='sint8',
    def_num=58,
    units='C',
), 59: Field(
    name='total_moving_time',
    type='uint32',
    def_num=59,
    scale=1000,
    units='s',
), 60: Field(
    name='avg_pos_vertical_speed',
    type='sint16',
    def_num=60,
    scale=1000,
    units='m/s',
), 61: Field(
    name='avg_neg_vertical_speed',
    type='sint16',
    def_num=61,
    scale=1000,
    units='m/s',
), 62: Field(
    name='max_pos_vertical_speed',
    type='sint16',
    def_num=62,
    scale=1000,
    units='m/s',
), 63: Field(
    name='max_neg_vertical_speed',
    type='sint16',
    def_num=63,
    scale=1000,
    units='m/s',
), 64: Field(
    name='min_heart_rate',
    type='uint8',
    def_num=64,
    units='bpm',
), 65: Field(
    name='time_in_hr_zone',
    type='uint32',
    def_num=65,
    scale=1000,
    units='s',
), 66: Field(
    name='time_in_speed_zone',
    type='uint32',
    def_num=66,
    scale=1000,
    units='s',
), 67: Field(
    name='time_in_cadence_zone',
    type='uint32',
    def_num=67,
    scale=1000,
    units='s',
), 68: Field(
    name='time_in_power_zone',
    type='uint32',
    def_num=68,
    scale=1000,
    units='s',
), 69: Field(
    name='avg_lap_time',
    type='uint32',
    def_num=69,
    scale=1000,
    units='s',
), 70: Field(
    name='best_lap_index',
    type='uint16',
    def_num=70,
), 71: Field(
    name='min_altitude',
    type='uint16',
    def_num=71,
    components=Map(
    map=[Component(
    name='enhanced_min_altitude',
    scale=5,
    offset=500,
    units='m',
    bits=16,
    accumulate=False,
    num=(127,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=5,
    offset=500,
    units='m',
), 82: Field(
    name='player_score',
    type='uint16',
    def_num=82,
), 83: Field(
    name='opponent_score',
    type='uint16',
    def_num=83,
), 84: Field(
    name='opponent_name',
    type='string',
    def_num=84,
), 85: Field(
    name='stroke_count',
    type='uint16',
    def_num=85,
    units='counts',
    comment='stroke_type enum used as the index',
), 86: Field(
    name='zone_count',
    type='uint16',
    def_num=86,
    units='counts',
    comment='zone number used as the index',
), 87: Field(
    name='max_ball_speed',
    type='uint16',
    def_num=87,
    scale=100,
    units='m/s',
), 88: Field(
    name='avg_ball_speed',
    type='uint16',
    def_num=88,
    scale=100,
    units='m/s',
), 89: Field(
    name='avg_vertical_oscillation',
    type='uint16',
    def_num=89,
    scale=10,
    units='mm',
), 90: Field(
    name='avg_stance_time_percent',
    type='uint16',
    def_num=90,
    scale=100,
    units='percent',
), 91: Field(
    name='avg_stance_time',
    type='uint16',
    def_num=91,
    scale=10,
    units='ms',
), 92: Field(
    name='avg_fractional_cadence',
    type='uint8',
    def_num=92,
    scale=128,
    units='rpm',
    comment='fractional part of the avg_cadence',
), 93: Field(
    name='max_fractional_cadence',
    type='uint8',
    def_num=93,
    scale=128,
    units='rpm',
    comment='fractional part of the max_cadence',
), 94: Field(
    name='total_fractional_cycles',
    type='uint8',
    def_num=94,
    scale=128,
    units='cycles',
    comment='fractional part of the total_cycles',
), 95: Field(
    name='avg_total_hemoglobin_conc',
    type='uint16',
    def_num=95,
    scale=100,
    units='g/dL',
    comment='Avg saturated and unsaturated hemoglobin',
), 96: Field(
    name='min_total_hemoglobin_conc',
    type='uint16',
    def_num=96,
    scale=100,
    units='g/dL',
    comment='Min saturated and unsaturated hemoglobin',
), 97: Field(
    name='max_total_hemoglobin_conc',
    type='uint16',
    def_num=97,
    scale=100,
    units='g/dL',
    comment='Max saturated and unsaturated hemoglobin',
), 98: Field(
    name='avg_saturated_hemoglobin_percent',
    type='uint16',
    def_num=98,
    scale=10,
    units='%',
    comment='Avg percentage of hemoglobin saturated with oxygen',
), 99: Field(
    name='min_saturated_hemoglobin_percent',
    type='uint16',
    def_num=99,
    scale=10,
    units='%',
    comment='Min percentage of hemoglobin saturated with oxygen',
), 100: Field(
    name='max_saturated_hemoglobin_percent',
    type='uint16',
    def_num=100,
    scale=10,
    units='%',
    comment='Max percentage of hemoglobin saturated with oxygen',
), 101: Field(
    name='avg_left_torque_effectiveness',
    type='uint8',
    def_num=101,
    scale=2,
    units='percent',
), 102: Field(
    name='avg_right_torque_effectiveness',
    type='uint8',
    def_num=102,
    scale=2,
    units='percent',
), 103: Field(
    name='avg_left_pedal_smoothness',
    type='uint8',
    def_num=103,
    scale=2,
    units='percent',
), 104: Field(
    name='avg_right_pedal_smoothness',
    type='uint8',
    def_num=104,
    scale=2,
    units='percent',
), 105: Field(
    name='avg_combined_pedal_smoothness',
    type='uint8',
    def_num=105,
    scale=2,
    units='percent',
), 111: Field(
    name='sport_index',
    type='uint8',
    def_num=111,
), 112: Field(
    name='time_standing',
    type='uint32',
    def_num=112,
    scale=1000,
    units='s',
    comment='Total time spend in the standing position',
), 113: Field(
    name='stand_count',
    type='uint16',
    def_num=113,
    comment='Number of transitions to the standing state',
), 114: Field(
    name='avg_left_pco',
    type='sint8',
    def_num=114,
    units='mm',
    comment='Average platform center offset Left',
), 115: Field(
    name='avg_right_pco',
    type='sint8',
    def_num=115,
    units='mm',
    comment='Average platform center offset Right',
), 116: Field(
    name='avg_left_power_phase',
    type='uint8',
    def_num=116,
    scale=0.7111111,
    units='degrees',
    comment='Average left power phase angles. Indexes defined by power_phase_type.',
), 117: Field(
    name='avg_left_power_phase_peak',
    type='uint8',
    def_num=117,
    scale=0.7111111,
    units='degrees',
    comment='Average left power phase peak angles. Data value indexes defined by power_phase_type.',
), 118: Field(
    name='avg_right_power_phase',
    type='uint8',
    def_num=118,
    scale=0.7111111,
    units='degrees',
    comment='Average right power phase angles. Data value indexes defined by power_phase_type.',
), 119: Field(
    name='avg_right_power_phase_peak',
    type='uint8',
    def_num=119,
    scale=0.7111111,
    units='degrees',
    comment='Average right power phase peak angles data value indexes  defined by power_phase_type.',
), 120: Field(
    name='avg_power_position',
    type='uint16',
    def_num=120,
    units='watts',
    comment='Average power by position. Data value indexes defined by rider_position_type.',
), 121: Field(
    name='max_power_position',
    type='uint16',
    def_num=121,
    units='watts',
    comment='Maximum power by position. Data value indexes defined by rider_position_type.',
), 122: Field(
    name='avg_cadence_position',
    type='uint8',
    def_num=122,
    units='rpm',
    comment='Average cadence by position. Data value indexes defined by rider_position_type.',
), 123: Field(
    name='max_cadence_position',
    type='uint8',
    def_num=123,
    units='rpm',
    comment='Maximum cadence by position. Data value indexes defined by rider_position_type.',
), 124: Field(
    name='enhanced_avg_speed',
    type='uint32',
    def_num=124,
    scale=1000,
    units='m/s',
    comment='total_distance / total_timer_time',
), 125: Field(
    name='enhanced_max_speed',
    type='uint32',
    def_num=125,
    scale=1000,
    units='m/s',
), 126: Field(
    name='enhanced_avg_altitude',
    type='uint32',
    def_num=126,
    scale=5,
    offset=500,
    units='m',
), 127: Field(
    name='enhanced_min_altitude',
    type='uint32',
    def_num=127,
    scale=5,
    offset=500,
    units='m',
), 128: Field(
    name='enhanced_max_altitude',
    type='uint32',
    def_num=128,
    scale=5,
    offset=500,
    units='m',
), 129: Field(
    name='avg_lev_motor_power',
    type='uint16',
    def_num=129,
    units='watts',
    comment='lev average motor power during session',
), 130: Field(
    name='max_lev_motor_power',
    type='uint16',
    def_num=130,
    units='watts',
    comment='lev maximum motor power during session',
), 131: Field(
    name='lev_battery_consumption',
    type='uint8',
    def_num=131,
    scale=2,
    units='percent',
    comment='lev battery consumption during session',
), 132: Field(
    name='avg_vertical_ratio',
    type='uint16',
    def_num=132,
    scale=100,
    units='percent',
), 133: Field(
    name='avg_stance_time_balance',
    type='uint16',
    def_num=133,
    scale=100,
    units='percent',
), 134: Field(
    name='avg_step_length',
    type='uint16',
    def_num=134,
    scale=10,
    units='mm',
), 137: Field(
    name='total_anaerobic_training_effect',
    type='uint8',
    def_num=137,
    scale=10,
), 139: Field(
    name='avg_vam',
    type='uint16',
    def_num=139,
    scale=1000,
    units='m/s',
), 181: Field(
    name='total_grit',
    type='float32',
    def_num=181,
    units='kGrit',
    comment='The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
), 182: Field(
    name='total_flow',
    type='float32',
    def_num=182,
    units='Flow',
    comment='The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
), 183: Field(
    name='jump_count',
    type='uint16',
    def_num=183,
), 186: Field(
    name='avg_grit',
    type='float32',
    def_num=186,
    units='kGrit',
    comment='The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
), 187: Field(
    name='avg_flow',
    type='float32',
    def_num=187,
    units='Flow',
    comment='The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
), 199: Field(
    name='total_fractional_ascent',
    type='uint8',
    def_num=199,
    scale=100,
    units='m',
    comment='fractional part of total_ascent',
), 200: Field(
    name='total_fractional_descent',
    type='uint8',
    def_num=200,
    scale=100,
    units='m',
    comment='fractional part of total_descent',
), 208: Field(
    name='avg_core_temperature',
    type='uint16',
    def_num=208,
    scale=100,
    units='C',
), 209: Field(
    name='min_core_temperature',
    type='uint16',
    def_num=209,
    scale=100,
    units='C',
), 210: Field(
    name='max_core_temperature',
    type='uint16',
    def_num=210,
    scale=100,
    units='C',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'lap': Message(
    name='lap',
    global_number=19,
    group_name='Activity File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Lap end time.',
), 0: Field(
    name='event',
    type='event',
    def_num=0,
), 1: Field(
    name='event_type',
    type='event_type',
    def_num=1,
), 2: Field(
    name='start_time',
    type='date_time',
    def_num=2,
), 3: Field(
    name='start_position_lat',
    type='sint32',
    def_num=3,
    units='semicircles',
), 4: Field(
    name='start_position_long',
    type='sint32',
    def_num=4,
    units='semicircles',
), 5: Field(
    name='end_position_lat',
    type='sint32',
    def_num=5,
    units='semicircles',
), 6: Field(
    name='end_position_long',
    type='sint32',
    def_num=6,
    units='semicircles',
), 7: Field(
    name='total_elapsed_time',
    type='uint32',
    def_num=7,
    scale=1000,
    units='s',
    comment='Time (includes pauses)',
), 8: Field(
    name='total_timer_time',
    type='uint32',
    def_num=8,
    scale=1000,
    units='s',
    comment='Timer Time (excludes pauses)',
), 9: Field(
    name='total_distance',
    type='uint32',
    def_num=9,
    scale=100,
    units='m',
), 10: Field(
    name='total_cycles',
    type='uint32',
    def_num=10,
    units='cycles',
    subfields=Map(
    map=[SubField(
    name='total_strides',
    type='uint32',
    units='strides',
    reference_fields=Map(
    map=[ReferenceField(
    name='sport',
    value='running',
    def_num=25,
    raw_value=1,
), ReferenceField(
    name='sport',
    value='walking',
    def_num=25,
    raw_value=11,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='total_strokes',
    type='uint32',
    units='strokes',
    reference_fields=Map(
    map=[ReferenceField(
    name='sport',
    value='cycling',
    def_num=25,
    raw_value=2,
), ReferenceField(
    name='sport',
    value='swimming',
    def_num=25,
    raw_value=5,
), ReferenceField(
    name='sport',
    value='rowing',
    def_num=25,
    raw_value=15,
), ReferenceField(
    name='sport',
    value='stand_up_paddleboarding',
    def_num=25,
    raw_value=37,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 11: Field(
    name='total_calories',
    type='uint16',
    def_num=11,
    units='kcal',
), 12: Field(
    name='total_fat_calories',
    type='uint16',
    def_num=12,
    units='kcal',
    comment='If New Leaf',
), 13: Field(
    name='avg_speed',
    type='uint16',
    def_num=13,
    components=Map(
    map=[Component(
    name='enhanced_avg_speed',
    scale=1000,
    units='m/s',
    bits=16,
    accumulate=False,
    num=(110,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=1000,
    units='m/s',
), 14: Field(
    name='max_speed',
    type='uint16',
    def_num=14,
    components=Map(
    map=[Component(
    name='enhanced_max_speed',
    scale=1000,
    units='m/s',
    bits=16,
    accumulate=False,
    num=(111,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=1000,
    units='m/s',
), 15: Field(
    name='avg_heart_rate',
    type='uint8',
    def_num=15,
    units='bpm',
), 16: Field(
    name='max_heart_rate',
    type='uint8',
    def_num=16,
    units='bpm',
), 17: Field(
    name='avg_cadence',
    type='uint8',
    def_num=17,
    units='rpm',
    comment='total_cycles / total_timer_time if non_zero_avg_cadence otherwise total_cycles / total_elapsed_time',
    subfields=Map(
    map=[SubField(
    name='avg_running_cadence',
    type='uint8',
    units='strides/min',
    reference_fields=Map(
    map=[ReferenceField(
    name='sport',
    value='running',
    def_num=25,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 18: Field(
    name='max_cadence',
    type='uint8',
    def_num=18,
    units='rpm',
    subfields=Map(
    map=[SubField(
    name='max_running_cadence',
    type='uint8',
    units='strides/min',
    reference_fields=Map(
    map=[ReferenceField(
    name='sport',
    value='running',
    def_num=25,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 19: Field(
    name='avg_power',
    type='uint16',
    def_num=19,
    units='watts',
    comment='total_power / total_timer_time if non_zero_avg_power otherwise total_power / total_elapsed_time',
), 20: Field(
    name='max_power',
    type='uint16',
    def_num=20,
    units='watts',
), 21: Field(
    name='total_ascent',
    type='uint16',
    def_num=21,
    units='m',
), 22: Field(
    name='total_descent',
    type='uint16',
    def_num=22,
    units='m',
), 23: Field(
    name='intensity',
    type='intensity',
    def_num=23,
), 24: Field(
    name='lap_trigger',
    type='lap_trigger',
    def_num=24,
), 25: Field(
    name='sport',
    type='sport',
    def_num=25,
), 26: Field(
    name='event_group',
    type='uint8',
    def_num=26,
), 32: Field(
    name='num_lengths',
    type='uint16',
    def_num=32,
    units='lengths',
    comment='# of lengths of swim pool',
), 33: Field(
    name='normalized_power',
    type='uint16',
    def_num=33,
    units='watts',
), 34: Field(
    name='left_right_balance',
    type='left_right_balance_100',
    def_num=34,
), 35: Field(
    name='first_length_index',
    type='uint16',
    def_num=35,
), 37: Field(
    name='avg_stroke_distance',
    type='uint16',
    def_num=37,
    scale=100,
    units='m',
), 38: Field(
    name='swim_stroke',
    type='swim_stroke',
    def_num=38,
), 39: Field(
    name='sub_sport',
    type='sub_sport',
    def_num=39,
), 40: Field(
    name='num_active_lengths',
    type='uint16',
    def_num=40,
    units='lengths',
    comment='# of active lengths of swim pool',
), 41: Field(
    name='total_work',
    type='uint32',
    def_num=41,
    units='J',
), 42: Field(
    name='avg_altitude',
    type='uint16',
    def_num=42,
    components=Map(
    map=[Component(
    name='enhanced_avg_altitude',
    scale=5,
    offset=500,
    units='m',
    bits=16,
    accumulate=False,
    num=(112,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=5,
    offset=500,
    units='m',
), 43: Field(
    name='max_altitude',
    type='uint16',
    def_num=43,
    components=Map(
    map=[Component(
    name='enhanced_max_altitude',
    scale=5,
    offset=500,
    units='m',
    bits=16,
    accumulate=False,
    num=(114,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=5,
    offset=500,
    units='m',
), 44: Field(
    name='gps_accuracy',
    type='uint8',
    def_num=44,
    units='m',
), 45: Field(
    name='avg_grade',
    type='sint16',
    def_num=45,
    scale=100,
    units='%',
), 46: Field(
    name='avg_pos_grade',
    type='sint16',
    def_num=46,
    scale=100,
    units='%',
), 47: Field(
    name='avg_neg_grade',
    type='sint16',
    def_num=47,
    scale=100,
    units='%',
), 48: Field(
    name='max_pos_grade',
    type='sint16',
    def_num=48,
    scale=100,
    units='%',
), 49: Field(
    name='max_neg_grade',
    type='sint16',
    def_num=49,
    scale=100,
    units='%',
), 50: Field(
    name='avg_temperature',
    type='sint8',
    def_num=50,
    units='C',
), 51: Field(
    name='max_temperature',
    type='sint8',
    def_num=51,
    units='C',
), 52: Field(
    name='total_moving_time',
    type='uint32',
    def_num=52,
    scale=1000,
    units='s',
), 53: Field(
    name='avg_pos_vertical_speed',
    type='sint16',
    def_num=53,
    scale=1000,
    units='m/s',
), 54: Field(
    name='avg_neg_vertical_speed',
    type='sint16',
    def_num=54,
    scale=1000,
    units='m/s',
), 55: Field(
    name='max_pos_vertical_speed',
    type='sint16',
    def_num=55,
    scale=1000,
    units='m/s',
), 56: Field(
    name='max_neg_vertical_speed',
    type='sint16',
    def_num=56,
    scale=1000,
    units='m/s',
), 57: Field(
    name='time_in_hr_zone',
    type='uint32',
    def_num=57,
    scale=1000,
    units='s',
), 58: Field(
    name='time_in_speed_zone',
    type='uint32',
    def_num=58,
    scale=1000,
    units='s',
), 59: Field(
    name='time_in_cadence_zone',
    type='uint32',
    def_num=59,
    scale=1000,
    units='s',
), 60: Field(
    name='time_in_power_zone',
    type='uint32',
    def_num=60,
    scale=1000,
    units='s',
), 61: Field(
    name='repetition_num',
    type='uint16',
    def_num=61,
), 62: Field(
    name='min_altitude',
    type='uint16',
    def_num=62,
    components=Map(
    map=[Component(
    name='enhanced_min_altitude',
    scale=5,
    offset=500,
    units='m',
    bits=16,
    accumulate=False,
    num=(113,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=5,
    offset=500,
    units='m',
), 63: Field(
    name='min_heart_rate',
    type='uint8',
    def_num=63,
    units='bpm',
), 71: Field(
    name='wkt_step_index',
    type='message_index',
    def_num=71,
), 74: Field(
    name='opponent_score',
    type='uint16',
    def_num=74,
), 75: Field(
    name='stroke_count',
    type='uint16',
    def_num=75,
    units='counts',
    comment='stroke_type enum used as the index',
), 76: Field(
    name='zone_count',
    type='uint16',
    def_num=76,
    units='counts',
    comment='zone number used as the index',
), 77: Field(
    name='avg_vertical_oscillation',
    type='uint16',
    def_num=77,
    scale=10,
    units='mm',
), 78: Field(
    name='avg_stance_time_percent',
    type='uint16',
    def_num=78,
    scale=100,
    units='percent',
), 79: Field(
    name='avg_stance_time',
    type='uint16',
    def_num=79,
    scale=10,
    units='ms',
), 80: Field(
    name='avg_fractional_cadence',
    type='uint8',
    def_num=80,
    scale=128,
    units='rpm',
    comment='fractional part of the avg_cadence',
), 81: Field(
    name='max_fractional_cadence',
    type='uint8',
    def_num=81,
    scale=128,
    units='rpm',
    comment='fractional part of the max_cadence',
), 82: Field(
    name='total_fractional_cycles',
    type='uint8',
    def_num=82,
    scale=128,
    units='cycles',
    comment='fractional part of the total_cycles',
), 83: Field(
    name='player_score',
    type='uint16',
    def_num=83,
), 84: Field(
    name='avg_total_hemoglobin_conc',
    type='uint16',
    def_num=84,
    scale=100,
    units='g/dL',
    comment='Avg saturated and unsaturated hemoglobin',
), 85: Field(
    name='min_total_hemoglobin_conc',
    type='uint16',
    def_num=85,
    scale=100,
    units='g/dL',
    comment='Min saturated and unsaturated hemoglobin',
), 86: Field(
    name='max_total_hemoglobin_conc',
    type='uint16',
    def_num=86,
    scale=100,
    units='g/dL',
    comment='Max saturated and unsaturated hemoglobin',
), 87: Field(
    name='avg_saturated_hemoglobin_percent',
    type='uint16',
    def_num=87,
    scale=10,
    units='%',
    comment='Avg percentage of hemoglobin saturated with oxygen',
), 88: Field(
    name='min_saturated_hemoglobin_percent',
    type='uint16',
    def_num=88,
    scale=10,
    units='%',
    comment='Min percentage of hemoglobin saturated with oxygen',
), 89: Field(
    name='max_saturated_hemoglobin_percent',
    type='uint16',
    def_num=89,
    scale=10,
    units='%',
    comment='Max percentage of hemoglobin saturated with oxygen',
), 91: Field(
    name='avg_left_torque_effectiveness',
    type='uint8',
    def_num=91,
    scale=2,
    units='percent',
), 92: Field(
    name='avg_right_torque_effectiveness',
    type='uint8',
    def_num=92,
    scale=2,
    units='percent',
), 93: Field(
    name='avg_left_pedal_smoothness',
    type='uint8',
    def_num=93,
    scale=2,
    units='percent',
), 94: Field(
    name='avg_right_pedal_smoothness',
    type='uint8',
    def_num=94,
    scale=2,
    units='percent',
), 95: Field(
    name='avg_combined_pedal_smoothness',
    type='uint8',
    def_num=95,
    scale=2,
    units='percent',
), 98: Field(
    name='time_standing',
    type='uint32',
    def_num=98,
    scale=1000,
    units='s',
    comment='Total time spent in the standing position',
), 99: Field(
    name='stand_count',
    type='uint16',
    def_num=99,
    comment='Number of transitions to the standing state',
), 100: Field(
    name='avg_left_pco',
    type='sint8',
    def_num=100,
    units='mm',
    comment='Average left platform center offset',
), 101: Field(
    name='avg_right_pco',
    type='sint8',
    def_num=101,
    units='mm',
    comment='Average right platform center offset',
), 102: Field(
    name='avg_left_power_phase',
    type='uint8',
    def_num=102,
    scale=0.7111111,
    units='degrees',
    comment='Average left power phase angles. Data value indexes defined by power_phase_type.',
), 103: Field(
    name='avg_left_power_phase_peak',
    type='uint8',
    def_num=103,
    scale=0.7111111,
    units='degrees',
    comment='Average left power phase peak angles. Data value indexes  defined by power_phase_type.',
), 104: Field(
    name='avg_right_power_phase',
    type='uint8',
    def_num=104,
    scale=0.7111111,
    units='degrees',
    comment='Average right power phase angles. Data value indexes defined by power_phase_type.',
), 105: Field(
    name='avg_right_power_phase_peak',
    type='uint8',
    def_num=105,
    scale=0.7111111,
    units='degrees',
    comment='Average right power phase peak angles. Data value indexes  defined by power_phase_type.',
), 106: Field(
    name='avg_power_position',
    type='uint16',
    def_num=106,
    units='watts',
    comment='Average power by position. Data value indexes defined by rider_position_type.',
), 107: Field(
    name='max_power_position',
    type='uint16',
    def_num=107,
    units='watts',
    comment='Maximum power by position. Data value indexes defined by rider_position_type.',
), 108: Field(
    name='avg_cadence_position',
    type='uint8',
    def_num=108,
    units='rpm',
    comment='Average cadence by position. Data value indexes defined by rider_position_type.',
), 109: Field(
    name='max_cadence_position',
    type='uint8',
    def_num=109,
    units='rpm',
    comment='Maximum cadence by position. Data value indexes defined by rider_position_type.',
), 110: Field(
    name='enhanced_avg_speed',
    type='uint32',
    def_num=110,
    scale=1000,
    units='m/s',
), 111: Field(
    name='enhanced_max_speed',
    type='uint32',
    def_num=111,
    scale=1000,
    units='m/s',
), 112: Field(
    name='enhanced_avg_altitude',
    type='uint32',
    def_num=112,
    scale=5,
    offset=500,
    units='m',
), 113: Field(
    name='enhanced_min_altitude',
    type='uint32',
    def_num=113,
    scale=5,
    offset=500,
    units='m',
), 114: Field(
    name='enhanced_max_altitude',
    type='uint32',
    def_num=114,
    scale=5,
    offset=500,
    units='m',
), 115: Field(
    name='avg_lev_motor_power',
    type='uint16',
    def_num=115,
    units='watts',
    comment='lev average motor power during lap',
), 116: Field(
    name='max_lev_motor_power',
    type='uint16',
    def_num=116,
    units='watts',
    comment='lev maximum motor power during lap',
), 117: Field(
    name='lev_battery_consumption',
    type='uint8',
    def_num=117,
    scale=2,
    units='percent',
    comment='lev battery consumption during lap',
), 118: Field(
    name='avg_vertical_ratio',
    type='uint16',
    def_num=118,
    scale=100,
    units='percent',
), 119: Field(
    name='avg_stance_time_balance',
    type='uint16',
    def_num=119,
    scale=100,
    units='percent',
), 120: Field(
    name='avg_step_length',
    type='uint16',
    def_num=120,
    scale=10,
    units='mm',
), 121: Field(
    name='avg_vam',
    type='uint16',
    def_num=121,
    scale=1000,
    units='m/s',
), 149: Field(
    name='total_grit',
    type='float32',
    def_num=149,
    units='kGrit',
    comment='The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
), 150: Field(
    name='total_flow',
    type='float32',
    def_num=150,
    units='Flow',
    comment='The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
), 151: Field(
    name='jump_count',
    type='uint16',
    def_num=151,
), 153: Field(
    name='avg_grit',
    type='float32',
    def_num=153,
    units='kGrit',
    comment='The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
), 154: Field(
    name='avg_flow',
    type='float32',
    def_num=154,
    units='Flow',
    comment='The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
), 156: Field(
    name='total_fractional_ascent',
    type='uint8',
    def_num=156,
    scale=100,
    units='m',
    comment='fractional part of total_ascent',
), 157: Field(
    name='total_fractional_descent',
    type='uint8',
    def_num=157,
    scale=100,
    units='m',
    comment='fractional part of total_descent',
), 158: Field(
    name='avg_core_temperature',
    type='uint16',
    def_num=158,
    scale=100,
    units='C',
), 159: Field(
    name='min_core_temperature',
    type='uint16',
    def_num=159,
    scale=100,
    units='C',
), 160: Field(
    name='max_core_temperature',
    type='uint16',
    def_num=160,
    scale=100,
    units='C',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'record': Message(
    name='record',
    global_number=20,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
), 0: Field(
    name='position_lat',
    type='sint32',
    def_num=0,
    units='semicircles',
), 1: Field(
    name='position_long',
    type='sint32',
    def_num=1,
    units='semicircles',
), 2: Field(
    name='altitude',
    type='uint16',
    def_num=2,
    components=Map(
    map=[Component(
    name='enhanced_altitude',
    scale=5,
    offset=500,
    units='m',
    bits=16,
    accumulate=False,
    num=(78,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=5,
    offset=500,
    units='m',
), 3: Field(
    name='heart_rate',
    type='uint8',
    def_num=3,
    units='bpm',
), 4: Field(
    name='cadence',
    type='uint8',
    def_num=4,
    units='rpm',
), 5: Field(
    name='distance',
    type='uint32',
    def_num=5,
    scale=100,
    units='m',
), 6: Field(
    name='speed',
    type='uint16',
    def_num=6,
    components=Map(
    map=[Component(
    name='enhanced_speed',
    scale=1000,
    units='m/s',
    bits=16,
    accumulate=False,
    num=(73,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=1000,
    units='m/s',
), 7: Field(
    name='power',
    type='uint16',
    def_num=7,
    units='watts',
), 8: Field(
    name='compressed_speed_distance',
    type='byte',
    def_num=8,
    components=Map(
    map=[Component(
    name='speed',
    scale=100,
    units='m/s',
    bits=12,
    accumulate=False,
    num=(6,),
    bit_offset=0,
), Component(
    name='distance',
    scale=16,
    units='m',
    bits=12,
    accumulate=True,
    num=(5,),
    bit_offset=12,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
), 9: Field(
    name='grade',
    type='sint16',
    def_num=9,
    scale=100,
    units='%',
), 10: Field(
    name='resistance',
    type='uint8',
    def_num=10,
    comment='Relative. 0 is none  254 is Max.',
), 11: Field(
    name='time_from_course',
    type='sint32',
    def_num=11,
    scale=1000,
    units='s',
), 12: Field(
    name='cycle_length',
    type='uint8',
    def_num=12,
    scale=100,
    units='m',
), 13: Field(
    name='temperature',
    type='sint8',
    def_num=13,
    units='C',
), 17: Field(
    name='speed_1s',
    type='uint8',
    def_num=17,
    scale=16,
    units='m/s',
    comment='Speed at 1s intervals.  Timestamp field indicates time of last array element.',
), 18: Field(
    name='cycles',
    type='uint8',
    def_num=18,
    components=Map(
    map=[Component(
    name='total_cycles',
    units='cycles',
    bits=8,
    accumulate=True,
    num=(19,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
), 19: Field(
    name='total_cycles',
    type='uint32',
    def_num=19,
    units='cycles',
), 28: Field(
    name='compressed_accumulated_power',
    type='uint16',
    def_num=28,
    components=Map(
    map=[Component(
    name='accumulated_power',
    units='watts',
    bits=16,
    accumulate=True,
    num=(29,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
), 29: Field(
    name='accumulated_power',
    type='uint32',
    def_num=29,
    units='watts',
), 30: Field(
    name='left_right_balance',
    type='left_right_balance',
    def_num=30,
), 31: Field(
    name='gps_accuracy',
    type='uint8',
    def_num=31,
    units='m',
), 32: Field(
    name='vertical_speed',
    type='sint16',
    def_num=32,
    scale=1000,
    units='m/s',
), 33: Field(
    name='calories',
    type='uint16',
    def_num=33,
    units='kcal',
), 39: Field(
    name='vertical_oscillation',
    type='uint16',
    def_num=39,
    scale=10,
    units='mm',
), 40: Field(
    name='stance_time_percent',
    type='uint16',
    def_num=40,
    scale=100,
    units='percent',
), 41: Field(
    name='stance_time',
    type='uint16',
    def_num=41,
    scale=10,
    units='ms',
), 42: Field(
    name='activity_type',
    type='activity_type',
    def_num=42,
), 43: Field(
    name='left_torque_effectiveness',
    type='uint8',
    def_num=43,
    scale=2,
    units='percent',
), 44: Field(
    name='right_torque_effectiveness',
    type='uint8',
    def_num=44,
    scale=2,
    units='percent',
), 45: Field(
    name='left_pedal_smoothness',
    type='uint8',
    def_num=45,
    scale=2,
    units='percent',
), 46: Field(
    name='right_pedal_smoothness',
    type='uint8',
    def_num=46,
    scale=2,
    units='percent',
), 47: Field(
    name='combined_pedal_smoothness',
    type='uint8',
    def_num=47,
    scale=2,
    units='percent',
), 48: Field(
    name='time128',
    type='uint8',
    def_num=48,
    scale=128,
    units='s',
), 49: Field(
    name='stroke_type',
    type='stroke_type',
    def_num=49,
), 50: Field(
    name='zone',
    type='uint8',
    def_num=50,
), 51: Field(
    name='ball_speed',
    type='uint16',
    def_num=51,
    scale=100,
    units='m/s',
), 52: Field(
    name='cadence256',
    type='uint16',
    def_num=52,
    scale=256,
    units='rpm',
    comment='Log cadence and fractional cadence for backwards compatability',
), 53: Field(
    name='fractional_cadence',
    type='uint8',
    def_num=53,
    scale=128,
    units='rpm',
), 54: Field(
    name='total_hemoglobin_conc',
    type='uint16',
    def_num=54,
    scale=100,
    units='g/dL',
    comment='Total saturated and unsaturated hemoglobin',
), 55: Field(
    name='total_hemoglobin_conc_min',
    type='uint16',
    def_num=55,
    scale=100,
    units='g/dL',
    comment='Min saturated and unsaturated hemoglobin',
), 56: Field(
    name='total_hemoglobin_conc_max',
    type='uint16',
    def_num=56,
    scale=100,
    units='g/dL',
    comment='Max saturated and unsaturated hemoglobin',
), 57: Field(
    name='saturated_hemoglobin_percent',
    type='uint16',
    def_num=57,
    scale=10,
    units='%',
    comment='Percentage of hemoglobin saturated with oxygen',
), 58: Field(
    name='saturated_hemoglobin_percent_min',
    type='uint16',
    def_num=58,
    scale=10,
    units='%',
    comment='Min percentage of hemoglobin saturated with oxygen',
), 59: Field(
    name='saturated_hemoglobin_percent_max',
    type='uint16',
    def_num=59,
    scale=10,
    units='%',
    comment='Max percentage of hemoglobin saturated with oxygen',
), 62: Field(
    name='device_index',
    type='device_index',
    def_num=62,
), 67: Field(
    name='left_pco',
    type='sint8',
    def_num=67,
    units='mm',
    comment='Left platform center offset',
), 68: Field(
    name='right_pco',
    type='sint8',
    def_num=68,
    units='mm',
    comment='Right platform center offset',
), 69: Field(
    name='left_power_phase',
    type='uint8',
    def_num=69,
    scale=0.7111111,
    units='degrees',
    comment='Left power phase angles. Data value indexes defined by power_phase_type.',
), 70: Field(
    name='left_power_phase_peak',
    type='uint8',
    def_num=70,
    scale=0.7111111,
    units='degrees',
    comment='Left power phase peak angles. Data value indexes defined by power_phase_type.',
), 71: Field(
    name='right_power_phase',
    type='uint8',
    def_num=71,
    scale=0.7111111,
    units='degrees',
    comment='Right power phase angles. Data value indexes defined by power_phase_type.',
), 72: Field(
    name='right_power_phase_peak',
    type='uint8',
    def_num=72,
    scale=0.7111111,
    units='degrees',
    comment='Right power phase peak angles. Data value indexes defined by power_phase_type.',
), 73: Field(
    name='enhanced_speed',
    type='uint32',
    def_num=73,
    scale=1000,
    units='m/s',
), 78: Field(
    name='enhanced_altitude',
    type='uint32',
    def_num=78,
    scale=5,
    offset=500,
    units='m',
), 81: Field(
    name='battery_soc',
    type='uint8',
    def_num=81,
    scale=2,
    units='percent',
    comment='lev battery state of charge',
), 82: Field(
    name='motor_power',
    type='uint16',
    def_num=82,
    units='watts',
    comment='lev motor power',
), 83: Field(
    name='vertical_ratio',
    type='uint16',
    def_num=83,
    scale=100,
    units='percent',
), 84: Field(
    name='stance_time_balance',
    type='uint16',
    def_num=84,
    scale=100,
    units='percent',
), 85: Field(
    name='step_length',
    type='uint16',
    def_num=85,
    scale=10,
    units='mm',
), 91: Field(
    name='absolute_pressure',
    type='uint32',
    def_num=91,
    units='Pa',
    comment='Includes atmospheric pressure',
), 92: Field(
    name='depth',
    type='uint32',
    def_num=92,
    scale=1000,
    units='m',
    comment='0 if above water',
), 93: Field(
    name='next_stop_depth',
    type='uint32',
    def_num=93,
    scale=1000,
    units='m',
    comment='0 if above water',
), 94: Field(
    name='next_stop_time',
    type='uint32',
    def_num=94,
    units='s',
), 95: Field(
    name='time_to_surface',
    type='uint32',
    def_num=95,
    units='s',
), 96: Field(
    name='ndl_time',
    type='uint32',
    def_num=96,
    units='s',
), 97: Field(
    name='cns_load',
    type='uint8',
    def_num=97,
    units='percent',
), 98: Field(
    name='n2_load',
    type='uint16',
    def_num=98,
    units='percent',
), 114: Field(
    name='grit',
    type='float32',
    def_num=114,
    comment='The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
), 115: Field(
    name='flow',
    type='float32',
    def_num=115,
    comment='The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
), 117: Field(
    name='ebike_travel_range',
    type='uint16',
    def_num=117,
    units='km',
), 118: Field(
    name='ebike_battery_level',
    type='uint8',
    def_num=118,
    units='percent',
), 119: Field(
    name='ebike_assist_mode',
    type='uint8',
    def_num=119,
    units='depends on sensor',
), 120: Field(
    name='ebike_assist_level_percent',
    type='uint8',
    def_num=120,
    units='percent',
), 139: Field(
    name='core_temperature',
    type='uint16',
    def_num=139,
    scale=100,
    units='C',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'event': Message(
    name='event',
    global_number=21,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
), 0: Field(
    name='event',
    type='event',
    def_num=0,
), 1: Field(
    name='event_type',
    type='event_type',
    def_num=1,
), 2: Field(
    name='data16',
    type='uint16',
    def_num=2,
    components=Map(
    map=[Component(
    name='data',
    bits=16,
    accumulate=False,
    num=(3,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
), 3: Field(
    name='data',
    type='uint32',
    def_num=3,
    subfields=Map(
    map=[SubField(
    name='timer_trigger',
    type='timer_trigger',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='timer',
    def_num=0,
    raw_value=0,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='course_point_index',
    type='message_index',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='course_point',
    def_num=0,
    raw_value=10,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='battery_level',
    type='uint16',
    scale=1000,
    units='V',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='battery',
    def_num=0,
    raw_value=11,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='virtual_partner_speed',
    type='uint16',
    scale=1000,
    units='m/s',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='virtual_partner_pace',
    def_num=0,
    raw_value=12,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='hr_high_alert',
    type='uint8',
    units='bpm',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='hr_high_alert',
    def_num=0,
    raw_value=13,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='hr_low_alert',
    type='uint8',
    units='bpm',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='hr_low_alert',
    def_num=0,
    raw_value=14,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='speed_high_alert',
    type='uint32',
    scale=1000,
    units='m/s',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='speed_high_alert',
    def_num=0,
    raw_value=15,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='speed_low_alert',
    type='uint32',
    scale=1000,
    units='m/s',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='speed_low_alert',
    def_num=0,
    raw_value=16,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='cad_high_alert',
    type='uint16',
    units='rpm',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='cad_high_alert',
    def_num=0,
    raw_value=17,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='cad_low_alert',
    type='uint16',
    units='rpm',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='cad_low_alert',
    def_num=0,
    raw_value=18,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='power_high_alert',
    type='uint16',
    units='watts',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='power_high_alert',
    def_num=0,
    raw_value=19,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='power_low_alert',
    type='uint16',
    units='watts',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='power_low_alert',
    def_num=0,
    raw_value=20,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='time_duration_alert',
    type='uint32',
    scale=1000,
    units='s',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='time_duration_alert',
    def_num=0,
    raw_value=23,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='distance_duration_alert',
    type='uint32',
    scale=100,
    units='m',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='distance_duration_alert',
    def_num=0,
    raw_value=24,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='calorie_duration_alert',
    type='uint32',
    units='calories',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='calorie_duration_alert',
    def_num=0,
    raw_value=25,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='fitness_equipment_state',
    type='fitness_equipment_state',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='fitness_equipment',
    def_num=0,
    raw_value=27,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='sport_point',
    type='uint32',
    components=Map(
    map=[Component(
    name='score',
    bits=16,
    accumulate=False,
    num=(7,),
    bit_offset=0,
), Component(
    name='opponent_score',
    bits=16,
    accumulate=False,
    num=(8,),
    bit_offset=16,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='sport_point',
    def_num=0,
    raw_value=33,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='gear_change_data',
    type='uint32',
    components=Map(
    map=[Component(
    name='rear_gear_num',
    bits=8,
    accumulate=False,
    num=(11,),
    bit_offset=0,
), Component(
    name='rear_gear',
    bits=8,
    accumulate=False,
    num=(12,),
    bit_offset=8,
), Component(
    name='front_gear_num',
    bits=8,
    accumulate=False,
    num=(9,),
    bit_offset=16,
), Component(
    name='front_gear',
    bits=8,
    accumulate=False,
    num=(10,),
    bit_offset=24,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='front_gear_change',
    def_num=0,
    raw_value=42,
), ReferenceField(
    name='event',
    value='rear_gear_change',
    def_num=0,
    raw_value=43,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='rider_position',
    type='rider_position_type',
    comment='Indicates the rider position value.',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='rider_position_change',
    def_num=0,
    raw_value=44,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='comm_timeout',
    type='comm_timeout_type',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='comm_timeout',
    def_num=0,
    raw_value=47,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='radar_threat_alert',
    type='uint32',
    components=Map(
    map=[Component(
    name='radar_threat_level_max',
    bits=8,
    accumulate=False,
    num=(21,),
    bit_offset=0,
), Component(
    name='radar_threat_count',
    bits=8,
    accumulate=False,
    num=(22,),
    bit_offset=8,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    comment='The\xa0first\xa0byte\xa0is\xa0the\xa0radar_threat_level_max, the\xa0second\xa0byte\xa0is\xa0the\xa0radar_threat_count, and the\xa0last\xa016\xa0bits\xa0are\xa0reserved\xa0for\xa0future\xa0use\xa0and\xa0should\xa0be\xa0set\xa0to\xa0FFFF.',
    reference_fields=Map(
    map=[ReferenceField(
    name='event',
    value='radar_threat_alert',
    def_num=0,
    raw_value=75,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 4: Field(
    name='event_group',
    type='uint8',
    def_num=4,
), 7: Field(
    name='score',
    type='uint16',
    def_num=7,
    comment='Do not populate directly. Autogenerated by decoder for sport_point subfield components',
), 8: Field(
    name='opponent_score',
    type='uint16',
    def_num=8,
    comment='Do not populate directly. Autogenerated by decoder for sport_point subfield components',
), 9: Field(
    name='front_gear_num',
    type='uint8z',
    def_num=9,
    comment='Do not populate directly. Autogenerated by decoder for gear_change subfield components.  Front gear number. 1 is innermost.',
), 10: Field(
    name='front_gear',
    type='uint8z',
    def_num=10,
    comment='Do not populate directly. Autogenerated by decoder for gear_change subfield components.  Number of front teeth.',
), 11: Field(
    name='rear_gear_num',
    type='uint8z',
    def_num=11,
    comment='Do not populate directly. Autogenerated by decoder for gear_change subfield components.  Rear gear number. 1 is innermost.',
), 12: Field(
    name='rear_gear',
    type='uint8z',
    def_num=12,
    comment='Do not populate directly. Autogenerated by decoder for gear_change subfield components.  Number of rear teeth.',
), 13: Field(
    name='device_index',
    type='device_index',
    def_num=13,
), 21: Field(
    name='radar_threat_level_max',
    type='radar_threat_level_type',
    def_num=21,
    comment='Do not populate directly. Autogenerated by decoder for threat_alert subfield components.',
), 22: Field(
    name='radar_threat_count',
    type='uint8',
    def_num=22,
    comment='Do not populate directly. Autogenerated by decoder for threat_alert subfield components.',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'device_info': Message(
    name='device_info',
    global_number=23,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
), 0: Field(
    name='device_index',
    type='device_index',
    def_num=0,
), 1: Field(
    name='device_type',
    type='uint8',
    def_num=1,
    subfields=Map(
    map=[SubField(
    name='antplus_device_type',
    type='antplus_device_type',
    reference_fields=Map(
    map=[ReferenceField(
    name='source_type',
    value='antplus',
    def_num=25,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='ant_device_type',
    type='uint8',
    reference_fields=Map(
    map=[ReferenceField(
    name='source_type',
    value='ant',
    def_num=25,
    raw_value=0,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 2: Field(
    name='manufacturer',
    type='manufacturer',
    def_num=2,
), 3: Field(
    name='serial_number',
    type='uint32z',
    def_num=3,
), 4: Field(
    name='product',
    type='uint16',
    def_num=4,
    subfields=Map(
    map=[SubField(
    name='favero_product',
    type='favero_product',
    reference_fields=Map(
    map=[ReferenceField(
    name='manufacturer',
    value='favero_electronics',
    def_num=2,
    raw_value=263,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='garmin_product',
    type='garmin_product',
    reference_fields=Map(
    map=[ReferenceField(
    name='manufacturer',
    value='garmin',
    def_num=2,
    raw_value=1,
), ReferenceField(
    name='manufacturer',
    value='dynastream',
    def_num=2,
    raw_value=15,
), ReferenceField(
    name='manufacturer',
    value='dynastream_oem',
    def_num=2,
    raw_value=13,
), ReferenceField(
    name='manufacturer',
    value='tacx',
    def_num=2,
    raw_value=89,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 5: Field(
    name='software_version',
    type='uint16',
    def_num=5,
    scale=100,
), 6: Field(
    name='hardware_version',
    type='uint8',
    def_num=6,
), 7: Field(
    name='cum_operating_time',
    type='uint32',
    def_num=7,
    units='s',
    comment='Reset by new battery or charge.',
), 10: Field(
    name='battery_voltage',
    type='uint16',
    def_num=10,
    scale=256,
    units='V',
), 11: Field(
    name='battery_status',
    type='battery_status',
    def_num=11,
), 18: Field(
    name='sensor_position',
    type='body_location',
    def_num=18,
    comment='Indicates the location of the sensor',
), 19: Field(
    name='descriptor',
    type='string',
    def_num=19,
    comment='Used to describe the sensor or location',
), 20: Field(
    name='ant_transmission_type',
    type='uint8z',
    def_num=20,
), 21: Field(
    name='ant_device_number',
    type='uint16z',
    def_num=21,
), 22: Field(
    name='ant_network',
    type='ant_network',
    def_num=22,
), 25: Field(
    name='source_type',
    type='source_type',
    def_num=25,
), 27: Field(
    name='product_name',
    type='string',
    def_num=27,
    comment='Optional free form string to indicate the devices name or model',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'workout': Message(
    name='workout',
    global_number=26,
    group_name='Workout File Messages',
    fields=Map(
    map={4: Field(
    name='sport',
    type='sport',
    def_num=4,
), 5: Field(
    name='capabilities',
    type='workout_capabilities',
    def_num=5,
), 6: Field(
    name='num_valid_steps',
    type='uint16',
    def_num=6,
    comment='number of valid steps',
), 8: Field(
    name='wkt_name',
    type='string',
    def_num=8,
), 11: Field(
    name='sub_sport',
    type='sub_sport',
    def_num=11,
), 14: Field(
    name='pool_length',
    type='uint16',
    def_num=14,
    scale=100,
    units='m',
), 15: Field(
    name='pool_length_unit',
    type='display_measure',
    def_num=15,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'workout_step': Message(
    name='workout_step',
    global_number=27,
    group_name='Workout File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='wkt_step_name',
    type='string',
    def_num=0,
), 1: Field(
    name='duration_type',
    type='wkt_step_duration',
    def_num=1,
), 2: Field(
    name='duration_value',
    type='uint32',
    def_num=2,
    subfields=Map(
    map=[SubField(
    name='duration_time',
    type='uint32',
    scale=1000,
    units='s',
    reference_fields=Map(
    map=[ReferenceField(
    name='duration_type',
    value='time',
    def_num=1,
    raw_value=0,
), ReferenceField(
    name='duration_type',
    value='repetition_time',
    def_num=1,
    raw_value=28,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='duration_distance',
    type='uint32',
    scale=100,
    units='m',
    reference_fields=Map(
    map=[ReferenceField(
    name='duration_type',
    value='distance',
    def_num=1,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='duration_hr',
    type='workout_hr',
    units='% or bpm',
    reference_fields=Map(
    map=[ReferenceField(
    name='duration_type',
    value='hr_less_than',
    def_num=1,
    raw_value=2,
), ReferenceField(
    name='duration_type',
    value='hr_greater_than',
    def_num=1,
    raw_value=3,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='duration_calories',
    type='uint32',
    units='calories',
    reference_fields=Map(
    map=[ReferenceField(
    name='duration_type',
    value='calories',
    def_num=1,
    raw_value=4,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='duration_step',
    type='uint32',
    comment='message_index of step to loop back to. Steps are assumed to be in the order by message_index. custom_name and intensity members are undefined for this duration type.',
    reference_fields=Map(
    map=[ReferenceField(
    name='duration_type',
    value='repeat_until_steps_cmplt',
    def_num=1,
    raw_value=6,
), ReferenceField(
    name='duration_type',
    value='repeat_until_time',
    def_num=1,
    raw_value=7,
), ReferenceField(
    name='duration_type',
    value='repeat_until_distance',
    def_num=1,
    raw_value=8,
), ReferenceField(
    name='duration_type',
    value='repeat_until_calories',
    def_num=1,
    raw_value=9,
), ReferenceField(
    name='duration_type',
    value='repeat_until_hr_less_than',
    def_num=1,
    raw_value=10,
), ReferenceField(
    name='duration_type',
    value='repeat_until_hr_greater_than',
    def_num=1,
    raw_value=11,
), ReferenceField(
    name='duration_type',
    value='repeat_until_power_less_than',
    def_num=1,
    raw_value=12,
), ReferenceField(
    name='duration_type',
    value='repeat_until_power_greater_than',
    def_num=1,
    raw_value=13,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='duration_power',
    type='workout_power',
    units='% or watts',
    reference_fields=Map(
    map=[ReferenceField(
    name='duration_type',
    value='power_less_than',
    def_num=1,
    raw_value=14,
), ReferenceField(
    name='duration_type',
    value='power_greater_than',
    def_num=1,
    raw_value=15,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='duration_reps',
    type='uint32',
    reference_fields=Map(
    map=[ReferenceField(
    name='duration_type',
    value='reps',
    def_num=1,
    raw_value=29,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 3: Field(
    name='target_type',
    type='wkt_step_target',
    def_num=3,
), 4: Field(
    name='target_value',
    type='uint32',
    def_num=4,
    subfields=Map(
    map=[SubField(
    name='target_speed_zone',
    type='uint32',
    comment='speed zone (1-10);Custom =0;',
    reference_fields=Map(
    map=[ReferenceField(
    name='target_type',
    value='speed',
    def_num=3,
    raw_value=0,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='target_hr_zone',
    type='uint32',
    comment='hr zone (1-5);Custom =0;',
    reference_fields=Map(
    map=[ReferenceField(
    name='target_type',
    value='heart_rate',
    def_num=3,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='target_cadence_zone',
    type='uint32',
    comment='Zone (1-?); Custom = 0;',
    reference_fields=Map(
    map=[ReferenceField(
    name='target_type',
    value='cadence',
    def_num=3,
    raw_value=3,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='target_power_zone',
    type='uint32',
    comment='Power Zone ( 1-7); Custom = 0;',
    reference_fields=Map(
    map=[ReferenceField(
    name='target_type',
    value='power',
    def_num=3,
    raw_value=4,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='repeat_steps',
    type='uint32',
    comment='# of repetitions',
    reference_fields=Map(
    map=[ReferenceField(
    name='duration_type',
    value='repeat_until_steps_cmplt',
    def_num=1,
    raw_value=6,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='repeat_time',
    type='uint32',
    scale=1000,
    units='s',
    reference_fields=Map(
    map=[ReferenceField(
    name='duration_type',
    value='repeat_until_time',
    def_num=1,
    raw_value=7,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='repeat_distance',
    type='uint32',
    scale=100,
    units='m',
    reference_fields=Map(
    map=[ReferenceField(
    name='duration_type',
    value='repeat_until_distance',
    def_num=1,
    raw_value=8,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='repeat_calories',
    type='uint32',
    units='calories',
    reference_fields=Map(
    map=[ReferenceField(
    name='duration_type',
    value='repeat_until_calories',
    def_num=1,
    raw_value=9,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='repeat_hr',
    type='workout_hr',
    units='% or bpm',
    reference_fields=Map(
    map=[ReferenceField(
    name='duration_type',
    value='repeat_until_hr_less_than',
    def_num=1,
    raw_value=10,
), ReferenceField(
    name='duration_type',
    value='repeat_until_hr_greater_than',
    def_num=1,
    raw_value=11,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='repeat_power',
    type='workout_power',
    units='% or watts',
    reference_fields=Map(
    map=[ReferenceField(
    name='duration_type',
    value='repeat_until_power_less_than',
    def_num=1,
    raw_value=12,
), ReferenceField(
    name='duration_type',
    value='repeat_until_power_greater_than',
    def_num=1,
    raw_value=13,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='target_stroke_type',
    type='swim_stroke',
    reference_fields=Map(
    map=[ReferenceField(
    name='target_type',
    value='swim_stroke',
    def_num=3,
    raw_value=11,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 5: Field(
    name='custom_target_value_low',
    type='uint32',
    def_num=5,
    subfields=Map(
    map=[SubField(
    name='custom_target_speed_low',
    type='uint32',
    scale=1000,
    units='m/s',
    reference_fields=Map(
    map=[ReferenceField(
    name='target_type',
    value='speed',
    def_num=3,
    raw_value=0,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='custom_target_heart_rate_low',
    type='workout_hr',
    units='% or bpm',
    reference_fields=Map(
    map=[ReferenceField(
    name='target_type',
    value='heart_rate',
    def_num=3,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='custom_target_cadence_low',
    type='uint32',
    units='rpm',
    reference_fields=Map(
    map=[ReferenceField(
    name='target_type',
    value='cadence',
    def_num=3,
    raw_value=3,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='custom_target_power_low',
    type='workout_power',
    units='% or watts',
    reference_fields=Map(
    map=[ReferenceField(
    name='target_type',
    value='power',
    def_num=3,
    raw_value=4,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 6: Field(
    name='custom_target_value_high',
    type='uint32',
    def_num=6,
    subfields=Map(
    map=[SubField(
    name='custom_target_speed_high',
    type='uint32',
    scale=1000,
    units='m/s',
    reference_fields=Map(
    map=[ReferenceField(
    name='target_type',
    value='speed',
    def_num=3,
    raw_value=0,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='custom_target_heart_rate_high',
    type='workout_hr',
    units='% or bpm',
    reference_fields=Map(
    map=[ReferenceField(
    name='target_type',
    value='heart_rate',
    def_num=3,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='custom_target_cadence_high',
    type='uint32',
    units='rpm',
    reference_fields=Map(
    map=[ReferenceField(
    name='target_type',
    value='cadence',
    def_num=3,
    raw_value=3,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='custom_target_power_high',
    type='workout_power',
    units='% or watts',
    reference_fields=Map(
    map=[ReferenceField(
    name='target_type',
    value='power',
    def_num=3,
    raw_value=4,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 7: Field(
    name='intensity',
    type='intensity',
    def_num=7,
), 8: Field(
    name='notes',
    type='string',
    def_num=8,
), 9: Field(
    name='equipment',
    type='workout_equipment',
    def_num=9,
), 10: Field(
    name='exercise_category',
    type='exercise_category',
    def_num=10,
), 11: Field(
    name='exercise_name',
    type='uint16',
    def_num=11,
), 12: Field(
    name='exercise_weight',
    type='uint16',
    def_num=12,
    scale=100,
    units='kg',
), 13: Field(
    name='weight_display_unit',
    type='fit_base_unit',
    def_num=13,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'schedule': Message(
    name='schedule',
    global_number=28,
    group_name='Schedule File Messages',
    fields=Map(
    map={0: Field(
    name='manufacturer',
    type='manufacturer',
    def_num=0,
    comment='Corresponds to file_id of scheduled workout / course.',
), 1: Field(
    name='product',
    type='uint16',
    def_num=1,
    comment='Corresponds to file_id of scheduled workout / course.',
    subfields=Map(
    map=[SubField(
    name='favero_product',
    type='favero_product',
    reference_fields=Map(
    map=[ReferenceField(
    name='manufacturer',
    value='favero_electronics',
    def_num=0,
    raw_value=263,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='garmin_product',
    type='garmin_product',
    reference_fields=Map(
    map=[ReferenceField(
    name='manufacturer',
    value='garmin',
    def_num=0,
    raw_value=1,
), ReferenceField(
    name='manufacturer',
    value='dynastream',
    def_num=0,
    raw_value=15,
), ReferenceField(
    name='manufacturer',
    value='dynastream_oem',
    def_num=0,
    raw_value=13,
), ReferenceField(
    name='manufacturer',
    value='tacx',
    def_num=0,
    raw_value=89,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 2: Field(
    name='serial_number',
    type='uint32z',
    def_num=2,
    comment='Corresponds to file_id of scheduled workout / course.',
), 3: Field(
    name='time_created',
    type='date_time',
    def_num=3,
    comment='Corresponds to file_id of scheduled workout / course.',
), 4: Field(
    name='completed',
    type='bool',
    def_num=4,
    comment='TRUE if this activity has been started',
), 5: Field(
    name='type',
    type='schedule',
    def_num=5,
), 6: Field(
    name='scheduled_time',
    type='local_date_time',
    def_num=6,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'weight_scale': Message(
    name='weight_scale',
    global_number=30,
    group_name='Weight Scale File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
), 0: Field(
    name='weight',
    type='weight',
    def_num=0,
    scale=100,
    units='kg',
), 1: Field(
    name='percent_fat',
    type='uint16',
    def_num=1,
    scale=100,
    units='%',
), 2: Field(
    name='percent_hydration',
    type='uint16',
    def_num=2,
    scale=100,
    units='%',
), 3: Field(
    name='visceral_fat_mass',
    type='uint16',
    def_num=3,
    scale=100,
    units='kg',
), 4: Field(
    name='bone_mass',
    type='uint16',
    def_num=4,
    scale=100,
    units='kg',
), 5: Field(
    name='muscle_mass',
    type='uint16',
    def_num=5,
    scale=100,
    units='kg',
), 7: Field(
    name='basal_met',
    type='uint16',
    def_num=7,
    scale=4,
    units='kcal/day',
), 8: Field(
    name='physique_rating',
    type='uint8',
    def_num=8,
), 9: Field(
    name='active_met',
    type='uint16',
    def_num=9,
    scale=4,
    units='kcal/day',
    comment='~4kJ per kcal, 0.25 allows max 16384 kcal',
), 10: Field(
    name='metabolic_age',
    type='uint8',
    def_num=10,
    units='years',
), 11: Field(
    name='visceral_fat_rating',
    type='uint8',
    def_num=11,
), 12: Field(
    name='user_profile_index',
    type='message_index',
    def_num=12,
    comment='Associates this weight scale message to a user.  This corresponds to the index of the user profile message in the weight scale file.',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'course': Message(
    name='course',
    global_number=31,
    group_name='Course File Messages',
    fields=Map(
    map={4: Field(
    name='sport',
    type='sport',
    def_num=4,
), 5: Field(
    name='name',
    type='string',
    def_num=5,
), 6: Field(
    name='capabilities',
    type='course_capabilities',
    def_num=6,
), 7: Field(
    name='sub_sport',
    type='sub_sport',
    def_num=7,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'course_point': Message(
    name='course_point',
    global_number=32,
    group_name='Course File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 1: Field(
    name='timestamp',
    type='date_time',
    def_num=1,
), 2: Field(
    name='position_lat',
    type='sint32',
    def_num=2,
    units='semicircles',
), 3: Field(
    name='position_long',
    type='sint32',
    def_num=3,
    units='semicircles',
), 4: Field(
    name='distance',
    type='uint32',
    def_num=4,
    scale=100,
    units='m',
), 5: Field(
    name='type',
    type='course_point',
    def_num=5,
), 6: Field(
    name='name',
    type='string',
    def_num=6,
), 8: Field(
    name='favorite',
    type='bool',
    def_num=8,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'totals': Message(
    name='totals',
    global_number=33,
    group_name='Totals File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
), 0: Field(
    name='timer_time',
    type='uint32',
    def_num=0,
    units='s',
    comment='Excludes pauses',
), 1: Field(
    name='distance',
    type='uint32',
    def_num=1,
    units='m',
), 2: Field(
    name='calories',
    type='uint32',
    def_num=2,
    units='kcal',
), 3: Field(
    name='sport',
    type='sport',
    def_num=3,
), 4: Field(
    name='elapsed_time',
    type='uint32',
    def_num=4,
    units='s',
    comment='Includes pauses',
), 5: Field(
    name='sessions',
    type='uint16',
    def_num=5,
), 6: Field(
    name='active_time',
    type='uint32',
    def_num=6,
    units='s',
), 9: Field(
    name='sport_index',
    type='uint8',
    def_num=9,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'activity': Message(
    name='activity',
    global_number=34,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
), 0: Field(
    name='total_timer_time',
    type='uint32',
    def_num=0,
    scale=1000,
    units='s',
    comment='Exclude pauses',
), 1: Field(
    name='num_sessions',
    type='uint16',
    def_num=1,
), 2: Field(
    name='type',
    type='activity',
    def_num=2,
), 3: Field(
    name='event',
    type='event',
    def_num=3,
), 4: Field(
    name='event_type',
    type='event_type',
    def_num=4,
), 5: Field(
    name='local_timestamp',
    type='local_date_time',
    def_num=5,
    comment='timestamp epoch expressed in local time, used to convert activity timestamps to local time ',
), 6: Field(
    name='event_group',
    type='uint8',
    def_num=6,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'software': Message(
    name='software',
    global_number=35,
    group_name='Device File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 3: Field(
    name='version',
    type='uint16',
    def_num=3,
    scale=100,
), 5: Field(
    name='part_number',
    type='string',
    def_num=5,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'file_capabilities': Message(
    name='file_capabilities',
    global_number=37,
    group_name='Device File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='type',
    type='file',
    def_num=0,
), 1: Field(
    name='flags',
    type='file_flags',
    def_num=1,
), 2: Field(
    name='directory',
    type='string',
    def_num=2,
), 3: Field(
    name='max_count',
    type='uint16',
    def_num=3,
), 4: Field(
    name='max_size',
    type='uint32',
    def_num=4,
    units='bytes',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'mesg_capabilities': Message(
    name='mesg_capabilities',
    global_number=38,
    group_name='Device File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='file',
    type='file',
    def_num=0,
), 1: Field(
    name='mesg_num',
    type='mesg_num',
    def_num=1,
), 2: Field(
    name='count_type',
    type='mesg_count',
    def_num=2,
), 3: Field(
    name='count',
    type='uint16',
    def_num=3,
    subfields=Map(
    map=[SubField(
    name='num_per_file',
    type='uint16',
    reference_fields=Map(
    map=[ReferenceField(
    name='count_type',
    value='num_per_file',
    def_num=2,
    raw_value=0,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='max_per_file',
    type='uint16',
    reference_fields=Map(
    map=[ReferenceField(
    name='count_type',
    value='max_per_file',
    def_num=2,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='max_per_file_type',
    type='uint16',
    reference_fields=Map(
    map=[ReferenceField(
    name='count_type',
    value='max_per_file_type',
    def_num=2,
    raw_value=2,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'field_capabilities': Message(
    name='field_capabilities',
    global_number=39,
    group_name='Device File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='file',
    type='file',
    def_num=0,
), 1: Field(
    name='mesg_num',
    type='mesg_num',
    def_num=1,
), 2: Field(
    name='field_num',
    type='uint8',
    def_num=2,
), 3: Field(
    name='count',
    type='uint16',
    def_num=3,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'file_creator': Message(
    name='file_creator',
    global_number=49,
    group_name='Common Messages',
    fields=Map(
    map={0: Field(
    name='software_version',
    type='uint16',
    def_num=0,
), 1: Field(
    name='hardware_version',
    type='uint8',
    def_num=1,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'blood_pressure': Message(
    name='blood_pressure',
    global_number=51,
    group_name='Blood Pressure File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
), 0: Field(
    name='systolic_pressure',
    type='uint16',
    def_num=0,
    units='mmHg',
), 1: Field(
    name='diastolic_pressure',
    type='uint16',
    def_num=1,
    units='mmHg',
), 2: Field(
    name='mean_arterial_pressure',
    type='uint16',
    def_num=2,
    units='mmHg',
), 3: Field(
    name='map_3_sample_mean',
    type='uint16',
    def_num=3,
    units='mmHg',
), 4: Field(
    name='map_morning_values',
    type='uint16',
    def_num=4,
    units='mmHg',
), 5: Field(
    name='map_evening_values',
    type='uint16',
    def_num=5,
    units='mmHg',
), 6: Field(
    name='heart_rate',
    type='uint8',
    def_num=6,
    units='bpm',
), 7: Field(
    name='heart_rate_type',
    type='hr_type',
    def_num=7,
), 8: Field(
    name='status',
    type='bp_status',
    def_num=8,
), 9: Field(
    name='user_profile_index',
    type='message_index',
    def_num=9,
    comment='Associates this blood pressure message to a user.  This corresponds to the index of the user profile message in the blood pressure file.',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'speed_zone': Message(
    name='speed_zone',
    global_number=53,
    group_name='Sport Settings File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='high_value',
    type='uint16',
    def_num=0,
    scale=1000,
    units='m/s',
), 1: Field(
    name='name',
    type='string',
    def_num=1,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'monitoring': Message(
    name='monitoring',
    global_number=55,
    group_name='Monitoring File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Must align to logging interval, for example, time must be 00:00:00 for daily log.',
), 0: Field(
    name='device_index',
    type='device_index',
    def_num=0,
    comment='Associates this data to device_info message.  Not required for file with single device (sensor).',
), 1: Field(
    name='calories',
    type='uint16',
    def_num=1,
    units='kcal',
    comment='Accumulated total calories.  Maintained by MonitoringReader for each activity_type.  See SDK documentation',
), 2: Field(
    name='distance',
    type='uint32',
    def_num=2,
    scale=100,
    units='m',
    comment='Accumulated distance.  Maintained by MonitoringReader for each activity_type.  See SDK documentation.',
), 3: Field(
    name='cycles',
    type='uint32',
    def_num=3,
    scale=2,
    units='cycles',
    comment='Accumulated cycles.  Maintained by MonitoringReader for each activity_type.  See SDK documentation.',
    subfields=Map(
    map=[SubField(
    name='steps',
    type='uint32',
    units='steps',
    reference_fields=Map(
    map=[ReferenceField(
    name='activity_type',
    value='walking',
    def_num=5,
    raw_value=6,
), ReferenceField(
    name='activity_type',
    value='running',
    def_num=5,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='strokes',
    type='uint32',
    scale=2,
    units='strokes',
    reference_fields=Map(
    map=[ReferenceField(
    name='activity_type',
    value='cycling',
    def_num=5,
    raw_value=2,
), ReferenceField(
    name='activity_type',
    value='swimming',
    def_num=5,
    raw_value=5,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 4: Field(
    name='active_time',
    type='uint32',
    def_num=4,
    scale=1000,
    units='s',
), 5: Field(
    name='activity_type',
    type='activity_type',
    def_num=5,
), 6: Field(
    name='activity_subtype',
    type='activity_subtype',
    def_num=6,
), 7: Field(
    name='activity_level',
    type='activity_level',
    def_num=7,
), 8: Field(
    name='distance_16',
    type='uint16',
    def_num=8,
    units='100*m',
), 9: Field(
    name='cycles_16',
    type='uint16',
    def_num=9,
    units='2*cycles or steps',
), 10: Field(
    name='active_time_16',
    type='uint16',
    def_num=10,
    units='s',
), 11: Field(
    name='local_timestamp',
    type='local_date_time',
    def_num=11,
    comment='Must align to logging interval, for example, time must be 00:00:00 for daily log.',
), 12: Field(
    name='temperature',
    type='sint16',
    def_num=12,
    scale=100,
    units='C',
    comment='Avg temperature during the logging interval ended at timestamp',
), 14: Field(
    name='temperature_min',
    type='sint16',
    def_num=14,
    scale=100,
    units='C',
    comment='Min temperature during the logging interval ended at timestamp',
), 15: Field(
    name='temperature_max',
    type='sint16',
    def_num=15,
    scale=100,
    units='C',
    comment='Max temperature during the logging interval ended at timestamp',
), 16: Field(
    name='activity_time',
    type='uint16',
    def_num=16,
    units='minutes',
    comment='Indexed using minute_activity_level enum',
), 19: Field(
    name='active_calories',
    type='uint16',
    def_num=19,
    units='kcal',
), 24: Field(
    name='current_activity_type_intensity',
    type='byte',
    def_num=24,
    components=Map(
    map=[Component(
    name='activity_type',
    bits=5,
    accumulate=False,
    num=(5,),
    bit_offset=0,
), Component(
    name='intensity',
    bits=3,
    accumulate=False,
    num=(28,),
    bit_offset=5,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    comment='Indicates single type / intensity for duration since last monitoring message.',
), 25: Field(
    name='timestamp_min_8',
    type='uint8',
    def_num=25,
    units='min',
), 26: Field(
    name='timestamp_16',
    type='uint16',
    def_num=26,
    units='s',
), 27: Field(
    name='heart_rate',
    type='uint8',
    def_num=27,
    units='bpm',
), 28: Field(
    name='intensity',
    type='uint8',
    def_num=28,
    scale=10,
), 29: Field(
    name='duration_min',
    type='uint16',
    def_num=29,
    units='min',
), 30: Field(
    name='duration',
    type='uint32',
    def_num=30,
    units='s',
), 31: Field(
    name='ascent',
    type='uint32',
    def_num=31,
    scale=1000,
    units='m',
), 32: Field(
    name='descent',
    type='uint32',
    def_num=32,
    scale=1000,
    units='m',
), 33: Field(
    name='moderate_activity_minutes',
    type='uint16',
    def_num=33,
    units='minutes',
), 34: Field(
    name='vigorous_activity_minutes',
    type='uint16',
    def_num=34,
    units='minutes',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'training_file': Message(
    name='training_file',
    global_number=72,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
), 0: Field(
    name='type',
    type='file',
    def_num=0,
), 1: Field(
    name='manufacturer',
    type='manufacturer',
    def_num=1,
), 2: Field(
    name='product',
    type='uint16',
    def_num=2,
    subfields=Map(
    map=[SubField(
    name='favero_product',
    type='favero_product',
    reference_fields=Map(
    map=[ReferenceField(
    name='manufacturer',
    value='favero_electronics',
    def_num=1,
    raw_value=263,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='garmin_product',
    type='garmin_product',
    reference_fields=Map(
    map=[ReferenceField(
    name='manufacturer',
    value='garmin',
    def_num=1,
    raw_value=1,
), ReferenceField(
    name='manufacturer',
    value='dynastream',
    def_num=1,
    raw_value=15,
), ReferenceField(
    name='manufacturer',
    value='dynastream_oem',
    def_num=1,
    raw_value=13,
), ReferenceField(
    name='manufacturer',
    value='tacx',
    def_num=1,
    raw_value=89,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 3: Field(
    name='serial_number',
    type='uint32z',
    def_num=3,
), 4: Field(
    name='time_created',
    type='date_time',
    def_num=4,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
    comment='Corresponds to file_id of workout or course.',
), 'hrv': Message(
    name='hrv',
    global_number=78,
    group_name='Other Messages',
    fields=Map(
    map={0: Field(
    name='time',
    type='uint16',
    def_num=0,
    scale=1000,
    units='s',
    comment='Time between beats',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
    comment='Heart rate variability',
), 'ant_rx': Message(
    name='ant_rx',
    global_number=80,
    group_name='Other Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
), 0: Field(
    name='fractional_timestamp',
    type='uint16',
    def_num=0,
    scale=32768,
    units='s',
), 1: Field(
    name='mesg_id',
    type='byte',
    def_num=1,
), 2: Field(
    name='mesg_data',
    type='byte',
    def_num=2,
    components=Map(
    map=[Component(
    name='channel_number',
    bits=8,
    accumulate=False,
    num=(3,),
    bit_offset=0,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=8,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=16,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=24,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=32,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=40,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=48,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=56,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=64,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
), 3: Field(
    name='channel_number',
    type='uint8',
    def_num=3,
), 4: Field(
    name='data',
    type='byte',
    def_num=4,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'ant_tx': Message(
    name='ant_tx',
    global_number=81,
    group_name='Other Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
), 0: Field(
    name='fractional_timestamp',
    type='uint16',
    def_num=0,
    scale=32768,
    units='s',
), 1: Field(
    name='mesg_id',
    type='byte',
    def_num=1,
), 2: Field(
    name='mesg_data',
    type='byte',
    def_num=2,
    components=Map(
    map=[Component(
    name='channel_number',
    bits=8,
    accumulate=False,
    num=(3,),
    bit_offset=0,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=8,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=16,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=24,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=32,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=40,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=48,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=56,
), Component(
    name='data',
    bits=8,
    accumulate=False,
    num=(4,),
    bit_offset=64,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
), 3: Field(
    name='channel_number',
    type='uint8',
    def_num=3,
), 4: Field(
    name='data',
    type='byte',
    def_num=4,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'ant_channel_id': Message(
    name='ant_channel_id',
    global_number=82,
    group_name='Other Messages',
    fields=Map(
    map={0: Field(
    name='channel_number',
    type='uint8',
    def_num=0,
), 1: Field(
    name='device_type',
    type='uint8z',
    def_num=1,
), 2: Field(
    name='device_number',
    type='uint16z',
    def_num=2,
), 3: Field(
    name='transmission_type',
    type='uint8z',
    def_num=3,
), 4: Field(
    name='device_index',
    type='device_index',
    def_num=4,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'length': Message(
    name='length',
    global_number=101,
    group_name='Activity File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
), 0: Field(
    name='event',
    type='event',
    def_num=0,
), 1: Field(
    name='event_type',
    type='event_type',
    def_num=1,
), 2: Field(
    name='start_time',
    type='date_time',
    def_num=2,
), 3: Field(
    name='total_elapsed_time',
    type='uint32',
    def_num=3,
    scale=1000,
    units='s',
), 4: Field(
    name='total_timer_time',
    type='uint32',
    def_num=4,
    scale=1000,
    units='s',
), 5: Field(
    name='total_strokes',
    type='uint16',
    def_num=5,
    units='strokes',
), 6: Field(
    name='avg_speed',
    type='uint16',
    def_num=6,
    scale=1000,
    units='m/s',
), 7: Field(
    name='swim_stroke',
    type='swim_stroke',
    def_num=7,
    units='swim_stroke',
), 9: Field(
    name='avg_swimming_cadence',
    type='uint8',
    def_num=9,
    units='strokes/min',
), 10: Field(
    name='event_group',
    type='uint8',
    def_num=10,
), 11: Field(
    name='total_calories',
    type='uint16',
    def_num=11,
    units='kcal',
), 12: Field(
    name='length_type',
    type='length_type',
    def_num=12,
), 18: Field(
    name='player_score',
    type='uint16',
    def_num=18,
), 19: Field(
    name='opponent_score',
    type='uint16',
    def_num=19,
), 20: Field(
    name='stroke_count',
    type='uint16',
    def_num=20,
    units='counts',
    comment='stroke_type enum used as the index',
), 21: Field(
    name='zone_count',
    type='uint16',
    def_num=21,
    units='counts',
    comment='zone number used as the index',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'monitoring_info': Message(
    name='monitoring_info',
    global_number=103,
    group_name='Monitoring File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
), 0: Field(
    name='local_timestamp',
    type='local_date_time',
    def_num=0,
    units='s',
    comment='Use to convert activity timestamps to local time if device does not support time zone and daylight savings time correction.',
), 1: Field(
    name='activity_type',
    type='activity_type',
    def_num=1,
), 3: Field(
    name='cycles_to_distance',
    type='uint16',
    def_num=3,
    scale=5000,
    units='m/cycle',
    comment='Indexed by activity_type',
), 4: Field(
    name='cycles_to_calories',
    type='uint16',
    def_num=4,
    scale=5000,
    units='kcal/cycle',
    comment='Indexed by activity_type',
), 5: Field(
    name='resting_metabolic_rate',
    type='uint16',
    def_num=5,
    units='kcal/day',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'slave_device': Message(
    name='slave_device',
    global_number=106,
    group_name='Device File Messages',
    fields=Map(
    map={0: Field(
    name='manufacturer',
    type='manufacturer',
    def_num=0,
), 1: Field(
    name='product',
    type='uint16',
    def_num=1,
    subfields=Map(
    map=[SubField(
    name='favero_product',
    type='favero_product',
    reference_fields=Map(
    map=[ReferenceField(
    name='manufacturer',
    value='favero_electronics',
    def_num=0,
    raw_value=263,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='garmin_product',
    type='garmin_product',
    reference_fields=Map(
    map=[ReferenceField(
    name='manufacturer',
    value='garmin',
    def_num=0,
    raw_value=1,
), ReferenceField(
    name='manufacturer',
    value='dynastream',
    def_num=0,
    raw_value=15,
), ReferenceField(
    name='manufacturer',
    value='dynastream_oem',
    def_num=0,
    raw_value=13,
), ReferenceField(
    name='manufacturer',
    value='tacx',
    def_num=0,
    raw_value=89,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'connectivity': Message(
    name='connectivity',
    global_number=127,
    group_name='Settings File Messages',
    fields=Map(
    map={0: Field(
    name='bluetooth_enabled',
    type='bool',
    def_num=0,
    comment='Use Bluetooth for connectivity features',
), 1: Field(
    name='bluetooth_le_enabled',
    type='bool',
    def_num=1,
    comment='Use Bluetooth Low Energy for connectivity features',
), 2: Field(
    name='ant_enabled',
    type='bool',
    def_num=2,
    comment='Use ANT for connectivity features',
), 3: Field(
    name='name',
    type='string',
    def_num=3,
), 4: Field(
    name='live_tracking_enabled',
    type='bool',
    def_num=4,
), 5: Field(
    name='weather_conditions_enabled',
    type='bool',
    def_num=5,
), 6: Field(
    name='weather_alerts_enabled',
    type='bool',
    def_num=6,
), 7: Field(
    name='auto_activity_upload_enabled',
    type='bool',
    def_num=7,
), 8: Field(
    name='course_download_enabled',
    type='bool',
    def_num=8,
), 9: Field(
    name='workout_download_enabled',
    type='bool',
    def_num=9,
), 10: Field(
    name='gps_ephemeris_download_enabled',
    type='bool',
    def_num=10,
), 11: Field(
    name='incident_detection_enabled',
    type='bool',
    def_num=11,
), 12: Field(
    name='grouptrack_enabled',
    type='bool',
    def_num=12,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'weather_conditions': Message(
    name='weather_conditions',
    global_number=128,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    comment='time of update for current conditions, else forecast time',
), 0: Field(
    name='weather_report',
    type='weather_report',
    def_num=0,
    comment='Current or forecast',
), 1: Field(
    name='temperature',
    type='sint8',
    def_num=1,
    units='C',
), 2: Field(
    name='condition',
    type='weather_status',
    def_num=2,
    comment='Corresponds to GSC Response weatherIcon field',
), 3: Field(
    name='wind_direction',
    type='uint16',
    def_num=3,
    units='degrees',
), 4: Field(
    name='wind_speed',
    type='uint16',
    def_num=4,
    scale=1000,
    units='m/s',
), 5: Field(
    name='precipitation_probability',
    type='uint8',
    def_num=5,
    comment='range 0-100',
), 6: Field(
    name='temperature_feels_like',
    type='sint8',
    def_num=6,
    units='C',
    comment='Heat Index if  GCS heatIdx above or equal to 90F or wind chill if GCS windChill below or equal to 32F',
), 7: Field(
    name='relative_humidity',
    type='uint8',
    def_num=7,
), 8: Field(
    name='location',
    type='string',
    def_num=8,
    comment='string corresponding to GCS response location string',
), 9: Field(
    name='observed_at_time',
    type='date_time',
    def_num=9,
), 10: Field(
    name='observed_location_lat',
    type='sint32',
    def_num=10,
    units='semicircles',
), 11: Field(
    name='observed_location_long',
    type='sint32',
    def_num=11,
    units='semicircles',
), 12: Field(
    name='day_of_week',
    type='day_of_week',
    def_num=12,
), 13: Field(
    name='high_temperature',
    type='sint8',
    def_num=13,
    units='C',
), 14: Field(
    name='low_temperature',
    type='sint8',
    def_num=14,
    units='C',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'weather_alert': Message(
    name='weather_alert',
    global_number=129,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
), 0: Field(
    name='report_id',
    type='string',
    def_num=0,
    comment='Unique identifier from GCS report ID string, length is 12',
), 1: Field(
    name='issue_time',
    type='date_time',
    def_num=1,
    comment='Time alert was issued',
), 2: Field(
    name='expire_time',
    type='date_time',
    def_num=2,
    comment='Time alert expires',
), 3: Field(
    name='severity',
    type='weather_severity',
    def_num=3,
    comment='Warning, Watch, Advisory, Statement',
), 4: Field(
    name='type',
    type='weather_severe_type',
    def_num=4,
    comment='Tornado, Severe Thunderstorm, etc.',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'cadence_zone': Message(
    name='cadence_zone',
    global_number=131,
    group_name='Sport Settings File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='high_value',
    type='uint8',
    def_num=0,
    units='rpm',
), 1: Field(
    name='name',
    type='string',
    def_num=1,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'hr': Message(
    name='hr',
    global_number=132,
    group_name='Monitoring File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
), 0: Field(
    name='fractional_timestamp',
    type='uint16',
    def_num=0,
    scale=32768,
    units='s',
), 1: Field(
    name='time256',
    type='uint8',
    def_num=1,
    components=Map(
    map=[Component(
    name='fractional_timestamp',
    scale=256,
    units='s',
    bits=8,
    accumulate=False,
    num=(0,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=256,
    units='s',
), 6: Field(
    name='filtered_bpm',
    type='uint8',
    def_num=6,
    units='bpm',
), 9: Field(
    name='event_timestamp',
    type='uint32',
    def_num=9,
    scale=1024,
    units='s',
), 10: Field(
    name='event_timestamp_12',
    type='byte',
    def_num=10,
    components=Map(
    map=[Component(
    name='event_timestamp',
    scale=1024,
    units='s',
    bits=12,
    accumulate=True,
    num=(9,),
    bit_offset=0,
), Component(
    name='event_timestamp',
    scale=1024,
    units='s',
    bits=12,
    accumulate=True,
    num=(9,),
    bit_offset=12,
), Component(
    name='event_timestamp',
    scale=1024,
    units='s',
    bits=12,
    accumulate=True,
    num=(9,),
    bit_offset=24,
), Component(
    name='event_timestamp',
    scale=1024,
    units='s',
    bits=12,
    accumulate=True,
    num=(9,),
    bit_offset=36,
), Component(
    name='event_timestamp',
    scale=1024,
    units='s',
    bits=12,
    accumulate=True,
    num=(9,),
    bit_offset=48,
), Component(
    name='event_timestamp',
    scale=1024,
    units='s',
    bits=12,
    accumulate=True,
    num=(9,),
    bit_offset=60,
), Component(
    name='event_timestamp',
    scale=1024,
    units='s',
    bits=12,
    accumulate=True,
    num=(9,),
    bit_offset=72,
), Component(
    name='event_timestamp',
    scale=1024,
    units='s',
    bits=12,
    accumulate=True,
    num=(9,),
    bit_offset=84,
), Component(
    name='event_timestamp',
    scale=1024,
    units='s',
    bits=12,
    accumulate=True,
    num=(9,),
    bit_offset=96,
), Component(
    name='event_timestamp',
    scale=1024,
    units='s',
    bits=12,
    accumulate=True,
    num=(9,),
    bit_offset=108,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'segment_lap': Message(
    name='segment_lap',
    global_number=142,
    group_name='Segment File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Lap end time.',
), 0: Field(
    name='event',
    type='event',
    def_num=0,
), 1: Field(
    name='event_type',
    type='event_type',
    def_num=1,
), 2: Field(
    name='start_time',
    type='date_time',
    def_num=2,
), 3: Field(
    name='start_position_lat',
    type='sint32',
    def_num=3,
    units='semicircles',
), 4: Field(
    name='start_position_long',
    type='sint32',
    def_num=4,
    units='semicircles',
), 5: Field(
    name='end_position_lat',
    type='sint32',
    def_num=5,
    units='semicircles',
), 6: Field(
    name='end_position_long',
    type='sint32',
    def_num=6,
    units='semicircles',
), 7: Field(
    name='total_elapsed_time',
    type='uint32',
    def_num=7,
    scale=1000,
    units='s',
    comment='Time (includes pauses)',
), 8: Field(
    name='total_timer_time',
    type='uint32',
    def_num=8,
    scale=1000,
    units='s',
    comment='Timer Time (excludes pauses)',
), 9: Field(
    name='total_distance',
    type='uint32',
    def_num=9,
    scale=100,
    units='m',
), 10: Field(
    name='total_cycles',
    type='uint32',
    def_num=10,
    units='cycles',
    subfields=Map(
    map=[SubField(
    name='total_strokes',
    type='uint32',
    units='strokes',
    reference_fields=Map(
    map=[ReferenceField(
    name='sport',
    value='cycling',
    def_num=23,
    raw_value=2,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 11: Field(
    name='total_calories',
    type='uint16',
    def_num=11,
    units='kcal',
), 12: Field(
    name='total_fat_calories',
    type='uint16',
    def_num=12,
    units='kcal',
    comment='If New Leaf',
), 13: Field(
    name='avg_speed',
    type='uint16',
    def_num=13,
    scale=1000,
    units='m/s',
), 14: Field(
    name='max_speed',
    type='uint16',
    def_num=14,
    scale=1000,
    units='m/s',
), 15: Field(
    name='avg_heart_rate',
    type='uint8',
    def_num=15,
    units='bpm',
), 16: Field(
    name='max_heart_rate',
    type='uint8',
    def_num=16,
    units='bpm',
), 17: Field(
    name='avg_cadence',
    type='uint8',
    def_num=17,
    units='rpm',
    comment='total_cycles / total_timer_time if non_zero_avg_cadence otherwise total_cycles / total_elapsed_time',
), 18: Field(
    name='max_cadence',
    type='uint8',
    def_num=18,
    units='rpm',
), 19: Field(
    name='avg_power',
    type='uint16',
    def_num=19,
    units='watts',
    comment='total_power / total_timer_time if non_zero_avg_power otherwise total_power / total_elapsed_time',
), 20: Field(
    name='max_power',
    type='uint16',
    def_num=20,
    units='watts',
), 21: Field(
    name='total_ascent',
    type='uint16',
    def_num=21,
    units='m',
), 22: Field(
    name='total_descent',
    type='uint16',
    def_num=22,
    units='m',
), 23: Field(
    name='sport',
    type='sport',
    def_num=23,
), 24: Field(
    name='event_group',
    type='uint8',
    def_num=24,
), 25: Field(
    name='nec_lat',
    type='sint32',
    def_num=25,
    units='semicircles',
    comment='North east corner latitude.',
), 26: Field(
    name='nec_long',
    type='sint32',
    def_num=26,
    units='semicircles',
    comment='North east corner longitude.',
), 27: Field(
    name='swc_lat',
    type='sint32',
    def_num=27,
    units='semicircles',
    comment='South west corner latitude.',
), 28: Field(
    name='swc_long',
    type='sint32',
    def_num=28,
    units='semicircles',
    comment='South west corner latitude.',
), 29: Field(
    name='name',
    type='string',
    def_num=29,
), 30: Field(
    name='normalized_power',
    type='uint16',
    def_num=30,
    units='watts',
), 31: Field(
    name='left_right_balance',
    type='left_right_balance_100',
    def_num=31,
), 32: Field(
    name='sub_sport',
    type='sub_sport',
    def_num=32,
), 33: Field(
    name='total_work',
    type='uint32',
    def_num=33,
    units='J',
), 34: Field(
    name='avg_altitude',
    type='uint16',
    def_num=34,
    scale=5,
    offset=500,
    units='m',
), 35: Field(
    name='max_altitude',
    type='uint16',
    def_num=35,
    scale=5,
    offset=500,
    units='m',
), 36: Field(
    name='gps_accuracy',
    type='uint8',
    def_num=36,
    units='m',
), 37: Field(
    name='avg_grade',
    type='sint16',
    def_num=37,
    scale=100,
    units='%',
), 38: Field(
    name='avg_pos_grade',
    type='sint16',
    def_num=38,
    scale=100,
    units='%',
), 39: Field(
    name='avg_neg_grade',
    type='sint16',
    def_num=39,
    scale=100,
    units='%',
), 40: Field(
    name='max_pos_grade',
    type='sint16',
    def_num=40,
    scale=100,
    units='%',
), 41: Field(
    name='max_neg_grade',
    type='sint16',
    def_num=41,
    scale=100,
    units='%',
), 42: Field(
    name='avg_temperature',
    type='sint8',
    def_num=42,
    units='C',
), 43: Field(
    name='max_temperature',
    type='sint8',
    def_num=43,
    units='C',
), 44: Field(
    name='total_moving_time',
    type='uint32',
    def_num=44,
    scale=1000,
    units='s',
), 45: Field(
    name='avg_pos_vertical_speed',
    type='sint16',
    def_num=45,
    scale=1000,
    units='m/s',
), 46: Field(
    name='avg_neg_vertical_speed',
    type='sint16',
    def_num=46,
    scale=1000,
    units='m/s',
), 47: Field(
    name='max_pos_vertical_speed',
    type='sint16',
    def_num=47,
    scale=1000,
    units='m/s',
), 48: Field(
    name='max_neg_vertical_speed',
    type='sint16',
    def_num=48,
    scale=1000,
    units='m/s',
), 49: Field(
    name='time_in_hr_zone',
    type='uint32',
    def_num=49,
    scale=1000,
    units='s',
), 50: Field(
    name='time_in_speed_zone',
    type='uint32',
    def_num=50,
    scale=1000,
    units='s',
), 51: Field(
    name='time_in_cadence_zone',
    type='uint32',
    def_num=51,
    scale=1000,
    units='s',
), 52: Field(
    name='time_in_power_zone',
    type='uint32',
    def_num=52,
    scale=1000,
    units='s',
), 53: Field(
    name='repetition_num',
    type='uint16',
    def_num=53,
), 54: Field(
    name='min_altitude',
    type='uint16',
    def_num=54,
    scale=5,
    offset=500,
    units='m',
), 55: Field(
    name='min_heart_rate',
    type='uint8',
    def_num=55,
    units='bpm',
), 56: Field(
    name='active_time',
    type='uint32',
    def_num=56,
    scale=1000,
    units='s',
), 57: Field(
    name='wkt_step_index',
    type='message_index',
    def_num=57,
), 58: Field(
    name='sport_event',
    type='sport_event',
    def_num=58,
), 59: Field(
    name='avg_left_torque_effectiveness',
    type='uint8',
    def_num=59,
    scale=2,
    units='percent',
), 60: Field(
    name='avg_right_torque_effectiveness',
    type='uint8',
    def_num=60,
    scale=2,
    units='percent',
), 61: Field(
    name='avg_left_pedal_smoothness',
    type='uint8',
    def_num=61,
    scale=2,
    units='percent',
), 62: Field(
    name='avg_right_pedal_smoothness',
    type='uint8',
    def_num=62,
    scale=2,
    units='percent',
), 63: Field(
    name='avg_combined_pedal_smoothness',
    type='uint8',
    def_num=63,
    scale=2,
    units='percent',
), 64: Field(
    name='status',
    type='segment_lap_status',
    def_num=64,
), 65: Field(
    name='uuid',
    type='string',
    def_num=65,
), 66: Field(
    name='avg_fractional_cadence',
    type='uint8',
    def_num=66,
    scale=128,
    units='rpm',
    comment='fractional part of the avg_cadence',
), 67: Field(
    name='max_fractional_cadence',
    type='uint8',
    def_num=67,
    scale=128,
    units='rpm',
    comment='fractional part of the max_cadence',
), 68: Field(
    name='total_fractional_cycles',
    type='uint8',
    def_num=68,
    scale=128,
    units='cycles',
    comment='fractional part of the total_cycles',
), 69: Field(
    name='front_gear_shift_count',
    type='uint16',
    def_num=69,
), 70: Field(
    name='rear_gear_shift_count',
    type='uint16',
    def_num=70,
), 71: Field(
    name='time_standing',
    type='uint32',
    def_num=71,
    scale=1000,
    units='s',
    comment='Total time spent in the standing position',
), 72: Field(
    name='stand_count',
    type='uint16',
    def_num=72,
    comment='Number of transitions to the standing state',
), 73: Field(
    name='avg_left_pco',
    type='sint8',
    def_num=73,
    units='mm',
    comment='Average left platform center offset',
), 74: Field(
    name='avg_right_pco',
    type='sint8',
    def_num=74,
    units='mm',
    comment='Average right platform center offset',
), 75: Field(
    name='avg_left_power_phase',
    type='uint8',
    def_num=75,
    scale=0.7111111,
    units='degrees',
    comment='Average left power phase angles. Data value indexes defined by power_phase_type.',
), 76: Field(
    name='avg_left_power_phase_peak',
    type='uint8',
    def_num=76,
    scale=0.7111111,
    units='degrees',
    comment='Average left power phase peak angles. Data value indexes defined by power_phase_type.',
), 77: Field(
    name='avg_right_power_phase',
    type='uint8',
    def_num=77,
    scale=0.7111111,
    units='degrees',
    comment='Average right power phase angles. Data value indexes defined by power_phase_type.',
), 78: Field(
    name='avg_right_power_phase_peak',
    type='uint8',
    def_num=78,
    scale=0.7111111,
    units='degrees',
    comment='Average right power phase peak angles. Data value indexes defined by power_phase_type.',
), 79: Field(
    name='avg_power_position',
    type='uint16',
    def_num=79,
    units='watts',
    comment='Average power by position. Data value indexes defined by rider_position_type.',
), 80: Field(
    name='max_power_position',
    type='uint16',
    def_num=80,
    units='watts',
    comment='Maximum power by position. Data value indexes defined by rider_position_type.',
), 81: Field(
    name='avg_cadence_position',
    type='uint8',
    def_num=81,
    units='rpm',
    comment='Average cadence by position. Data value indexes defined by rider_position_type.',
), 82: Field(
    name='max_cadence_position',
    type='uint8',
    def_num=82,
    units='rpm',
    comment='Maximum cadence by position. Data value indexes defined by rider_position_type.',
), 83: Field(
    name='manufacturer',
    type='manufacturer',
    def_num=83,
    comment='Manufacturer that produced the segment',
), 84: Field(
    name='total_grit',
    type='float32',
    def_num=84,
    units='kGrit',
    comment='The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
), 85: Field(
    name='total_flow',
    type='float32',
    def_num=85,
    units='Flow',
    comment='The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
), 86: Field(
    name='avg_grit',
    type='float32',
    def_num=86,
    units='kGrit',
    comment='The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
), 87: Field(
    name='avg_flow',
    type='float32',
    def_num=87,
    units='Flow',
    comment='The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
), 89: Field(
    name='total_fractional_ascent',
    type='uint8',
    def_num=89,
    scale=100,
    units='m',
    comment='fractional part of total_ascent',
), 90: Field(
    name='total_fractional_descent',
    type='uint8',
    def_num=90,
    scale=100,
    units='m',
    comment='fractional part of total_descent',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'memo_glob': Message(
    name='memo_glob',
    global_number=145,
    group_name='Other Messages',
    fields=Map(
    map={250: Field(
    name='part_index',
    type='uint32',
    def_num=250,
    comment='Sequence number of memo blocks',
), 0: Field(
    name='memo',
    type='byte',
    def_num=0,
    comment='Block of utf8 bytes',
), 1: Field(
    name='message_number',
    type='uint16',
    def_num=1,
    comment='Allows relating glob to another mesg  If used only required for first part of each memo_glob',
), 2: Field(
    name='message_index',
    type='message_index',
    def_num=2,
    comment='Index of external mesg',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'segment_id': Message(
    name='segment_id',
    global_number=148,
    group_name='Segment File Messages',
    fields=Map(
    map={0: Field(
    name='name',
    type='string',
    def_num=0,
    comment='Friendly name assigned to segment',
), 1: Field(
    name='uuid',
    type='string',
    def_num=1,
    comment='UUID of the segment',
), 2: Field(
    name='sport',
    type='sport',
    def_num=2,
    comment='Sport associated with the segment',
), 3: Field(
    name='enabled',
    type='bool',
    def_num=3,
    comment='Segment enabled for evaluation',
), 4: Field(
    name='user_profile_primary_key',
    type='uint32',
    def_num=4,
    comment='Primary key of the user that created the segment',
), 5: Field(
    name='device_id',
    type='uint32',
    def_num=5,
    comment='ID of the device that created the segment',
), 6: Field(
    name='default_race_leader',
    type='uint8',
    def_num=6,
    comment='Index for the Leader Board entry selected as the default race participant',
), 7: Field(
    name='delete_status',
    type='segment_delete_status',
    def_num=7,
    comment='Indicates if any segments should be deleted',
), 8: Field(
    name='selection_type',
    type='segment_selection_type',
    def_num=8,
    comment='Indicates how the segment was selected to be sent to the device',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
    comment='Unique Identification data for a segment file',
), 'segment_leaderboard_entry': Message(
    name='segment_leaderboard_entry',
    global_number=149,
    group_name='Segment File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='name',
    type='string',
    def_num=0,
    comment='Friendly name assigned to leader',
), 1: Field(
    name='type',
    type='segment_leaderboard_type',
    def_num=1,
    comment='Leader classification',
), 2: Field(
    name='group_primary_key',
    type='uint32',
    def_num=2,
    comment='Primary user ID of this leader',
), 3: Field(
    name='activity_id',
    type='uint32',
    def_num=3,
    comment='ID of the activity associated with this leader time',
), 4: Field(
    name='segment_time',
    type='uint32',
    def_num=4,
    scale=1000,
    units='s',
    comment='Segment Time (includes pauses)',
), 5: Field(
    name='activity_id_string',
    type='string',
    def_num=5,
    comment='String version of the activity_id. 21 characters long, express in decimal',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
    comment='Unique Identification data for an individual segment leader within a segment file',
), 'segment_point': Message(
    name='segment_point',
    global_number=150,
    group_name='Segment File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 1: Field(
    name='position_lat',
    type='sint32',
    def_num=1,
    units='semicircles',
), 2: Field(
    name='position_long',
    type='sint32',
    def_num=2,
    units='semicircles',
), 3: Field(
    name='distance',
    type='uint32',
    def_num=3,
    scale=100,
    units='m',
    comment='Accumulated distance along the segment at the described point',
), 4: Field(
    name='altitude',
    type='uint16',
    def_num=4,
    scale=5,
    offset=500,
    units='m',
    comment='Accumulated altitude along the segment at the described point',
), 5: Field(
    name='leader_time',
    type='uint32',
    def_num=5,
    scale=1000,
    units='s',
    comment='Accumualted time each leader board member required to reach the described point. This value is zero for all leader board members at the starting point of the segment.',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
    comment='Navigation and race evaluation point for a segment decribing a point along the segment path and time it took each segment leader to reach that point',
), 'segment_file': Message(
    name='segment_file',
    global_number=151,
    group_name='Segment File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 1: Field(
    name='file_uuid',
    type='string',
    def_num=1,
    comment='UUID of the segment file',
), 3: Field(
    name='enabled',
    type='bool',
    def_num=3,
    comment='Enabled state of the segment file',
), 4: Field(
    name='user_profile_primary_key',
    type='uint32',
    def_num=4,
    comment='Primary key of the user that created the segment file',
), 7: Field(
    name='leader_type',
    type='segment_leaderboard_type',
    def_num=7,
    comment='Leader type of each leader in the segment file',
), 8: Field(
    name='leader_group_primary_key',
    type='uint32',
    def_num=8,
    comment='Group primary key of each leader in the segment file',
), 9: Field(
    name='leader_activity_id',
    type='uint32',
    def_num=9,
    comment='Activity ID of each leader in the segment file',
), 10: Field(
    name='leader_activity_id_string',
    type='string',
    def_num=10,
    comment='String version of the activity ID of each leader in the segment file. 21 characters long for each ID, express in decimal',
), 11: Field(
    name='default_race_leader',
    type='uint8',
    def_num=11,
    comment='Index for the Leader Board entry selected as the default race participant',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
    comment='Summary of the unique segment and leaderboard information associated with a segment file. This message is used to compile a segment list file describing all segment files on a device. The segment list file is used when refreshing the contents of a segment file with the latest available leaderboard information.',
), 'workout_session': Message(
    name='workout_session',
    global_number=158,
    group_name='Workout File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='sport',
    type='sport',
    def_num=0,
), 1: Field(
    name='sub_sport',
    type='sub_sport',
    def_num=1,
), 2: Field(
    name='num_valid_steps',
    type='uint16',
    def_num=2,
), 3: Field(
    name='first_step_index',
    type='uint16',
    def_num=3,
), 4: Field(
    name='pool_length',
    type='uint16',
    def_num=4,
    scale=100,
    units='m',
), 5: Field(
    name='pool_length_unit',
    type='display_measure',
    def_num=5,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'watchface_settings': Message(
    name='watchface_settings',
    global_number=159,
    group_name='Settings File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='mode',
    type='watchface_mode',
    def_num=0,
), 1: Field(
    name='layout',
    type='byte',
    def_num=1,
    subfields=Map(
    map=[SubField(
    name='digital_layout',
    type='digital_watchface_layout',
    reference_fields=Map(
    map=[ReferenceField(
    name='mode',
    value='digital',
    def_num=0,
    raw_value=0,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='analog_layout',
    type='analog_watchface_layout',
    reference_fields=Map(
    map=[ReferenceField(
    name='mode',
    value='analog',
    def_num=0,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'gps_metadata': Message(
    name='gps_metadata',
    global_number=160,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Whole second part of the timestamp.',
), 0: Field(
    name='timestamp_ms',
    type='uint16',
    def_num=0,
    units='ms',
    comment='Millisecond part of the timestamp.',
), 1: Field(
    name='position_lat',
    type='sint32',
    def_num=1,
    units='semicircles',
), 2: Field(
    name='position_long',
    type='sint32',
    def_num=2,
    units='semicircles',
), 3: Field(
    name='enhanced_altitude',
    type='uint32',
    def_num=3,
    scale=5,
    offset=500,
    units='m',
), 4: Field(
    name='enhanced_speed',
    type='uint32',
    def_num=4,
    scale=1000,
    units='m/s',
), 5: Field(
    name='heading',
    type='uint16',
    def_num=5,
    scale=100,
    units='degrees',
), 6: Field(
    name='utc_timestamp',
    type='date_time',
    def_num=6,
    units='s',
    comment='Used to correlate UTC to system time if the timestamp of the message is in system time.  This UTC time is derived from the GPS data.',
), 7: Field(
    name='velocity',
    type='sint16',
    def_num=7,
    scale=100,
    units='m/s',
    comment='velocity[0] is lon velocity.  Velocity[1] is lat velocity.  Velocity[2] is altitude velocity.',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'camera_event': Message(
    name='camera_event',
    global_number=161,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Whole second part of the timestamp.',
), 0: Field(
    name='timestamp_ms',
    type='uint16',
    def_num=0,
    units='ms',
    comment='Millisecond part of the timestamp.',
), 1: Field(
    name='camera_event_type',
    type='camera_event_type',
    def_num=1,
), 2: Field(
    name='camera_file_uuid',
    type='string',
    def_num=2,
), 3: Field(
    name='camera_orientation',
    type='camera_orientation_type',
    def_num=3,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'timestamp_correlation': Message(
    name='timestamp_correlation',
    global_number=162,
    group_name='Common Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Whole second part of UTC timestamp at the time the system timestamp was recorded.',
), 0: Field(
    name='fractional_timestamp',
    type='uint16',
    def_num=0,
    scale=32768,
    units='s',
    comment='Fractional part of the UTC timestamp at the time the system timestamp was recorded.',
), 1: Field(
    name='system_timestamp',
    type='date_time',
    def_num=1,
    units='s',
    comment='Whole second part of the system timestamp',
), 2: Field(
    name='fractional_system_timestamp',
    type='uint16',
    def_num=2,
    scale=32768,
    units='s',
    comment='Fractional part of the system timestamp',
), 3: Field(
    name='local_timestamp',
    type='local_date_time',
    def_num=3,
    units='s',
    comment='timestamp epoch expressed in local time used to convert timestamps to local time',
), 4: Field(
    name='timestamp_ms',
    type='uint16',
    def_num=4,
    units='ms',
    comment='Millisecond part of the UTC timestamp at the time the system timestamp was recorded.',
), 5: Field(
    name='system_timestamp_ms',
    type='uint16',
    def_num=5,
    units='ms',
    comment='Millisecond part of the system timestamp',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'gyroscope_data': Message(
    name='gyroscope_data',
    global_number=164,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Whole second part of the timestamp',
), 0: Field(
    name='timestamp_ms',
    type='uint16',
    def_num=0,
    units='ms',
    comment='Millisecond part of the timestamp.',
), 1: Field(
    name='sample_time_offset',
    type='uint16',
    def_num=1,
    units='ms',
    comment='Each time in the array describes the time at which the gyro sample with the corrosponding index was taken. Limited to 30 samples in each message. The samples may span across seconds. Array size must match the number of samples in gyro_x and gyro_y and gyro_z',
), 2: Field(
    name='gyro_x',
    type='uint16',
    def_num=2,
    units='counts',
    comment='These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
), 3: Field(
    name='gyro_y',
    type='uint16',
    def_num=3,
    units='counts',
    comment='These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
), 4: Field(
    name='gyro_z',
    type='uint16',
    def_num=4,
    units='counts',
    comment='These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
), 5: Field(
    name='calibrated_gyro_x',
    type='float32',
    def_num=5,
    units='deg/s',
    comment='Calibrated gyro reading',
), 6: Field(
    name='calibrated_gyro_y',
    type='float32',
    def_num=6,
    units='deg/s',
    comment='Calibrated gyro reading',
), 7: Field(
    name='calibrated_gyro_z',
    type='float32',
    def_num=7,
    units='deg/s',
    comment='Calibrated gyro reading',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'accelerometer_data': Message(
    name='accelerometer_data',
    global_number=165,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Whole second part of the timestamp',
), 0: Field(
    name='timestamp_ms',
    type='uint16',
    def_num=0,
    units='ms',
    comment='Millisecond part of the timestamp.',
), 1: Field(
    name='sample_time_offset',
    type='uint16',
    def_num=1,
    units='ms',
    comment='Each time in the array describes the time at which the accelerometer sample with the corrosponding index was taken. Limited to 30 samples in each message. The samples may span across seconds. Array size must match the number of samples in accel_x and accel_y and accel_z',
), 2: Field(
    name='accel_x',
    type='uint16',
    def_num=2,
    units='counts',
    comment='These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
), 3: Field(
    name='accel_y',
    type='uint16',
    def_num=3,
    units='counts',
    comment='These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
), 4: Field(
    name='accel_z',
    type='uint16',
    def_num=4,
    units='counts',
    comment='These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
), 5: Field(
    name='calibrated_accel_x',
    type='float32',
    def_num=5,
    units='g',
    comment='Calibrated accel reading',
), 6: Field(
    name='calibrated_accel_y',
    type='float32',
    def_num=6,
    units='g',
    comment='Calibrated accel reading',
), 7: Field(
    name='calibrated_accel_z',
    type='float32',
    def_num=7,
    units='g',
    comment='Calibrated accel reading',
), 8: Field(
    name='compressed_calibrated_accel_x',
    type='sint16',
    def_num=8,
    units='mG',
    comment='Calibrated accel reading',
), 9: Field(
    name='compressed_calibrated_accel_y',
    type='sint16',
    def_num=9,
    units='mG',
    comment='Calibrated accel reading',
), 10: Field(
    name='compressed_calibrated_accel_z',
    type='sint16',
    def_num=10,
    units='mG',
    comment='Calibrated accel reading',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'three_d_sensor_calibration': Message(
    name='three_d_sensor_calibration',
    global_number=167,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Whole second part of the timestamp',
), 0: Field(
    name='sensor_type',
    type='sensor_type',
    def_num=0,
    comment='Indicates which sensor the calibration is for',
), 1: Field(
    name='calibration_factor',
    type='uint32',
    def_num=1,
    comment='Calibration factor used to convert from raw ADC value to degrees, g,  etc.',
    subfields=Map(
    map=[SubField(
    name='accel_cal_factor',
    type='uint32',
    units='g',
    comment='Accelerometer calibration factor',
    reference_fields=Map(
    map=[ReferenceField(
    name='sensor_type',
    value='accelerometer',
    def_num=0,
    raw_value=0,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='gyro_cal_factor',
    type='uint32',
    units='deg/s',
    comment='Gyro calibration factor',
    reference_fields=Map(
    map=[ReferenceField(
    name='sensor_type',
    value='gyroscope',
    def_num=0,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 2: Field(
    name='calibration_divisor',
    type='uint32',
    def_num=2,
    units='counts',
    comment='Calibration factor divisor',
), 3: Field(
    name='level_shift',
    type='uint32',
    def_num=3,
    comment='Level shift value used to shift the ADC value back into range',
), 4: Field(
    name='offset_cal',
    type='sint32',
    def_num=4,
    comment='Internal calibration factors, one for each: xy, yx, zx',
), 5: Field(
    name='orientation_matrix',
    type='sint32',
    def_num=5,
    scale=65535,
    comment='3 x 3 rotation matrix (row major)',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'video_frame': Message(
    name='video_frame',
    global_number=169,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Whole second part of the timestamp',
), 0: Field(
    name='timestamp_ms',
    type='uint16',
    def_num=0,
    units='ms',
    comment='Millisecond part of the timestamp.',
), 1: Field(
    name='frame_number',
    type='uint32',
    def_num=1,
    comment='Number of the frame that the timestamp and timestamp_ms correlate to',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'obdii_data': Message(
    name='obdii_data',
    global_number=174,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Timestamp message was output',
), 0: Field(
    name='timestamp_ms',
    type='uint16',
    def_num=0,
    units='ms',
    comment='Fractional part of timestamp, added to timestamp',
), 1: Field(
    name='time_offset',
    type='uint16',
    def_num=1,
    units='ms',
    comment='Offset of PID reading [i] from start_timestamp+start_timestamp_ms. Readings may span accross seconds.',
), 2: Field(
    name='pid',
    type='byte',
    def_num=2,
    comment='Parameter ID',
), 3: Field(
    name='raw_data',
    type='byte',
    def_num=3,
    comment='Raw parameter data',
), 4: Field(
    name='pid_data_size',
    type='uint8',
    def_num=4,
    comment='Optional, data size of PID[i].  If not specified refer to SAE J1979.',
), 5: Field(
    name='system_time',
    type='uint32',
    def_num=5,
    comment='System time associated with sample expressed in ms, can be used instead of time_offset.  There will be a system_time value for each raw_data element.  For multibyte pids the system_time is repeated.',
), 6: Field(
    name='start_timestamp',
    type='date_time',
    def_num=6,
    comment='Timestamp of first sample recorded in the message.  Used with time_offset to generate time of each sample',
), 7: Field(
    name='start_timestamp_ms',
    type='uint16',
    def_num=7,
    units='ms',
    comment='Fractional part of start_timestamp',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'nmea_sentence': Message(
    name='nmea_sentence',
    global_number=177,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Timestamp message was output',
), 0: Field(
    name='timestamp_ms',
    type='uint16',
    def_num=0,
    units='ms',
    comment='Fractional part of timestamp, added to timestamp',
), 1: Field(
    name='sentence',
    type='string',
    def_num=1,
    comment='NMEA sentence',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'aviation_attitude': Message(
    name='aviation_attitude',
    global_number=178,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Timestamp message was output',
), 0: Field(
    name='timestamp_ms',
    type='uint16',
    def_num=0,
    units='ms',
    comment='Fractional part of timestamp, added to timestamp',
), 1: Field(
    name='system_time',
    type='uint32',
    def_num=1,
    units='ms',
    comment='System time associated with sample expressed in ms.',
), 2: Field(
    name='pitch',
    type='sint16',
    def_num=2,
    scale=10430.38,
    units='radians',
    comment='Range -PI/2 to +PI/2',
), 3: Field(
    name='roll',
    type='sint16',
    def_num=3,
    scale=10430.38,
    units='radians',
    comment='Range -PI to +PI',
), 4: Field(
    name='accel_lateral',
    type='sint16',
    def_num=4,
    scale=100,
    units='m/s^2',
    comment='Range -78.4 to +78.4 (-8 Gs to 8 Gs)',
), 5: Field(
    name='accel_normal',
    type='sint16',
    def_num=5,
    scale=100,
    units='m/s^2',
    comment='Range -78.4 to +78.4 (-8 Gs to 8 Gs)',
), 6: Field(
    name='turn_rate',
    type='sint16',
    def_num=6,
    scale=1024,
    units='radians/second',
    comment='Range -8.727 to +8.727 (-500 degs/sec to +500 degs/sec)',
), 7: Field(
    name='stage',
    type='attitude_stage',
    def_num=7,
), 8: Field(
    name='attitude_stage_complete',
    type='uint8',
    def_num=8,
    units='%',
    comment='The percent complete of the current attitude stage.  Set to 0 for attitude stages 0, 1 and 2 and to 100 for attitude stage 3 by AHRS modules that do not support it.  Range - 100',
), 9: Field(
    name='track',
    type='uint16',
    def_num=9,
    scale=10430.38,
    units='radians',
    comment='Track Angle/Heading Range 0 - 2pi',
), 10: Field(
    name='validity',
    type='attitude_validity',
    def_num=10,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'video': Message(
    name='video',
    global_number=184,
    group_name='Activity File Messages',
    fields=Map(
    map={0: Field(
    name='url',
    type='string',
    def_num=0,
), 1: Field(
    name='hosting_provider',
    type='string',
    def_num=1,
), 2: Field(
    name='duration',
    type='uint32',
    def_num=2,
    units='ms',
    comment='Playback time of video',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'video_title': Message(
    name='video_title',
    global_number=185,
    group_name='Activity File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
    comment='Long titles will be split into multiple parts',
), 0: Field(
    name='message_count',
    type='uint16',
    def_num=0,
    comment='Total number of title parts',
), 1: Field(
    name='text',
    type='string',
    def_num=1,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'video_description': Message(
    name='video_description',
    global_number=186,
    group_name='Activity File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
    comment='Long descriptions will be split into multiple parts',
), 0: Field(
    name='message_count',
    type='uint16',
    def_num=0,
    comment='Total number of description parts',
), 1: Field(
    name='text',
    type='string',
    def_num=1,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'video_clip': Message(
    name='video_clip',
    global_number=187,
    group_name='Activity File Messages',
    fields=Map(
    map={0: Field(
    name='clip_number',
    type='uint16',
    def_num=0,
), 1: Field(
    name='start_timestamp',
    type='date_time',
    def_num=1,
), 2: Field(
    name='start_timestamp_ms',
    type='uint16',
    def_num=2,
), 3: Field(
    name='end_timestamp',
    type='date_time',
    def_num=3,
), 4: Field(
    name='end_timestamp_ms',
    type='uint16',
    def_num=4,
), 6: Field(
    name='clip_start',
    type='uint32',
    def_num=6,
    units='ms',
    comment='Start of clip in video time',
), 7: Field(
    name='clip_end',
    type='uint32',
    def_num=7,
    units='ms',
    comment='End of clip in video time',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'ohr_settings': Message(
    name='ohr_settings',
    global_number=188,
    group_name='Settings File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
), 0: Field(
    name='enabled',
    type='switch',
    def_num=0,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'exd_screen_configuration': Message(
    name='exd_screen_configuration',
    global_number=200,
    group_name='Other Messages',
    fields=Map(
    map={0: Field(
    name='screen_index',
    type='uint8',
    def_num=0,
), 1: Field(
    name='field_count',
    type='uint8',
    def_num=1,
    comment='number of fields in screen',
), 2: Field(
    name='layout',
    type='exd_layout',
    def_num=2,
), 3: Field(
    name='screen_enabled',
    type='bool',
    def_num=3,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'exd_data_field_configuration': Message(
    name='exd_data_field_configuration',
    global_number=201,
    group_name='Other Messages',
    fields=Map(
    map={0: Field(
    name='screen_index',
    type='uint8',
    def_num=0,
), 1: Field(
    name='concept_field',
    type='byte',
    def_num=1,
    components=Map(
    map=[Component(
    name='field_id',
    bits=4,
    accumulate=False,
    num=(2,),
    bit_offset=0,
), Component(
    name='concept_count',
    bits=4,
    accumulate=False,
    num=(3,),
    bit_offset=4,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
), 2: Field(
    name='field_id',
    type='uint8',
    def_num=2,
), 3: Field(
    name='concept_count',
    type='uint8',
    def_num=3,
), 4: Field(
    name='display_type',
    type='exd_display_type',
    def_num=4,
), 5: Field(
    name='title',
    type='string',
    def_num=5,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'exd_data_concept_configuration': Message(
    name='exd_data_concept_configuration',
    global_number=202,
    group_name='Other Messages',
    fields=Map(
    map={0: Field(
    name='screen_index',
    type='uint8',
    def_num=0,
), 1: Field(
    name='concept_field',
    type='byte',
    def_num=1,
    components=Map(
    map=[Component(
    name='field_id',
    bits=4,
    accumulate=False,
    num=(2,),
    bit_offset=0,
), Component(
    name='concept_index',
    bits=4,
    accumulate=False,
    num=(3,),
    bit_offset=4,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
), 2: Field(
    name='field_id',
    type='uint8',
    def_num=2,
), 3: Field(
    name='concept_index',
    type='uint8',
    def_num=3,
), 4: Field(
    name='data_page',
    type='uint8',
    def_num=4,
), 5: Field(
    name='concept_key',
    type='uint8',
    def_num=5,
), 6: Field(
    name='scaling',
    type='uint8',
    def_num=6,
), 8: Field(
    name='data_units',
    type='exd_data_units',
    def_num=8,
), 9: Field(
    name='qualifier',
    type='exd_qualifiers',
    def_num=9,
), 10: Field(
    name='descriptor',
    type='exd_descriptors',
    def_num=10,
), 11: Field(
    name='is_signed',
    type='bool',
    def_num=11,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'field_description': Message(
    name='field_description',
    global_number=206,
    group_name='Activity File Messages',
    fields=Map(
    map={0: Field(
    name='developer_data_index',
    type='uint8',
    def_num=0,
), 1: Field(
    name='field_definition_number',
    type='uint8',
    def_num=1,
), 2: Field(
    name='fit_base_type_id',
    type='fit_base_type',
    def_num=2,
), 3: Field(
    name='field_name',
    type='string',
    def_num=3,
), 4: Field(
    name='array',
    type='uint8',
    def_num=4,
), 5: Field(
    name='components',
    type='string',
    def_num=5,
), 6: Field(
    name='scale',
    type='uint8',
    def_num=6,
), 7: Field(
    name='offset',
    type='sint8',
    def_num=7,
), 8: Field(
    name='units',
    type='string',
    def_num=8,
), 9: Field(
    name='bits',
    type='string',
    def_num=9,
), 10: Field(
    name='accumulate',
    type='string',
    def_num=10,
), 13: Field(
    name='fit_base_unit_id',
    type='fit_base_unit',
    def_num=13,
), 14: Field(
    name='native_mesg_num',
    type='mesg_num',
    def_num=14,
), 15: Field(
    name='native_field_num',
    type='uint8',
    def_num=15,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
    comment='Must be logged before developer field is used',
), 'developer_data_id': Message(
    name='developer_data_id',
    global_number=207,
    group_name='Activity File Messages',
    fields=Map(
    map={0: Field(
    name='developer_id',
    type='byte',
    def_num=0,
), 1: Field(
    name='application_id',
    type='byte',
    def_num=1,
), 2: Field(
    name='manufacturer_id',
    type='manufacturer',
    def_num=2,
), 3: Field(
    name='developer_data_index',
    type='uint8',
    def_num=3,
), 4: Field(
    name='application_version',
    type='uint32',
    def_num=4,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
    comment='Must be logged before field description',
), 'magnetometer_data': Message(
    name='magnetometer_data',
    global_number=208,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Whole second part of the timestamp',
), 0: Field(
    name='timestamp_ms',
    type='uint16',
    def_num=0,
    units='ms',
    comment='Millisecond part of the timestamp.',
), 1: Field(
    name='sample_time_offset',
    type='uint16',
    def_num=1,
    units='ms',
    comment='Each time in the array describes the time at which the compass sample with the corrosponding index was taken. Limited to 30 samples in each message. The samples may span across seconds. Array size must match the number of samples in cmps_x and cmps_y and cmps_z',
), 2: Field(
    name='mag_x',
    type='uint16',
    def_num=2,
    units='counts',
    comment='These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
), 3: Field(
    name='mag_y',
    type='uint16',
    def_num=3,
    units='counts',
    comment='These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
), 4: Field(
    name='mag_z',
    type='uint16',
    def_num=4,
    units='counts',
    comment='These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
), 5: Field(
    name='calibrated_mag_x',
    type='float32',
    def_num=5,
    units='G',
    comment='Calibrated Magnetometer reading',
), 6: Field(
    name='calibrated_mag_y',
    type='float32',
    def_num=6,
    units='G',
    comment='Calibrated Magnetometer reading',
), 7: Field(
    name='calibrated_mag_z',
    type='float32',
    def_num=7,
    units='G',
    comment='Calibrated Magnetometer reading',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'barometer_data': Message(
    name='barometer_data',
    global_number=209,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Whole second part of the timestamp',
), 0: Field(
    name='timestamp_ms',
    type='uint16',
    def_num=0,
    units='ms',
    comment='Millisecond part of the timestamp.',
), 1: Field(
    name='sample_time_offset',
    type='uint16',
    def_num=1,
    units='ms',
    comment='Each time in the array describes the time at which the barometer sample with the corrosponding index was taken. The samples may span across seconds. Array size must match the number of samples in baro_cal',
), 2: Field(
    name='baro_pres',
    type='uint32',
    def_num=2,
    units='Pa',
    comment='These are the raw ADC reading. The samples may span across seconds. A conversion will need to be done on this data once read.',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'one_d_sensor_calibration': Message(
    name='one_d_sensor_calibration',
    global_number=210,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
    comment='Whole second part of the timestamp',
), 0: Field(
    name='sensor_type',
    type='sensor_type',
    def_num=0,
    comment='Indicates which sensor the calibration is for',
), 1: Field(
    name='calibration_factor',
    type='uint32',
    def_num=1,
    comment='Calibration factor used to convert from raw ADC value to degrees, g,  etc.',
    subfields=Map(
    map=[SubField(
    name='baro_cal_factor',
    type='uint32',
    units='Pa',
    comment='Barometer calibration factor',
    reference_fields=Map(
    map=[ReferenceField(
    name='sensor_type',
    value='barometer',
    def_num=0,
    raw_value=3,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
), 2: Field(
    name='calibration_divisor',
    type='uint32',
    def_num=2,
    units='counts',
    comment='Calibration factor divisor',
), 3: Field(
    name='level_shift',
    type='uint32',
    def_num=3,
    comment='Level shift value used to shift the ADC value back into range',
), 4: Field(
    name='offset_cal',
    type='sint32',
    def_num=4,
    comment='Internal Calibration factor',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'set': Message(
    name='set',
    global_number=225,
    group_name='Activity File Messages',
    fields=Map(
    map={254: Field(
    name='timestamp',
    type='date_time',
    def_num=254,
    comment='Timestamp of the set',
), 0: Field(
    name='duration',
    type='uint32',
    def_num=0,
    scale=1000,
    units='s',
), 3: Field(
    name='repetitions',
    type='uint16',
    def_num=3,
    comment='# of repitions of the movement',
), 4: Field(
    name='weight',
    type='uint16',
    def_num=4,
    scale=16,
    units='kg',
    comment='Amount of weight applied for the set',
), 5: Field(
    name='set_type',
    type='set_type',
    def_num=5,
), 6: Field(
    name='start_time',
    type='date_time',
    def_num=6,
    comment='Start time of the set',
), 7: Field(
    name='category',
    type='exercise_category',
    def_num=7,
), 8: Field(
    name='category_subtype',
    type='uint16',
    def_num=8,
    comment='Based on the associated category, see [category]_exercise_names',
), 9: Field(
    name='weight_display_unit',
    type='fit_base_unit',
    def_num=9,
), 10: Field(
    name='message_index',
    type='message_index',
    def_num=10,
), 11: Field(
    name='wkt_step_index',
    type='message_index',
    def_num=11,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'stress_level': Message(
    name='stress_level',
    global_number=227,
    group_name='Monitoring File Messages',
    fields=Map(
    map={0: Field(
    name='stress_level_value',
    type='sint16',
    def_num=0,
), 1: Field(
    name='stress_level_time',
    type='date_time',
    def_num=1,
    units='s',
    comment='Time stress score was calculated',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
    comment='Value from 1 to 100 calculated by FirstBeat',
), 'dive_settings': Message(
    name='dive_settings',
    global_number=258,
    group_name='Sport Settings File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='name',
    type='string',
    def_num=0,
), 1: Field(
    name='model',
    type='tissue_model_type',
    def_num=1,
), 2: Field(
    name='gf_low',
    type='uint8',
    def_num=2,
    units='percent',
), 3: Field(
    name='gf_high',
    type='uint8',
    def_num=3,
    units='percent',
), 4: Field(
    name='water_type',
    type='water_type',
    def_num=4,
), 5: Field(
    name='water_density',
    type='float32',
    def_num=5,
    units='kg/m^3',
    comment='Fresh water is usually 1000; salt water is usually 1025',
), 6: Field(
    name='po2_warn',
    type='uint8',
    def_num=6,
    scale=100,
    units='percent',
    comment='Typically 1.40',
), 7: Field(
    name='po2_critical',
    type='uint8',
    def_num=7,
    scale=100,
    units='percent',
    comment='Typically 1.60',
), 8: Field(
    name='po2_deco',
    type='uint8',
    def_num=8,
    scale=100,
    units='percent',
), 9: Field(
    name='safety_stop_enabled',
    type='bool',
    def_num=9,
), 10: Field(
    name='bottom_depth',
    type='float32',
    def_num=10,
), 11: Field(
    name='bottom_time',
    type='uint32',
    def_num=11,
), 12: Field(
    name='apnea_countdown_enabled',
    type='bool',
    def_num=12,
), 13: Field(
    name='apnea_countdown_time',
    type='uint32',
    def_num=13,
), 14: Field(
    name='backlight_mode',
    type='dive_backlight_mode',
    def_num=14,
), 15: Field(
    name='backlight_brightness',
    type='uint8',
    def_num=15,
), 16: Field(
    name='backlight_timeout',
    type='backlight_timeout',
    def_num=16,
), 17: Field(
    name='repeat_dive_interval',
    type='uint16',
    def_num=17,
    units='s',
    comment='Time between surfacing and ending the activity',
), 18: Field(
    name='safety_stop_time',
    type='uint16',
    def_num=18,
    units='s',
    comment='Time at safety stop (if enabled)',
), 19: Field(
    name='heart_rate_source_type',
    type='source_type',
    def_num=19,
), 20: Field(
    name='heart_rate_source',
    type='uint8',
    def_num=20,
    subfields=Map(
    map=[SubField(
    name='heart_rate_antplus_device_type',
    type='antplus_device_type',
    reference_fields=Map(
    map=[ReferenceField(
    name='heart_rate_source_type',
    value='antplus',
    def_num=19,
    raw_value=1,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
), SubField(
    name='heart_rate_local_device_type',
    type='local_device_type',
    reference_fields=Map(
    map=[ReferenceField(
    name='heart_rate_source_type',
    value='local',
    def_num=19,
    raw_value=5,
)],
    map_type=list,
    value_type=ReferenceField,
    key_type=int,
),
)],
    map_type=list,
    value_type=SubField,
    key_type=int,
),
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'dive_gas': Message(
    name='dive_gas',
    global_number=259,
    group_name='Sport Settings File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='helium_content',
    type='uint8',
    def_num=0,
    units='percent',
), 1: Field(
    name='oxygen_content',
    type='uint8',
    def_num=1,
    units='percent',
), 2: Field(
    name='status',
    type='dive_gas_status',
    def_num=2,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'dive_alarm': Message(
    name='dive_alarm',
    global_number=262,
    group_name='Sport Settings File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
    comment='Index of the alarm',
), 0: Field(
    name='depth',
    type='uint32',
    def_num=0,
    scale=1000,
    units='m',
), 1: Field(
    name='time',
    type='sint32',
    def_num=1,
    units='s',
), 2: Field(
    name='enabled',
    type='bool',
    def_num=2,
), 3: Field(
    name='alarm_type',
    type='dive_alarm_type',
    def_num=3,
), 4: Field(
    name='sound',
    type='tone',
    def_num=4,
), 5: Field(
    name='dive_types',
    type='sub_sport',
    def_num=5,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'exercise_title': Message(
    name='exercise_title',
    global_number=264,
    group_name='Workout File Messages',
    fields=Map(
    map={254: Field(
    name='message_index',
    type='message_index',
    def_num=254,
), 0: Field(
    name='exercise_category',
    type='exercise_category',
    def_num=0,
), 1: Field(
    name='exercise_name',
    type='uint16',
    def_num=1,
), 2: Field(
    name='wkt_step_name',
    type='string',
    def_num=2,
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'dive_summary': Message(
    name='dive_summary',
    global_number=268,
    group_name='Other Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
), 0: Field(
    name='reference_mesg',
    type='mesg_num',
    def_num=0,
), 1: Field(
    name='reference_index',
    type='message_index',
    def_num=1,
), 2: Field(
    name='avg_depth',
    type='uint32',
    def_num=2,
    scale=1000,
    units='m',
    comment='0 if above water',
), 3: Field(
    name='max_depth',
    type='uint32',
    def_num=3,
    scale=1000,
    units='m',
    comment='0 if above water',
), 4: Field(
    name='surface_interval',
    type='uint32',
    def_num=4,
    units='s',
    comment='Time since end of last dive',
), 5: Field(
    name='start_cns',
    type='uint8',
    def_num=5,
    units='percent',
), 6: Field(
    name='end_cns',
    type='uint8',
    def_num=6,
    units='percent',
), 7: Field(
    name='start_n2',
    type='uint16',
    def_num=7,
    units='percent',
), 8: Field(
    name='end_n2',
    type='uint16',
    def_num=8,
    units='percent',
), 9: Field(
    name='o2_toxicity',
    type='uint16',
    def_num=9,
    units='OTUs',
), 10: Field(
    name='dive_number',
    type='uint32',
    def_num=10,
), 11: Field(
    name='bottom_time',
    type='uint32',
    def_num=11,
    scale=1000,
    units='s',
), 17: Field(
    name='avg_ascent_rate',
    type='sint32',
    def_num=17,
    scale=1000,
    units='m/s',
    comment='Average ascent rate, not including descents or stops',
), 22: Field(
    name='avg_descent_rate',
    type='uint32',
    def_num=22,
    scale=1000,
    units='m/s',
    comment='Average descent rate, not including ascents or stops',
), 23: Field(
    name='max_ascent_rate',
    type='uint32',
    def_num=23,
    scale=1000,
    units='m/s',
    comment='Maximum ascent rate',
), 24: Field(
    name='max_descent_rate',
    type='uint32',
    def_num=24,
    scale=1000,
    units='m/s',
    comment='Maximum descent rate',
), 25: Field(
    name='hang_time',
    type='uint32',
    def_num=25,
    scale=1000,
    units='s',
    comment='Time spent neither ascending nor descending',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'jump': Message(
    name='jump',
    global_number=285,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
), 0: Field(
    name='distance',
    type='float32',
    def_num=0,
    units='m',
), 1: Field(
    name='height',
    type='float32',
    def_num=1,
    units='m',
), 2: Field(
    name='rotations',
    type='uint8',
    def_num=2,
), 3: Field(
    name='hang_time',
    type='float32',
    def_num=3,
    units='s',
), 4: Field(
    name='score',
    type='float32',
    def_num=4,
    comment='A score for a jump calculated based on hang time, rotations, and distance.',
), 5: Field(
    name='position_lat',
    type='sint32',
    def_num=5,
    units='semicircles',
), 6: Field(
    name='position_long',
    type='sint32',
    def_num=6,
    units='semicircles',
), 7: Field(
    name='speed',
    type='uint16',
    def_num=7,
    components=Map(
    map=[Component(
    name='enhanced_speed',
    scale=1000,
    units='m/s',
    bits=16,
    accumulate=False,
    num=(8,),
    bit_offset=0,
)],
    map_type=list,
    value_type=Component,
    key_type=int,
),
    scale=1000,
    units='m/s',
), 8: Field(
    name='enhanced_speed',
    type='uint32',
    def_num=8,
    scale=1000,
    units='m/s',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
), 'climb_pro': Message(
    name='climb_pro',
    global_number=317,
    group_name='Activity File Messages',
    fields=Map(
    map={253: Field(
    name='timestamp',
    type='date_time',
    def_num=253,
    units='s',
), 0: Field(
    name='position_lat',
    type='sint32',
    def_num=0,
    units='semicircles',
), 1: Field(
    name='position_long',
    type='sint32',
    def_num=1,
    units='semicircles',
), 2: Field(
    name='climb_pro_event',
    type='climb_pro_event',
    def_num=2,
), 3: Field(
    name='climb_number',
    type='uint16',
    def_num=3,
), 4: Field(
    name='climb_category',
    type='uint8',
    def_num=4,
), 5: Field(
    name='current_dist',
    type='float32',
    def_num=5,
    units='m',
)},
    map_type=dict,
    value_type=Field,
    key_type=int,
),
)},
    map_type=dict,
    value_type=Message,
    key_type=str,
)
