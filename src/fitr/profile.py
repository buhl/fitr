# -*- coding: utf-8 -*-

import math
import datetime
import functools

GARMIN_EPOC_OFFSET=631065600.0

def noop(x): return x



@functools.lru_cache(typed=True)
def picker(values, filters):
    try:
        return next(
            filter(
                lambda x: all(x[1][k] == v for k, v in filters.items()),
                values.items()
            )
        )
    except StopIteration:
        return (None, None)



def resolve(value, values): 
    return values.get(value, {}).get("name", value)



def parse_component_value(component, value):
    if value is None:
        return None

    if isinstance(value, tuple):
        if component["bit_offset"] and component["bit_offset"] >= len(value) << 3:
            raise ValueError()

        unpacked_num = 0
        for v in reversed(value):
            unpacked_num = (unpacked_num << 8) + v
        value = unpacked_num

    if isinstance(value, int):
        value = (value >> component["bit_offset"]) & ((1 << component["bits"]) - 1)

    return value



class dict(dict):
    def __hash__(self):
        return hash(tuple(self.items()))



class list(list):
    def __hash__(self):
        return hash(tuple(self))



class BaseTypeParsers():
    def enum(v, *_):
        return None if v == 0xFF else v

    def sint8(v, *_):
        return None if v == 0x7F else v

    def uint8(v, *_):
        return None if v == 0xFF else v

    def string(v, *_):
        if v is None:
            return None
        elif isinstance(v, bytes):
            v = v.decode('utf-8', errors="replace")
        try:
            s = v[:v.index('\x00')]
        except ValueError:
            s = v
        return s or None

    def uint8z(v, *_):
        return None if v == 0x0 else v

    def byte(v, *_):
        if v is None:
            return None
        if isinstance(v, int):
            return None if v == 0xFF else v
        return None if all(b == 0xFF for b in v) else v

    def sint16(v, *_):
        return None if v == 0x7FFF else v

    def uint16(v, *_):
        return None if v == 0xFFFF else v

    def sint32(v, *_):
        return None if v == 0x7FFFFFFF else v

    def uint32(v, *_):
        return None if v == 0xFFFFFFFF else v

    def float32(v, *_):
        return None if math.isnan(v) else v

    def float64(v, *_):
        return None if math.isnan(v) else v

    def uint16z(v, *_):
        return None if v == 0x0 else v

    def uint32z(v, *_):
        return None if v == 0x0 else v

    def sint64(v, *_):
        return None if v == 0x7FFFFFFFFFFFFFFF else v

    def uint64(v, *_):
        return None if v == 0xFFFFFFFFFFFFFFFF else v

    def uint64z(v, *_):
        return None if v == 0 else v

    def bool(v, *_):
        return True if v else False



class TypeParsers():
    def date_time(value, values):
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            return value
        max_offset_value = picker(values, dict(name="min") )[0]
        if value < max_offset_value:
            return value
        return datetime.datetime.utcfromtimestamp(value + GARMIN_EPOC_OFFSET) 
    local_date_time = date_time

    #def product(value, values):
    #    if value in values:
    #        return values[value]["name"]
    #    return value
    #product_name = product
    #garmin_product = product



base_types = dict({
  'enum': dict({
  'fmt': 'B',
  'size': 1,
  'parser': BaseTypeParsers.enum,
  'name': 'enum',
  'byte': 0,
  'type_num': 0,
}),
  'sint8': dict({
  'fmt': 'b',
  'size': 1,
  'parser': BaseTypeParsers.sint8,
  'name': 'sint8',
  'byte': 1,
  'type_num': 1,
}),
  'uint8': dict({
  'fmt': 'B',
  'size': 1,
  'parser': BaseTypeParsers.uint8,
  'name': 'uint8',
  'byte': 2,
  'type_num': 2,
}),
  'string': dict({
  'fmt': 's',
  'size': 1,
  'parser': BaseTypeParsers.string,
  'name': 'string',
  'byte': 7,
  'type_num': 7,
}),
  'uint8z': dict({
  'fmt': 'B',
  'size': 1,
  'parser': BaseTypeParsers.uint8z,
  'name': 'uint8z',
  'byte': 10,
  'type_num': 10,
}),
  'byte': dict({
  'fmt': 'B',
  'size': 1,
  'parser': BaseTypeParsers.byte,
  'name': 'byte',
  'byte': 13,
  'type_num': 13,
}),
  'sint16': dict({
  'fmt': 'h',
  'size': 2,
  'parser': BaseTypeParsers.sint16,
  'name': 'sint16',
  'byte': 131,
  'type_num': 3,
}),
  'uint16': dict({
  'fmt': 'H',
  'size': 2,
  'parser': BaseTypeParsers.uint16,
  'name': 'uint16',
  'byte': 132,
  'type_num': 4,
}),
  'sint32': dict({
  'fmt': 'i',
  'size': 4,
  'parser': BaseTypeParsers.sint32,
  'name': 'sint32',
  'byte': 133,
  'type_num': 5,
}),
  'uint32': dict({
  'fmt': 'I',
  'size': 4,
  'parser': BaseTypeParsers.uint32,
  'name': 'uint32',
  'byte': 134,
  'type_num': 6,
}),
  'float32': dict({
  'fmt': 'f',
  'size': 4,
  'parser': BaseTypeParsers.float32,
  'name': 'float32',
  'byte': 136,
  'type_num': 8,
}),
  'float64': dict({
  'fmt': 'd',
  'size': 8,
  'parser': BaseTypeParsers.float64,
  'name': 'float64',
  'byte': 137,
  'type_num': 9,
}),
  'uint16z': dict({
  'fmt': 'H',
  'size': 2,
  'parser': BaseTypeParsers.uint16z,
  'name': 'uint16z',
  'byte': 139,
  'type_num': 11,
}),
  'uint32z': dict({
  'fmt': 'I',
  'size': 4,
  'parser': BaseTypeParsers.uint32z,
  'name': 'uint32z',
  'byte': 140,
  'type_num': 12,
}),
  'sint64': dict({
  'fmt': 'q',
  'size': 8,
  'parser': BaseTypeParsers.sint64,
  'name': 'sint64',
  'byte': 142,
  'type_num': 14,
}),
  'uint64': dict({
  'fmt': 'Q',
  'size': 8,
  'parser': BaseTypeParsers.uint64,
  'name': 'uint64',
  'byte': 143,
  'type_num': 15,
}),
  'uint64z': dict({
  'fmt': 'Q',
  'size': 8,
  'parser': BaseTypeParsers.uint64z,
  'name': 'uint64z',
  'byte': 144,
  'type_num': 16,
}),
})
types = dict({
  'file': dict({
  'name': 'file',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'device',
  'value': 1,
  'comment': 'Read only, single file. Must be in root directory.',
}),
  2: dict({
  'name': 'settings',
  'value': 2,
  'comment': 'Read/write, single file. Directory=Settings',
}),
  3: dict({
  'name': 'sport',
  'value': 3,
  'comment': 'Read/write, multiple files, file number = sport type. Directory=Sports',
}),
  4: dict({
  'name': 'activity',
  'value': 4,
  'comment': 'Read/erase, multiple files. Directory=Activities',
}),
  5: dict({
  'name': 'workout',
  'value': 5,
  'comment': 'Read/write/erase, multiple files. Directory=Workouts',
}),
  6: dict({
  'name': 'course',
  'value': 6,
  'comment': 'Read/write/erase, multiple files. Directory=Courses',
}),
  7: dict({
  'name': 'schedules',
  'value': 7,
  'comment': 'Read/write, single file. Directory=Schedules',
}),
  9: dict({
  'name': 'weight',
  'value': 9,
  'comment': 'Read only, single file. Circular buffer. All message definitions at start of file. Directory=Weight',
}),
  10: dict({
  'name': 'totals',
  'value': 10,
  'comment': 'Read only, single file. Directory=Totals',
}),
  11: dict({
  'name': 'goals',
  'value': 11,
  'comment': 'Read/write, single file. Directory=Goals',
}),
  14: dict({
  'name': 'blood_pressure',
  'value': 14,
  'comment': 'Read only. Directory=Blood Pressure',
}),
  15: dict({
  'name': 'monitoring_a',
  'value': 15,
  'comment': 'Read only. Directory=Monitoring. File number=sub type.',
}),
  20: dict({
  'name': 'activity_summary',
  'value': 20,
  'comment': 'Read/erase, multiple files. Directory=Activities',
}),
  28: dict({
  'name': 'monitoring_daily',
  'value': 28,
}),
  32: dict({
  'name': 'monitoring_b',
  'value': 32,
  'comment': 'Read only. Directory=Monitoring. File number=identifier',
}),
  34: dict({
  'name': 'segment',
  'value': 34,
  'comment': 'Read/write/erase. Multiple Files.  Directory=Segments',
}),
  35: dict({
  'name': 'segment_list',
  'value': 35,
  'comment': 'Read/write/erase. Single File.  Directory=Segments',
}),
  40: dict({
  'name': 'exd_configuration',
  'value': 40,
  'comment': 'Read/write/erase. Single File. Directory=Settings',
}),
  247: dict({
  'name': 'mfg_range_min',
  'value': 247,
  'comment': '0xF7 - 0xFE reserved for manufacturer specific file types',
}),
  248: dict({
  'name': 'mfg_range_248',
  'value': 248,
  'comment': '0xF7 - 0xFE reserved for manufacturer specific file types',
}),
  249: dict({
  'name': 'mfg_range_249',
  'value': 249,
  'comment': '0xF7 - 0xFE reserved for manufacturer specific file types',
}),
  250: dict({
  'name': 'mfg_range_250',
  'value': 250,
  'comment': '0xF7 - 0xFE reserved for manufacturer specific file types',
}),
  251: dict({
  'name': 'mfg_range_251',
  'value': 251,
  'comment': '0xF7 - 0xFE reserved for manufacturer specific file types',
}),
  252: dict({
  'name': 'mfg_range_252',
  'value': 252,
  'comment': '0xF7 - 0xFE reserved for manufacturer specific file types',
}),
  253: dict({
  'name': 'mfg_range_253',
  'value': 253,
  'comment': '0xF7 - 0xFE reserved for manufacturer specific file types',
}),
  254: dict({
  'name': 'mfg_range_max',
  'value': 254,
  'comment': '0xF7 - 0xFE reserved for manufacturer specific file types',
}),
}),
}),
  'mesg_num': dict({
  'name': 'mesg_num',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'file_id',
  'value': 0,
}),
  1: dict({
  'name': 'capabilities',
  'value': 1,
}),
  2: dict({
  'name': 'device_settings',
  'value': 2,
}),
  3: dict({
  'name': 'user_profile',
  'value': 3,
}),
  4: dict({
  'name': 'hrm_profile',
  'value': 4,
}),
  5: dict({
  'name': 'sdm_profile',
  'value': 5,
}),
  6: dict({
  'name': 'bike_profile',
  'value': 6,
}),
  7: dict({
  'name': 'zones_target',
  'value': 7,
}),
  8: dict({
  'name': 'hr_zone',
  'value': 8,
}),
  9: dict({
  'name': 'power_zone',
  'value': 9,
}),
  10: dict({
  'name': 'met_zone',
  'value': 10,
}),
  12: dict({
  'name': 'sport',
  'value': 12,
}),
  15: dict({
  'name': 'goal',
  'value': 15,
}),
  18: dict({
  'name': 'session',
  'value': 18,
}),
  19: dict({
  'name': 'lap',
  'value': 19,
}),
  20: dict({
  'name': 'record',
  'value': 20,
}),
  21: dict({
  'name': 'event',
  'value': 21,
}),
  23: dict({
  'name': 'device_info',
  'value': 23,
}),
  26: dict({
  'name': 'workout',
  'value': 26,
}),
  27: dict({
  'name': 'workout_step',
  'value': 27,
}),
  28: dict({
  'name': 'schedule',
  'value': 28,
}),
  30: dict({
  'name': 'weight_scale',
  'value': 30,
}),
  31: dict({
  'name': 'course',
  'value': 31,
}),
  32: dict({
  'name': 'course_point',
  'value': 32,
}),
  33: dict({
  'name': 'totals',
  'value': 33,
}),
  34: dict({
  'name': 'activity',
  'value': 34,
}),
  35: dict({
  'name': 'software',
  'value': 35,
}),
  37: dict({
  'name': 'file_capabilities',
  'value': 37,
}),
  38: dict({
  'name': 'mesg_capabilities',
  'value': 38,
}),
  39: dict({
  'name': 'field_capabilities',
  'value': 39,
}),
  49: dict({
  'name': 'file_creator',
  'value': 49,
}),
  51: dict({
  'name': 'blood_pressure',
  'value': 51,
}),
  53: dict({
  'name': 'speed_zone',
  'value': 53,
}),
  55: dict({
  'name': 'monitoring',
  'value': 55,
}),
  72: dict({
  'name': 'training_file',
  'value': 72,
}),
  78: dict({
  'name': 'hrv',
  'value': 78,
}),
  80: dict({
  'name': 'ant_rx',
  'value': 80,
}),
  81: dict({
  'name': 'ant_tx',
  'value': 81,
}),
  82: dict({
  'name': 'ant_channel_id',
  'value': 82,
}),
  101: dict({
  'name': 'length',
  'value': 101,
}),
  103: dict({
  'name': 'monitoring_info',
  'value': 103,
}),
  105: dict({
  'name': 'pad',
  'value': 105,
}),
  106: dict({
  'name': 'slave_device',
  'value': 106,
}),
  127: dict({
  'name': 'connectivity',
  'value': 127,
}),
  128: dict({
  'name': 'weather_conditions',
  'value': 128,
}),
  129: dict({
  'name': 'weather_alert',
  'value': 129,
}),
  131: dict({
  'name': 'cadence_zone',
  'value': 131,
}),
  132: dict({
  'name': 'hr',
  'value': 132,
}),
  142: dict({
  'name': 'segment_lap',
  'value': 142,
}),
  145: dict({
  'name': 'memo_glob',
  'value': 145,
}),
  148: dict({
  'name': 'segment_id',
  'value': 148,
}),
  149: dict({
  'name': 'segment_leaderboard_entry',
  'value': 149,
}),
  150: dict({
  'name': 'segment_point',
  'value': 150,
}),
  151: dict({
  'name': 'segment_file',
  'value': 151,
}),
  158: dict({
  'name': 'workout_session',
  'value': 158,
}),
  159: dict({
  'name': 'watchface_settings',
  'value': 159,
}),
  160: dict({
  'name': 'gps_metadata',
  'value': 160,
}),
  161: dict({
  'name': 'camera_event',
  'value': 161,
}),
  162: dict({
  'name': 'timestamp_correlation',
  'value': 162,
}),
  164: dict({
  'name': 'gyroscope_data',
  'value': 164,
}),
  165: dict({
  'name': 'accelerometer_data',
  'value': 165,
}),
  167: dict({
  'name': 'three_d_sensor_calibration',
  'value': 167,
}),
  169: dict({
  'name': 'video_frame',
  'value': 169,
}),
  174: dict({
  'name': 'obdii_data',
  'value': 174,
}),
  177: dict({
  'name': 'nmea_sentence',
  'value': 177,
}),
  178: dict({
  'name': 'aviation_attitude',
  'value': 178,
}),
  184: dict({
  'name': 'video',
  'value': 184,
}),
  185: dict({
  'name': 'video_title',
  'value': 185,
}),
  186: dict({
  'name': 'video_description',
  'value': 186,
}),
  187: dict({
  'name': 'video_clip',
  'value': 187,
}),
  188: dict({
  'name': 'ohr_settings',
  'value': 188,
}),
  200: dict({
  'name': 'exd_screen_configuration',
  'value': 200,
}),
  201: dict({
  'name': 'exd_data_field_configuration',
  'value': 201,
}),
  202: dict({
  'name': 'exd_data_concept_configuration',
  'value': 202,
}),
  206: dict({
  'name': 'field_description',
  'value': 206,
}),
  207: dict({
  'name': 'developer_data_id',
  'value': 207,
}),
  208: dict({
  'name': 'magnetometer_data',
  'value': 208,
}),
  209: dict({
  'name': 'barometer_data',
  'value': 209,
}),
  210: dict({
  'name': 'one_d_sensor_calibration',
  'value': 210,
}),
  225: dict({
  'name': 'set',
  'value': 225,
}),
  227: dict({
  'name': 'stress_level',
  'value': 227,
}),
  258: dict({
  'name': 'dive_settings',
  'value': 258,
}),
  259: dict({
  'name': 'dive_gas',
  'value': 259,
}),
  262: dict({
  'name': 'dive_alarm',
  'value': 262,
}),
  264: dict({
  'name': 'exercise_title',
  'value': 264,
}),
  268: dict({
  'name': 'dive_summary',
  'value': 268,
}),
  285: dict({
  'name': 'jump',
  'value': 285,
}),
  317: dict({
  'name': 'climb_pro',
  'value': 317,
}),
  65280: dict({
  'name': 'mfg_range_min',
  'value': 65280,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65281: dict({
  'name': 'mfg_range_65281',
  'value': 65281,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65282: dict({
  'name': 'mfg_range_65282',
  'value': 65282,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65283: dict({
  'name': 'mfg_range_65283',
  'value': 65283,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65284: dict({
  'name': 'mfg_range_65284',
  'value': 65284,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65285: dict({
  'name': 'mfg_range_65285',
  'value': 65285,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65286: dict({
  'name': 'mfg_range_65286',
  'value': 65286,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65287: dict({
  'name': 'mfg_range_65287',
  'value': 65287,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65288: dict({
  'name': 'mfg_range_65288',
  'value': 65288,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65289: dict({
  'name': 'mfg_range_65289',
  'value': 65289,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65290: dict({
  'name': 'mfg_range_65290',
  'value': 65290,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65291: dict({
  'name': 'mfg_range_65291',
  'value': 65291,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65292: dict({
  'name': 'mfg_range_65292',
  'value': 65292,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65293: dict({
  'name': 'mfg_range_65293',
  'value': 65293,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65294: dict({
  'name': 'mfg_range_65294',
  'value': 65294,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65295: dict({
  'name': 'mfg_range_65295',
  'value': 65295,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65296: dict({
  'name': 'mfg_range_65296',
  'value': 65296,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65297: dict({
  'name': 'mfg_range_65297',
  'value': 65297,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65298: dict({
  'name': 'mfg_range_65298',
  'value': 65298,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65299: dict({
  'name': 'mfg_range_65299',
  'value': 65299,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65300: dict({
  'name': 'mfg_range_65300',
  'value': 65300,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65301: dict({
  'name': 'mfg_range_65301',
  'value': 65301,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65302: dict({
  'name': 'mfg_range_65302',
  'value': 65302,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65303: dict({
  'name': 'mfg_range_65303',
  'value': 65303,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65304: dict({
  'name': 'mfg_range_65304',
  'value': 65304,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65305: dict({
  'name': 'mfg_range_65305',
  'value': 65305,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65306: dict({
  'name': 'mfg_range_65306',
  'value': 65306,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65307: dict({
  'name': 'mfg_range_65307',
  'value': 65307,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65308: dict({
  'name': 'mfg_range_65308',
  'value': 65308,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65309: dict({
  'name': 'mfg_range_65309',
  'value': 65309,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65310: dict({
  'name': 'mfg_range_65310',
  'value': 65310,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65311: dict({
  'name': 'mfg_range_65311',
  'value': 65311,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65312: dict({
  'name': 'mfg_range_65312',
  'value': 65312,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65313: dict({
  'name': 'mfg_range_65313',
  'value': 65313,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65314: dict({
  'name': 'mfg_range_65314',
  'value': 65314,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65315: dict({
  'name': 'mfg_range_65315',
  'value': 65315,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65316: dict({
  'name': 'mfg_range_65316',
  'value': 65316,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65317: dict({
  'name': 'mfg_range_65317',
  'value': 65317,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65318: dict({
  'name': 'mfg_range_65318',
  'value': 65318,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65319: dict({
  'name': 'mfg_range_65319',
  'value': 65319,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65320: dict({
  'name': 'mfg_range_65320',
  'value': 65320,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65321: dict({
  'name': 'mfg_range_65321',
  'value': 65321,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65322: dict({
  'name': 'mfg_range_65322',
  'value': 65322,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65323: dict({
  'name': 'mfg_range_65323',
  'value': 65323,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65324: dict({
  'name': 'mfg_range_65324',
  'value': 65324,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65325: dict({
  'name': 'mfg_range_65325',
  'value': 65325,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65326: dict({
  'name': 'mfg_range_65326',
  'value': 65326,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65327: dict({
  'name': 'mfg_range_65327',
  'value': 65327,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65328: dict({
  'name': 'mfg_range_65328',
  'value': 65328,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65329: dict({
  'name': 'mfg_range_65329',
  'value': 65329,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65330: dict({
  'name': 'mfg_range_65330',
  'value': 65330,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65331: dict({
  'name': 'mfg_range_65331',
  'value': 65331,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65332: dict({
  'name': 'mfg_range_65332',
  'value': 65332,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65333: dict({
  'name': 'mfg_range_65333',
  'value': 65333,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65334: dict({
  'name': 'mfg_range_65334',
  'value': 65334,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65335: dict({
  'name': 'mfg_range_65335',
  'value': 65335,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65336: dict({
  'name': 'mfg_range_65336',
  'value': 65336,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65337: dict({
  'name': 'mfg_range_65337',
  'value': 65337,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65338: dict({
  'name': 'mfg_range_65338',
  'value': 65338,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65339: dict({
  'name': 'mfg_range_65339',
  'value': 65339,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65340: dict({
  'name': 'mfg_range_65340',
  'value': 65340,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65341: dict({
  'name': 'mfg_range_65341',
  'value': 65341,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65342: dict({
  'name': 'mfg_range_65342',
  'value': 65342,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65343: dict({
  'name': 'mfg_range_65343',
  'value': 65343,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65344: dict({
  'name': 'mfg_range_65344',
  'value': 65344,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65345: dict({
  'name': 'mfg_range_65345',
  'value': 65345,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65346: dict({
  'name': 'mfg_range_65346',
  'value': 65346,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65347: dict({
  'name': 'mfg_range_65347',
  'value': 65347,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65348: dict({
  'name': 'mfg_range_65348',
  'value': 65348,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65349: dict({
  'name': 'mfg_range_65349',
  'value': 65349,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65350: dict({
  'name': 'mfg_range_65350',
  'value': 65350,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65351: dict({
  'name': 'mfg_range_65351',
  'value': 65351,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65352: dict({
  'name': 'mfg_range_65352',
  'value': 65352,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65353: dict({
  'name': 'mfg_range_65353',
  'value': 65353,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65354: dict({
  'name': 'mfg_range_65354',
  'value': 65354,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65355: dict({
  'name': 'mfg_range_65355',
  'value': 65355,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65356: dict({
  'name': 'mfg_range_65356',
  'value': 65356,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65357: dict({
  'name': 'mfg_range_65357',
  'value': 65357,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65358: dict({
  'name': 'mfg_range_65358',
  'value': 65358,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65359: dict({
  'name': 'mfg_range_65359',
  'value': 65359,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65360: dict({
  'name': 'mfg_range_65360',
  'value': 65360,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65361: dict({
  'name': 'mfg_range_65361',
  'value': 65361,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65362: dict({
  'name': 'mfg_range_65362',
  'value': 65362,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65363: dict({
  'name': 'mfg_range_65363',
  'value': 65363,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65364: dict({
  'name': 'mfg_range_65364',
  'value': 65364,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65365: dict({
  'name': 'mfg_range_65365',
  'value': 65365,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65366: dict({
  'name': 'mfg_range_65366',
  'value': 65366,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65367: dict({
  'name': 'mfg_range_65367',
  'value': 65367,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65368: dict({
  'name': 'mfg_range_65368',
  'value': 65368,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65369: dict({
  'name': 'mfg_range_65369',
  'value': 65369,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65370: dict({
  'name': 'mfg_range_65370',
  'value': 65370,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65371: dict({
  'name': 'mfg_range_65371',
  'value': 65371,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65372: dict({
  'name': 'mfg_range_65372',
  'value': 65372,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65373: dict({
  'name': 'mfg_range_65373',
  'value': 65373,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65374: dict({
  'name': 'mfg_range_65374',
  'value': 65374,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65375: dict({
  'name': 'mfg_range_65375',
  'value': 65375,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65376: dict({
  'name': 'mfg_range_65376',
  'value': 65376,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65377: dict({
  'name': 'mfg_range_65377',
  'value': 65377,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65378: dict({
  'name': 'mfg_range_65378',
  'value': 65378,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65379: dict({
  'name': 'mfg_range_65379',
  'value': 65379,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65380: dict({
  'name': 'mfg_range_65380',
  'value': 65380,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65381: dict({
  'name': 'mfg_range_65381',
  'value': 65381,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65382: dict({
  'name': 'mfg_range_65382',
  'value': 65382,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65383: dict({
  'name': 'mfg_range_65383',
  'value': 65383,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65384: dict({
  'name': 'mfg_range_65384',
  'value': 65384,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65385: dict({
  'name': 'mfg_range_65385',
  'value': 65385,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65386: dict({
  'name': 'mfg_range_65386',
  'value': 65386,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65387: dict({
  'name': 'mfg_range_65387',
  'value': 65387,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65388: dict({
  'name': 'mfg_range_65388',
  'value': 65388,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65389: dict({
  'name': 'mfg_range_65389',
  'value': 65389,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65390: dict({
  'name': 'mfg_range_65390',
  'value': 65390,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65391: dict({
  'name': 'mfg_range_65391',
  'value': 65391,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65392: dict({
  'name': 'mfg_range_65392',
  'value': 65392,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65393: dict({
  'name': 'mfg_range_65393',
  'value': 65393,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65394: dict({
  'name': 'mfg_range_65394',
  'value': 65394,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65395: dict({
  'name': 'mfg_range_65395',
  'value': 65395,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65396: dict({
  'name': 'mfg_range_65396',
  'value': 65396,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65397: dict({
  'name': 'mfg_range_65397',
  'value': 65397,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65398: dict({
  'name': 'mfg_range_65398',
  'value': 65398,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65399: dict({
  'name': 'mfg_range_65399',
  'value': 65399,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65400: dict({
  'name': 'mfg_range_65400',
  'value': 65400,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65401: dict({
  'name': 'mfg_range_65401',
  'value': 65401,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65402: dict({
  'name': 'mfg_range_65402',
  'value': 65402,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65403: dict({
  'name': 'mfg_range_65403',
  'value': 65403,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65404: dict({
  'name': 'mfg_range_65404',
  'value': 65404,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65405: dict({
  'name': 'mfg_range_65405',
  'value': 65405,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65406: dict({
  'name': 'mfg_range_65406',
  'value': 65406,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65407: dict({
  'name': 'mfg_range_65407',
  'value': 65407,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65408: dict({
  'name': 'mfg_range_65408',
  'value': 65408,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65409: dict({
  'name': 'mfg_range_65409',
  'value': 65409,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65410: dict({
  'name': 'mfg_range_65410',
  'value': 65410,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65411: dict({
  'name': 'mfg_range_65411',
  'value': 65411,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65412: dict({
  'name': 'mfg_range_65412',
  'value': 65412,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65413: dict({
  'name': 'mfg_range_65413',
  'value': 65413,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65414: dict({
  'name': 'mfg_range_65414',
  'value': 65414,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65415: dict({
  'name': 'mfg_range_65415',
  'value': 65415,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65416: dict({
  'name': 'mfg_range_65416',
  'value': 65416,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65417: dict({
  'name': 'mfg_range_65417',
  'value': 65417,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65418: dict({
  'name': 'mfg_range_65418',
  'value': 65418,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65419: dict({
  'name': 'mfg_range_65419',
  'value': 65419,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65420: dict({
  'name': 'mfg_range_65420',
  'value': 65420,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65421: dict({
  'name': 'mfg_range_65421',
  'value': 65421,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65422: dict({
  'name': 'mfg_range_65422',
  'value': 65422,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65423: dict({
  'name': 'mfg_range_65423',
  'value': 65423,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65424: dict({
  'name': 'mfg_range_65424',
  'value': 65424,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65425: dict({
  'name': 'mfg_range_65425',
  'value': 65425,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65426: dict({
  'name': 'mfg_range_65426',
  'value': 65426,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65427: dict({
  'name': 'mfg_range_65427',
  'value': 65427,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65428: dict({
  'name': 'mfg_range_65428',
  'value': 65428,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65429: dict({
  'name': 'mfg_range_65429',
  'value': 65429,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65430: dict({
  'name': 'mfg_range_65430',
  'value': 65430,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65431: dict({
  'name': 'mfg_range_65431',
  'value': 65431,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65432: dict({
  'name': 'mfg_range_65432',
  'value': 65432,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65433: dict({
  'name': 'mfg_range_65433',
  'value': 65433,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65434: dict({
  'name': 'mfg_range_65434',
  'value': 65434,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65435: dict({
  'name': 'mfg_range_65435',
  'value': 65435,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65436: dict({
  'name': 'mfg_range_65436',
  'value': 65436,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65437: dict({
  'name': 'mfg_range_65437',
  'value': 65437,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65438: dict({
  'name': 'mfg_range_65438',
  'value': 65438,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65439: dict({
  'name': 'mfg_range_65439',
  'value': 65439,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65440: dict({
  'name': 'mfg_range_65440',
  'value': 65440,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65441: dict({
  'name': 'mfg_range_65441',
  'value': 65441,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65442: dict({
  'name': 'mfg_range_65442',
  'value': 65442,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65443: dict({
  'name': 'mfg_range_65443',
  'value': 65443,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65444: dict({
  'name': 'mfg_range_65444',
  'value': 65444,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65445: dict({
  'name': 'mfg_range_65445',
  'value': 65445,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65446: dict({
  'name': 'mfg_range_65446',
  'value': 65446,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65447: dict({
  'name': 'mfg_range_65447',
  'value': 65447,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65448: dict({
  'name': 'mfg_range_65448',
  'value': 65448,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65449: dict({
  'name': 'mfg_range_65449',
  'value': 65449,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65450: dict({
  'name': 'mfg_range_65450',
  'value': 65450,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65451: dict({
  'name': 'mfg_range_65451',
  'value': 65451,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65452: dict({
  'name': 'mfg_range_65452',
  'value': 65452,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65453: dict({
  'name': 'mfg_range_65453',
  'value': 65453,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65454: dict({
  'name': 'mfg_range_65454',
  'value': 65454,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65455: dict({
  'name': 'mfg_range_65455',
  'value': 65455,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65456: dict({
  'name': 'mfg_range_65456',
  'value': 65456,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65457: dict({
  'name': 'mfg_range_65457',
  'value': 65457,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65458: dict({
  'name': 'mfg_range_65458',
  'value': 65458,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65459: dict({
  'name': 'mfg_range_65459',
  'value': 65459,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65460: dict({
  'name': 'mfg_range_65460',
  'value': 65460,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65461: dict({
  'name': 'mfg_range_65461',
  'value': 65461,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65462: dict({
  'name': 'mfg_range_65462',
  'value': 65462,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65463: dict({
  'name': 'mfg_range_65463',
  'value': 65463,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65464: dict({
  'name': 'mfg_range_65464',
  'value': 65464,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65465: dict({
  'name': 'mfg_range_65465',
  'value': 65465,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65466: dict({
  'name': 'mfg_range_65466',
  'value': 65466,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65467: dict({
  'name': 'mfg_range_65467',
  'value': 65467,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65468: dict({
  'name': 'mfg_range_65468',
  'value': 65468,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65469: dict({
  'name': 'mfg_range_65469',
  'value': 65469,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65470: dict({
  'name': 'mfg_range_65470',
  'value': 65470,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65471: dict({
  'name': 'mfg_range_65471',
  'value': 65471,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65472: dict({
  'name': 'mfg_range_65472',
  'value': 65472,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65473: dict({
  'name': 'mfg_range_65473',
  'value': 65473,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65474: dict({
  'name': 'mfg_range_65474',
  'value': 65474,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65475: dict({
  'name': 'mfg_range_65475',
  'value': 65475,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65476: dict({
  'name': 'mfg_range_65476',
  'value': 65476,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65477: dict({
  'name': 'mfg_range_65477',
  'value': 65477,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65478: dict({
  'name': 'mfg_range_65478',
  'value': 65478,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65479: dict({
  'name': 'mfg_range_65479',
  'value': 65479,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65480: dict({
  'name': 'mfg_range_65480',
  'value': 65480,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65481: dict({
  'name': 'mfg_range_65481',
  'value': 65481,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65482: dict({
  'name': 'mfg_range_65482',
  'value': 65482,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65483: dict({
  'name': 'mfg_range_65483',
  'value': 65483,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65484: dict({
  'name': 'mfg_range_65484',
  'value': 65484,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65485: dict({
  'name': 'mfg_range_65485',
  'value': 65485,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65486: dict({
  'name': 'mfg_range_65486',
  'value': 65486,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65487: dict({
  'name': 'mfg_range_65487',
  'value': 65487,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65488: dict({
  'name': 'mfg_range_65488',
  'value': 65488,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65489: dict({
  'name': 'mfg_range_65489',
  'value': 65489,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65490: dict({
  'name': 'mfg_range_65490',
  'value': 65490,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65491: dict({
  'name': 'mfg_range_65491',
  'value': 65491,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65492: dict({
  'name': 'mfg_range_65492',
  'value': 65492,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65493: dict({
  'name': 'mfg_range_65493',
  'value': 65493,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65494: dict({
  'name': 'mfg_range_65494',
  'value': 65494,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65495: dict({
  'name': 'mfg_range_65495',
  'value': 65495,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65496: dict({
  'name': 'mfg_range_65496',
  'value': 65496,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65497: dict({
  'name': 'mfg_range_65497',
  'value': 65497,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65498: dict({
  'name': 'mfg_range_65498',
  'value': 65498,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65499: dict({
  'name': 'mfg_range_65499',
  'value': 65499,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65500: dict({
  'name': 'mfg_range_65500',
  'value': 65500,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65501: dict({
  'name': 'mfg_range_65501',
  'value': 65501,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65502: dict({
  'name': 'mfg_range_65502',
  'value': 65502,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65503: dict({
  'name': 'mfg_range_65503',
  'value': 65503,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65504: dict({
  'name': 'mfg_range_65504',
  'value': 65504,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65505: dict({
  'name': 'mfg_range_65505',
  'value': 65505,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65506: dict({
  'name': 'mfg_range_65506',
  'value': 65506,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65507: dict({
  'name': 'mfg_range_65507',
  'value': 65507,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65508: dict({
  'name': 'mfg_range_65508',
  'value': 65508,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65509: dict({
  'name': 'mfg_range_65509',
  'value': 65509,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65510: dict({
  'name': 'mfg_range_65510',
  'value': 65510,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65511: dict({
  'name': 'mfg_range_65511',
  'value': 65511,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65512: dict({
  'name': 'mfg_range_65512',
  'value': 65512,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65513: dict({
  'name': 'mfg_range_65513',
  'value': 65513,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65514: dict({
  'name': 'mfg_range_65514',
  'value': 65514,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65515: dict({
  'name': 'mfg_range_65515',
  'value': 65515,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65516: dict({
  'name': 'mfg_range_65516',
  'value': 65516,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65517: dict({
  'name': 'mfg_range_65517',
  'value': 65517,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65518: dict({
  'name': 'mfg_range_65518',
  'value': 65518,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65519: dict({
  'name': 'mfg_range_65519',
  'value': 65519,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65520: dict({
  'name': 'mfg_range_65520',
  'value': 65520,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65521: dict({
  'name': 'mfg_range_65521',
  'value': 65521,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65522: dict({
  'name': 'mfg_range_65522',
  'value': 65522,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65523: dict({
  'name': 'mfg_range_65523',
  'value': 65523,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65524: dict({
  'name': 'mfg_range_65524',
  'value': 65524,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65525: dict({
  'name': 'mfg_range_65525',
  'value': 65525,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65526: dict({
  'name': 'mfg_range_65526',
  'value': 65526,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65527: dict({
  'name': 'mfg_range_65527',
  'value': 65527,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65528: dict({
  'name': 'mfg_range_65528',
  'value': 65528,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65529: dict({
  'name': 'mfg_range_65529',
  'value': 65529,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65530: dict({
  'name': 'mfg_range_65530',
  'value': 65530,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65531: dict({
  'name': 'mfg_range_65531',
  'value': 65531,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65532: dict({
  'name': 'mfg_range_65532',
  'value': 65532,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65533: dict({
  'name': 'mfg_range_65533',
  'value': 65533,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
  65534: dict({
  'name': 'mfg_range_max',
  'value': 65534,
  'comment': '0xFF00 - 0xFFFE reserved for manufacturer specific messages',
}),
}),
}),
  'checksum': dict({
  'name': 'checksum',
  'base_type': 'uint8',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'clear',
  'value': 0,
  'comment': 'Allows clear of checksum for flash memory where can only write 1 to 0 without erasing sector.',
}),
  1: dict({
  'name': 'ok',
  'value': 1,
  'comment': 'Set to mark checksum as valid if computes to invalid values 0 or 0xFF.  Checksum can also be set to ok to save encoding computation time.',
}),
}),
}),
  'file_flags': dict({
  'name': 'file_flags',
  'base_type': 'uint8z',
  'parser': resolve,
  'values': dict({
  2: dict({
  'name': 'read',
  'value': 2,
}),
  4: dict({
  'name': 'write',
  'value': 4,
}),
  8: dict({
  'name': 'erase',
  'value': 8,
}),
}),
}),
  'mesg_count': dict({
  'name': 'mesg_count',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'num_per_file',
  'value': 0,
}),
  1: dict({
  'name': 'max_per_file',
  'value': 1,
}),
  2: dict({
  'name': 'max_per_file_type',
  'value': 2,
}),
}),
}),
  'date_time': dict({
  'name': 'date_time',
  'base_type': 'uint32',
  'parser': TypeParsers.date_time,
  'values': dict({
  268435456: dict({
  'name': 'min',
  'value': 268435456,
  'comment': 'if date_time is < 0x10000000 then it is system time (seconds from device power on)',
}),
}),
  'comment': 'seconds since UTC 00:00 Dec 31 1989',
}),
  'local_date_time': dict({
  'name': 'local_date_time',
  'base_type': 'uint32',
  'parser': TypeParsers.date_time,
  'values': dict({
  268435456: dict({
  'name': 'min',
  'value': 268435456,
  'comment': 'if date_time is < 0x10000000 then it is system time (seconds from device power on)',
}),
}),
  'comment': 'seconds since 00:00 Dec 31 1989 in local time zone',
}),
  'message_index': dict({
  'name': 'message_index',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  32768: dict({
  'name': 'selected',
  'value': 32768,
  'comment': 'message is selected if set',
}),
  28672: dict({
  'name': 'reserved',
  'value': 28672,
  'comment': 'reserved (default 0)',
}),
  4095: dict({
  'name': 'mask',
  'value': 4095,
  'comment': 'index',
}),
}),
}),
  'device_index': dict({
  'name': 'device_index',
  'base_type': 'uint8',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'creator',
  'value': 0,
  'comment': 'Creator of the file is always device index 0.',
}),
}),
}),
  'gender': dict({
  'name': 'gender',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'female',
  'value': 0,
}),
  1: dict({
  'name': 'male',
  'value': 1,
}),
}),
}),
  'language': dict({
  'name': 'language',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'english',
  'value': 0,
}),
  1: dict({
  'name': 'french',
  'value': 1,
}),
  2: dict({
  'name': 'italian',
  'value': 2,
}),
  3: dict({
  'name': 'german',
  'value': 3,
}),
  4: dict({
  'name': 'spanish',
  'value': 4,
}),
  5: dict({
  'name': 'croatian',
  'value': 5,
}),
  6: dict({
  'name': 'czech',
  'value': 6,
}),
  7: dict({
  'name': 'danish',
  'value': 7,
}),
  8: dict({
  'name': 'dutch',
  'value': 8,
}),
  9: dict({
  'name': 'finnish',
  'value': 9,
}),
  10: dict({
  'name': 'greek',
  'value': 10,
}),
  11: dict({
  'name': 'hungarian',
  'value': 11,
}),
  12: dict({
  'name': 'norwegian',
  'value': 12,
}),
  13: dict({
  'name': 'polish',
  'value': 13,
}),
  14: dict({
  'name': 'portuguese',
  'value': 14,
}),
  15: dict({
  'name': 'slovakian',
  'value': 15,
}),
  16: dict({
  'name': 'slovenian',
  'value': 16,
}),
  17: dict({
  'name': 'swedish',
  'value': 17,
}),
  18: dict({
  'name': 'russian',
  'value': 18,
}),
  19: dict({
  'name': 'turkish',
  'value': 19,
}),
  20: dict({
  'name': 'latvian',
  'value': 20,
}),
  21: dict({
  'name': 'ukrainian',
  'value': 21,
}),
  22: dict({
  'name': 'arabic',
  'value': 22,
}),
  23: dict({
  'name': 'farsi',
  'value': 23,
}),
  24: dict({
  'name': 'bulgarian',
  'value': 24,
}),
  25: dict({
  'name': 'romanian',
  'value': 25,
}),
  26: dict({
  'name': 'chinese',
  'value': 26,
}),
  27: dict({
  'name': 'japanese',
  'value': 27,
}),
  28: dict({
  'name': 'korean',
  'value': 28,
}),
  29: dict({
  'name': 'taiwanese',
  'value': 29,
}),
  30: dict({
  'name': 'thai',
  'value': 30,
}),
  31: dict({
  'name': 'hebrew',
  'value': 31,
}),
  32: dict({
  'name': 'brazilian_portuguese',
  'value': 32,
}),
  33: dict({
  'name': 'indonesian',
  'value': 33,
}),
  34: dict({
  'name': 'malaysian',
  'value': 34,
}),
  35: dict({
  'name': 'vietnamese',
  'value': 35,
}),
  36: dict({
  'name': 'burmese',
  'value': 36,
}),
  37: dict({
  'name': 'mongolian',
  'value': 37,
}),
  254: dict({
  'name': 'custom',
  'value': 254,
}),
}),
}),
  'language_bits_0': dict({
  'name': 'language_bits_0',
  'base_type': 'uint8z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'english',
  'value': 1,
}),
  2: dict({
  'name': 'french',
  'value': 2,
}),
  4: dict({
  'name': 'italian',
  'value': 4,
}),
  8: dict({
  'name': 'german',
  'value': 8,
}),
  16: dict({
  'name': 'spanish',
  'value': 16,
}),
  32: dict({
  'name': 'croatian',
  'value': 32,
}),
  64: dict({
  'name': 'czech',
  'value': 64,
}),
  128: dict({
  'name': 'danish',
  'value': 128,
}),
}),
  'comment': 'Bit field corresponding to language enum type (1 << language).',
}),
  'language_bits_1': dict({
  'name': 'language_bits_1',
  'base_type': 'uint8z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'dutch',
  'value': 1,
}),
  2: dict({
  'name': 'finnish',
  'value': 2,
}),
  4: dict({
  'name': 'greek',
  'value': 4,
}),
  8: dict({
  'name': 'hungarian',
  'value': 8,
}),
  16: dict({
  'name': 'norwegian',
  'value': 16,
}),
  32: dict({
  'name': 'polish',
  'value': 32,
}),
  64: dict({
  'name': 'portuguese',
  'value': 64,
}),
  128: dict({
  'name': 'slovakian',
  'value': 128,
}),
}),
}),
  'language_bits_2': dict({
  'name': 'language_bits_2',
  'base_type': 'uint8z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'slovenian',
  'value': 1,
}),
  2: dict({
  'name': 'swedish',
  'value': 2,
}),
  4: dict({
  'name': 'russian',
  'value': 4,
}),
  8: dict({
  'name': 'turkish',
  'value': 8,
}),
  16: dict({
  'name': 'latvian',
  'value': 16,
}),
  32: dict({
  'name': 'ukrainian',
  'value': 32,
}),
  64: dict({
  'name': 'arabic',
  'value': 64,
}),
  128: dict({
  'name': 'farsi',
  'value': 128,
}),
}),
}),
  'language_bits_3': dict({
  'name': 'language_bits_3',
  'base_type': 'uint8z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'bulgarian',
  'value': 1,
}),
  2: dict({
  'name': 'romanian',
  'value': 2,
}),
  4: dict({
  'name': 'chinese',
  'value': 4,
}),
  8: dict({
  'name': 'japanese',
  'value': 8,
}),
  16: dict({
  'name': 'korean',
  'value': 16,
}),
  32: dict({
  'name': 'taiwanese',
  'value': 32,
}),
  64: dict({
  'name': 'thai',
  'value': 64,
}),
  128: dict({
  'name': 'hebrew',
  'value': 128,
}),
}),
}),
  'language_bits_4': dict({
  'name': 'language_bits_4',
  'base_type': 'uint8z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'brazilian_portuguese',
  'value': 1,
}),
  2: dict({
  'name': 'indonesian',
  'value': 2,
}),
  4: dict({
  'name': 'malaysian',
  'value': 4,
}),
  8: dict({
  'name': 'vietnamese',
  'value': 8,
}),
  16: dict({
  'name': 'burmese',
  'value': 16,
}),
  32: dict({
  'name': 'mongolian',
  'value': 32,
}),
}),
}),
  'time_zone': dict({
  'name': 'time_zone',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'almaty',
  'value': 0,
}),
  1: dict({
  'name': 'bangkok',
  'value': 1,
}),
  2: dict({
  'name': 'bombay',
  'value': 2,
}),
  3: dict({
  'name': 'brasilia',
  'value': 3,
}),
  4: dict({
  'name': 'cairo',
  'value': 4,
}),
  5: dict({
  'name': 'cape_verde_is',
  'value': 5,
}),
  6: dict({
  'name': 'darwin',
  'value': 6,
}),
  7: dict({
  'name': 'eniwetok',
  'value': 7,
}),
  8: dict({
  'name': 'fiji',
  'value': 8,
}),
  9: dict({
  'name': 'hong_kong',
  'value': 9,
}),
  10: dict({
  'name': 'islamabad',
  'value': 10,
}),
  11: dict({
  'name': 'kabul',
  'value': 11,
}),
  12: dict({
  'name': 'magadan',
  'value': 12,
}),
  13: dict({
  'name': 'mid_atlantic',
  'value': 13,
}),
  14: dict({
  'name': 'moscow',
  'value': 14,
}),
  15: dict({
  'name': 'muscat',
  'value': 15,
}),
  16: dict({
  'name': 'newfoundland',
  'value': 16,
}),
  17: dict({
  'name': 'samoa',
  'value': 17,
}),
  18: dict({
  'name': 'sydney',
  'value': 18,
}),
  19: dict({
  'name': 'tehran',
  'value': 19,
}),
  20: dict({
  'name': 'tokyo',
  'value': 20,
}),
  21: dict({
  'name': 'us_alaska',
  'value': 21,
}),
  22: dict({
  'name': 'us_atlantic',
  'value': 22,
}),
  23: dict({
  'name': 'us_central',
  'value': 23,
}),
  24: dict({
  'name': 'us_eastern',
  'value': 24,
}),
  25: dict({
  'name': 'us_hawaii',
  'value': 25,
}),
  26: dict({
  'name': 'us_mountain',
  'value': 26,
}),
  27: dict({
  'name': 'us_pacific',
  'value': 27,
}),
  28: dict({
  'name': 'other',
  'value': 28,
}),
  29: dict({
  'name': 'auckland',
  'value': 29,
}),
  30: dict({
  'name': 'kathmandu',
  'value': 30,
}),
  31: dict({
  'name': 'europe_western_wet',
  'value': 31,
}),
  32: dict({
  'name': 'europe_central_cet',
  'value': 32,
}),
  33: dict({
  'name': 'europe_eastern_eet',
  'value': 33,
}),
  34: dict({
  'name': 'jakarta',
  'value': 34,
}),
  35: dict({
  'name': 'perth',
  'value': 35,
}),
  36: dict({
  'name': 'adelaide',
  'value': 36,
}),
  37: dict({
  'name': 'brisbane',
  'value': 37,
}),
  38: dict({
  'name': 'tasmania',
  'value': 38,
}),
  39: dict({
  'name': 'iceland',
  'value': 39,
}),
  40: dict({
  'name': 'amsterdam',
  'value': 40,
}),
  41: dict({
  'name': 'athens',
  'value': 41,
}),
  42: dict({
  'name': 'barcelona',
  'value': 42,
}),
  43: dict({
  'name': 'berlin',
  'value': 43,
}),
  44: dict({
  'name': 'brussels',
  'value': 44,
}),
  45: dict({
  'name': 'budapest',
  'value': 45,
}),
  46: dict({
  'name': 'copenhagen',
  'value': 46,
}),
  47: dict({
  'name': 'dublin',
  'value': 47,
}),
  48: dict({
  'name': 'helsinki',
  'value': 48,
}),
  49: dict({
  'name': 'lisbon',
  'value': 49,
}),
  50: dict({
  'name': 'london',
  'value': 50,
}),
  51: dict({
  'name': 'madrid',
  'value': 51,
}),
  52: dict({
  'name': 'munich',
  'value': 52,
}),
  53: dict({
  'name': 'oslo',
  'value': 53,
}),
  54: dict({
  'name': 'paris',
  'value': 54,
}),
  55: dict({
  'name': 'prague',
  'value': 55,
}),
  56: dict({
  'name': 'reykjavik',
  'value': 56,
}),
  57: dict({
  'name': 'rome',
  'value': 57,
}),
  58: dict({
  'name': 'stockholm',
  'value': 58,
}),
  59: dict({
  'name': 'vienna',
  'value': 59,
}),
  60: dict({
  'name': 'warsaw',
  'value': 60,
}),
  61: dict({
  'name': 'zurich',
  'value': 61,
}),
  62: dict({
  'name': 'quebec',
  'value': 62,
}),
  63: dict({
  'name': 'ontario',
  'value': 63,
}),
  64: dict({
  'name': 'manitoba',
  'value': 64,
}),
  65: dict({
  'name': 'saskatchewan',
  'value': 65,
}),
  66: dict({
  'name': 'alberta',
  'value': 66,
}),
  67: dict({
  'name': 'british_columbia',
  'value': 67,
}),
  68: dict({
  'name': 'boise',
  'value': 68,
}),
  69: dict({
  'name': 'boston',
  'value': 69,
}),
  70: dict({
  'name': 'chicago',
  'value': 70,
}),
  71: dict({
  'name': 'dallas',
  'value': 71,
}),
  72: dict({
  'name': 'denver',
  'value': 72,
}),
  73: dict({
  'name': 'kansas_city',
  'value': 73,
}),
  74: dict({
  'name': 'las_vegas',
  'value': 74,
}),
  75: dict({
  'name': 'los_angeles',
  'value': 75,
}),
  76: dict({
  'name': 'miami',
  'value': 76,
}),
  77: dict({
  'name': 'minneapolis',
  'value': 77,
}),
  78: dict({
  'name': 'new_york',
  'value': 78,
}),
  79: dict({
  'name': 'new_orleans',
  'value': 79,
}),
  80: dict({
  'name': 'phoenix',
  'value': 80,
}),
  81: dict({
  'name': 'santa_fe',
  'value': 81,
}),
  82: dict({
  'name': 'seattle',
  'value': 82,
}),
  83: dict({
  'name': 'washington_dc',
  'value': 83,
}),
  84: dict({
  'name': 'us_arizona',
  'value': 84,
}),
  85: dict({
  'name': 'chita',
  'value': 85,
}),
  86: dict({
  'name': 'ekaterinburg',
  'value': 86,
}),
  87: dict({
  'name': 'irkutsk',
  'value': 87,
}),
  88: dict({
  'name': 'kaliningrad',
  'value': 88,
}),
  89: dict({
  'name': 'krasnoyarsk',
  'value': 89,
}),
  90: dict({
  'name': 'novosibirsk',
  'value': 90,
}),
  91: dict({
  'name': 'petropavlovsk_kamchatskiy',
  'value': 91,
}),
  92: dict({
  'name': 'samara',
  'value': 92,
}),
  93: dict({
  'name': 'vladivostok',
  'value': 93,
}),
  94: dict({
  'name': 'mexico_central',
  'value': 94,
}),
  95: dict({
  'name': 'mexico_mountain',
  'value': 95,
}),
  96: dict({
  'name': 'mexico_pacific',
  'value': 96,
}),
  97: dict({
  'name': 'cape_town',
  'value': 97,
}),
  98: dict({
  'name': 'winkhoek',
  'value': 98,
}),
  99: dict({
  'name': 'lagos',
  'value': 99,
}),
  100: dict({
  'name': 'riyahd',
  'value': 100,
}),
  101: dict({
  'name': 'venezuela',
  'value': 101,
}),
  102: dict({
  'name': 'australia_lh',
  'value': 102,
}),
  103: dict({
  'name': 'santiago',
  'value': 103,
}),
  253: dict({
  'name': 'manual',
  'value': 253,
}),
  254: dict({
  'name': 'automatic',
  'value': 254,
}),
}),
}),
  'display_measure': dict({
  'name': 'display_measure',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'metric',
  'value': 0,
}),
  1: dict({
  'name': 'statute',
  'value': 1,
}),
  2: dict({
  'name': 'nautical',
  'value': 2,
}),
}),
}),
  'display_heart': dict({
  'name': 'display_heart',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'bpm',
  'value': 0,
}),
  1: dict({
  'name': 'max',
  'value': 1,
}),
  2: dict({
  'name': 'reserve',
  'value': 2,
}),
}),
}),
  'display_power': dict({
  'name': 'display_power',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'watts',
  'value': 0,
}),
  1: dict({
  'name': 'percent_ftp',
  'value': 1,
}),
}),
}),
  'display_position': dict({
  'name': 'display_position',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'degree',
  'value': 0,
  'comment': 'dd.dddddd',
}),
  1: dict({
  'name': 'degree_minute',
  'value': 1,
  'comment': 'dddmm.mmm',
}),
  2: dict({
  'name': 'degree_minute_second',
  'value': 2,
  'comment': 'dddmmss',
}),
  3: dict({
  'name': 'austrian_grid',
  'value': 3,
  'comment': 'Austrian Grid (BMN)',
}),
  4: dict({
  'name': 'british_grid',
  'value': 4,
  'comment': 'British National Grid',
}),
  5: dict({
  'name': 'dutch_grid',
  'value': 5,
  'comment': 'Dutch grid system',
}),
  6: dict({
  'name': 'hungarian_grid',
  'value': 6,
  'comment': 'Hungarian grid system',
}),
  7: dict({
  'name': 'finnish_grid',
  'value': 7,
  'comment': 'Finnish grid system Zone3 KKJ27',
}),
  8: dict({
  'name': 'german_grid',
  'value': 8,
  'comment': 'Gausss Krueger (German)',
}),
  9: dict({
  'name': 'icelandic_grid',
  'value': 9,
  'comment': 'Icelandic Grid',
}),
  10: dict({
  'name': 'indonesian_equatorial',
  'value': 10,
  'comment': 'Indonesian Equatorial LCO',
}),
  11: dict({
  'name': 'indonesian_irian',
  'value': 11,
  'comment': 'Indonesian Irian LCO',
}),
  12: dict({
  'name': 'indonesian_southern',
  'value': 12,
  'comment': 'Indonesian Southern LCO',
}),
  13: dict({
  'name': 'india_zone_0',
  'value': 13,
  'comment': 'India zone 0',
}),
  14: dict({
  'name': 'india_zone_IA',
  'value': 14,
  'comment': 'India zone IA',
}),
  15: dict({
  'name': 'india_zone_IB',
  'value': 15,
  'comment': 'India zone IB',
}),
  16: dict({
  'name': 'india_zone_IIA',
  'value': 16,
  'comment': 'India zone IIA',
}),
  17: dict({
  'name': 'india_zone_IIB',
  'value': 17,
  'comment': 'India zone IIB',
}),
  18: dict({
  'name': 'india_zone_IIIA',
  'value': 18,
  'comment': 'India zone IIIA',
}),
  19: dict({
  'name': 'india_zone_IIIB',
  'value': 19,
  'comment': 'India zone IIIB',
}),
  20: dict({
  'name': 'india_zone_IVA',
  'value': 20,
  'comment': 'India zone IVA',
}),
  21: dict({
  'name': 'india_zone_IVB',
  'value': 21,
  'comment': 'India zone IVB',
}),
  22: dict({
  'name': 'irish_transverse',
  'value': 22,
  'comment': 'Irish Transverse Mercator',
}),
  23: dict({
  'name': 'irish_grid',
  'value': 23,
  'comment': 'Irish Grid',
}),
  24: dict({
  'name': 'loran',
  'value': 24,
  'comment': 'Loran TD',
}),
  25: dict({
  'name': 'maidenhead_grid',
  'value': 25,
  'comment': 'Maidenhead grid system',
}),
  26: dict({
  'name': 'mgrs_grid',
  'value': 26,
  'comment': 'MGRS grid system',
}),
  27: dict({
  'name': 'new_zealand_grid',
  'value': 27,
  'comment': 'New Zealand grid system',
}),
  28: dict({
  'name': 'new_zealand_transverse',
  'value': 28,
  'comment': 'New Zealand Transverse Mercator',
}),
  29: dict({
  'name': 'qatar_grid',
  'value': 29,
  'comment': 'Qatar National Grid',
}),
  30: dict({
  'name': 'modified_swedish_grid',
  'value': 30,
  'comment': 'Modified RT-90 (Sweden)',
}),
  31: dict({
  'name': 'swedish_grid',
  'value': 31,
  'comment': 'RT-90 (Sweden)',
}),
  32: dict({
  'name': 'south_african_grid',
  'value': 32,
  'comment': 'South African Grid',
}),
  33: dict({
  'name': 'swiss_grid',
  'value': 33,
  'comment': 'Swiss CH-1903 grid',
}),
  34: dict({
  'name': 'taiwan_grid',
  'value': 34,
  'comment': 'Taiwan Grid',
}),
  35: dict({
  'name': 'united_states_grid',
  'value': 35,
  'comment': 'United States National Grid',
}),
  36: dict({
  'name': 'utm_ups_grid',
  'value': 36,
  'comment': 'UTM/UPS grid system',
}),
  37: dict({
  'name': 'west_malayan',
  'value': 37,
  'comment': 'West Malayan RSO',
}),
  38: dict({
  'name': 'borneo_rso',
  'value': 38,
  'comment': 'Borneo RSO',
}),
  39: dict({
  'name': 'estonian_grid',
  'value': 39,
  'comment': 'Estonian grid system',
}),
  40: dict({
  'name': 'latvian_grid',
  'value': 40,
  'comment': 'Latvian Transverse Mercator',
}),
  41: dict({
  'name': 'swedish_ref_99_grid',
  'value': 41,
  'comment': 'Reference Grid 99 TM (Swedish)',
}),
}),
}),
  'switch': dict({
  'name': 'switch',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'off',
  'value': 0,
}),
  1: dict({
  'name': 'on',
  'value': 1,
}),
  2: dict({
  'name': 'auto',
  'value': 2,
}),
}),
}),
  'sport': dict({
  'name': 'sport',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'generic',
  'value': 0,
}),
  1: dict({
  'name': 'running',
  'value': 1,
}),
  2: dict({
  'name': 'cycling',
  'value': 2,
}),
  3: dict({
  'name': 'transition',
  'value': 3,
  'comment': 'Mulitsport transition',
}),
  4: dict({
  'name': 'fitness_equipment',
  'value': 4,
}),
  5: dict({
  'name': 'swimming',
  'value': 5,
}),
  6: dict({
  'name': 'basketball',
  'value': 6,
}),
  7: dict({
  'name': 'soccer',
  'value': 7,
}),
  8: dict({
  'name': 'tennis',
  'value': 8,
}),
  9: dict({
  'name': 'american_football',
  'value': 9,
}),
  10: dict({
  'name': 'training',
  'value': 10,
}),
  11: dict({
  'name': 'walking',
  'value': 11,
}),
  12: dict({
  'name': 'cross_country_skiing',
  'value': 12,
}),
  13: dict({
  'name': 'alpine_skiing',
  'value': 13,
}),
  14: dict({
  'name': 'snowboarding',
  'value': 14,
}),
  15: dict({
  'name': 'rowing',
  'value': 15,
}),
  16: dict({
  'name': 'mountaineering',
  'value': 16,
}),
  17: dict({
  'name': 'hiking',
  'value': 17,
}),
  18: dict({
  'name': 'multisport',
  'value': 18,
}),
  19: dict({
  'name': 'paddling',
  'value': 19,
}),
  20: dict({
  'name': 'flying',
  'value': 20,
}),
  21: dict({
  'name': 'e_biking',
  'value': 21,
}),
  22: dict({
  'name': 'motorcycling',
  'value': 22,
}),
  23: dict({
  'name': 'boating',
  'value': 23,
}),
  24: dict({
  'name': 'driving',
  'value': 24,
}),
  25: dict({
  'name': 'golf',
  'value': 25,
}),
  26: dict({
  'name': 'hang_gliding',
  'value': 26,
}),
  27: dict({
  'name': 'horseback_riding',
  'value': 27,
}),
  28: dict({
  'name': 'hunting',
  'value': 28,
}),
  29: dict({
  'name': 'fishing',
  'value': 29,
}),
  30: dict({
  'name': 'inline_skating',
  'value': 30,
}),
  31: dict({
  'name': 'rock_climbing',
  'value': 31,
}),
  32: dict({
  'name': 'sailing',
  'value': 32,
}),
  33: dict({
  'name': 'ice_skating',
  'value': 33,
}),
  34: dict({
  'name': 'sky_diving',
  'value': 34,
}),
  35: dict({
  'name': 'snowshoeing',
  'value': 35,
}),
  36: dict({
  'name': 'snowmobiling',
  'value': 36,
}),
  37: dict({
  'name': 'stand_up_paddleboarding',
  'value': 37,
}),
  38: dict({
  'name': 'surfing',
  'value': 38,
}),
  39: dict({
  'name': 'wakeboarding',
  'value': 39,
}),
  40: dict({
  'name': 'water_skiing',
  'value': 40,
}),
  41: dict({
  'name': 'kayaking',
  'value': 41,
}),
  42: dict({
  'name': 'rafting',
  'value': 42,
}),
  43: dict({
  'name': 'windsurfing',
  'value': 43,
}),
  44: dict({
  'name': 'kitesurfing',
  'value': 44,
}),
  45: dict({
  'name': 'tactical',
  'value': 45,
}),
  46: dict({
  'name': 'jumpmaster',
  'value': 46,
}),
  47: dict({
  'name': 'boxing',
  'value': 47,
}),
  48: dict({
  'name': 'floor_climbing',
  'value': 48,
}),
  53: dict({
  'name': 'diving',
  'value': 53,
}),
  254: dict({
  'name': 'all',
  'value': 254,
  'comment': 'All is for goals only to include all sports.',
}),
}),
}),
  'sport_bits_0': dict({
  'name': 'sport_bits_0',
  'base_type': 'uint8z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'generic',
  'value': 1,
}),
  2: dict({
  'name': 'running',
  'value': 2,
}),
  4: dict({
  'name': 'cycling',
  'value': 4,
}),
  8: dict({
  'name': 'transition',
  'value': 8,
  'comment': 'Mulitsport transition',
}),
  16: dict({
  'name': 'fitness_equipment',
  'value': 16,
}),
  32: dict({
  'name': 'swimming',
  'value': 32,
}),
  64: dict({
  'name': 'basketball',
  'value': 64,
}),
  128: dict({
  'name': 'soccer',
  'value': 128,
}),
}),
  'comment': 'Bit field corresponding to sport enum type (1 << sport).',
}),
  'sport_bits_1': dict({
  'name': 'sport_bits_1',
  'base_type': 'uint8z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'tennis',
  'value': 1,
}),
  2: dict({
  'name': 'american_football',
  'value': 2,
}),
  4: dict({
  'name': 'training',
  'value': 4,
}),
  8: dict({
  'name': 'walking',
  'value': 8,
}),
  16: dict({
  'name': 'cross_country_skiing',
  'value': 16,
}),
  32: dict({
  'name': 'alpine_skiing',
  'value': 32,
}),
  64: dict({
  'name': 'snowboarding',
  'value': 64,
}),
  128: dict({
  'name': 'rowing',
  'value': 128,
}),
}),
  'comment': 'Bit field corresponding to sport enum type (1 << (sport-8)).',
}),
  'sport_bits_2': dict({
  'name': 'sport_bits_2',
  'base_type': 'uint8z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'mountaineering',
  'value': 1,
}),
  2: dict({
  'name': 'hiking',
  'value': 2,
}),
  4: dict({
  'name': 'multisport',
  'value': 4,
}),
  8: dict({
  'name': 'paddling',
  'value': 8,
}),
  16: dict({
  'name': 'flying',
  'value': 16,
}),
  32: dict({
  'name': 'e_biking',
  'value': 32,
}),
  64: dict({
  'name': 'motorcycling',
  'value': 64,
}),
  128: dict({
  'name': 'boating',
  'value': 128,
}),
}),
  'comment': 'Bit field corresponding to sport enum type (1 << (sport-16)).',
}),
  'sport_bits_3': dict({
  'name': 'sport_bits_3',
  'base_type': 'uint8z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'driving',
  'value': 1,
}),
  2: dict({
  'name': 'golf',
  'value': 2,
}),
  4: dict({
  'name': 'hang_gliding',
  'value': 4,
}),
  8: dict({
  'name': 'horseback_riding',
  'value': 8,
}),
  16: dict({
  'name': 'hunting',
  'value': 16,
}),
  32: dict({
  'name': 'fishing',
  'value': 32,
}),
  64: dict({
  'name': 'inline_skating',
  'value': 64,
}),
  128: dict({
  'name': 'rock_climbing',
  'value': 128,
}),
}),
  'comment': 'Bit field corresponding to sport enum type (1 << (sport-24)).',
}),
  'sport_bits_4': dict({
  'name': 'sport_bits_4',
  'base_type': 'uint8z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'sailing',
  'value': 1,
}),
  2: dict({
  'name': 'ice_skating',
  'value': 2,
}),
  4: dict({
  'name': 'sky_diving',
  'value': 4,
}),
  8: dict({
  'name': 'snowshoeing',
  'value': 8,
}),
  16: dict({
  'name': 'snowmobiling',
  'value': 16,
}),
  32: dict({
  'name': 'stand_up_paddleboarding',
  'value': 32,
}),
  64: dict({
  'name': 'surfing',
  'value': 64,
}),
  128: dict({
  'name': 'wakeboarding',
  'value': 128,
}),
}),
  'comment': 'Bit field corresponding to sport enum type (1 << (sport-32)).',
}),
  'sport_bits_5': dict({
  'name': 'sport_bits_5',
  'base_type': 'uint8z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'water_skiing',
  'value': 1,
}),
  2: dict({
  'name': 'kayaking',
  'value': 2,
}),
  4: dict({
  'name': 'rafting',
  'value': 4,
}),
  8: dict({
  'name': 'windsurfing',
  'value': 8,
}),
  16: dict({
  'name': 'kitesurfing',
  'value': 16,
}),
  32: dict({
  'name': 'tactical',
  'value': 32,
}),
  64: dict({
  'name': 'jumpmaster',
  'value': 64,
}),
  128: dict({
  'name': 'boxing',
  'value': 128,
}),
}),
  'comment': 'Bit field corresponding to sport enum type (1 << (sport-40)).',
}),
  'sport_bits_6': dict({
  'name': 'sport_bits_6',
  'base_type': 'uint8z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'floor_climbing',
  'value': 1,
}),
}),
  'comment': 'Bit field corresponding to sport enum type (1 << (sport-48)).',
}),
  'sub_sport': dict({
  'name': 'sub_sport',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'generic',
  'value': 0,
}),
  1: dict({
  'name': 'treadmill',
  'value': 1,
  'comment': 'Run/Fitness Equipment',
}),
  2: dict({
  'name': 'street',
  'value': 2,
  'comment': 'Run',
}),
  3: dict({
  'name': 'trail',
  'value': 3,
  'comment': 'Run',
}),
  4: dict({
  'name': 'track',
  'value': 4,
  'comment': 'Run',
}),
  5: dict({
  'name': 'spin',
  'value': 5,
  'comment': 'Cycling',
}),
  6: dict({
  'name': 'indoor_cycling',
  'value': 6,
  'comment': 'Cycling/Fitness Equipment',
}),
  7: dict({
  'name': 'road',
  'value': 7,
  'comment': 'Cycling',
}),
  8: dict({
  'name': 'mountain',
  'value': 8,
  'comment': 'Cycling',
}),
  9: dict({
  'name': 'downhill',
  'value': 9,
  'comment': 'Cycling',
}),
  10: dict({
  'name': 'recumbent',
  'value': 10,
  'comment': 'Cycling',
}),
  11: dict({
  'name': 'cyclocross',
  'value': 11,
  'comment': 'Cycling',
}),
  12: dict({
  'name': 'hand_cycling',
  'value': 12,
  'comment': 'Cycling',
}),
  13: dict({
  'name': 'track_cycling',
  'value': 13,
  'comment': 'Cycling',
}),
  14: dict({
  'name': 'indoor_rowing',
  'value': 14,
  'comment': 'Fitness Equipment',
}),
  15: dict({
  'name': 'elliptical',
  'value': 15,
  'comment': 'Fitness Equipment',
}),
  16: dict({
  'name': 'stair_climbing',
  'value': 16,
  'comment': 'Fitness Equipment',
}),
  17: dict({
  'name': 'lap_swimming',
  'value': 17,
  'comment': 'Swimming',
}),
  18: dict({
  'name': 'open_water',
  'value': 18,
  'comment': 'Swimming',
}),
  19: dict({
  'name': 'flexibility_training',
  'value': 19,
  'comment': 'Training',
}),
  20: dict({
  'name': 'strength_training',
  'value': 20,
  'comment': 'Training',
}),
  21: dict({
  'name': 'warm_up',
  'value': 21,
  'comment': 'Tennis',
}),
  22: dict({
  'name': 'match',
  'value': 22,
  'comment': 'Tennis',
}),
  23: dict({
  'name': 'exercise',
  'value': 23,
  'comment': 'Tennis',
}),
  24: dict({
  'name': 'challenge',
  'value': 24,
}),
  25: dict({
  'name': 'indoor_skiing',
  'value': 25,
  'comment': 'Fitness Equipment',
}),
  26: dict({
  'name': 'cardio_training',
  'value': 26,
  'comment': 'Training',
}),
  27: dict({
  'name': 'indoor_walking',
  'value': 27,
  'comment': 'Walking/Fitness Equipment',
}),
  28: dict({
  'name': 'e_bike_fitness',
  'value': 28,
  'comment': 'E-Biking',
}),
  29: dict({
  'name': 'bmx',
  'value': 29,
  'comment': 'Cycling',
}),
  30: dict({
  'name': 'casual_walking',
  'value': 30,
  'comment': 'Walking',
}),
  31: dict({
  'name': 'speed_walking',
  'value': 31,
  'comment': 'Walking',
}),
  32: dict({
  'name': 'bike_to_run_transition',
  'value': 32,
  'comment': 'Transition',
}),
  33: dict({
  'name': 'run_to_bike_transition',
  'value': 33,
  'comment': 'Transition',
}),
  34: dict({
  'name': 'swim_to_bike_transition',
  'value': 34,
  'comment': 'Transition',
}),
  35: dict({
  'name': 'atv',
  'value': 35,
  'comment': 'Motorcycling',
}),
  36: dict({
  'name': 'motocross',
  'value': 36,
  'comment': 'Motorcycling',
}),
  37: dict({
  'name': 'backcountry',
  'value': 37,
  'comment': 'Alpine Skiing/Snowboarding',
}),
  38: dict({
  'name': 'resort',
  'value': 38,
  'comment': 'Alpine Skiing/Snowboarding',
}),
  39: dict({
  'name': 'rc_drone',
  'value': 39,
  'comment': 'Flying',
}),
  40: dict({
  'name': 'wingsuit',
  'value': 40,
  'comment': 'Flying',
}),
  41: dict({
  'name': 'whitewater',
  'value': 41,
  'comment': 'Kayaking/Rafting',
}),
  42: dict({
  'name': 'skate_skiing',
  'value': 42,
  'comment': 'Cross Country Skiing',
}),
  43: dict({
  'name': 'yoga',
  'value': 43,
  'comment': 'Training',
}),
  44: dict({
  'name': 'pilates',
  'value': 44,
  'comment': 'Fitness Equipment',
}),
  45: dict({
  'name': 'indoor_running',
  'value': 45,
  'comment': 'Run',
}),
  46: dict({
  'name': 'gravel_cycling',
  'value': 46,
  'comment': 'Cycling',
}),
  47: dict({
  'name': 'e_bike_mountain',
  'value': 47,
  'comment': 'Cycling',
}),
  48: dict({
  'name': 'commuting',
  'value': 48,
  'comment': 'Cycling',
}),
  49: dict({
  'name': 'mixed_surface',
  'value': 49,
  'comment': 'Cycling',
}),
  50: dict({
  'name': 'navigate',
  'value': 50,
}),
  51: dict({
  'name': 'track_me',
  'value': 51,
}),
  52: dict({
  'name': 'map',
  'value': 52,
}),
  53: dict({
  'name': 'single_gas_diving',
  'value': 53,
  'comment': 'Diving',
}),
  54: dict({
  'name': 'multi_gas_diving',
  'value': 54,
  'comment': 'Diving',
}),
  55: dict({
  'name': 'gauge_diving',
  'value': 55,
  'comment': 'Diving',
}),
  56: dict({
  'name': 'apnea_diving',
  'value': 56,
  'comment': 'Diving',
}),
  57: dict({
  'name': 'apnea_hunting',
  'value': 57,
  'comment': 'Diving',
}),
  58: dict({
  'name': 'virtual_activity',
  'value': 58,
}),
  59: dict({
  'name': 'obstacle',
  'value': 59,
  'comment': 'Used for events where participants run, crawl through mud, climb over walls, etc.',
}),
  62: dict({
  'name': 'breathing',
  'value': 62,
}),
  65: dict({
  'name': 'sail_race',
  'value': 65,
  'comment': 'Sailing',
}),
  67: dict({
  'name': 'ultra',
  'value': 67,
  'comment': 'Ultramarathon',
}),
  68: dict({
  'name': 'indoor_climbing',
  'value': 68,
  'comment': 'Climbing',
}),
  69: dict({
  'name': 'bouldering',
  'value': 69,
  'comment': 'Climbing',
}),
  254: dict({
  'name': 'all',
  'value': 254,
}),
}),
}),
  'sport_event': dict({
  'name': 'sport_event',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'uncategorized',
  'value': 0,
}),
  1: dict({
  'name': 'geocaching',
  'value': 1,
}),
  2: dict({
  'name': 'fitness',
  'value': 2,
}),
  3: dict({
  'name': 'recreation',
  'value': 3,
}),
  4: dict({
  'name': 'race',
  'value': 4,
}),
  5: dict({
  'name': 'special_event',
  'value': 5,
}),
  6: dict({
  'name': 'training',
  'value': 6,
}),
  7: dict({
  'name': 'transportation',
  'value': 7,
}),
  8: dict({
  'name': 'touring',
  'value': 8,
}),
}),
}),
  'activity': dict({
  'name': 'activity',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'manual',
  'value': 0,
}),
  1: dict({
  'name': 'auto_multi_sport',
  'value': 1,
}),
}),
}),
  'intensity': dict({
  'name': 'intensity',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'active',
  'value': 0,
}),
  1: dict({
  'name': 'rest',
  'value': 1,
}),
  2: dict({
  'name': 'warmup',
  'value': 2,
}),
  3: dict({
  'name': 'cooldown',
  'value': 3,
}),
  4: dict({
  'name': 'recovery',
  'value': 4,
}),
  5: dict({
  'name': 'interval',
  'value': 5,
}),
  6: dict({
  'name': 'other',
  'value': 6,
}),
}),
}),
  'session_trigger': dict({
  'name': 'session_trigger',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'activity_end',
  'value': 0,
}),
  1: dict({
  'name': 'manual',
  'value': 1,
  'comment': 'User changed sport.',
}),
  2: dict({
  'name': 'auto_multi_sport',
  'value': 2,
  'comment': 'Auto multi-sport feature is enabled and user pressed lap button to advance session.',
}),
  3: dict({
  'name': 'fitness_equipment',
  'value': 3,
  'comment': 'Auto sport change caused by user linking to fitness equipment.',
}),
}),
}),
  'autolap_trigger': dict({
  'name': 'autolap_trigger',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'time',
  'value': 0,
}),
  1: dict({
  'name': 'distance',
  'value': 1,
}),
  2: dict({
  'name': 'position_start',
  'value': 2,
}),
  3: dict({
  'name': 'position_lap',
  'value': 3,
}),
  4: dict({
  'name': 'position_waypoint',
  'value': 4,
}),
  5: dict({
  'name': 'position_marked',
  'value': 5,
}),
  6: dict({
  'name': 'off',
  'value': 6,
}),
}),
}),
  'lap_trigger': dict({
  'name': 'lap_trigger',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'manual',
  'value': 0,
}),
  1: dict({
  'name': 'time',
  'value': 1,
}),
  2: dict({
  'name': 'distance',
  'value': 2,
}),
  3: dict({
  'name': 'position_start',
  'value': 3,
}),
  4: dict({
  'name': 'position_lap',
  'value': 4,
}),
  5: dict({
  'name': 'position_waypoint',
  'value': 5,
}),
  6: dict({
  'name': 'position_marked',
  'value': 6,
}),
  7: dict({
  'name': 'session_end',
  'value': 7,
}),
  8: dict({
  'name': 'fitness_equipment',
  'value': 8,
}),
}),
}),
  'time_mode': dict({
  'name': 'time_mode',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'hour12',
  'value': 0,
}),
  1: dict({
  'name': 'hour24',
  'value': 1,
  'comment': 'Does not use a leading zero and has a colon',
}),
  2: dict({
  'name': 'military',
  'value': 2,
  'comment': 'Uses a leading zero and does not have a colon',
}),
  3: dict({
  'name': 'hour_12_with_seconds',
  'value': 3,
}),
  4: dict({
  'name': 'hour_24_with_seconds',
  'value': 4,
}),
  5: dict({
  'name': 'utc',
  'value': 5,
}),
}),
}),
  'backlight_mode': dict({
  'name': 'backlight_mode',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'off',
  'value': 0,
}),
  1: dict({
  'name': 'manual',
  'value': 1,
}),
  2: dict({
  'name': 'key_and_messages',
  'value': 2,
}),
  3: dict({
  'name': 'auto_brightness',
  'value': 3,
}),
  4: dict({
  'name': 'smart_notifications',
  'value': 4,
}),
  5: dict({
  'name': 'key_and_messages_night',
  'value': 5,
}),
  6: dict({
  'name': 'key_and_messages_and_smart_notifications',
  'value': 6,
}),
}),
}),
  'date_mode': dict({
  'name': 'date_mode',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'day_month',
  'value': 0,
}),
  1: dict({
  'name': 'month_day',
  'value': 1,
}),
}),
}),
  'backlight_timeout': dict({
  'name': 'backlight_timeout',
  'base_type': 'uint8',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'infinite',
  'value': 0,
  'comment': 'Backlight stays on forever.',
}),
}),
  'comment': 'Timeout in seconds.',
}),
  'event': dict({
  'name': 'event',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'timer',
  'value': 0,
  'comment': 'Group 0.  Start / stop_all',
}),
  3: dict({
  'name': 'workout',
  'value': 3,
  'comment': 'start / stop',
}),
  4: dict({
  'name': 'workout_step',
  'value': 4,
  'comment': 'Start at beginning of workout.  Stop at end of each step.',
}),
  5: dict({
  'name': 'power_down',
  'value': 5,
  'comment': 'stop_all group 0',
}),
  6: dict({
  'name': 'power_up',
  'value': 6,
  'comment': 'stop_all group 0',
}),
  7: dict({
  'name': 'off_course',
  'value': 7,
  'comment': 'start / stop group 0',
}),
  8: dict({
  'name': 'session',
  'value': 8,
  'comment': 'Stop at end of each session.',
}),
  9: dict({
  'name': 'lap',
  'value': 9,
  'comment': 'Stop at end of each lap.',
}),
  10: dict({
  'name': 'course_point',
  'value': 10,
  'comment': 'marker',
}),
  11: dict({
  'name': 'battery',
  'value': 11,
  'comment': 'marker',
}),
  12: dict({
  'name': 'virtual_partner_pace',
  'value': 12,
  'comment': 'Group 1. Start at beginning of activity if VP enabled, when VP pace is changed during activity or VP enabled mid activity.  stop_disable when VP disabled.',
}),
  13: dict({
  'name': 'hr_high_alert',
  'value': 13,
  'comment': 'Group 0.  Start / stop when in alert condition.',
}),
  14: dict({
  'name': 'hr_low_alert',
  'value': 14,
  'comment': 'Group 0.  Start / stop when in alert condition.',
}),
  15: dict({
  'name': 'speed_high_alert',
  'value': 15,
  'comment': 'Group 0.  Start / stop when in alert condition.',
}),
  16: dict({
  'name': 'speed_low_alert',
  'value': 16,
  'comment': 'Group 0.  Start / stop when in alert condition.',
}),
  17: dict({
  'name': 'cad_high_alert',
  'value': 17,
  'comment': 'Group 0.  Start / stop when in alert condition.',
}),
  18: dict({
  'name': 'cad_low_alert',
  'value': 18,
  'comment': 'Group 0.  Start / stop when in alert condition.',
}),
  19: dict({
  'name': 'power_high_alert',
  'value': 19,
  'comment': 'Group 0.  Start / stop when in alert condition.',
}),
  20: dict({
  'name': 'power_low_alert',
  'value': 20,
  'comment': 'Group 0.  Start / stop when in alert condition.',
}),
  21: dict({
  'name': 'recovery_hr',
  'value': 21,
  'comment': 'marker',
}),
  22: dict({
  'name': 'battery_low',
  'value': 22,
  'comment': 'marker',
}),
  23: dict({
  'name': 'time_duration_alert',
  'value': 23,
  'comment': 'Group 1.  Start if enabled mid activity (not required at start of activity). Stop when duration is reached.  stop_disable if disabled.',
}),
  24: dict({
  'name': 'distance_duration_alert',
  'value': 24,
  'comment': 'Group 1.  Start if enabled mid activity (not required at start of activity). Stop when duration is reached.  stop_disable if disabled.',
}),
  25: dict({
  'name': 'calorie_duration_alert',
  'value': 25,
  'comment': 'Group 1.  Start if enabled mid activity (not required at start of activity). Stop when duration is reached.  stop_disable if disabled.',
}),
  26: dict({
  'name': 'activity',
  'value': 26,
  'comment': 'Group 1..  Stop at end of activity.',
}),
  27: dict({
  'name': 'fitness_equipment',
  'value': 27,
  'comment': 'marker',
}),
  28: dict({
  'name': 'length',
  'value': 28,
  'comment': 'Stop at end of each length.',
}),
  32: dict({
  'name': 'user_marker',
  'value': 32,
  'comment': 'marker',
}),
  33: dict({
  'name': 'sport_point',
  'value': 33,
  'comment': 'marker',
}),
  36: dict({
  'name': 'calibration',
  'value': 36,
  'comment': 'start/stop/marker',
}),
  42: dict({
  'name': 'front_gear_change',
  'value': 42,
  'comment': 'marker',
}),
  43: dict({
  'name': 'rear_gear_change',
  'value': 43,
  'comment': 'marker',
}),
  44: dict({
  'name': 'rider_position_change',
  'value': 44,
  'comment': 'marker',
}),
  45: dict({
  'name': 'elev_high_alert',
  'value': 45,
  'comment': 'Group 0.  Start / stop when in alert condition.',
}),
  46: dict({
  'name': 'elev_low_alert',
  'value': 46,
  'comment': 'Group 0.  Start / stop when in alert condition.',
}),
  47: dict({
  'name': 'comm_timeout',
  'value': 47,
  'comment': 'marker',
}),
  75: dict({
  'name': 'radar_threat_alert',
  'value': 75,
  'comment': 'start/stop/marker',
}),
}),
}),
  'event_type': dict({
  'name': 'event_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'start',
  'value': 0,
}),
  1: dict({
  'name': 'stop',
  'value': 1,
}),
  2: dict({
  'name': 'consecutive_depreciated',
  'value': 2,
}),
  3: dict({
  'name': 'marker',
  'value': 3,
}),
  4: dict({
  'name': 'stop_all',
  'value': 4,
}),
  5: dict({
  'name': 'begin_depreciated',
  'value': 5,
}),
  6: dict({
  'name': 'end_depreciated',
  'value': 6,
}),
  7: dict({
  'name': 'end_all_depreciated',
  'value': 7,
}),
  8: dict({
  'name': 'stop_disable',
  'value': 8,
}),
  9: dict({
  'name': 'stop_disable_all',
  'value': 9,
}),
}),
}),
  'timer_trigger': dict({
  'name': 'timer_trigger',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'manual',
  'value': 0,
}),
  1: dict({
  'name': 'auto',
  'value': 1,
}),
  2: dict({
  'name': 'fitness_equipment',
  'value': 2,
}),
}),
  'comment': 'timer event data',
}),
  'fitness_equipment_state': dict({
  'name': 'fitness_equipment_state',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'ready',
  'value': 0,
}),
  1: dict({
  'name': 'in_use',
  'value': 1,
}),
  2: dict({
  'name': 'paused',
  'value': 2,
}),
  3: dict({
  'name': 'unknown',
  'value': 3,
  'comment': 'lost connection to fitness equipment',
}),
}),
  'comment': 'fitness equipment event data',
}),
  'tone': dict({
  'name': 'tone',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'off',
  'value': 0,
}),
  1: dict({
  'name': 'tone',
  'value': 1,
}),
  2: dict({
  'name': 'vibrate',
  'value': 2,
}),
  3: dict({
  'name': 'tone_and_vibrate',
  'value': 3,
}),
}),
}),
  'autoscroll': dict({
  'name': 'autoscroll',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'none',
  'value': 0,
}),
  1: dict({
  'name': 'slow',
  'value': 1,
}),
  2: dict({
  'name': 'medium',
  'value': 2,
}),
  3: dict({
  'name': 'fast',
  'value': 3,
}),
}),
}),
  'activity_class': dict({
  'name': 'activity_class',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  127: dict({
  'name': 'level',
  'value': 127,
  'comment': '0 to 100',
}),
  100: dict({
  'name': 'level_max',
  'value': 100,
}),
  128: dict({
  'name': 'athlete',
  'value': 128,
}),
}),
}),
  'hr_zone_calc': dict({
  'name': 'hr_zone_calc',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'custom',
  'value': 0,
}),
  1: dict({
  'name': 'percent_max_hr',
  'value': 1,
}),
  2: dict({
  'name': 'percent_hrr',
  'value': 2,
}),
}),
}),
  'pwr_zone_calc': dict({
  'name': 'pwr_zone_calc',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'custom',
  'value': 0,
}),
  1: dict({
  'name': 'percent_ftp',
  'value': 1,
}),
}),
}),
  'wkt_step_duration': dict({
  'name': 'wkt_step_duration',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'time',
  'value': 0,
}),
  1: dict({
  'name': 'distance',
  'value': 1,
}),
  2: dict({
  'name': 'hr_less_than',
  'value': 2,
}),
  3: dict({
  'name': 'hr_greater_than',
  'value': 3,
}),
  4: dict({
  'name': 'calories',
  'value': 4,
}),
  5: dict({
  'name': 'open',
  'value': 5,
}),
  6: dict({
  'name': 'repeat_until_steps_cmplt',
  'value': 6,
}),
  7: dict({
  'name': 'repeat_until_time',
  'value': 7,
}),
  8: dict({
  'name': 'repeat_until_distance',
  'value': 8,
}),
  9: dict({
  'name': 'repeat_until_calories',
  'value': 9,
}),
  10: dict({
  'name': 'repeat_until_hr_less_than',
  'value': 10,
}),
  11: dict({
  'name': 'repeat_until_hr_greater_than',
  'value': 11,
}),
  12: dict({
  'name': 'repeat_until_power_less_than',
  'value': 12,
}),
  13: dict({
  'name': 'repeat_until_power_greater_than',
  'value': 13,
}),
  14: dict({
  'name': 'power_less_than',
  'value': 14,
}),
  15: dict({
  'name': 'power_greater_than',
  'value': 15,
}),
  16: dict({
  'name': 'training_peaks_tss',
  'value': 16,
}),
  17: dict({
  'name': 'repeat_until_power_last_lap_less_than',
  'value': 17,
}),
  18: dict({
  'name': 'repeat_until_max_power_last_lap_less_than',
  'value': 18,
}),
  19: dict({
  'name': 'power_3s_less_than',
  'value': 19,
}),
  20: dict({
  'name': 'power_10s_less_than',
  'value': 20,
}),
  21: dict({
  'name': 'power_30s_less_than',
  'value': 21,
}),
  22: dict({
  'name': 'power_3s_greater_than',
  'value': 22,
}),
  23: dict({
  'name': 'power_10s_greater_than',
  'value': 23,
}),
  24: dict({
  'name': 'power_30s_greater_than',
  'value': 24,
}),
  25: dict({
  'name': 'power_lap_less_than',
  'value': 25,
}),
  26: dict({
  'name': 'power_lap_greater_than',
  'value': 26,
}),
  27: dict({
  'name': 'repeat_until_training_peaks_tss',
  'value': 27,
}),
  28: dict({
  'name': 'repetition_time',
  'value': 28,
}),
  29: dict({
  'name': 'reps',
  'value': 29,
}),
  31: dict({
  'name': 'time_only',
  'value': 31,
}),
}),
}),
  'wkt_step_target': dict({
  'name': 'wkt_step_target',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'speed',
  'value': 0,
}),
  1: dict({
  'name': 'heart_rate',
  'value': 1,
}),
  2: dict({
  'name': 'open',
  'value': 2,
}),
  3: dict({
  'name': 'cadence',
  'value': 3,
}),
  4: dict({
  'name': 'power',
  'value': 4,
}),
  5: dict({
  'name': 'grade',
  'value': 5,
}),
  6: dict({
  'name': 'resistance',
  'value': 6,
}),
  7: dict({
  'name': 'power_3s',
  'value': 7,
}),
  8: dict({
  'name': 'power_10s',
  'value': 8,
}),
  9: dict({
  'name': 'power_30s',
  'value': 9,
}),
  10: dict({
  'name': 'power_lap',
  'value': 10,
}),
  11: dict({
  'name': 'swim_stroke',
  'value': 11,
}),
  12: dict({
  'name': 'speed_lap',
  'value': 12,
}),
  13: dict({
  'name': 'heart_rate_lap',
  'value': 13,
}),
}),
}),
  'goal': dict({
  'name': 'goal',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'time',
  'value': 0,
}),
  1: dict({
  'name': 'distance',
  'value': 1,
}),
  2: dict({
  'name': 'calories',
  'value': 2,
}),
  3: dict({
  'name': 'frequency',
  'value': 3,
}),
  4: dict({
  'name': 'steps',
  'value': 4,
}),
  5: dict({
  'name': 'ascent',
  'value': 5,
}),
  6: dict({
  'name': 'active_minutes',
  'value': 6,
}),
}),
}),
  'goal_recurrence': dict({
  'name': 'goal_recurrence',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'off',
  'value': 0,
}),
  1: dict({
  'name': 'daily',
  'value': 1,
}),
  2: dict({
  'name': 'weekly',
  'value': 2,
}),
  3: dict({
  'name': 'monthly',
  'value': 3,
}),
  4: dict({
  'name': 'yearly',
  'value': 4,
}),
  5: dict({
  'name': 'custom',
  'value': 5,
}),
}),
}),
  'goal_source': dict({
  'name': 'goal_source',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'auto',
  'value': 0,
  'comment': 'Device generated',
}),
  1: dict({
  'name': 'community',
  'value': 1,
  'comment': 'Social network sourced goal',
}),
  2: dict({
  'name': 'user',
  'value': 2,
  'comment': 'Manually generated',
}),
}),
}),
  'schedule': dict({
  'name': 'schedule',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'workout',
  'value': 0,
}),
  1: dict({
  'name': 'course',
  'value': 1,
}),
}),
}),
  'course_point': dict({
  'name': 'course_point',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'generic',
  'value': 0,
}),
  1: dict({
  'name': 'summit',
  'value': 1,
}),
  2: dict({
  'name': 'valley',
  'value': 2,
}),
  3: dict({
  'name': 'water',
  'value': 3,
}),
  4: dict({
  'name': 'food',
  'value': 4,
}),
  5: dict({
  'name': 'danger',
  'value': 5,
}),
  6: dict({
  'name': 'left',
  'value': 6,
}),
  7: dict({
  'name': 'right',
  'value': 7,
}),
  8: dict({
  'name': 'straight',
  'value': 8,
}),
  9: dict({
  'name': 'first_aid',
  'value': 9,
}),
  10: dict({
  'name': 'fourth_category',
  'value': 10,
}),
  11: dict({
  'name': 'third_category',
  'value': 11,
}),
  12: dict({
  'name': 'second_category',
  'value': 12,
}),
  13: dict({
  'name': 'first_category',
  'value': 13,
}),
  14: dict({
  'name': 'hors_category',
  'value': 14,
}),
  15: dict({
  'name': 'sprint',
  'value': 15,
}),
  16: dict({
  'name': 'left_fork',
  'value': 16,
}),
  17: dict({
  'name': 'right_fork',
  'value': 17,
}),
  18: dict({
  'name': 'middle_fork',
  'value': 18,
}),
  19: dict({
  'name': 'slight_left',
  'value': 19,
}),
  20: dict({
  'name': 'sharp_left',
  'value': 20,
}),
  21: dict({
  'name': 'slight_right',
  'value': 21,
}),
  22: dict({
  'name': 'sharp_right',
  'value': 22,
}),
  23: dict({
  'name': 'u_turn',
  'value': 23,
}),
  24: dict({
  'name': 'segment_start',
  'value': 24,
}),
  25: dict({
  'name': 'segment_end',
  'value': 25,
}),
}),
}),
  'manufacturer': dict({
  'name': 'manufacturer',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'garmin',
  'value': 1,
}),
  2: dict({
  'name': 'garmin_fr405_antfs',
  'value': 2,
  'comment': 'Do not use.  Used by FR405 for ANTFS man id.',
}),
  3: dict({
  'name': 'zephyr',
  'value': 3,
}),
  4: dict({
  'name': 'dayton',
  'value': 4,
}),
  5: dict({
  'name': 'idt',
  'value': 5,
}),
  6: dict({
  'name': 'srm',
  'value': 6,
}),
  7: dict({
  'name': 'quarq',
  'value': 7,
}),
  8: dict({
  'name': 'ibike',
  'value': 8,
}),
  9: dict({
  'name': 'saris',
  'value': 9,
}),
  10: dict({
  'name': 'spark_hk',
  'value': 10,
}),
  11: dict({
  'name': 'tanita',
  'value': 11,
}),
  12: dict({
  'name': 'echowell',
  'value': 12,
}),
  13: dict({
  'name': 'dynastream_oem',
  'value': 13,
}),
  14: dict({
  'name': 'nautilus',
  'value': 14,
}),
  15: dict({
  'name': 'dynastream',
  'value': 15,
}),
  16: dict({
  'name': 'timex',
  'value': 16,
}),
  17: dict({
  'name': 'metrigear',
  'value': 17,
}),
  18: dict({
  'name': 'xelic',
  'value': 18,
}),
  19: dict({
  'name': 'beurer',
  'value': 19,
}),
  20: dict({
  'name': 'cardiosport',
  'value': 20,
}),
  21: dict({
  'name': 'a_and_d',
  'value': 21,
}),
  22: dict({
  'name': 'hmm',
  'value': 22,
}),
  23: dict({
  'name': 'suunto',
  'value': 23,
}),
  24: dict({
  'name': 'thita_elektronik',
  'value': 24,
}),
  25: dict({
  'name': 'gpulse',
  'value': 25,
}),
  26: dict({
  'name': 'clean_mobile',
  'value': 26,
}),
  27: dict({
  'name': 'pedal_brain',
  'value': 27,
}),
  28: dict({
  'name': 'peaksware',
  'value': 28,
}),
  29: dict({
  'name': 'saxonar',
  'value': 29,
}),
  30: dict({
  'name': 'lemond_fitness',
  'value': 30,
}),
  31: dict({
  'name': 'dexcom',
  'value': 31,
}),
  32: dict({
  'name': 'wahoo_fitness',
  'value': 32,
}),
  33: dict({
  'name': 'octane_fitness',
  'value': 33,
}),
  34: dict({
  'name': 'archinoetics',
  'value': 34,
}),
  35: dict({
  'name': 'the_hurt_box',
  'value': 35,
}),
  36: dict({
  'name': 'citizen_systems',
  'value': 36,
}),
  37: dict({
  'name': 'magellan',
  'value': 37,
}),
  38: dict({
  'name': 'osynce',
  'value': 38,
}),
  39: dict({
  'name': 'holux',
  'value': 39,
}),
  40: dict({
  'name': 'concept2',
  'value': 40,
}),
  41: dict({
  'name': 'shimano',
  'value': 41,
}),
  42: dict({
  'name': 'one_giant_leap',
  'value': 42,
}),
  43: dict({
  'name': 'ace_sensor',
  'value': 43,
}),
  44: dict({
  'name': 'brim_brothers',
  'value': 44,
}),
  45: dict({
  'name': 'xplova',
  'value': 45,
}),
  46: dict({
  'name': 'perception_digital',
  'value': 46,
}),
  47: dict({
  'name': 'bf1systems',
  'value': 47,
}),
  48: dict({
  'name': 'pioneer',
  'value': 48,
}),
  49: dict({
  'name': 'spantec',
  'value': 49,
}),
  50: dict({
  'name': 'metalogics',
  'value': 50,
}),
  51: dict({
  'name': '4iiiis',
  'value': 51,
}),
  52: dict({
  'name': 'seiko_epson',
  'value': 52,
}),
  53: dict({
  'name': 'seiko_epson_oem',
  'value': 53,
}),
  54: dict({
  'name': 'ifor_powell',
  'value': 54,
}),
  55: dict({
  'name': 'maxwell_guider',
  'value': 55,
}),
  56: dict({
  'name': 'star_trac',
  'value': 56,
}),
  57: dict({
  'name': 'breakaway',
  'value': 57,
}),
  58: dict({
  'name': 'alatech_technology_ltd',
  'value': 58,
}),
  59: dict({
  'name': 'mio_technology_europe',
  'value': 59,
}),
  60: dict({
  'name': 'rotor',
  'value': 60,
}),
  61: dict({
  'name': 'geonaute',
  'value': 61,
}),
  62: dict({
  'name': 'id_bike',
  'value': 62,
}),
  63: dict({
  'name': 'specialized',
  'value': 63,
}),
  64: dict({
  'name': 'wtek',
  'value': 64,
}),
  65: dict({
  'name': 'physical_enterprises',
  'value': 65,
}),
  66: dict({
  'name': 'north_pole_engineering',
  'value': 66,
}),
  67: dict({
  'name': 'bkool',
  'value': 67,
}),
  68: dict({
  'name': 'cateye',
  'value': 68,
}),
  69: dict({
  'name': 'stages_cycling',
  'value': 69,
}),
  70: dict({
  'name': 'sigmasport',
  'value': 70,
}),
  71: dict({
  'name': 'tomtom',
  'value': 71,
}),
  72: dict({
  'name': 'peripedal',
  'value': 72,
}),
  73: dict({
  'name': 'wattbike',
  'value': 73,
}),
  76: dict({
  'name': 'moxy',
  'value': 76,
}),
  77: dict({
  'name': 'ciclosport',
  'value': 77,
}),
  78: dict({
  'name': 'powerbahn',
  'value': 78,
}),
  79: dict({
  'name': 'acorn_projects_aps',
  'value': 79,
}),
  80: dict({
  'name': 'lifebeam',
  'value': 80,
}),
  81: dict({
  'name': 'bontrager',
  'value': 81,
}),
  82: dict({
  'name': 'wellgo',
  'value': 82,
}),
  83: dict({
  'name': 'scosche',
  'value': 83,
}),
  84: dict({
  'name': 'magura',
  'value': 84,
}),
  85: dict({
  'name': 'woodway',
  'value': 85,
}),
  86: dict({
  'name': 'elite',
  'value': 86,
}),
  87: dict({
  'name': 'nielsen_kellerman',
  'value': 87,
}),
  88: dict({
  'name': 'dk_city',
  'value': 88,
}),
  89: dict({
  'name': 'tacx',
  'value': 89,
}),
  90: dict({
  'name': 'direction_technology',
  'value': 90,
}),
  91: dict({
  'name': 'magtonic',
  'value': 91,
}),
  92: dict({
  'name': '1partcarbon',
  'value': 92,
}),
  93: dict({
  'name': 'inside_ride_technologies',
  'value': 93,
}),
  94: dict({
  'name': 'sound_of_motion',
  'value': 94,
}),
  95: dict({
  'name': 'stryd',
  'value': 95,
}),
  96: dict({
  'name': 'icg',
  'value': 96,
  'comment': 'Indoorcycling Group',
}),
  97: dict({
  'name': 'MiPulse',
  'value': 97,
}),
  98: dict({
  'name': 'bsx_athletics',
  'value': 98,
}),
  99: dict({
  'name': 'look',
  'value': 99,
}),
  100: dict({
  'name': 'campagnolo_srl',
  'value': 100,
}),
  101: dict({
  'name': 'body_bike_smart',
  'value': 101,
}),
  102: dict({
  'name': 'praxisworks',
  'value': 102,
}),
  103: dict({
  'name': 'limits_technology',
  'value': 103,
  'comment': 'Limits Technology Ltd.',
}),
  104: dict({
  'name': 'topaction_technology',
  'value': 104,
  'comment': 'TopAction Technology Inc.',
}),
  105: dict({
  'name': 'cosinuss',
  'value': 105,
}),
  106: dict({
  'name': 'fitcare',
  'value': 106,
}),
  107: dict({
  'name': 'magene',
  'value': 107,
}),
  108: dict({
  'name': 'giant_manufacturing_co',
  'value': 108,
}),
  109: dict({
  'name': 'tigrasport',
  'value': 109,
  'comment': 'Tigrasport',
}),
  110: dict({
  'name': 'salutron',
  'value': 110,
}),
  111: dict({
  'name': 'technogym',
  'value': 111,
}),
  112: dict({
  'name': 'bryton_sensors',
  'value': 112,
}),
  113: dict({
  'name': 'latitude_limited',
  'value': 113,
}),
  114: dict({
  'name': 'soaring_technology',
  'value': 114,
}),
  115: dict({
  'name': 'igpsport',
  'value': 115,
}),
  116: dict({
  'name': 'thinkrider',
  'value': 116,
}),
  117: dict({
  'name': 'gopher_sport',
  'value': 117,
}),
  118: dict({
  'name': 'waterrower',
  'value': 118,
}),
  119: dict({
  'name': 'orangetheory',
  'value': 119,
}),
  120: dict({
  'name': 'inpeak',
  'value': 120,
}),
  121: dict({
  'name': 'kinetic',
  'value': 121,
}),
  122: dict({
  'name': 'johnson_health_tech',
  'value': 122,
}),
  123: dict({
  'name': 'polar_electro',
  'value': 123,
}),
  124: dict({
  'name': 'seesense',
  'value': 124,
}),
  125: dict({
  'name': 'nci_technology',
  'value': 125,
}),
  126: dict({
  'name': 'iqsquare',
  'value': 126,
}),
  127: dict({
  'name': 'leomo',
  'value': 127,
}),
  128: dict({
  'name': 'ifit_com',
  'value': 128,
}),
  129: dict({
  'name': 'coros_byte',
  'value': 129,
}),
  130: dict({
  'name': 'versa_design',
  'value': 130,
}),
  131: dict({
  'name': 'chileaf',
  'value': 131,
}),
  132: dict({
  'name': 'cycplus',
  'value': 132,
}),
  133: dict({
  'name': 'gravaa_byte',
  'value': 133,
}),
  134: dict({
  'name': 'sigeyi',
  'value': 134,
}),
  135: dict({
  'name': 'coospo',
  'value': 135,
}),
  136: dict({
  'name': 'geoid',
  'value': 136,
}),
  255: dict({
  'name': 'development',
  'value': 255,
}),
  257: dict({
  'name': 'healthandlife',
  'value': 257,
}),
  258: dict({
  'name': 'lezyne',
  'value': 258,
}),
  259: dict({
  'name': 'scribe_labs',
  'value': 259,
}),
  260: dict({
  'name': 'zwift',
  'value': 260,
}),
  261: dict({
  'name': 'watteam',
  'value': 261,
}),
  262: dict({
  'name': 'recon',
  'value': 262,
}),
  263: dict({
  'name': 'favero_electronics',
  'value': 263,
}),
  264: dict({
  'name': 'dynovelo',
  'value': 264,
}),
  265: dict({
  'name': 'strava',
  'value': 265,
}),
  266: dict({
  'name': 'precor',
  'value': 266,
  'comment': 'Amer Sports',
}),
  267: dict({
  'name': 'bryton',
  'value': 267,
}),
  268: dict({
  'name': 'sram',
  'value': 268,
}),
  269: dict({
  'name': 'navman',
  'value': 269,
  'comment': 'MiTAC Global Corporation (Mio Technology)',
}),
  270: dict({
  'name': 'cobi',
  'value': 270,
  'comment': 'COBI GmbH',
}),
  271: dict({
  'name': 'spivi',
  'value': 271,
}),
  272: dict({
  'name': 'mio_magellan',
  'value': 272,
}),
  273: dict({
  'name': 'evesports',
  'value': 273,
}),
  274: dict({
  'name': 'sensitivus_gauge',
  'value': 274,
}),
  275: dict({
  'name': 'podoon',
  'value': 275,
}),
  276: dict({
  'name': 'life_time_fitness',
  'value': 276,
}),
  277: dict({
  'name': 'falco_e_motors',
  'value': 277,
  'comment': 'Falco eMotors Inc.',
}),
  278: dict({
  'name': 'minoura',
  'value': 278,
}),
  279: dict({
  'name': 'cycliq',
  'value': 279,
}),
  280: dict({
  'name': 'luxottica',
  'value': 280,
}),
  281: dict({
  'name': 'trainer_road',
  'value': 281,
}),
  282: dict({
  'name': 'the_sufferfest',
  'value': 282,
}),
  283: dict({
  'name': 'fullspeedahead',
  'value': 283,
}),
  284: dict({
  'name': 'virtualtraining',
  'value': 284,
}),
  285: dict({
  'name': 'feedbacksports',
  'value': 285,
}),
  286: dict({
  'name': 'omata',
  'value': 286,
}),
  287: dict({
  'name': 'vdo',
  'value': 287,
}),
  288: dict({
  'name': 'magneticdays',
  'value': 288,
}),
  289: dict({
  'name': 'hammerhead',
  'value': 289,
}),
  290: dict({
  'name': 'kinetic_by_kurt',
  'value': 290,
}),
  291: dict({
  'name': 'shapelog',
  'value': 291,
}),
  292: dict({
  'name': 'dabuziduo',
  'value': 292,
}),
  293: dict({
  'name': 'jetblack',
  'value': 293,
}),
  294: dict({
  'name': 'coros',
  'value': 294,
}),
  295: dict({
  'name': 'virtugo',
  'value': 295,
}),
  296: dict({
  'name': 'velosense',
  'value': 296,
}),
  297: dict({
  'name': 'cycligentinc',
  'value': 297,
}),
  298: dict({
  'name': 'trailforks',
  'value': 298,
}),
  299: dict({
  'name': 'mahle_ebikemotion',
  'value': 299,
}),
  300: dict({
  'name': 'nurvv',
  'value': 300,
}),
  301: dict({
  'name': 'microprogram',
  'value': 301,
}),
  302: dict({
  'name': 'zone5cloud',
  'value': 302,
}),
  303: dict({
  'name': 'greenteg',
  'value': 303,
}),
  304: dict({
  'name': 'yamaha_motors',
  'value': 304,
}),
  305: dict({
  'name': 'whoop',
  'value': 305,
}),
  306: dict({
  'name': 'gravaa',
  'value': 306,
}),
  307: dict({
  'name': 'onelap',
  'value': 307,
}),
  308: dict({
  'name': 'monark_exercise',
  'value': 308,
}),
  309: dict({
  'name': 'form',
  'value': 309,
}),
  310: dict({
  'name': 'decathlon',
  'value': 310,
}),
  311: dict({
  'name': 'syncros',
  'value': 311,
}),
  5759: dict({
  'name': 'actigraphcorp',
  'value': 5759,
}),
}),
}),
  'garmin_product': dict({
  'name': 'garmin_product',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'hrm1',
  'value': 1,
}),
  2: dict({
  'name': 'axh01',
  'value': 2,
  'comment': 'AXH01 HRM chipset',
}),
  3: dict({
  'name': 'axb01',
  'value': 3,
}),
  4: dict({
  'name': 'axb02',
  'value': 4,
}),
  5: dict({
  'name': 'hrm2ss',
  'value': 5,
}),
  6: dict({
  'name': 'dsi_alf02',
  'value': 6,
}),
  7: dict({
  'name': 'hrm3ss',
  'value': 7,
}),
  8: dict({
  'name': 'hrm_run_single_byte_product_id',
  'value': 8,
  'comment': 'hrm_run model for HRM ANT+ messaging',
}),
  9: dict({
  'name': 'bsm',
  'value': 9,
  'comment': 'BSM model for ANT+ messaging',
}),
  10: dict({
  'name': 'bcm',
  'value': 10,
  'comment': 'BCM model for ANT+ messaging',
}),
  11: dict({
  'name': 'axs01',
  'value': 11,
  'comment': 'AXS01 HRM Bike Chipset model for ANT+ messaging',
}),
  12: dict({
  'name': 'hrm_tri_single_byte_product_id',
  'value': 12,
  'comment': 'hrm_tri model for HRM ANT+ messaging',
}),
  13: dict({
  'name': 'hrm4_run_single_byte_product_id',
  'value': 13,
  'comment': 'hrm4 run model for HRM ANT+ messaging',
}),
  14: dict({
  'name': 'fr225_single_byte_product_id',
  'value': 14,
  'comment': 'fr225 model for HRM ANT+ messaging',
}),
  15: dict({
  'name': 'gen3_bsm_single_byte_product_id',
  'value': 15,
  'comment': 'gen3_bsm model for Bike Speed ANT+ messaging',
}),
  16: dict({
  'name': 'gen3_bcm_single_byte_product_id',
  'value': 16,
  'comment': 'gen3_bcm model for Bike Cadence ANT+ messaging',
}),
  473: dict({
  'name': 'fr301_china',
  'value': 473,
}),
  474: dict({
  'name': 'fr301_japan',
  'value': 474,
}),
  475: dict({
  'name': 'fr301_korea',
  'value': 475,
}),
  494: dict({
  'name': 'fr301_taiwan',
  'value': 494,
}),
  717: dict({
  'name': 'fr405',
  'value': 717,
  'comment': 'Forerunner 405',
}),
  782: dict({
  'name': 'fr50',
  'value': 782,
  'comment': 'Forerunner 50',
}),
  987: dict({
  'name': 'fr405_japan',
  'value': 987,
}),
  988: dict({
  'name': 'fr60',
  'value': 988,
  'comment': 'Forerunner 60',
}),
  1011: dict({
  'name': 'dsi_alf01',
  'value': 1011,
}),
  1018: dict({
  'name': 'fr310xt',
  'value': 1018,
  'comment': 'Forerunner 310',
}),
  1036: dict({
  'name': 'edge500',
  'value': 1036,
}),
  1124: dict({
  'name': 'fr110',
  'value': 1124,
  'comment': 'Forerunner 110',
}),
  1169: dict({
  'name': 'edge800',
  'value': 1169,
}),
  1199: dict({
  'name': 'edge500_taiwan',
  'value': 1199,
}),
  1213: dict({
  'name': 'edge500_japan',
  'value': 1213,
}),
  1253: dict({
  'name': 'chirp',
  'value': 1253,
}),
  1274: dict({
  'name': 'fr110_japan',
  'value': 1274,
}),
  1325: dict({
  'name': 'edge200',
  'value': 1325,
}),
  1328: dict({
  'name': 'fr910xt',
  'value': 1328,
}),
  1333: dict({
  'name': 'edge800_taiwan',
  'value': 1333,
}),
  1334: dict({
  'name': 'edge800_japan',
  'value': 1334,
}),
  1341: dict({
  'name': 'alf04',
  'value': 1341,
}),
  1345: dict({
  'name': 'fr610',
  'value': 1345,
}),
  1360: dict({
  'name': 'fr210_japan',
  'value': 1360,
}),
  1380: dict({
  'name': 'vector_ss',
  'value': 1380,
}),
  1381: dict({
  'name': 'vector_cp',
  'value': 1381,
}),
  1386: dict({
  'name': 'edge800_china',
  'value': 1386,
}),
  1387: dict({
  'name': 'edge500_china',
  'value': 1387,
}),
  1405: dict({
  'name': 'approach_g10',
  'value': 1405,
}),
  1410: dict({
  'name': 'fr610_japan',
  'value': 1410,
}),
  1422: dict({
  'name': 'edge500_korea',
  'value': 1422,
}),
  1436: dict({
  'name': 'fr70',
  'value': 1436,
}),
  1446: dict({
  'name': 'fr310xt_4t',
  'value': 1446,
}),
  1461: dict({
  'name': 'amx',
  'value': 1461,
}),
  1482: dict({
  'name': 'fr10',
  'value': 1482,
}),
  1497: dict({
  'name': 'edge800_korea',
  'value': 1497,
}),
  1499: dict({
  'name': 'swim',
  'value': 1499,
}),
  1537: dict({
  'name': 'fr910xt_china',
  'value': 1537,
}),
  1551: dict({
  'name': 'fenix',
  'value': 1551,
}),
  1555: dict({
  'name': 'edge200_taiwan',
  'value': 1555,
}),
  1561: dict({
  'name': 'edge510',
  'value': 1561,
}),
  1567: dict({
  'name': 'edge810',
  'value': 1567,
}),
  1570: dict({
  'name': 'tempe',
  'value': 1570,
}),
  1600: dict({
  'name': 'fr910xt_japan',
  'value': 1600,
}),
  1623: dict({
  'name': 'fr620',
  'value': 1623,
}),
  1632: dict({
  'name': 'fr220',
  'value': 1632,
}),
  1664: dict({
  'name': 'fr910xt_korea',
  'value': 1664,
}),
  1688: dict({
  'name': 'fr10_japan',
  'value': 1688,
}),
  1721: dict({
  'name': 'edge810_japan',
  'value': 1721,
}),
  1735: dict({
  'name': 'virb_elite',
  'value': 1735,
}),
  1736: dict({
  'name': 'edge_touring',
  'value': 1736,
  'comment': 'Also Edge Touring Plus',
}),
  1742: dict({
  'name': 'edge510_japan',
  'value': 1742,
}),
  1743: dict({
  'name': 'hrm_tri',
  'value': 1743,
  'comment': 'Also HRM-Swim',
}),
  1752: dict({
  'name': 'hrm_run',
  'value': 1752,
}),
  1765: dict({
  'name': 'fr920xt',
  'value': 1765,
}),
  1821: dict({
  'name': 'edge510_asia',
  'value': 1821,
}),
  1822: dict({
  'name': 'edge810_china',
  'value': 1822,
}),
  1823: dict({
  'name': 'edge810_taiwan',
  'value': 1823,
}),
  1836: dict({
  'name': 'edge1000',
  'value': 1836,
}),
  1837: dict({
  'name': 'vivo_fit',
  'value': 1837,
}),
  1853: dict({
  'name': 'virb_remote',
  'value': 1853,
}),
  1885: dict({
  'name': 'vivo_ki',
  'value': 1885,
}),
  1903: dict({
  'name': 'fr15',
  'value': 1903,
}),
  1907: dict({
  'name': 'vivo_active',
  'value': 1907,
}),
  1918: dict({
  'name': 'edge510_korea',
  'value': 1918,
}),
  1928: dict({
  'name': 'fr620_japan',
  'value': 1928,
}),
  1929: dict({
  'name': 'fr620_china',
  'value': 1929,
}),
  1930: dict({
  'name': 'fr220_japan',
  'value': 1930,
}),
  1931: dict({
  'name': 'fr220_china',
  'value': 1931,
}),
  1936: dict({
  'name': 'approach_s6',
  'value': 1936,
}),
  1956: dict({
  'name': 'vivo_smart',
  'value': 1956,
}),
  1967: dict({
  'name': 'fenix2',
  'value': 1967,
}),
  1988: dict({
  'name': 'epix',
  'value': 1988,
}),
  2050: dict({
  'name': 'fenix3',
  'value': 2050,
}),
  2052: dict({
  'name': 'edge1000_taiwan',
  'value': 2052,
}),
  2053: dict({
  'name': 'edge1000_japan',
  'value': 2053,
}),
  2061: dict({
  'name': 'fr15_japan',
  'value': 2061,
}),
  2067: dict({
  'name': 'edge520',
  'value': 2067,
}),
  2070: dict({
  'name': 'edge1000_china',
  'value': 2070,
}),
  2072: dict({
  'name': 'fr620_russia',
  'value': 2072,
}),
  2073: dict({
  'name': 'fr220_russia',
  'value': 2073,
}),
  2079: dict({
  'name': 'vector_s',
  'value': 2079,
}),
  2100: dict({
  'name': 'edge1000_korea',
  'value': 2100,
}),
  2130: dict({
  'name': 'fr920xt_taiwan',
  'value': 2130,
}),
  2131: dict({
  'name': 'fr920xt_china',
  'value': 2131,
}),
  2132: dict({
  'name': 'fr920xt_japan',
  'value': 2132,
}),
  2134: dict({
  'name': 'virbx',
  'value': 2134,
}),
  2135: dict({
  'name': 'vivo_smart_apac',
  'value': 2135,
}),
  2140: dict({
  'name': 'etrex_touch',
  'value': 2140,
}),
  2147: dict({
  'name': 'edge25',
  'value': 2147,
}),
  2148: dict({
  'name': 'fr25',
  'value': 2148,
}),
  2150: dict({
  'name': 'vivo_fit2',
  'value': 2150,
}),
  2153: dict({
  'name': 'fr225',
  'value': 2153,
}),
  2156: dict({
  'name': 'fr630',
  'value': 2156,
}),
  2157: dict({
  'name': 'fr230',
  'value': 2157,
}),
  2158: dict({
  'name': 'fr735xt',
  'value': 2158,
}),
  2160: dict({
  'name': 'vivo_active_apac',
  'value': 2160,
}),
  2161: dict({
  'name': 'vector_2',
  'value': 2161,
}),
  2162: dict({
  'name': 'vector_2s',
  'value': 2162,
}),
  2172: dict({
  'name': 'virbxe',
  'value': 2172,
}),
  2173: dict({
  'name': 'fr620_taiwan',
  'value': 2173,
}),
  2174: dict({
  'name': 'fr220_taiwan',
  'value': 2174,
}),
  2175: dict({
  'name': 'truswing',
  'value': 2175,
}),
  2187: dict({
  'name': 'd2airvenu',
  'value': 2187,
}),
  2188: dict({
  'name': 'fenix3_china',
  'value': 2188,
}),
  2189: dict({
  'name': 'fenix3_twn',
  'value': 2189,
}),
  2192: dict({
  'name': 'varia_headlight',
  'value': 2192,
}),
  2193: dict({
  'name': 'varia_taillight_old',
  'value': 2193,
}),
  2204: dict({
  'name': 'edge_explore_1000',
  'value': 2204,
}),
  2219: dict({
  'name': 'fr225_asia',
  'value': 2219,
}),
  2225: dict({
  'name': 'varia_radar_taillight',
  'value': 2225,
}),
  2226: dict({
  'name': 'varia_radar_display',
  'value': 2226,
}),
  2238: dict({
  'name': 'edge20',
  'value': 2238,
}),
  2260: dict({
  'name': 'edge520_asia',
  'value': 2260,
}),
  2261: dict({
  'name': 'edge520_japan',
  'value': 2261,
}),
  2262: dict({
  'name': 'd2_bravo',
  'value': 2262,
}),
  2266: dict({
  'name': 'approach_s20',
  'value': 2266,
}),
  2271: dict({
  'name': 'vivo_smart2',
  'value': 2271,
}),
  2274: dict({
  'name': 'edge1000_thai',
  'value': 2274,
}),
  2276: dict({
  'name': 'varia_remote',
  'value': 2276,
}),
  2288: dict({
  'name': 'edge25_asia',
  'value': 2288,
}),
  2289: dict({
  'name': 'edge25_jpn',
  'value': 2289,
}),
  2290: dict({
  'name': 'edge20_asia',
  'value': 2290,
}),
  2292: dict({
  'name': 'approach_x40',
  'value': 2292,
}),
  2293: dict({
  'name': 'fenix3_japan',
  'value': 2293,
}),
  2294: dict({
  'name': 'vivo_smart_emea',
  'value': 2294,
}),
  2310: dict({
  'name': 'fr630_asia',
  'value': 2310,
}),
  2311: dict({
  'name': 'fr630_jpn',
  'value': 2311,
}),
  2313: dict({
  'name': 'fr230_jpn',
  'value': 2313,
}),
  2327: dict({
  'name': 'hrm4_run',
  'value': 2327,
}),
  2332: dict({
  'name': 'epix_japan',
  'value': 2332,
}),
  2337: dict({
  'name': 'vivo_active_hr',
  'value': 2337,
}),
  2347: dict({
  'name': 'vivo_smart_gps_hr',
  'value': 2347,
}),
  2348: dict({
  'name': 'vivo_smart_hr',
  'value': 2348,
}),
  2361: dict({
  'name': 'vivo_smart_hr_asia',
  'value': 2361,
}),
  2362: dict({
  'name': 'vivo_smart_gps_hr_asia',
  'value': 2362,
}),
  2368: dict({
  'name': 'vivo_move',
  'value': 2368,
}),
  2379: dict({
  'name': 'varia_taillight',
  'value': 2379,
}),
  2396: dict({
  'name': 'fr235_asia',
  'value': 2396,
}),
  2397: dict({
  'name': 'fr235_japan',
  'value': 2397,
}),
  2398: dict({
  'name': 'varia_vision',
  'value': 2398,
}),
  2406: dict({
  'name': 'vivo_fit3',
  'value': 2406,
}),
  2407: dict({
  'name': 'fenix3_korea',
  'value': 2407,
}),
  2408: dict({
  'name': 'fenix3_sea',
  'value': 2408,
}),
  2413: dict({
  'name': 'fenix3_hr',
  'value': 2413,
}),
  2417: dict({
  'name': 'virb_ultra_30',
  'value': 2417,
}),
  2429: dict({
  'name': 'index_smart_scale',
  'value': 2429,
}),
  2431: dict({
  'name': 'fr235',
  'value': 2431,
}),
  2432: dict({
  'name': 'fenix3_chronos',
  'value': 2432,
}),
  2441: dict({
  'name': 'oregon7xx',
  'value': 2441,
}),
  2444: dict({
  'name': 'rino7xx',
  'value': 2444,
}),
  2457: dict({
  'name': 'epix_korea',
  'value': 2457,
}),
  2473: dict({
  'name': 'fenix3_hr_chn',
  'value': 2473,
}),
  2474: dict({
  'name': 'fenix3_hr_twn',
  'value': 2474,
}),
  2475: dict({
  'name': 'fenix3_hr_jpn',
  'value': 2475,
}),
  2476: dict({
  'name': 'fenix3_hr_sea',
  'value': 2476,
}),
  2477: dict({
  'name': 'fenix3_hr_kor',
  'value': 2477,
}),
  2496: dict({
  'name': 'nautix',
  'value': 2496,
}),
  2497: dict({
  'name': 'vivo_active_hr_apac',
  'value': 2497,
}),
  2512: dict({
  'name': 'oregon7xx_ww',
  'value': 2512,
}),
  2530: dict({
  'name': 'edge_820',
  'value': 2530,
}),
  2531: dict({
  'name': 'edge_explore_820',
  'value': 2531,
}),
  2533: dict({
  'name': 'fr735xt_apac',
  'value': 2533,
}),
  2534: dict({
  'name': 'fr735xt_japan',
  'value': 2534,
}),
  2544: dict({
  'name': 'fenix5s',
  'value': 2544,
}),
  2547: dict({
  'name': 'd2_bravo_titanium',
  'value': 2547,
}),
  2567: dict({
  'name': 'varia_ut800',
  'value': 2567,
  'comment': 'Varia UT 800 SW',
}),
  2593: dict({
  'name': 'running_dynamics_pod',
  'value': 2593,
}),
  2599: dict({
  'name': 'edge_820_china',
  'value': 2599,
}),
  2600: dict({
  'name': 'edge_820_japan',
  'value': 2600,
}),
  2604: dict({
  'name': 'fenix5x',
  'value': 2604,
}),
  2606: dict({
  'name': 'vivo_fit_jr',
  'value': 2606,
}),
  2622: dict({
  'name': 'vivo_smart3',
  'value': 2622,
}),
  2623: dict({
  'name': 'vivo_sport',
  'value': 2623,
}),
  2628: dict({
  'name': 'edge_820_taiwan',
  'value': 2628,
}),
  2629: dict({
  'name': 'edge_820_korea',
  'value': 2629,
}),
  2630: dict({
  'name': 'edge_820_sea',
  'value': 2630,
}),
  2650: dict({
  'name': 'fr35_hebrew',
  'value': 2650,
}),
  2656: dict({
  'name': 'approach_s60',
  'value': 2656,
}),
  2667: dict({
  'name': 'fr35_apac',
  'value': 2667,
}),
  2668: dict({
  'name': 'fr35_japan',
  'value': 2668,
}),
  2675: dict({
  'name': 'fenix3_chronos_asia',
  'value': 2675,
}),
  2687: dict({
  'name': 'virb_360',
  'value': 2687,
}),
  2691: dict({
  'name': 'fr935',
  'value': 2691,
}),
  2697: dict({
  'name': 'fenix5',
  'value': 2697,
}),
  2700: dict({
  'name': 'vivoactive3',
  'value': 2700,
}),
  2733: dict({
  'name': 'fr235_china_nfc',
  'value': 2733,
}),
  2769: dict({
  'name': 'foretrex_601_701',
  'value': 2769,
}),
  2772: dict({
  'name': 'vivo_move_hr',
  'value': 2772,
}),
  2713: dict({
  'name': 'edge_1030',
  'value': 2713,
}),
  2787: dict({
  'name': 'vector_3',
  'value': 2787,
}),
  2796: dict({
  'name': 'fenix5_asia',
  'value': 2796,
}),
  2797: dict({
  'name': 'fenix5s_asia',
  'value': 2797,
}),
  2798: dict({
  'name': 'fenix5x_asia',
  'value': 2798,
}),
  2806: dict({
  'name': 'approach_z80',
  'value': 2806,
}),
  2814: dict({
  'name': 'fr35_korea',
  'value': 2814,
}),
  2819: dict({
  'name': 'd2charlie',
  'value': 2819,
}),
  2831: dict({
  'name': 'vivo_smart3_apac',
  'value': 2831,
}),
  2832: dict({
  'name': 'vivo_sport_apac',
  'value': 2832,
}),
  2833: dict({
  'name': 'fr935_asia',
  'value': 2833,
}),
  2859: dict({
  'name': 'descent',
  'value': 2859,
}),
  2878: dict({
  'name': 'vivo_fit4',
  'value': 2878,
}),
  2886: dict({
  'name': 'fr645',
  'value': 2886,
}),
  2888: dict({
  'name': 'fr645m',
  'value': 2888,
}),
  2891: dict({
  'name': 'fr30',
  'value': 2891,
}),
  2900: dict({
  'name': 'fenix5s_plus',
  'value': 2900,
}),
  2909: dict({
  'name': 'Edge_130',
  'value': 2909,
}),
  2924: dict({
  'name': 'edge_1030_asia',
  'value': 2924,
}),
  2927: dict({
  'name': 'vivosmart_4',
  'value': 2927,
}),
  2945: dict({
  'name': 'vivo_move_hr_asia',
  'value': 2945,
}),
  2962: dict({
  'name': 'approach_x10',
  'value': 2962,
}),
  2977: dict({
  'name': 'fr30_asia',
  'value': 2977,
}),
  2988: dict({
  'name': 'vivoactive3m_w',
  'value': 2988,
}),
  3003: dict({
  'name': 'fr645_asia',
  'value': 3003,
}),
  3004: dict({
  'name': 'fr645m_asia',
  'value': 3004,
}),
  3011: dict({
  'name': 'edge_explore',
  'value': 3011,
}),
  3028: dict({
  'name': 'gpsmap66',
  'value': 3028,
}),
  3049: dict({
  'name': 'approach_s10',
  'value': 3049,
}),
  3066: dict({
  'name': 'vivoactive3m_l',
  'value': 3066,
}),
  3085: dict({
  'name': 'approach_g80',
  'value': 3085,
}),
  3092: dict({
  'name': 'edge_130_asia',
  'value': 3092,
}),
  3095: dict({
  'name': 'edge_1030_bontrager',
  'value': 3095,
}),
  3110: dict({
  'name': 'fenix5_plus',
  'value': 3110,
}),
  3111: dict({
  'name': 'fenix5x_plus',
  'value': 3111,
}),
  3112: dict({
  'name': 'edge_520_plus',
  'value': 3112,
}),
  3113: dict({
  'name': 'fr945',
  'value': 3113,
}),
  3121: dict({
  'name': 'edge_530',
  'value': 3121,
}),
  3122: dict({
  'name': 'edge_830',
  'value': 3122,
}),
  3126: dict({
  'name': 'instinct_esports',
  'value': 3126,
}),
  3134: dict({
  'name': 'fenix5s_plus_apac',
  'value': 3134,
}),
  3135: dict({
  'name': 'fenix5x_plus_apac',
  'value': 3135,
}),
  3142: dict({
  'name': 'edge_520_plus_apac',
  'value': 3142,
}),
  3144: dict({
  'name': 'fr235l_asia',
  'value': 3144,
}),
  3145: dict({
  'name': 'fr245_asia',
  'value': 3145,
}),
  3163: dict({
  'name': 'vivo_active3m_apac',
  'value': 3163,
}),
  3192: dict({
  'name': 'gen3_bsm',
  'value': 3192,
  'comment': 'gen3 bike speed sensor',
}),
  3193: dict({
  'name': 'gen3_bcm',
  'value': 3193,
  'comment': 'gen3 bike cadence sensor',
}),
  3218: dict({
  'name': 'vivo_smart4_asia',
  'value': 3218,
}),
  3224: dict({
  'name': 'vivoactive4_small',
  'value': 3224,
}),
  3225: dict({
  'name': 'vivoactive4_large',
  'value': 3225,
}),
  3226: dict({
  'name': 'venu',
  'value': 3226,
}),
  3246: dict({
  'name': 'marq_driver',
  'value': 3246,
}),
  3247: dict({
  'name': 'marq_aviator',
  'value': 3247,
}),
  3248: dict({
  'name': 'marq_captain',
  'value': 3248,
}),
  3249: dict({
  'name': 'marq_commander',
  'value': 3249,
}),
  3250: dict({
  'name': 'marq_expedition',
  'value': 3250,
}),
  3251: dict({
  'name': 'marq_athlete',
  'value': 3251,
}),
  3258: dict({
  'name': 'descent_mk2',
  'value': 3258,
}),
  3284: dict({
  'name': 'gpsmap66i',
  'value': 3284,
}),
  3287: dict({
  'name': 'fenix6S_sport',
  'value': 3287,
}),
  3288: dict({
  'name': 'fenix6S',
  'value': 3288,
}),
  3289: dict({
  'name': 'fenix6_sport',
  'value': 3289,
}),
  3290: dict({
  'name': 'fenix6',
  'value': 3290,
}),
  3291: dict({
  'name': 'fenix6x',
  'value': 3291,
}),
  3299: dict({
  'name': 'hrm_dual',
  'value': 3299,
  'comment': 'HRM-Dual',
}),
  3300: dict({
  'name': 'hrm_pro',
  'value': 3300,
  'comment': 'HRM-Pro',
}),
  3308: dict({
  'name': 'vivo_move3_premium',
  'value': 3308,
}),
  3314: dict({
  'name': 'approach_s40',
  'value': 3314,
}),
  3321: dict({
  'name': 'fr245m_asia',
  'value': 3321,
}),
  3349: dict({
  'name': 'edge_530_apac',
  'value': 3349,
}),
  3350: dict({
  'name': 'edge_830_apac',
  'value': 3350,
}),
  3378: dict({
  'name': 'vivo_move3',
  'value': 3378,
}),
  3387: dict({
  'name': 'vivo_active4_small_asia',
  'value': 3387,
}),
  3388: dict({
  'name': 'vivo_active4_large_asia',
  'value': 3388,
}),
  3389: dict({
  'name': 'vivo_active4_oled_asia',
  'value': 3389,
}),
  3405: dict({
  'name': 'swim2',
  'value': 3405,
}),
  3420: dict({
  'name': 'marq_driver_asia',
  'value': 3420,
}),
  3421: dict({
  'name': 'marq_aviator_asia',
  'value': 3421,
}),
  3422: dict({
  'name': 'vivo_move3_asia',
  'value': 3422,
}),
  3441: dict({
  'name': 'fr945_asia',
  'value': 3441,
}),
  3446: dict({
  'name': 'vivo_active3t_chn',
  'value': 3446,
}),
  3448: dict({
  'name': 'marq_captain_asia',
  'value': 3448,
}),
  3449: dict({
  'name': 'marq_commander_asia',
  'value': 3449,
}),
  3450: dict({
  'name': 'marq_expedition_asia',
  'value': 3450,
}),
  3451: dict({
  'name': 'marq_athlete_asia',
  'value': 3451,
}),
  3469: dict({
  'name': 'fr45_asia',
  'value': 3469,
}),
  3473: dict({
  'name': 'vivoactive3_daimler',
  'value': 3473,
}),
  3498: dict({
  'name': 'legacy_rey',
  'value': 3498,
}),
  3499: dict({
  'name': 'legacy_darth_vader',
  'value': 3499,
}),
  3500: dict({
  'name': 'legacy_captain_marvel',
  'value': 3500,
}),
  3501: dict({
  'name': 'legacy_first_avenger',
  'value': 3501,
}),
  3512: dict({
  'name': 'fenix6s_sport_asia',
  'value': 3512,
}),
  3513: dict({
  'name': 'fenix6s_asia',
  'value': 3513,
}),
  3514: dict({
  'name': 'fenix6_sport_asia',
  'value': 3514,
}),
  3515: dict({
  'name': 'fenix6_asia',
  'value': 3515,
}),
  3516: dict({
  'name': 'fenix6x_asia',
  'value': 3516,
}),
  3535: dict({
  'name': 'legacy_captain_marvel_asia',
  'value': 3535,
}),
  3536: dict({
  'name': 'legacy_first_avenger_asia',
  'value': 3536,
}),
  3537: dict({
  'name': 'legacy_rey_asia',
  'value': 3537,
}),
  3538: dict({
  'name': 'legacy_darth_vader_asia',
  'value': 3538,
}),
  3542: dict({
  'name': 'descent_mk2s',
  'value': 3542,
}),
  3558: dict({
  'name': 'edge_130_plus',
  'value': 3558,
}),
  3570: dict({
  'name': 'edge_1030_plus',
  'value': 3570,
}),
  3578: dict({
  'name': 'rally_200',
  'value': 3578,
  'comment': 'Rally 100/200 Power Meter Series',
}),
  3589: dict({
  'name': 'fr745',
  'value': 3589,
}),
  3600: dict({
  'name': 'venusq',
  'value': 3600,
}),
  3615: dict({
  'name': 'lily',
  'value': 3615,
}),
  3624: dict({
  'name': 'marq_adventurer',
  'value': 3624,
}),
  3638: dict({
  'name': 'enduro',
  'value': 3638,
}),
  3639: dict({
  'name': 'swim2_apac',
  'value': 3639,
}),
  3648: dict({
  'name': 'marq_adventurer_asia',
  'value': 3648,
}),
  3652: dict({
  'name': 'fr945_lte',
  'value': 3652,
}),
  3702: dict({
  'name': 'descent_mk2_asia',
  'value': 3702,
  'comment': 'Mk2 and Mk2i',
}),
  3703: dict({
  'name': 'venu2',
  'value': 3703,
}),
  3704: dict({
  'name': 'venu2s',
  'value': 3704,
}),
  3737: dict({
  'name': 'venu_daimler_asia',
  'value': 3737,
}),
  3739: dict({
  'name': 'marq_golfer',
  'value': 3739,
}),
  3740: dict({
  'name': 'venu_daimler',
  'value': 3740,
}),
  3794: dict({
  'name': 'fr745_asia',
  'value': 3794,
}),
  3809: dict({
  'name': 'lily_asia',
  'value': 3809,
}),
  3812: dict({
  'name': 'edge_1030_plus_asia',
  'value': 3812,
}),
  3813: dict({
  'name': 'edge_130_plus_asia',
  'value': 3813,
}),
  3823: dict({
  'name': 'approach_s12',
  'value': 3823,
}),
  3872: dict({
  'name': 'enduro_asia',
  'value': 3872,
}),
  3837: dict({
  'name': 'venusq_asia',
  'value': 3837,
}),
  3850: dict({
  'name': 'marq_golfer_asia',
  'value': 3850,
}),
  3869: dict({
  'name': 'fr55',
  'value': 3869,
}),
  3927: dict({
  'name': 'approach_g12',
  'value': 3927,
}),
  3930: dict({
  'name': 'descent_mk2s_asia',
  'value': 3930,
}),
  3934: dict({
  'name': 'approach_s42',
  'value': 3934,
}),
  3949: dict({
  'name': 'venu2s_asia',
  'value': 3949,
}),
  3950: dict({
  'name': 'venu2_asia',
  'value': 3950,
}),
  3978: dict({
  'name': 'fr945_lte_asia',
  'value': 3978,
}),
  3986: dict({
  'name': 'approach_S12_asia',
  'value': 3986,
}),
  4001: dict({
  'name': 'approach_g12_asia',
  'value': 4001,
}),
  4002: dict({
  'name': 'approach_s42_asia',
  'value': 4002,
}),
  4033: dict({
  'name': 'fr55_asia',
  'value': 4033,
}),
  10007: dict({
  'name': 'sdm4',
  'value': 10007,
  'comment': 'SDM4 footpod',
}),
  10014: dict({
  'name': 'edge_remote',
  'value': 10014,
}),
  20533: dict({
  'name': 'tacx_training_app_win',
  'value': 20533,
}),
  20534: dict({
  'name': 'tacx_training_app_mac',
  'value': 20534,
}),
  20119: dict({
  'name': 'training_center',
  'value': 20119,
}),
  30045: dict({
  'name': 'tacx_training_app_android',
  'value': 30045,
}),
  30046: dict({
  'name': 'tacx_training_app_ios',
  'value': 30046,
}),
  30047: dict({
  'name': 'tacx_training_app_legacy',
  'value': 30047,
}),
  65531: dict({
  'name': 'connectiq_simulator',
  'value': 65531,
}),
  65532: dict({
  'name': 'android_antplus_plugin',
  'value': 65532,
}),
  65534: dict({
  'name': 'connect',
  'value': 65534,
  'comment': 'Garmin Connect website',
}),
}),
}),
  'antplus_device_type': dict({
  'name': 'antplus_device_type',
  'base_type': 'uint8',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'antfs',
  'value': 1,
}),
  11: dict({
  'name': 'bike_power',
  'value': 11,
}),
  12: dict({
  'name': 'environment_sensor_legacy',
  'value': 12,
}),
  15: dict({
  'name': 'multi_sport_speed_distance',
  'value': 15,
}),
  16: dict({
  'name': 'control',
  'value': 16,
}),
  17: dict({
  'name': 'fitness_equipment',
  'value': 17,
}),
  18: dict({
  'name': 'blood_pressure',
  'value': 18,
}),
  19: dict({
  'name': 'geocache_node',
  'value': 19,
}),
  20: dict({
  'name': 'light_electric_vehicle',
  'value': 20,
}),
  25: dict({
  'name': 'env_sensor',
  'value': 25,
}),
  26: dict({
  'name': 'racquet',
  'value': 26,
}),
  27: dict({
  'name': 'control_hub',
  'value': 27,
}),
  31: dict({
  'name': 'muscle_oxygen',
  'value': 31,
}),
  34: dict({
  'name': 'shifting',
  'value': 34,
}),
  35: dict({
  'name': 'bike_light_main',
  'value': 35,
}),
  36: dict({
  'name': 'bike_light_shared',
  'value': 36,
}),
  38: dict({
  'name': 'exd',
  'value': 38,
}),
  40: dict({
  'name': 'bike_radar',
  'value': 40,
}),
  46: dict({
  'name': 'bike_aero',
  'value': 46,
}),
  119: dict({
  'name': 'weight_scale',
  'value': 119,
}),
  120: dict({
  'name': 'heart_rate',
  'value': 120,
}),
  121: dict({
  'name': 'bike_speed_cadence',
  'value': 121,
}),
  122: dict({
  'name': 'bike_cadence',
  'value': 122,
}),
  123: dict({
  'name': 'bike_speed',
  'value': 123,
}),
  124: dict({
  'name': 'stride_speed_distance',
  'value': 124,
}),
}),
}),
  'ant_network': dict({
  'name': 'ant_network',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'public',
  'value': 0,
}),
  1: dict({
  'name': 'antplus',
  'value': 1,
}),
  2: dict({
  'name': 'antfs',
  'value': 2,
}),
  3: dict({
  'name': 'private',
  'value': 3,
}),
}),
}),
  'workout_capabilities': dict({
  'name': 'workout_capabilities',
  'base_type': 'uint32z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'interval',
  'value': 1,
}),
  2: dict({
  'name': 'custom',
  'value': 2,
}),
  4: dict({
  'name': 'fitness_equipment',
  'value': 4,
}),
  8: dict({
  'name': 'firstbeat',
  'value': 8,
}),
  16: dict({
  'name': 'new_leaf',
  'value': 16,
}),
  32: dict({
  'name': 'tcx',
  'value': 32,
  'comment': 'For backwards compatibility.  Watch should add missing id fields then clear flag.',
}),
  128: dict({
  'name': 'speed',
  'value': 128,
  'comment': 'Speed source required for workout step.',
}),
  256: dict({
  'name': 'heart_rate',
  'value': 256,
  'comment': 'Heart rate source required for workout step.',
}),
  512: dict({
  'name': 'distance',
  'value': 512,
  'comment': 'Distance source required for workout step.',
}),
  1024: dict({
  'name': 'cadence',
  'value': 1024,
  'comment': 'Cadence source required for workout step.',
}),
  2048: dict({
  'name': 'power',
  'value': 2048,
  'comment': 'Power source required for workout step.',
}),
  4096: dict({
  'name': 'grade',
  'value': 4096,
  'comment': 'Grade source required for workout step.',
}),
  8192: dict({
  'name': 'resistance',
  'value': 8192,
  'comment': 'Resistance source required for workout step.',
}),
  16384: dict({
  'name': 'protected',
  'value': 16384,
}),
}),
}),
  'battery_status': dict({
  'name': 'battery_status',
  'base_type': 'uint8',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'new',
  'value': 1,
}),
  2: dict({
  'name': 'good',
  'value': 2,
}),
  3: dict({
  'name': 'ok',
  'value': 3,
}),
  4: dict({
  'name': 'low',
  'value': 4,
}),
  5: dict({
  'name': 'critical',
  'value': 5,
}),
  6: dict({
  'name': 'charging',
  'value': 6,
}),
  7: dict({
  'name': 'unknown',
  'value': 7,
}),
}),
}),
  'hr_type': dict({
  'name': 'hr_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'normal',
  'value': 0,
}),
  1: dict({
  'name': 'irregular',
  'value': 1,
}),
}),
}),
  'course_capabilities': dict({
  'name': 'course_capabilities',
  'base_type': 'uint32z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'processed',
  'value': 1,
}),
  2: dict({
  'name': 'valid',
  'value': 2,
}),
  4: dict({
  'name': 'time',
  'value': 4,
}),
  8: dict({
  'name': 'distance',
  'value': 8,
}),
  16: dict({
  'name': 'position',
  'value': 16,
}),
  32: dict({
  'name': 'heart_rate',
  'value': 32,
}),
  64: dict({
  'name': 'power',
  'value': 64,
}),
  128: dict({
  'name': 'cadence',
  'value': 128,
}),
  256: dict({
  'name': 'training',
  'value': 256,
}),
  512: dict({
  'name': 'navigation',
  'value': 512,
}),
  1024: dict({
  'name': 'bikeway',
  'value': 1024,
}),
}),
}),
  'weight': dict({
  'name': 'weight',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  65534: dict({
  'name': 'calculating',
  'value': 65534,
}),
}),
}),
  'workout_hr': dict({
  'name': 'workout_hr',
  'base_type': 'uint32',
  'parser': resolve,
  'values': dict({
  100: dict({
  'name': 'bpm_offset',
  'value': 100,
}),
}),
  'comment': '0 - 100 indicates% of max hr; >100 indicates bpm (255 max) plus 100',
}),
  'workout_power': dict({
  'name': 'workout_power',
  'base_type': 'uint32',
  'parser': resolve,
  'values': dict({
  1000: dict({
  'name': 'watts_offset',
  'value': 1000,
}),
}),
  'comment': '0 - 1000 indicates % of functional threshold power; >1000 indicates watts plus 1000.',
}),
  'bp_status': dict({
  'name': 'bp_status',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'no_error',
  'value': 0,
}),
  1: dict({
  'name': 'error_incomplete_data',
  'value': 1,
}),
  2: dict({
  'name': 'error_no_measurement',
  'value': 2,
}),
  3: dict({
  'name': 'error_data_out_of_range',
  'value': 3,
}),
  4: dict({
  'name': 'error_irregular_heart_rate',
  'value': 4,
}),
}),
}),
  'user_local_id': dict({
  'name': 'user_local_id',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'local_min',
  'value': 0,
}),
  15: dict({
  'name': 'local_max',
  'value': 15,
}),
  16: dict({
  'name': 'stationary_min',
  'value': 16,
}),
  255: dict({
  'name': 'stationary_max',
  'value': 255,
}),
  256: dict({
  'name': 'portable_min',
  'value': 256,
}),
  65534: dict({
  'name': 'portable_max',
  'value': 65534,
}),
}),
}),
  'swim_stroke': dict({
  'name': 'swim_stroke',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'freestyle',
  'value': 0,
}),
  1: dict({
  'name': 'backstroke',
  'value': 1,
}),
  2: dict({
  'name': 'breaststroke',
  'value': 2,
}),
  3: dict({
  'name': 'butterfly',
  'value': 3,
}),
  4: dict({
  'name': 'drill',
  'value': 4,
}),
  5: dict({
  'name': 'mixed',
  'value': 5,
}),
  6: dict({
  'name': 'im',
  'value': 6,
  'comment': 'IM is a mixed interval containing the same number of lengths for each of: Butterfly, Backstroke, Breaststroke, Freestyle, swam in that order.',
}),
}),
}),
  'activity_type': dict({
  'name': 'activity_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'generic',
  'value': 0,
}),
  1: dict({
  'name': 'running',
  'value': 1,
}),
  2: dict({
  'name': 'cycling',
  'value': 2,
}),
  3: dict({
  'name': 'transition',
  'value': 3,
  'comment': 'Mulitsport transition',
}),
  4: dict({
  'name': 'fitness_equipment',
  'value': 4,
}),
  5: dict({
  'name': 'swimming',
  'value': 5,
}),
  6: dict({
  'name': 'walking',
  'value': 6,
}),
  8: dict({
  'name': 'sedentary',
  'value': 8,
}),
  254: dict({
  'name': 'all',
  'value': 254,
  'comment': 'All is for goals only to include all sports.',
}),
}),
}),
  'activity_subtype': dict({
  'name': 'activity_subtype',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'generic',
  'value': 0,
}),
  1: dict({
  'name': 'treadmill',
  'value': 1,
  'comment': 'Run',
}),
  2: dict({
  'name': 'street',
  'value': 2,
  'comment': 'Run',
}),
  3: dict({
  'name': 'trail',
  'value': 3,
  'comment': 'Run',
}),
  4: dict({
  'name': 'track',
  'value': 4,
  'comment': 'Run',
}),
  5: dict({
  'name': 'spin',
  'value': 5,
  'comment': 'Cycling',
}),
  6: dict({
  'name': 'indoor_cycling',
  'value': 6,
  'comment': 'Cycling',
}),
  7: dict({
  'name': 'road',
  'value': 7,
  'comment': 'Cycling',
}),
  8: dict({
  'name': 'mountain',
  'value': 8,
  'comment': 'Cycling',
}),
  9: dict({
  'name': 'downhill',
  'value': 9,
  'comment': 'Cycling',
}),
  10: dict({
  'name': 'recumbent',
  'value': 10,
  'comment': 'Cycling',
}),
  11: dict({
  'name': 'cyclocross',
  'value': 11,
  'comment': 'Cycling',
}),
  12: dict({
  'name': 'hand_cycling',
  'value': 12,
  'comment': 'Cycling',
}),
  13: dict({
  'name': 'track_cycling',
  'value': 13,
  'comment': 'Cycling',
}),
  14: dict({
  'name': 'indoor_rowing',
  'value': 14,
  'comment': 'Fitness Equipment',
}),
  15: dict({
  'name': 'elliptical',
  'value': 15,
  'comment': 'Fitness Equipment',
}),
  16: dict({
  'name': 'stair_climbing',
  'value': 16,
  'comment': 'Fitness Equipment',
}),
  17: dict({
  'name': 'lap_swimming',
  'value': 17,
  'comment': 'Swimming',
}),
  18: dict({
  'name': 'open_water',
  'value': 18,
  'comment': 'Swimming',
}),
  254: dict({
  'name': 'all',
  'value': 254,
}),
}),
}),
  'activity_level': dict({
  'name': 'activity_level',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'low',
  'value': 0,
}),
  1: dict({
  'name': 'medium',
  'value': 1,
}),
  2: dict({
  'name': 'high',
  'value': 2,
}),
}),
}),
  'side': dict({
  'name': 'side',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'right',
  'value': 0,
}),
  1: dict({
  'name': 'left',
  'value': 1,
}),
}),
}),
  'left_right_balance': dict({
  'name': 'left_right_balance',
  'base_type': 'uint8',
  'parser': resolve,
  'values': dict({
  127: dict({
  'name': 'mask',
  'value': 127,
  'comment': '% contribution',
}),
  128: dict({
  'name': 'right',
  'value': 128,
  'comment': 'data corresponds to right if set, otherwise unknown',
}),
}),
}),
  'left_right_balance_100': dict({
  'name': 'left_right_balance_100',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  16383: dict({
  'name': 'mask',
  'value': 16383,
  'comment': '% contribution scaled by 100',
}),
  32768: dict({
  'name': 'right',
  'value': 32768,
  'comment': 'data corresponds to right if set, otherwise unknown',
}),
}),
}),
  'length_type': dict({
  'name': 'length_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'idle',
  'value': 0,
  'comment': 'Rest period. Length with no strokes',
}),
  1: dict({
  'name': 'active',
  'value': 1,
  'comment': 'Length with strokes.',
}),
}),
}),
  'day_of_week': dict({
  'name': 'day_of_week',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'sunday',
  'value': 0,
}),
  1: dict({
  'name': 'monday',
  'value': 1,
}),
  2: dict({
  'name': 'tuesday',
  'value': 2,
}),
  3: dict({
  'name': 'wednesday',
  'value': 3,
}),
  4: dict({
  'name': 'thursday',
  'value': 4,
}),
  5: dict({
  'name': 'friday',
  'value': 5,
}),
  6: dict({
  'name': 'saturday',
  'value': 6,
}),
}),
}),
  'connectivity_capabilities': dict({
  'name': 'connectivity_capabilities',
  'base_type': 'uint32z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'bluetooth',
  'value': 1,
}),
  2: dict({
  'name': 'bluetooth_le',
  'value': 2,
}),
  4: dict({
  'name': 'ant',
  'value': 4,
}),
  8: dict({
  'name': 'activity_upload',
  'value': 8,
}),
  16: dict({
  'name': 'course_download',
  'value': 16,
}),
  32: dict({
  'name': 'workout_download',
  'value': 32,
}),
  64: dict({
  'name': 'live_track',
  'value': 64,
}),
  128: dict({
  'name': 'weather_conditions',
  'value': 128,
}),
  256: dict({
  'name': 'weather_alerts',
  'value': 256,
}),
  512: dict({
  'name': 'gps_ephemeris_download',
  'value': 512,
}),
  1024: dict({
  'name': 'explicit_archive',
  'value': 1024,
}),
  2048: dict({
  'name': 'setup_incomplete',
  'value': 2048,
}),
  4096: dict({
  'name': 'continue_sync_after_software_update',
  'value': 4096,
}),
  8192: dict({
  'name': 'connect_iq_app_download',
  'value': 8192,
}),
  16384: dict({
  'name': 'golf_course_download',
  'value': 16384,
}),
  32768: dict({
  'name': 'device_initiates_sync',
  'value': 32768,
  'comment': 'Indicates device is in control of initiating all syncs',
}),
  65536: dict({
  'name': 'connect_iq_watch_app_download',
  'value': 65536,
}),
  131072: dict({
  'name': 'connect_iq_widget_download',
  'value': 131072,
}),
  262144: dict({
  'name': 'connect_iq_watch_face_download',
  'value': 262144,
}),
  524288: dict({
  'name': 'connect_iq_data_field_download',
  'value': 524288,
}),
  1048576: dict({
  'name': 'connect_iq_app_managment',
  'value': 1048576,
  'comment': 'Device supports delete and reorder of apps via GCM',
}),
  2097152: dict({
  'name': 'swing_sensor',
  'value': 2097152,
}),
  4194304: dict({
  'name': 'swing_sensor_remote',
  'value': 4194304,
}),
  8388608: dict({
  'name': 'incident_detection',
  'value': 8388608,
  'comment': 'Device supports incident detection',
}),
  16777216: dict({
  'name': 'audio_prompts',
  'value': 16777216,
}),
  33554432: dict({
  'name': 'wifi_verification',
  'value': 33554432,
  'comment': 'Device supports reporting wifi verification via GCM',
}),
  67108864: dict({
  'name': 'true_up',
  'value': 67108864,
  'comment': 'Device supports True Up',
}),
  134217728: dict({
  'name': 'find_my_watch',
  'value': 134217728,
  'comment': 'Device supports Find My Watch',
}),
  268435456: dict({
  'name': 'remote_manual_sync',
  'value': 268435456,
}),
  536870912: dict({
  'name': 'live_track_auto_start',
  'value': 536870912,
  'comment': 'Device supports LiveTrack auto start',
}),
  1073741824: dict({
  'name': 'live_track_messaging',
  'value': 1073741824,
  'comment': 'Device supports LiveTrack Messaging',
}),
  2147483648: dict({
  'name': 'instant_input',
  'value': 2147483648,
  'comment': 'Device supports instant input feature',
}),
}),
}),
  'weather_report': dict({
  'name': 'weather_report',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'current',
  'value': 0,
}),
  1: dict({
  'name': 'hourly_forecast',
  'value': 1,
}),
  2: dict({
  'name': 'daily_forecast',
  'value': 2,
}),
}),
}),
  'weather_status': dict({
  'name': 'weather_status',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'clear',
  'value': 0,
}),
  1: dict({
  'name': 'partly_cloudy',
  'value': 1,
}),
  2: dict({
  'name': 'mostly_cloudy',
  'value': 2,
}),
  3: dict({
  'name': 'rain',
  'value': 3,
}),
  4: dict({
  'name': 'snow',
  'value': 4,
}),
  5: dict({
  'name': 'windy',
  'value': 5,
}),
  6: dict({
  'name': 'thunderstorms',
  'value': 6,
}),
  7: dict({
  'name': 'wintry_mix',
  'value': 7,
}),
  8: dict({
  'name': 'fog',
  'value': 8,
}),
  11: dict({
  'name': 'hazy',
  'value': 11,
}),
  12: dict({
  'name': 'hail',
  'value': 12,
}),
  13: dict({
  'name': 'scattered_showers',
  'value': 13,
}),
  14: dict({
  'name': 'scattered_thunderstorms',
  'value': 14,
}),
  15: dict({
  'name': 'unknown_precipitation',
  'value': 15,
}),
  16: dict({
  'name': 'light_rain',
  'value': 16,
}),
  17: dict({
  'name': 'heavy_rain',
  'value': 17,
}),
  18: dict({
  'name': 'light_snow',
  'value': 18,
}),
  19: dict({
  'name': 'heavy_snow',
  'value': 19,
}),
  20: dict({
  'name': 'light_rain_snow',
  'value': 20,
}),
  21: dict({
  'name': 'heavy_rain_snow',
  'value': 21,
}),
  22: dict({
  'name': 'cloudy',
  'value': 22,
}),
}),
}),
  'weather_severity': dict({
  'name': 'weather_severity',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'unknown',
  'value': 0,
}),
  1: dict({
  'name': 'warning',
  'value': 1,
}),
  2: dict({
  'name': 'watch',
  'value': 2,
}),
  3: dict({
  'name': 'advisory',
  'value': 3,
}),
  4: dict({
  'name': 'statement',
  'value': 4,
}),
}),
}),
  'weather_severe_type': dict({
  'name': 'weather_severe_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'unspecified',
  'value': 0,
}),
  1: dict({
  'name': 'tornado',
  'value': 1,
}),
  2: dict({
  'name': 'tsunami',
  'value': 2,
}),
  3: dict({
  'name': 'hurricane',
  'value': 3,
}),
  4: dict({
  'name': 'extreme_wind',
  'value': 4,
}),
  5: dict({
  'name': 'typhoon',
  'value': 5,
}),
  6: dict({
  'name': 'inland_hurricane',
  'value': 6,
}),
  7: dict({
  'name': 'hurricane_force_wind',
  'value': 7,
}),
  8: dict({
  'name': 'waterspout',
  'value': 8,
}),
  9: dict({
  'name': 'severe_thunderstorm',
  'value': 9,
}),
  10: dict({
  'name': 'wreckhouse_winds',
  'value': 10,
}),
  11: dict({
  'name': 'les_suetes_wind',
  'value': 11,
}),
  12: dict({
  'name': 'avalanche',
  'value': 12,
}),
  13: dict({
  'name': 'flash_flood',
  'value': 13,
}),
  14: dict({
  'name': 'tropical_storm',
  'value': 14,
}),
  15: dict({
  'name': 'inland_tropical_storm',
  'value': 15,
}),
  16: dict({
  'name': 'blizzard',
  'value': 16,
}),
  17: dict({
  'name': 'ice_storm',
  'value': 17,
}),
  18: dict({
  'name': 'freezing_rain',
  'value': 18,
}),
  19: dict({
  'name': 'debris_flow',
  'value': 19,
}),
  20: dict({
  'name': 'flash_freeze',
  'value': 20,
}),
  21: dict({
  'name': 'dust_storm',
  'value': 21,
}),
  22: dict({
  'name': 'high_wind',
  'value': 22,
}),
  23: dict({
  'name': 'winter_storm',
  'value': 23,
}),
  24: dict({
  'name': 'heavy_freezing_spray',
  'value': 24,
}),
  25: dict({
  'name': 'extreme_cold',
  'value': 25,
}),
  26: dict({
  'name': 'wind_chill',
  'value': 26,
}),
  27: dict({
  'name': 'cold_wave',
  'value': 27,
}),
  28: dict({
  'name': 'heavy_snow_alert',
  'value': 28,
}),
  29: dict({
  'name': 'lake_effect_blowing_snow',
  'value': 29,
}),
  30: dict({
  'name': 'snow_squall',
  'value': 30,
}),
  31: dict({
  'name': 'lake_effect_snow',
  'value': 31,
}),
  32: dict({
  'name': 'winter_weather',
  'value': 32,
}),
  33: dict({
  'name': 'sleet',
  'value': 33,
}),
  34: dict({
  'name': 'snowfall',
  'value': 34,
}),
  35: dict({
  'name': 'snow_and_blowing_snow',
  'value': 35,
}),
  36: dict({
  'name': 'blowing_snow',
  'value': 36,
}),
  37: dict({
  'name': 'snow_alert',
  'value': 37,
}),
  38: dict({
  'name': 'arctic_outflow',
  'value': 38,
}),
  39: dict({
  'name': 'freezing_drizzle',
  'value': 39,
}),
  40: dict({
  'name': 'storm',
  'value': 40,
}),
  41: dict({
  'name': 'storm_surge',
  'value': 41,
}),
  42: dict({
  'name': 'rainfall',
  'value': 42,
}),
  43: dict({
  'name': 'areal_flood',
  'value': 43,
}),
  44: dict({
  'name': 'coastal_flood',
  'value': 44,
}),
  45: dict({
  'name': 'lakeshore_flood',
  'value': 45,
}),
  46: dict({
  'name': 'excessive_heat',
  'value': 46,
}),
  47: dict({
  'name': 'heat',
  'value': 47,
}),
  48: dict({
  'name': 'weather',
  'value': 48,
}),
  49: dict({
  'name': 'high_heat_and_humidity',
  'value': 49,
}),
  50: dict({
  'name': 'humidex_and_health',
  'value': 50,
}),
  51: dict({
  'name': 'humidex',
  'value': 51,
}),
  52: dict({
  'name': 'gale',
  'value': 52,
}),
  53: dict({
  'name': 'freezing_spray',
  'value': 53,
}),
  54: dict({
  'name': 'special_marine',
  'value': 54,
}),
  55: dict({
  'name': 'squall',
  'value': 55,
}),
  56: dict({
  'name': 'strong_wind',
  'value': 56,
}),
  57: dict({
  'name': 'lake_wind',
  'value': 57,
}),
  58: dict({
  'name': 'marine_weather',
  'value': 58,
}),
  59: dict({
  'name': 'wind',
  'value': 59,
}),
  60: dict({
  'name': 'small_craft_hazardous_seas',
  'value': 60,
}),
  61: dict({
  'name': 'hazardous_seas',
  'value': 61,
}),
  62: dict({
  'name': 'small_craft',
  'value': 62,
}),
  63: dict({
  'name': 'small_craft_winds',
  'value': 63,
}),
  64: dict({
  'name': 'small_craft_rough_bar',
  'value': 64,
}),
  65: dict({
  'name': 'high_water_level',
  'value': 65,
}),
  66: dict({
  'name': 'ashfall',
  'value': 66,
}),
  67: dict({
  'name': 'freezing_fog',
  'value': 67,
}),
  68: dict({
  'name': 'dense_fog',
  'value': 68,
}),
  69: dict({
  'name': 'dense_smoke',
  'value': 69,
}),
  70: dict({
  'name': 'blowing_dust',
  'value': 70,
}),
  71: dict({
  'name': 'hard_freeze',
  'value': 71,
}),
  72: dict({
  'name': 'freeze',
  'value': 72,
}),
  73: dict({
  'name': 'frost',
  'value': 73,
}),
  74: dict({
  'name': 'fire_weather',
  'value': 74,
}),
  75: dict({
  'name': 'flood',
  'value': 75,
}),
  76: dict({
  'name': 'rip_tide',
  'value': 76,
}),
  77: dict({
  'name': 'high_surf',
  'value': 77,
}),
  78: dict({
  'name': 'smog',
  'value': 78,
}),
  79: dict({
  'name': 'air_quality',
  'value': 79,
}),
  80: dict({
  'name': 'brisk_wind',
  'value': 80,
}),
  81: dict({
  'name': 'air_stagnation',
  'value': 81,
}),
  82: dict({
  'name': 'low_water',
  'value': 82,
}),
  83: dict({
  'name': 'hydrological',
  'value': 83,
}),
  84: dict({
  'name': 'special_weather',
  'value': 84,
}),
}),
}),
  'time_into_day': dict({
  'name': 'time_into_day',
  'base_type': 'uint32',
  'parser': resolve,
  'values': dict({
}),
  'comment': 'number of seconds into the day since 00:00:00 UTC',
}),
  'localtime_into_day': dict({
  'name': 'localtime_into_day',
  'base_type': 'uint32',
  'parser': resolve,
  'values': dict({
}),
  'comment': 'number of seconds into the day since local 00:00:00',
}),
  'stroke_type': dict({
  'name': 'stroke_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'no_event',
  'value': 0,
}),
  1: dict({
  'name': 'other',
  'value': 1,
  'comment': 'stroke was detected but cannot be identified',
}),
  2: dict({
  'name': 'serve',
  'value': 2,
}),
  3: dict({
  'name': 'forehand',
  'value': 3,
}),
  4: dict({
  'name': 'backhand',
  'value': 4,
}),
  5: dict({
  'name': 'smash',
  'value': 5,
}),
}),
}),
  'body_location': dict({
  'name': 'body_location',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'left_leg',
  'value': 0,
}),
  1: dict({
  'name': 'left_calf',
  'value': 1,
}),
  2: dict({
  'name': 'left_shin',
  'value': 2,
}),
  3: dict({
  'name': 'left_hamstring',
  'value': 3,
}),
  4: dict({
  'name': 'left_quad',
  'value': 4,
}),
  5: dict({
  'name': 'left_glute',
  'value': 5,
}),
  6: dict({
  'name': 'right_leg',
  'value': 6,
}),
  7: dict({
  'name': 'right_calf',
  'value': 7,
}),
  8: dict({
  'name': 'right_shin',
  'value': 8,
}),
  9: dict({
  'name': 'right_hamstring',
  'value': 9,
}),
  10: dict({
  'name': 'right_quad',
  'value': 10,
}),
  11: dict({
  'name': 'right_glute',
  'value': 11,
}),
  12: dict({
  'name': 'torso_back',
  'value': 12,
}),
  13: dict({
  'name': 'left_lower_back',
  'value': 13,
}),
  14: dict({
  'name': 'left_upper_back',
  'value': 14,
}),
  15: dict({
  'name': 'right_lower_back',
  'value': 15,
}),
  16: dict({
  'name': 'right_upper_back',
  'value': 16,
}),
  17: dict({
  'name': 'torso_front',
  'value': 17,
}),
  18: dict({
  'name': 'left_abdomen',
  'value': 18,
}),
  19: dict({
  'name': 'left_chest',
  'value': 19,
}),
  20: dict({
  'name': 'right_abdomen',
  'value': 20,
}),
  21: dict({
  'name': 'right_chest',
  'value': 21,
}),
  22: dict({
  'name': 'left_arm',
  'value': 22,
}),
  23: dict({
  'name': 'left_shoulder',
  'value': 23,
}),
  24: dict({
  'name': 'left_bicep',
  'value': 24,
}),
  25: dict({
  'name': 'left_tricep',
  'value': 25,
}),
  26: dict({
  'name': 'left_brachioradialis',
  'value': 26,
  'comment': 'Left anterior forearm',
}),
  27: dict({
  'name': 'left_forearm_extensors',
  'value': 27,
  'comment': 'Left posterior forearm',
}),
  28: dict({
  'name': 'right_arm',
  'value': 28,
}),
  29: dict({
  'name': 'right_shoulder',
  'value': 29,
}),
  30: dict({
  'name': 'right_bicep',
  'value': 30,
}),
  31: dict({
  'name': 'right_tricep',
  'value': 31,
}),
  32: dict({
  'name': 'right_brachioradialis',
  'value': 32,
  'comment': 'Right anterior forearm',
}),
  33: dict({
  'name': 'right_forearm_extensors',
  'value': 33,
  'comment': 'Right posterior forearm',
}),
  34: dict({
  'name': 'neck',
  'value': 34,
}),
  35: dict({
  'name': 'throat',
  'value': 35,
}),
  36: dict({
  'name': 'waist_mid_back',
  'value': 36,
}),
  37: dict({
  'name': 'waist_front',
  'value': 37,
}),
  38: dict({
  'name': 'waist_left',
  'value': 38,
}),
  39: dict({
  'name': 'waist_right',
  'value': 39,
}),
}),
}),
  'segment_lap_status': dict({
  'name': 'segment_lap_status',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'end',
  'value': 0,
}),
  1: dict({
  'name': 'fail',
  'value': 1,
}),
}),
}),
  'segment_leaderboard_type': dict({
  'name': 'segment_leaderboard_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'overall',
  'value': 0,
}),
  1: dict({
  'name': 'personal_best',
  'value': 1,
}),
  2: dict({
  'name': 'connections',
  'value': 2,
}),
  3: dict({
  'name': 'group',
  'value': 3,
}),
  4: dict({
  'name': 'challenger',
  'value': 4,
}),
  5: dict({
  'name': 'kom',
  'value': 5,
}),
  6: dict({
  'name': 'qom',
  'value': 6,
}),
  7: dict({
  'name': 'pr',
  'value': 7,
}),
  8: dict({
  'name': 'goal',
  'value': 8,
}),
  9: dict({
  'name': 'rival',
  'value': 9,
}),
  10: dict({
  'name': 'club_leader',
  'value': 10,
}),
}),
}),
  'segment_delete_status': dict({
  'name': 'segment_delete_status',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'do_not_delete',
  'value': 0,
}),
  1: dict({
  'name': 'delete_one',
  'value': 1,
}),
  2: dict({
  'name': 'delete_all',
  'value': 2,
}),
}),
}),
  'segment_selection_type': dict({
  'name': 'segment_selection_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'starred',
  'value': 0,
}),
  1: dict({
  'name': 'suggested',
  'value': 1,
}),
}),
}),
  'source_type': dict({
  'name': 'source_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'ant',
  'value': 0,
  'comment': 'External device connected with ANT',
}),
  1: dict({
  'name': 'antplus',
  'value': 1,
  'comment': 'External device connected with ANT+',
}),
  2: dict({
  'name': 'bluetooth',
  'value': 2,
  'comment': 'External device connected with BT',
}),
  3: dict({
  'name': 'bluetooth_low_energy',
  'value': 3,
  'comment': 'External device connected with BLE',
}),
  4: dict({
  'name': 'wifi',
  'value': 4,
  'comment': 'External device connected with Wifi',
}),
  5: dict({
  'name': 'local',
  'value': 5,
  'comment': 'Onboard device',
}),
}),
}),
  'local_device_type': dict({
  'name': 'local_device_type',
  'base_type': 'uint8',
  'parser': resolve,
  'values': dict({
}),
}),
  'display_orientation': dict({
  'name': 'display_orientation',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'auto',
  'value': 0,
  'comment': 'automatic if the device supports it',
}),
  1: dict({
  'name': 'portrait',
  'value': 1,
}),
  2: dict({
  'name': 'landscape',
  'value': 2,
}),
  3: dict({
  'name': 'portrait_flipped',
  'value': 3,
  'comment': 'portrait mode but rotated 180 degrees',
}),
  4: dict({
  'name': 'landscape_flipped',
  'value': 4,
  'comment': 'landscape mode but rotated 180 degrees',
}),
}),
}),
  'workout_equipment': dict({
  'name': 'workout_equipment',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'none',
  'value': 0,
}),
  1: dict({
  'name': 'swim_fins',
  'value': 1,
}),
  2: dict({
  'name': 'swim_kickboard',
  'value': 2,
}),
  3: dict({
  'name': 'swim_paddles',
  'value': 3,
}),
  4: dict({
  'name': 'swim_pull_buoy',
  'value': 4,
}),
  5: dict({
  'name': 'swim_snorkel',
  'value': 5,
}),
}),
}),
  'watchface_mode': dict({
  'name': 'watchface_mode',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'digital',
  'value': 0,
}),
  1: dict({
  'name': 'analog',
  'value': 1,
}),
  2: dict({
  'name': 'connect_iq',
  'value': 2,
}),
  3: dict({
  'name': 'disabled',
  'value': 3,
}),
}),
}),
  'digital_watchface_layout': dict({
  'name': 'digital_watchface_layout',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'traditional',
  'value': 0,
}),
  1: dict({
  'name': 'modern',
  'value': 1,
}),
  2: dict({
  'name': 'bold',
  'value': 2,
}),
}),
}),
  'analog_watchface_layout': dict({
  'name': 'analog_watchface_layout',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'minimal',
  'value': 0,
}),
  1: dict({
  'name': 'traditional',
  'value': 1,
}),
  2: dict({
  'name': 'modern',
  'value': 2,
}),
}),
}),
  'rider_position_type': dict({
  'name': 'rider_position_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'seated',
  'value': 0,
}),
  1: dict({
  'name': 'standing',
  'value': 1,
}),
  2: dict({
  'name': 'transition_to_seated',
  'value': 2,
}),
  3: dict({
  'name': 'transition_to_standing',
  'value': 3,
}),
}),
}),
  'power_phase_type': dict({
  'name': 'power_phase_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'power_phase_start_angle',
  'value': 0,
}),
  1: dict({
  'name': 'power_phase_end_angle',
  'value': 1,
}),
  2: dict({
  'name': 'power_phase_arc_length',
  'value': 2,
}),
  3: dict({
  'name': 'power_phase_center',
  'value': 3,
}),
}),
}),
  'camera_event_type': dict({
  'name': 'camera_event_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'video_start',
  'value': 0,
  'comment': 'Start of video recording',
}),
  1: dict({
  'name': 'video_split',
  'value': 1,
  'comment': 'Mark of video file split (end of one file, beginning of the other)',
}),
  2: dict({
  'name': 'video_end',
  'value': 2,
  'comment': 'End of video recording',
}),
  3: dict({
  'name': 'photo_taken',
  'value': 3,
  'comment': 'Still photo taken',
}),
  4: dict({
  'name': 'video_second_stream_start',
  'value': 4,
}),
  5: dict({
  'name': 'video_second_stream_split',
  'value': 5,
}),
  6: dict({
  'name': 'video_second_stream_end',
  'value': 6,
}),
  7: dict({
  'name': 'video_split_start',
  'value': 7,
  'comment': 'Mark of video file split start',
}),
  8: dict({
  'name': 'video_second_stream_split_start',
  'value': 8,
}),
  11: dict({
  'name': 'video_pause',
  'value': 11,
  'comment': 'Mark when a video recording has been paused',
}),
  12: dict({
  'name': 'video_second_stream_pause',
  'value': 12,
}),
  13: dict({
  'name': 'video_resume',
  'value': 13,
  'comment': 'Mark when a video recording has been resumed',
}),
  14: dict({
  'name': 'video_second_stream_resume',
  'value': 14,
}),
}),
}),
  'sensor_type': dict({
  'name': 'sensor_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'accelerometer',
  'value': 0,
}),
  1: dict({
  'name': 'gyroscope',
  'value': 1,
}),
  2: dict({
  'name': 'compass',
  'value': 2,
  'comment': 'Magnetometer',
}),
  3: dict({
  'name': 'barometer',
  'value': 3,
}),
}),
}),
  'bike_light_network_config_type': dict({
  'name': 'bike_light_network_config_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'auto',
  'value': 0,
}),
  4: dict({
  'name': 'individual',
  'value': 4,
}),
  5: dict({
  'name': 'high_visibility',
  'value': 5,
}),
  6: dict({
  'name': 'trail',
  'value': 6,
}),
}),
}),
  'comm_timeout_type': dict({
  'name': 'comm_timeout_type',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'wildcard_pairing_timeout',
  'value': 0,
  'comment': 'Timeout pairing to any device',
}),
  1: dict({
  'name': 'pairing_timeout',
  'value': 1,
  'comment': 'Timeout pairing to previously paired device',
}),
  2: dict({
  'name': 'connection_lost',
  'value': 2,
  'comment': 'Temporary loss of communications',
}),
  3: dict({
  'name': 'connection_timeout',
  'value': 3,
  'comment': 'Connection closed due to extended bad communications',
}),
}),
}),
  'camera_orientation_type': dict({
  'name': 'camera_orientation_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'camera_orientation_0',
  'value': 0,
}),
  1: dict({
  'name': 'camera_orientation_90',
  'value': 1,
}),
  2: dict({
  'name': 'camera_orientation_180',
  'value': 2,
}),
  3: dict({
  'name': 'camera_orientation_270',
  'value': 3,
}),
}),
}),
  'attitude_stage': dict({
  'name': 'attitude_stage',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'failed',
  'value': 0,
}),
  1: dict({
  'name': 'aligning',
  'value': 1,
}),
  2: dict({
  'name': 'degraded',
  'value': 2,
}),
  3: dict({
  'name': 'valid',
  'value': 3,
}),
}),
}),
  'attitude_validity': dict({
  'name': 'attitude_validity',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'track_angle_heading_valid',
  'value': 1,
}),
  2: dict({
  'name': 'pitch_valid',
  'value': 2,
}),
  4: dict({
  'name': 'roll_valid',
  'value': 4,
}),
  8: dict({
  'name': 'lateral_body_accel_valid',
  'value': 8,
}),
  16: dict({
  'name': 'normal_body_accel_valid',
  'value': 16,
}),
  32: dict({
  'name': 'turn_rate_valid',
  'value': 32,
}),
  64: dict({
  'name': 'hw_fail',
  'value': 64,
}),
  128: dict({
  'name': 'mag_invalid',
  'value': 128,
}),
  256: dict({
  'name': 'no_gps',
  'value': 256,
}),
  512: dict({
  'name': 'gps_invalid',
  'value': 512,
}),
  1024: dict({
  'name': 'solution_coasting',
  'value': 1024,
}),
  2048: dict({
  'name': 'true_track_angle',
  'value': 2048,
}),
  4096: dict({
  'name': 'magnetic_heading',
  'value': 4096,
}),
}),
}),
  'auto_sync_frequency': dict({
  'name': 'auto_sync_frequency',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'never',
  'value': 0,
}),
  1: dict({
  'name': 'occasionally',
  'value': 1,
}),
  2: dict({
  'name': 'frequent',
  'value': 2,
}),
  3: dict({
  'name': 'once_a_day',
  'value': 3,
}),
  4: dict({
  'name': 'remote',
  'value': 4,
}),
}),
}),
  'exd_layout': dict({
  'name': 'exd_layout',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'full_screen',
  'value': 0,
}),
  1: dict({
  'name': 'half_vertical',
  'value': 1,
}),
  2: dict({
  'name': 'half_horizontal',
  'value': 2,
}),
  3: dict({
  'name': 'half_vertical_right_split',
  'value': 3,
}),
  4: dict({
  'name': 'half_horizontal_bottom_split',
  'value': 4,
}),
  5: dict({
  'name': 'full_quarter_split',
  'value': 5,
}),
  6: dict({
  'name': 'half_vertical_left_split',
  'value': 6,
}),
  7: dict({
  'name': 'half_horizontal_top_split',
  'value': 7,
}),
  8: dict({
  'name': 'dynamic',
  'value': 8,
  'comment': 'The EXD may display the configured concepts in any layout it sees fit.',
}),
}),
}),
  'exd_display_type': dict({
  'name': 'exd_display_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'numerical',
  'value': 0,
}),
  1: dict({
  'name': 'simple',
  'value': 1,
}),
  2: dict({
  'name': 'graph',
  'value': 2,
}),
  3: dict({
  'name': 'bar',
  'value': 3,
}),
  4: dict({
  'name': 'circle_graph',
  'value': 4,
}),
  5: dict({
  'name': 'virtual_partner',
  'value': 5,
}),
  6: dict({
  'name': 'balance',
  'value': 6,
}),
  7: dict({
  'name': 'string_list',
  'value': 7,
}),
  8: dict({
  'name': 'string',
  'value': 8,
}),
  9: dict({
  'name': 'simple_dynamic_icon',
  'value': 9,
}),
  10: dict({
  'name': 'gauge',
  'value': 10,
}),
}),
}),
  'exd_data_units': dict({
  'name': 'exd_data_units',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'no_units',
  'value': 0,
}),
  1: dict({
  'name': 'laps',
  'value': 1,
}),
  2: dict({
  'name': 'miles_per_hour',
  'value': 2,
}),
  3: dict({
  'name': 'kilometers_per_hour',
  'value': 3,
}),
  4: dict({
  'name': 'feet_per_hour',
  'value': 4,
}),
  5: dict({
  'name': 'meters_per_hour',
  'value': 5,
}),
  6: dict({
  'name': 'degrees_celsius',
  'value': 6,
}),
  7: dict({
  'name': 'degrees_farenheit',
  'value': 7,
}),
  8: dict({
  'name': 'zone',
  'value': 8,
}),
  9: dict({
  'name': 'gear',
  'value': 9,
}),
  10: dict({
  'name': 'rpm',
  'value': 10,
}),
  11: dict({
  'name': 'bpm',
  'value': 11,
}),
  12: dict({
  'name': 'degrees',
  'value': 12,
}),
  13: dict({
  'name': 'millimeters',
  'value': 13,
}),
  14: dict({
  'name': 'meters',
  'value': 14,
}),
  15: dict({
  'name': 'kilometers',
  'value': 15,
}),
  16: dict({
  'name': 'feet',
  'value': 16,
}),
  17: dict({
  'name': 'yards',
  'value': 17,
}),
  18: dict({
  'name': 'kilofeet',
  'value': 18,
}),
  19: dict({
  'name': 'miles',
  'value': 19,
}),
  20: dict({
  'name': 'time',
  'value': 20,
}),
  21: dict({
  'name': 'enum_turn_type',
  'value': 21,
}),
  22: dict({
  'name': 'percent',
  'value': 22,
}),
  23: dict({
  'name': 'watts',
  'value': 23,
}),
  24: dict({
  'name': 'watts_per_kilogram',
  'value': 24,
}),
  25: dict({
  'name': 'enum_battery_status',
  'value': 25,
}),
  26: dict({
  'name': 'enum_bike_light_beam_angle_mode',
  'value': 26,
}),
  27: dict({
  'name': 'enum_bike_light_battery_status',
  'value': 27,
}),
  28: dict({
  'name': 'enum_bike_light_network_config_type',
  'value': 28,
}),
  29: dict({
  'name': 'lights',
  'value': 29,
}),
  30: dict({
  'name': 'seconds',
  'value': 30,
}),
  31: dict({
  'name': 'minutes',
  'value': 31,
}),
  32: dict({
  'name': 'hours',
  'value': 32,
}),
  33: dict({
  'name': 'calories',
  'value': 33,
}),
  34: dict({
  'name': 'kilojoules',
  'value': 34,
}),
  35: dict({
  'name': 'milliseconds',
  'value': 35,
}),
  36: dict({
  'name': 'second_per_mile',
  'value': 36,
}),
  37: dict({
  'name': 'second_per_kilometer',
  'value': 37,
}),
  38: dict({
  'name': 'centimeter',
  'value': 38,
}),
  39: dict({
  'name': 'enum_course_point',
  'value': 39,
}),
  40: dict({
  'name': 'bradians',
  'value': 40,
}),
  41: dict({
  'name': 'enum_sport',
  'value': 41,
}),
  42: dict({
  'name': 'inches_hg',
  'value': 42,
}),
  43: dict({
  'name': 'mm_hg',
  'value': 43,
}),
  44: dict({
  'name': 'mbars',
  'value': 44,
}),
  45: dict({
  'name': 'hecto_pascals',
  'value': 45,
}),
  46: dict({
  'name': 'feet_per_min',
  'value': 46,
}),
  47: dict({
  'name': 'meters_per_min',
  'value': 47,
}),
  48: dict({
  'name': 'meters_per_sec',
  'value': 48,
}),
  49: dict({
  'name': 'eight_cardinal',
  'value': 49,
}),
}),
}),
  'exd_qualifiers': dict({
  'name': 'exd_qualifiers',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'no_qualifier',
  'value': 0,
}),
  1: dict({
  'name': 'instantaneous',
  'value': 1,
}),
  2: dict({
  'name': 'average',
  'value': 2,
}),
  3: dict({
  'name': 'lap',
  'value': 3,
}),
  4: dict({
  'name': 'maximum',
  'value': 4,
}),
  5: dict({
  'name': 'maximum_average',
  'value': 5,
}),
  6: dict({
  'name': 'maximum_lap',
  'value': 6,
}),
  7: dict({
  'name': 'last_lap',
  'value': 7,
}),
  8: dict({
  'name': 'average_lap',
  'value': 8,
}),
  9: dict({
  'name': 'to_destination',
  'value': 9,
}),
  10: dict({
  'name': 'to_go',
  'value': 10,
}),
  11: dict({
  'name': 'to_next',
  'value': 11,
}),
  12: dict({
  'name': 'next_course_point',
  'value': 12,
}),
  13: dict({
  'name': 'total',
  'value': 13,
}),
  14: dict({
  'name': 'three_second_average',
  'value': 14,
}),
  15: dict({
  'name': 'ten_second_average',
  'value': 15,
}),
  16: dict({
  'name': 'thirty_second_average',
  'value': 16,
}),
  17: dict({
  'name': 'percent_maximum',
  'value': 17,
}),
  18: dict({
  'name': 'percent_maximum_average',
  'value': 18,
}),
  19: dict({
  'name': 'lap_percent_maximum',
  'value': 19,
}),
  20: dict({
  'name': 'elapsed',
  'value': 20,
}),
  21: dict({
  'name': 'sunrise',
  'value': 21,
}),
  22: dict({
  'name': 'sunset',
  'value': 22,
}),
  23: dict({
  'name': 'compared_to_virtual_partner',
  'value': 23,
}),
  24: dict({
  'name': 'maximum_24h',
  'value': 24,
}),
  25: dict({
  'name': 'minimum_24h',
  'value': 25,
}),
  26: dict({
  'name': 'minimum',
  'value': 26,
}),
  27: dict({
  'name': 'first',
  'value': 27,
}),
  28: dict({
  'name': 'second',
  'value': 28,
}),
  29: dict({
  'name': 'third',
  'value': 29,
}),
  30: dict({
  'name': 'shifter',
  'value': 30,
}),
  31: dict({
  'name': 'last_sport',
  'value': 31,
}),
  32: dict({
  'name': 'moving',
  'value': 32,
}),
  33: dict({
  'name': 'stopped',
  'value': 33,
}),
  34: dict({
  'name': 'estimated_total',
  'value': 34,
}),
  242: dict({
  'name': 'zone_9',
  'value': 242,
}),
  243: dict({
  'name': 'zone_8',
  'value': 243,
}),
  244: dict({
  'name': 'zone_7',
  'value': 244,
}),
  245: dict({
  'name': 'zone_6',
  'value': 245,
}),
  246: dict({
  'name': 'zone_5',
  'value': 246,
}),
  247: dict({
  'name': 'zone_4',
  'value': 247,
}),
  248: dict({
  'name': 'zone_3',
  'value': 248,
}),
  249: dict({
  'name': 'zone_2',
  'value': 249,
}),
  250: dict({
  'name': 'zone_1',
  'value': 250,
}),
}),
}),
  'exd_descriptors': dict({
  'name': 'exd_descriptors',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'bike_light_battery_status',
  'value': 0,
}),
  1: dict({
  'name': 'beam_angle_status',
  'value': 1,
}),
  2: dict({
  'name': 'batery_level',
  'value': 2,
}),
  3: dict({
  'name': 'light_network_mode',
  'value': 3,
}),
  4: dict({
  'name': 'number_lights_connected',
  'value': 4,
}),
  5: dict({
  'name': 'cadence',
  'value': 5,
}),
  6: dict({
  'name': 'distance',
  'value': 6,
}),
  7: dict({
  'name': 'estimated_time_of_arrival',
  'value': 7,
}),
  8: dict({
  'name': 'heading',
  'value': 8,
}),
  9: dict({
  'name': 'time',
  'value': 9,
}),
  10: dict({
  'name': 'battery_level',
  'value': 10,
}),
  11: dict({
  'name': 'trainer_resistance',
  'value': 11,
}),
  12: dict({
  'name': 'trainer_target_power',
  'value': 12,
}),
  13: dict({
  'name': 'time_seated',
  'value': 13,
}),
  14: dict({
  'name': 'time_standing',
  'value': 14,
}),
  15: dict({
  'name': 'elevation',
  'value': 15,
}),
  16: dict({
  'name': 'grade',
  'value': 16,
}),
  17: dict({
  'name': 'ascent',
  'value': 17,
}),
  18: dict({
  'name': 'descent',
  'value': 18,
}),
  19: dict({
  'name': 'vertical_speed',
  'value': 19,
}),
  20: dict({
  'name': 'di2_battery_level',
  'value': 20,
}),
  21: dict({
  'name': 'front_gear',
  'value': 21,
}),
  22: dict({
  'name': 'rear_gear',
  'value': 22,
}),
  23: dict({
  'name': 'gear_ratio',
  'value': 23,
}),
  24: dict({
  'name': 'heart_rate',
  'value': 24,
}),
  25: dict({
  'name': 'heart_rate_zone',
  'value': 25,
}),
  26: dict({
  'name': 'time_in_heart_rate_zone',
  'value': 26,
}),
  27: dict({
  'name': 'heart_rate_reserve',
  'value': 27,
}),
  28: dict({
  'name': 'calories',
  'value': 28,
}),
  29: dict({
  'name': 'gps_accuracy',
  'value': 29,
}),
  30: dict({
  'name': 'gps_signal_strength',
  'value': 30,
}),
  31: dict({
  'name': 'temperature',
  'value': 31,
}),
  32: dict({
  'name': 'time_of_day',
  'value': 32,
}),
  33: dict({
  'name': 'balance',
  'value': 33,
}),
  34: dict({
  'name': 'pedal_smoothness',
  'value': 34,
}),
  35: dict({
  'name': 'power',
  'value': 35,
}),
  36: dict({
  'name': 'functional_threshold_power',
  'value': 36,
}),
  37: dict({
  'name': 'intensity_factor',
  'value': 37,
}),
  38: dict({
  'name': 'work',
  'value': 38,
}),
  39: dict({
  'name': 'power_ratio',
  'value': 39,
}),
  40: dict({
  'name': 'normalized_power',
  'value': 40,
}),
  41: dict({
  'name': 'training_stress_Score',
  'value': 41,
}),
  42: dict({
  'name': 'time_on_zone',
  'value': 42,
}),
  43: dict({
  'name': 'speed',
  'value': 43,
}),
  44: dict({
  'name': 'laps',
  'value': 44,
}),
  45: dict({
  'name': 'reps',
  'value': 45,
}),
  46: dict({
  'name': 'workout_step',
  'value': 46,
}),
  47: dict({
  'name': 'course_distance',
  'value': 47,
}),
  48: dict({
  'name': 'navigation_distance',
  'value': 48,
}),
  49: dict({
  'name': 'course_estimated_time_of_arrival',
  'value': 49,
}),
  50: dict({
  'name': 'navigation_estimated_time_of_arrival',
  'value': 50,
}),
  51: dict({
  'name': 'course_time',
  'value': 51,
}),
  52: dict({
  'name': 'navigation_time',
  'value': 52,
}),
  53: dict({
  'name': 'course_heading',
  'value': 53,
}),
  54: dict({
  'name': 'navigation_heading',
  'value': 54,
}),
  55: dict({
  'name': 'power_zone',
  'value': 55,
}),
  56: dict({
  'name': 'torque_effectiveness',
  'value': 56,
}),
  57: dict({
  'name': 'timer_time',
  'value': 57,
}),
  58: dict({
  'name': 'power_weight_ratio',
  'value': 58,
}),
  59: dict({
  'name': 'left_platform_center_offset',
  'value': 59,
}),
  60: dict({
  'name': 'right_platform_center_offset',
  'value': 60,
}),
  61: dict({
  'name': 'left_power_phase_start_angle',
  'value': 61,
}),
  62: dict({
  'name': 'right_power_phase_start_angle',
  'value': 62,
}),
  63: dict({
  'name': 'left_power_phase_finish_angle',
  'value': 63,
}),
  64: dict({
  'name': 'right_power_phase_finish_angle',
  'value': 64,
}),
  65: dict({
  'name': 'gears',
  'value': 65,
  'comment': 'Combined gear information',
}),
  66: dict({
  'name': 'pace',
  'value': 66,
}),
  67: dict({
  'name': 'training_effect',
  'value': 67,
}),
  68: dict({
  'name': 'vertical_oscillation',
  'value': 68,
}),
  69: dict({
  'name': 'vertical_ratio',
  'value': 69,
}),
  70: dict({
  'name': 'ground_contact_time',
  'value': 70,
}),
  71: dict({
  'name': 'left_ground_contact_time_balance',
  'value': 71,
}),
  72: dict({
  'name': 'right_ground_contact_time_balance',
  'value': 72,
}),
  73: dict({
  'name': 'stride_length',
  'value': 73,
}),
  74: dict({
  'name': 'running_cadence',
  'value': 74,
}),
  75: dict({
  'name': 'performance_condition',
  'value': 75,
}),
  76: dict({
  'name': 'course_type',
  'value': 76,
}),
  77: dict({
  'name': 'time_in_power_zone',
  'value': 77,
}),
  78: dict({
  'name': 'navigation_turn',
  'value': 78,
}),
  79: dict({
  'name': 'course_location',
  'value': 79,
}),
  80: dict({
  'name': 'navigation_location',
  'value': 80,
}),
  81: dict({
  'name': 'compass',
  'value': 81,
}),
  82: dict({
  'name': 'gear_combo',
  'value': 82,
}),
  83: dict({
  'name': 'muscle_oxygen',
  'value': 83,
}),
  84: dict({
  'name': 'icon',
  'value': 84,
}),
  85: dict({
  'name': 'compass_heading',
  'value': 85,
}),
  86: dict({
  'name': 'gps_heading',
  'value': 86,
}),
  87: dict({
  'name': 'gps_elevation',
  'value': 87,
}),
  88: dict({
  'name': 'anaerobic_training_effect',
  'value': 88,
}),
  89: dict({
  'name': 'course',
  'value': 89,
}),
  90: dict({
  'name': 'off_course',
  'value': 90,
}),
  91: dict({
  'name': 'glide_ratio',
  'value': 91,
}),
  92: dict({
  'name': 'vertical_distance',
  'value': 92,
}),
  93: dict({
  'name': 'vmg',
  'value': 93,
}),
  94: dict({
  'name': 'ambient_pressure',
  'value': 94,
}),
  95: dict({
  'name': 'pressure',
  'value': 95,
}),
  96: dict({
  'name': 'vam',
  'value': 96,
}),
}),
}),
  'auto_activity_detect': dict({
  'name': 'auto_activity_detect',
  'base_type': 'uint32',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'none',
  'value': 0,
}),
  1: dict({
  'name': 'running',
  'value': 1,
}),
  2: dict({
  'name': 'cycling',
  'value': 2,
}),
  4: dict({
  'name': 'swimming',
  'value': 4,
}),
  8: dict({
  'name': 'walking',
  'value': 8,
}),
  32: dict({
  'name': 'elliptical',
  'value': 32,
}),
  1024: dict({
  'name': 'sedentary',
  'value': 1024,
}),
}),
}),
  'supported_exd_screen_layouts': dict({
  'name': 'supported_exd_screen_layouts',
  'base_type': 'uint32z',
  'parser': resolve,
  'values': dict({
  1: dict({
  'name': 'full_screen',
  'value': 1,
}),
  2: dict({
  'name': 'half_vertical',
  'value': 2,
}),
  4: dict({
  'name': 'half_horizontal',
  'value': 4,
}),
  8: dict({
  'name': 'half_vertical_right_split',
  'value': 8,
}),
  16: dict({
  'name': 'half_horizontal_bottom_split',
  'value': 16,
}),
  32: dict({
  'name': 'full_quarter_split',
  'value': 32,
}),
  64: dict({
  'name': 'half_vertical_left_split',
  'value': 64,
}),
  128: dict({
  'name': 'half_horizontal_top_split',
  'value': 128,
}),
}),
}),
  'fit_base_type': dict({
  'name': 'fit_base_type',
  'base_type': 'uint8',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'enum',
  'value': 0,
}),
  1: dict({
  'name': 'sint8',
  'value': 1,
}),
  2: dict({
  'name': 'uint8',
  'value': 2,
}),
  131: dict({
  'name': 'sint16',
  'value': 131,
}),
  132: dict({
  'name': 'uint16',
  'value': 132,
}),
  133: dict({
  'name': 'sint32',
  'value': 133,
}),
  134: dict({
  'name': 'uint32',
  'value': 134,
}),
  7: dict({
  'name': 'string',
  'value': 7,
}),
  136: dict({
  'name': 'float32',
  'value': 136,
}),
  137: dict({
  'name': 'float64',
  'value': 137,
}),
  10: dict({
  'name': 'uint8z',
  'value': 10,
}),
  139: dict({
  'name': 'uint16z',
  'value': 139,
}),
  140: dict({
  'name': 'uint32z',
  'value': 140,
}),
  13: dict({
  'name': 'byte',
  'value': 13,
}),
  142: dict({
  'name': 'sint64',
  'value': 142,
}),
  143: dict({
  'name': 'uint64',
  'value': 143,
}),
  144: dict({
  'name': 'uint64z',
  'value': 144,
}),
}),
}),
  'turn_type': dict({
  'name': 'turn_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'arriving_idx',
  'value': 0,
}),
  1: dict({
  'name': 'arriving_left_idx',
  'value': 1,
}),
  2: dict({
  'name': 'arriving_right_idx',
  'value': 2,
}),
  3: dict({
  'name': 'arriving_via_idx',
  'value': 3,
}),
  4: dict({
  'name': 'arriving_via_left_idx',
  'value': 4,
}),
  5: dict({
  'name': 'arriving_via_right_idx',
  'value': 5,
}),
  6: dict({
  'name': 'bear_keep_left_idx',
  'value': 6,
}),
  7: dict({
  'name': 'bear_keep_right_idx',
  'value': 7,
}),
  8: dict({
  'name': 'continue_idx',
  'value': 8,
}),
  9: dict({
  'name': 'exit_left_idx',
  'value': 9,
}),
  10: dict({
  'name': 'exit_right_idx',
  'value': 10,
}),
  11: dict({
  'name': 'ferry_idx',
  'value': 11,
}),
  12: dict({
  'name': 'roundabout_45_idx',
  'value': 12,
}),
  13: dict({
  'name': 'roundabout_90_idx',
  'value': 13,
}),
  14: dict({
  'name': 'roundabout_135_idx',
  'value': 14,
}),
  15: dict({
  'name': 'roundabout_180_idx',
  'value': 15,
}),
  16: dict({
  'name': 'roundabout_225_idx',
  'value': 16,
}),
  17: dict({
  'name': 'roundabout_270_idx',
  'value': 17,
}),
  18: dict({
  'name': 'roundabout_315_idx',
  'value': 18,
}),
  19: dict({
  'name': 'roundabout_360_idx',
  'value': 19,
}),
  20: dict({
  'name': 'roundabout_neg_45_idx',
  'value': 20,
}),
  21: dict({
  'name': 'roundabout_neg_90_idx',
  'value': 21,
}),
  22: dict({
  'name': 'roundabout_neg_135_idx',
  'value': 22,
}),
  23: dict({
  'name': 'roundabout_neg_180_idx',
  'value': 23,
}),
  24: dict({
  'name': 'roundabout_neg_225_idx',
  'value': 24,
}),
  25: dict({
  'name': 'roundabout_neg_270_idx',
  'value': 25,
}),
  26: dict({
  'name': 'roundabout_neg_315_idx',
  'value': 26,
}),
  27: dict({
  'name': 'roundabout_neg_360_idx',
  'value': 27,
}),
  28: dict({
  'name': 'roundabout_generic_idx',
  'value': 28,
}),
  29: dict({
  'name': 'roundabout_neg_generic_idx',
  'value': 29,
}),
  30: dict({
  'name': 'sharp_turn_left_idx',
  'value': 30,
}),
  31: dict({
  'name': 'sharp_turn_right_idx',
  'value': 31,
}),
  32: dict({
  'name': 'turn_left_idx',
  'value': 32,
}),
  33: dict({
  'name': 'turn_right_idx',
  'value': 33,
}),
  34: dict({
  'name': 'uturn_left_idx',
  'value': 34,
}),
  35: dict({
  'name': 'uturn_right_idx',
  'value': 35,
}),
  36: dict({
  'name': 'icon_inv_idx',
  'value': 36,
}),
  37: dict({
  'name': 'icon_idx_cnt',
  'value': 37,
}),
}),
}),
  'bike_light_beam_angle_mode': dict({
  'name': 'bike_light_beam_angle_mode',
  'base_type': 'uint8',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'manual',
  'value': 0,
}),
  1: dict({
  'name': 'auto',
  'value': 1,
}),
}),
}),
  'fit_base_unit': dict({
  'name': 'fit_base_unit',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'other',
  'value': 0,
}),
  1: dict({
  'name': 'kilogram',
  'value': 1,
}),
  2: dict({
  'name': 'pound',
  'value': 2,
}),
}),
}),
  'set_type': dict({
  'name': 'set_type',
  'base_type': 'uint8',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'rest',
  'value': 0,
}),
  1: dict({
  'name': 'active',
  'value': 1,
}),
}),
}),
  'exercise_category': dict({
  'name': 'exercise_category',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'bench_press',
  'value': 0,
}),
  1: dict({
  'name': 'calf_raise',
  'value': 1,
}),
  2: dict({
  'name': 'cardio',
  'value': 2,
}),
  3: dict({
  'name': 'carry',
  'value': 3,
}),
  4: dict({
  'name': 'chop',
  'value': 4,
}),
  5: dict({
  'name': 'core',
  'value': 5,
}),
  6: dict({
  'name': 'crunch',
  'value': 6,
}),
  7: dict({
  'name': 'curl',
  'value': 7,
}),
  8: dict({
  'name': 'deadlift',
  'value': 8,
}),
  9: dict({
  'name': 'flye',
  'value': 9,
}),
  10: dict({
  'name': 'hip_raise',
  'value': 10,
}),
  11: dict({
  'name': 'hip_stability',
  'value': 11,
}),
  12: dict({
  'name': 'hip_swing',
  'value': 12,
}),
  13: dict({
  'name': 'hyperextension',
  'value': 13,
}),
  14: dict({
  'name': 'lateral_raise',
  'value': 14,
}),
  15: dict({
  'name': 'leg_curl',
  'value': 15,
}),
  16: dict({
  'name': 'leg_raise',
  'value': 16,
}),
  17: dict({
  'name': 'lunge',
  'value': 17,
}),
  18: dict({
  'name': 'olympic_lift',
  'value': 18,
}),
  19: dict({
  'name': 'plank',
  'value': 19,
}),
  20: dict({
  'name': 'plyo',
  'value': 20,
}),
  21: dict({
  'name': 'pull_up',
  'value': 21,
}),
  22: dict({
  'name': 'push_up',
  'value': 22,
}),
  23: dict({
  'name': 'row',
  'value': 23,
}),
  24: dict({
  'name': 'shoulder_press',
  'value': 24,
}),
  25: dict({
  'name': 'shoulder_stability',
  'value': 25,
}),
  26: dict({
  'name': 'shrug',
  'value': 26,
}),
  27: dict({
  'name': 'sit_up',
  'value': 27,
}),
  28: dict({
  'name': 'squat',
  'value': 28,
}),
  29: dict({
  'name': 'total_body',
  'value': 29,
}),
  30: dict({
  'name': 'triceps_extension',
  'value': 30,
}),
  31: dict({
  'name': 'warm_up',
  'value': 31,
}),
  32: dict({
  'name': 'run',
  'value': 32,
}),
  65534: dict({
  'name': 'unknown',
  'value': 65534,
}),
}),
}),
  'bench_press_exercise_name': dict({
  'name': 'bench_press_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'alternating_dumbbell_chest_press_on_swiss_ball',
  'value': 0,
}),
  1: dict({
  'name': 'barbell_bench_press',
  'value': 1,
}),
  2: dict({
  'name': 'barbell_board_bench_press',
  'value': 2,
}),
  3: dict({
  'name': 'barbell_floor_press',
  'value': 3,
}),
  4: dict({
  'name': 'close_grip_barbell_bench_press',
  'value': 4,
}),
  5: dict({
  'name': 'decline_dumbbell_bench_press',
  'value': 5,
}),
  6: dict({
  'name': 'dumbbell_bench_press',
  'value': 6,
}),
  7: dict({
  'name': 'dumbbell_floor_press',
  'value': 7,
}),
  8: dict({
  'name': 'incline_barbell_bench_press',
  'value': 8,
}),
  9: dict({
  'name': 'incline_dumbbell_bench_press',
  'value': 9,
}),
  10: dict({
  'name': 'incline_smith_machine_bench_press',
  'value': 10,
}),
  11: dict({
  'name': 'isometric_barbell_bench_press',
  'value': 11,
}),
  12: dict({
  'name': 'kettlebell_chest_press',
  'value': 12,
}),
  13: dict({
  'name': 'neutral_grip_dumbbell_bench_press',
  'value': 13,
}),
  14: dict({
  'name': 'neutral_grip_dumbbell_incline_bench_press',
  'value': 14,
}),
  15: dict({
  'name': 'one_arm_floor_press',
  'value': 15,
}),
  16: dict({
  'name': 'weighted_one_arm_floor_press',
  'value': 16,
}),
  17: dict({
  'name': 'partial_lockout',
  'value': 17,
}),
  18: dict({
  'name': 'reverse_grip_barbell_bench_press',
  'value': 18,
}),
  19: dict({
  'name': 'reverse_grip_incline_bench_press',
  'value': 19,
}),
  20: dict({
  'name': 'single_arm_cable_chest_press',
  'value': 20,
}),
  21: dict({
  'name': 'single_arm_dumbbell_bench_press',
  'value': 21,
}),
  22: dict({
  'name': 'smith_machine_bench_press',
  'value': 22,
}),
  23: dict({
  'name': 'swiss_ball_dumbbell_chest_press',
  'value': 23,
}),
  24: dict({
  'name': 'triple_stop_barbell_bench_press',
  'value': 24,
}),
  25: dict({
  'name': 'wide_grip_barbell_bench_press',
  'value': 25,
}),
  26: dict({
  'name': 'alternating_dumbbell_chest_press',
  'value': 26,
}),
}),
}),
  'calf_raise_exercise_name': dict({
  'name': 'calf_raise_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': '3_way_calf_raise',
  'value': 0,
}),
  1: dict({
  'name': '3_way_weighted_calf_raise',
  'value': 1,
}),
  2: dict({
  'name': '3_way_single_leg_calf_raise',
  'value': 2,
}),
  3: dict({
  'name': '3_way_weighted_single_leg_calf_raise',
  'value': 3,
}),
  4: dict({
  'name': 'donkey_calf_raise',
  'value': 4,
}),
  5: dict({
  'name': 'weighted_donkey_calf_raise',
  'value': 5,
}),
  6: dict({
  'name': 'seated_calf_raise',
  'value': 6,
}),
  7: dict({
  'name': 'weighted_seated_calf_raise',
  'value': 7,
}),
  8: dict({
  'name': 'seated_dumbbell_toe_raise',
  'value': 8,
}),
  9: dict({
  'name': 'single_leg_bent_knee_calf_raise',
  'value': 9,
}),
  10: dict({
  'name': 'weighted_single_leg_bent_knee_calf_raise',
  'value': 10,
}),
  11: dict({
  'name': 'single_leg_decline_push_up',
  'value': 11,
}),
  12: dict({
  'name': 'single_leg_donkey_calf_raise',
  'value': 12,
}),
  13: dict({
  'name': 'weighted_single_leg_donkey_calf_raise',
  'value': 13,
}),
  14: dict({
  'name': 'single_leg_hip_raise_with_knee_hold',
  'value': 14,
}),
  15: dict({
  'name': 'single_leg_standing_calf_raise',
  'value': 15,
}),
  16: dict({
  'name': 'single_leg_standing_dumbbell_calf_raise',
  'value': 16,
}),
  17: dict({
  'name': 'standing_barbell_calf_raise',
  'value': 17,
}),
  18: dict({
  'name': 'standing_calf_raise',
  'value': 18,
}),
  19: dict({
  'name': 'weighted_standing_calf_raise',
  'value': 19,
}),
  20: dict({
  'name': 'standing_dumbbell_calf_raise',
  'value': 20,
}),
}),
}),
  'cardio_exercise_name': dict({
  'name': 'cardio_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'bob_and_weave_circle',
  'value': 0,
}),
  1: dict({
  'name': 'weighted_bob_and_weave_circle',
  'value': 1,
}),
  2: dict({
  'name': 'cardio_core_crawl',
  'value': 2,
}),
  3: dict({
  'name': 'weighted_cardio_core_crawl',
  'value': 3,
}),
  4: dict({
  'name': 'double_under',
  'value': 4,
}),
  5: dict({
  'name': 'weighted_double_under',
  'value': 5,
}),
  6: dict({
  'name': 'jump_rope',
  'value': 6,
}),
  7: dict({
  'name': 'weighted_jump_rope',
  'value': 7,
}),
  8: dict({
  'name': 'jump_rope_crossover',
  'value': 8,
}),
  9: dict({
  'name': 'weighted_jump_rope_crossover',
  'value': 9,
}),
  10: dict({
  'name': 'jump_rope_jog',
  'value': 10,
}),
  11: dict({
  'name': 'weighted_jump_rope_jog',
  'value': 11,
}),
  12: dict({
  'name': 'jumping_jacks',
  'value': 12,
}),
  13: dict({
  'name': 'weighted_jumping_jacks',
  'value': 13,
}),
  14: dict({
  'name': 'ski_moguls',
  'value': 14,
}),
  15: dict({
  'name': 'weighted_ski_moguls',
  'value': 15,
}),
  16: dict({
  'name': 'split_jacks',
  'value': 16,
}),
  17: dict({
  'name': 'weighted_split_jacks',
  'value': 17,
}),
  18: dict({
  'name': 'squat_jacks',
  'value': 18,
}),
  19: dict({
  'name': 'weighted_squat_jacks',
  'value': 19,
}),
  20: dict({
  'name': 'triple_under',
  'value': 20,
}),
  21: dict({
  'name': 'weighted_triple_under',
  'value': 21,
}),
}),
}),
  'carry_exercise_name': dict({
  'name': 'carry_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'bar_holds',
  'value': 0,
}),
  1: dict({
  'name': 'farmers_walk',
  'value': 1,
}),
  2: dict({
  'name': 'farmers_walk_on_toes',
  'value': 2,
}),
  3: dict({
  'name': 'hex_dumbbell_hold',
  'value': 3,
}),
  4: dict({
  'name': 'overhead_carry',
  'value': 4,
}),
}),
}),
  'chop_exercise_name': dict({
  'name': 'chop_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'cable_pull_through',
  'value': 0,
}),
  1: dict({
  'name': 'cable_rotational_lift',
  'value': 1,
}),
  2: dict({
  'name': 'cable_woodchop',
  'value': 2,
}),
  3: dict({
  'name': 'cross_chop_to_knee',
  'value': 3,
}),
  4: dict({
  'name': 'weighted_cross_chop_to_knee',
  'value': 4,
}),
  5: dict({
  'name': 'dumbbell_chop',
  'value': 5,
}),
  6: dict({
  'name': 'half_kneeling_rotation',
  'value': 6,
}),
  7: dict({
  'name': 'weighted_half_kneeling_rotation',
  'value': 7,
}),
  8: dict({
  'name': 'half_kneeling_rotational_chop',
  'value': 8,
}),
  9: dict({
  'name': 'half_kneeling_rotational_reverse_chop',
  'value': 9,
}),
  10: dict({
  'name': 'half_kneeling_stability_chop',
  'value': 10,
}),
  11: dict({
  'name': 'half_kneeling_stability_reverse_chop',
  'value': 11,
}),
  12: dict({
  'name': 'kneeling_rotational_chop',
  'value': 12,
}),
  13: dict({
  'name': 'kneeling_rotational_reverse_chop',
  'value': 13,
}),
  14: dict({
  'name': 'kneeling_stability_chop',
  'value': 14,
}),
  15: dict({
  'name': 'kneeling_woodchopper',
  'value': 15,
}),
  16: dict({
  'name': 'medicine_ball_wood_chops',
  'value': 16,
}),
  17: dict({
  'name': 'power_squat_chops',
  'value': 17,
}),
  18: dict({
  'name': 'weighted_power_squat_chops',
  'value': 18,
}),
  19: dict({
  'name': 'standing_rotational_chop',
  'value': 19,
}),
  20: dict({
  'name': 'standing_split_rotational_chop',
  'value': 20,
}),
  21: dict({
  'name': 'standing_split_rotational_reverse_chop',
  'value': 21,
}),
  22: dict({
  'name': 'standing_stability_reverse_chop',
  'value': 22,
}),
}),
}),
  'core_exercise_name': dict({
  'name': 'core_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'abs_jabs',
  'value': 0,
}),
  1: dict({
  'name': 'weighted_abs_jabs',
  'value': 1,
}),
  2: dict({
  'name': 'alternating_plate_reach',
  'value': 2,
}),
  3: dict({
  'name': 'barbell_rollout',
  'value': 3,
}),
  4: dict({
  'name': 'weighted_barbell_rollout',
  'value': 4,
}),
  5: dict({
  'name': 'body_bar_oblique_twist',
  'value': 5,
}),
  6: dict({
  'name': 'cable_core_press',
  'value': 6,
}),
  7: dict({
  'name': 'cable_side_bend',
  'value': 7,
}),
  8: dict({
  'name': 'side_bend',
  'value': 8,
}),
  9: dict({
  'name': 'weighted_side_bend',
  'value': 9,
}),
  10: dict({
  'name': 'crescent_circle',
  'value': 10,
}),
  11: dict({
  'name': 'weighted_crescent_circle',
  'value': 11,
}),
  12: dict({
  'name': 'cycling_russian_twist',
  'value': 12,
}),
  13: dict({
  'name': 'weighted_cycling_russian_twist',
  'value': 13,
}),
  14: dict({
  'name': 'elevated_feet_russian_twist',
  'value': 14,
}),
  15: dict({
  'name': 'weighted_elevated_feet_russian_twist',
  'value': 15,
}),
  16: dict({
  'name': 'half_turkish_get_up',
  'value': 16,
}),
  17: dict({
  'name': 'kettlebell_windmill',
  'value': 17,
}),
  18: dict({
  'name': 'kneeling_ab_wheel',
  'value': 18,
}),
  19: dict({
  'name': 'weighted_kneeling_ab_wheel',
  'value': 19,
}),
  20: dict({
  'name': 'modified_front_lever',
  'value': 20,
}),
  21: dict({
  'name': 'open_knee_tucks',
  'value': 21,
}),
  22: dict({
  'name': 'weighted_open_knee_tucks',
  'value': 22,
}),
  23: dict({
  'name': 'side_abs_leg_lift',
  'value': 23,
}),
  24: dict({
  'name': 'weighted_side_abs_leg_lift',
  'value': 24,
}),
  25: dict({
  'name': 'swiss_ball_jackknife',
  'value': 25,
}),
  26: dict({
  'name': 'weighted_swiss_ball_jackknife',
  'value': 26,
}),
  27: dict({
  'name': 'swiss_ball_pike',
  'value': 27,
}),
  28: dict({
  'name': 'weighted_swiss_ball_pike',
  'value': 28,
}),
  29: dict({
  'name': 'swiss_ball_rollout',
  'value': 29,
}),
  30: dict({
  'name': 'weighted_swiss_ball_rollout',
  'value': 30,
}),
  31: dict({
  'name': 'triangle_hip_press',
  'value': 31,
}),
  32: dict({
  'name': 'weighted_triangle_hip_press',
  'value': 32,
}),
  33: dict({
  'name': 'trx_suspended_jackknife',
  'value': 33,
}),
  34: dict({
  'name': 'weighted_trx_suspended_jackknife',
  'value': 34,
}),
  35: dict({
  'name': 'u_boat',
  'value': 35,
}),
  36: dict({
  'name': 'weighted_u_boat',
  'value': 36,
}),
  37: dict({
  'name': 'windmill_switches',
  'value': 37,
}),
  38: dict({
  'name': 'weighted_windmill_switches',
  'value': 38,
}),
  39: dict({
  'name': 'alternating_slide_out',
  'value': 39,
}),
  40: dict({
  'name': 'weighted_alternating_slide_out',
  'value': 40,
}),
  41: dict({
  'name': 'ghd_back_extensions',
  'value': 41,
}),
  42: dict({
  'name': 'weighted_ghd_back_extensions',
  'value': 42,
}),
  43: dict({
  'name': 'overhead_walk',
  'value': 43,
}),
  44: dict({
  'name': 'inchworm',
  'value': 44,
}),
  45: dict({
  'name': 'weighted_modified_front_lever',
  'value': 45,
}),
  46: dict({
  'name': 'russian_twist',
  'value': 46,
}),
  47: dict({
  'name': 'abdominal_leg_rotations',
  'value': 47,
  'comment': 'Deprecated do not use',
}),
  48: dict({
  'name': 'arm_and_leg_extension_on_knees',
  'value': 48,
}),
  49: dict({
  'name': 'bicycle',
  'value': 49,
}),
  50: dict({
  'name': 'bicep_curl_with_leg_extension',
  'value': 50,
}),
  51: dict({
  'name': 'cat_cow',
  'value': 51,
}),
  52: dict({
  'name': 'corkscrew',
  'value': 52,
}),
  53: dict({
  'name': 'criss_cross',
  'value': 53,
}),
  54: dict({
  'name': 'criss_cross_with_ball',
  'value': 54,
  'comment': 'Deprecated do not use',
}),
  55: dict({
  'name': 'double_leg_stretch',
  'value': 55,
}),
  56: dict({
  'name': 'knee_folds',
  'value': 56,
}),
  57: dict({
  'name': 'lower_lift',
  'value': 57,
}),
  58: dict({
  'name': 'neck_pull',
  'value': 58,
}),
  59: dict({
  'name': 'pelvic_clocks',
  'value': 59,
}),
  60: dict({
  'name': 'roll_over',
  'value': 60,
}),
  61: dict({
  'name': 'roll_up',
  'value': 61,
}),
  62: dict({
  'name': 'rolling',
  'value': 62,
}),
  63: dict({
  'name': 'rowing_1',
  'value': 63,
}),
  64: dict({
  'name': 'rowing_2',
  'value': 64,
}),
  65: dict({
  'name': 'scissors',
  'value': 65,
}),
  66: dict({
  'name': 'single_leg_circles',
  'value': 66,
}),
  67: dict({
  'name': 'single_leg_stretch',
  'value': 67,
}),
  68: dict({
  'name': 'snake_twist_1_and_2',
  'value': 68,
  'comment': 'Deprecated do not use',
}),
  69: dict({
  'name': 'swan',
  'value': 69,
}),
  70: dict({
  'name': 'swimming',
  'value': 70,
}),
  71: dict({
  'name': 'teaser',
  'value': 71,
}),
  72: dict({
  'name': 'the_hundred',
  'value': 72,
}),
}),
}),
  'crunch_exercise_name': dict({
  'name': 'crunch_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'bicycle_crunch',
  'value': 0,
}),
  1: dict({
  'name': 'cable_crunch',
  'value': 1,
}),
  2: dict({
  'name': 'circular_arm_crunch',
  'value': 2,
}),
  3: dict({
  'name': 'crossed_arms_crunch',
  'value': 3,
}),
  4: dict({
  'name': 'weighted_crossed_arms_crunch',
  'value': 4,
}),
  5: dict({
  'name': 'cross_leg_reverse_crunch',
  'value': 5,
}),
  6: dict({
  'name': 'weighted_cross_leg_reverse_crunch',
  'value': 6,
}),
  7: dict({
  'name': 'crunch_chop',
  'value': 7,
}),
  8: dict({
  'name': 'weighted_crunch_chop',
  'value': 8,
}),
  9: dict({
  'name': 'double_crunch',
  'value': 9,
}),
  10: dict({
  'name': 'weighted_double_crunch',
  'value': 10,
}),
  11: dict({
  'name': 'elbow_to_knee_crunch',
  'value': 11,
}),
  12: dict({
  'name': 'weighted_elbow_to_knee_crunch',
  'value': 12,
}),
  13: dict({
  'name': 'flutter_kicks',
  'value': 13,
}),
  14: dict({
  'name': 'weighted_flutter_kicks',
  'value': 14,
}),
  15: dict({
  'name': 'foam_roller_reverse_crunch_on_bench',
  'value': 15,
}),
  16: dict({
  'name': 'weighted_foam_roller_reverse_crunch_on_bench',
  'value': 16,
}),
  17: dict({
  'name': 'foam_roller_reverse_crunch_with_dumbbell',
  'value': 17,
}),
  18: dict({
  'name': 'foam_roller_reverse_crunch_with_medicine_ball',
  'value': 18,
}),
  19: dict({
  'name': 'frog_press',
  'value': 19,
}),
  20: dict({
  'name': 'hanging_knee_raise_oblique_crunch',
  'value': 20,
}),
  21: dict({
  'name': 'weighted_hanging_knee_raise_oblique_crunch',
  'value': 21,
}),
  22: dict({
  'name': 'hip_crossover',
  'value': 22,
}),
  23: dict({
  'name': 'weighted_hip_crossover',
  'value': 23,
}),
  24: dict({
  'name': 'hollow_rock',
  'value': 24,
}),
  25: dict({
  'name': 'weighted_hollow_rock',
  'value': 25,
}),
  26: dict({
  'name': 'incline_reverse_crunch',
  'value': 26,
}),
  27: dict({
  'name': 'weighted_incline_reverse_crunch',
  'value': 27,
}),
  28: dict({
  'name': 'kneeling_cable_crunch',
  'value': 28,
}),
  29: dict({
  'name': 'kneeling_cross_crunch',
  'value': 29,
}),
  30: dict({
  'name': 'weighted_kneeling_cross_crunch',
  'value': 30,
}),
  31: dict({
  'name': 'kneeling_oblique_cable_crunch',
  'value': 31,
}),
  32: dict({
  'name': 'knees_to_elbow',
  'value': 32,
}),
  33: dict({
  'name': 'leg_extensions',
  'value': 33,
}),
  34: dict({
  'name': 'weighted_leg_extensions',
  'value': 34,
}),
  35: dict({
  'name': 'leg_levers',
  'value': 35,
}),
  36: dict({
  'name': 'mcgill_curl_up',
  'value': 36,
}),
  37: dict({
  'name': 'weighted_mcgill_curl_up',
  'value': 37,
}),
  38: dict({
  'name': 'modified_pilates_roll_up_with_ball',
  'value': 38,
}),
  39: dict({
  'name': 'weighted_modified_pilates_roll_up_with_ball',
  'value': 39,
}),
  40: dict({
  'name': 'pilates_crunch',
  'value': 40,
}),
  41: dict({
  'name': 'weighted_pilates_crunch',
  'value': 41,
}),
  42: dict({
  'name': 'pilates_roll_up_with_ball',
  'value': 42,
}),
  43: dict({
  'name': 'weighted_pilates_roll_up_with_ball',
  'value': 43,
}),
  44: dict({
  'name': 'raised_legs_crunch',
  'value': 44,
}),
  45: dict({
  'name': 'weighted_raised_legs_crunch',
  'value': 45,
}),
  46: dict({
  'name': 'reverse_crunch',
  'value': 46,
}),
  47: dict({
  'name': 'weighted_reverse_crunch',
  'value': 47,
}),
  48: dict({
  'name': 'reverse_crunch_on_a_bench',
  'value': 48,
}),
  49: dict({
  'name': 'weighted_reverse_crunch_on_a_bench',
  'value': 49,
}),
  50: dict({
  'name': 'reverse_curl_and_lift',
  'value': 50,
}),
  51: dict({
  'name': 'weighted_reverse_curl_and_lift',
  'value': 51,
}),
  52: dict({
  'name': 'rotational_lift',
  'value': 52,
}),
  53: dict({
  'name': 'weighted_rotational_lift',
  'value': 53,
}),
  54: dict({
  'name': 'seated_alternating_reverse_crunch',
  'value': 54,
}),
  55: dict({
  'name': 'weighted_seated_alternating_reverse_crunch',
  'value': 55,
}),
  56: dict({
  'name': 'seated_leg_u',
  'value': 56,
}),
  57: dict({
  'name': 'weighted_seated_leg_u',
  'value': 57,
}),
  58: dict({
  'name': 'side_to_side_crunch_and_weave',
  'value': 58,
}),
  59: dict({
  'name': 'weighted_side_to_side_crunch_and_weave',
  'value': 59,
}),
  60: dict({
  'name': 'single_leg_reverse_crunch',
  'value': 60,
}),
  61: dict({
  'name': 'weighted_single_leg_reverse_crunch',
  'value': 61,
}),
  62: dict({
  'name': 'skater_crunch_cross',
  'value': 62,
}),
  63: dict({
  'name': 'weighted_skater_crunch_cross',
  'value': 63,
}),
  64: dict({
  'name': 'standing_cable_crunch',
  'value': 64,
}),
  65: dict({
  'name': 'standing_side_crunch',
  'value': 65,
}),
  66: dict({
  'name': 'step_climb',
  'value': 66,
}),
  67: dict({
  'name': 'weighted_step_climb',
  'value': 67,
}),
  68: dict({
  'name': 'swiss_ball_crunch',
  'value': 68,
}),
  69: dict({
  'name': 'swiss_ball_reverse_crunch',
  'value': 69,
}),
  70: dict({
  'name': 'weighted_swiss_ball_reverse_crunch',
  'value': 70,
}),
  71: dict({
  'name': 'swiss_ball_russian_twist',
  'value': 71,
}),
  72: dict({
  'name': 'weighted_swiss_ball_russian_twist',
  'value': 72,
}),
  73: dict({
  'name': 'swiss_ball_side_crunch',
  'value': 73,
}),
  74: dict({
  'name': 'weighted_swiss_ball_side_crunch',
  'value': 74,
}),
  75: dict({
  'name': 'thoracic_crunches_on_foam_roller',
  'value': 75,
}),
  76: dict({
  'name': 'weighted_thoracic_crunches_on_foam_roller',
  'value': 76,
}),
  77: dict({
  'name': 'triceps_crunch',
  'value': 77,
}),
  78: dict({
  'name': 'weighted_bicycle_crunch',
  'value': 78,
}),
  79: dict({
  'name': 'weighted_crunch',
  'value': 79,
}),
  80: dict({
  'name': 'weighted_swiss_ball_crunch',
  'value': 80,
}),
  81: dict({
  'name': 'toes_to_bar',
  'value': 81,
}),
  82: dict({
  'name': 'weighted_toes_to_bar',
  'value': 82,
}),
  83: dict({
  'name': 'crunch',
  'value': 83,
}),
  84: dict({
  'name': 'straight_leg_crunch_with_ball',
  'value': 84,
}),
}),
}),
  'curl_exercise_name': dict({
  'name': 'curl_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'alternating_dumbbell_biceps_curl',
  'value': 0,
}),
  1: dict({
  'name': 'alternating_dumbbell_biceps_curl_on_swiss_ball',
  'value': 1,
}),
  2: dict({
  'name': 'alternating_incline_dumbbell_biceps_curl',
  'value': 2,
}),
  3: dict({
  'name': 'barbell_biceps_curl',
  'value': 3,
}),
  4: dict({
  'name': 'barbell_reverse_wrist_curl',
  'value': 4,
}),
  5: dict({
  'name': 'barbell_wrist_curl',
  'value': 5,
}),
  6: dict({
  'name': 'behind_the_back_barbell_reverse_wrist_curl',
  'value': 6,
}),
  7: dict({
  'name': 'behind_the_back_one_arm_cable_curl',
  'value': 7,
}),
  8: dict({
  'name': 'cable_biceps_curl',
  'value': 8,
}),
  9: dict({
  'name': 'cable_hammer_curl',
  'value': 9,
}),
  10: dict({
  'name': 'cheating_barbell_biceps_curl',
  'value': 10,
}),
  11: dict({
  'name': 'close_grip_ez_bar_biceps_curl',
  'value': 11,
}),
  12: dict({
  'name': 'cross_body_dumbbell_hammer_curl',
  'value': 12,
}),
  13: dict({
  'name': 'dead_hang_biceps_curl',
  'value': 13,
}),
  14: dict({
  'name': 'decline_hammer_curl',
  'value': 14,
}),
  15: dict({
  'name': 'dumbbell_biceps_curl_with_static_hold',
  'value': 15,
}),
  16: dict({
  'name': 'dumbbell_hammer_curl',
  'value': 16,
}),
  17: dict({
  'name': 'dumbbell_reverse_wrist_curl',
  'value': 17,
}),
  18: dict({
  'name': 'dumbbell_wrist_curl',
  'value': 18,
}),
  19: dict({
  'name': 'ez_bar_preacher_curl',
  'value': 19,
}),
  20: dict({
  'name': 'forward_bend_biceps_curl',
  'value': 20,
}),
  21: dict({
  'name': 'hammer_curl_to_press',
  'value': 21,
}),
  22: dict({
  'name': 'incline_dumbbell_biceps_curl',
  'value': 22,
}),
  23: dict({
  'name': 'incline_offset_thumb_dumbbell_curl',
  'value': 23,
}),
  24: dict({
  'name': 'kettlebell_biceps_curl',
  'value': 24,
}),
  25: dict({
  'name': 'lying_concentration_cable_curl',
  'value': 25,
}),
  26: dict({
  'name': 'one_arm_preacher_curl',
  'value': 26,
}),
  27: dict({
  'name': 'plate_pinch_curl',
  'value': 27,
}),
  28: dict({
  'name': 'preacher_curl_with_cable',
  'value': 28,
}),
  29: dict({
  'name': 'reverse_ez_bar_curl',
  'value': 29,
}),
  30: dict({
  'name': 'reverse_grip_wrist_curl',
  'value': 30,
}),
  31: dict({
  'name': 'reverse_grip_barbell_biceps_curl',
  'value': 31,
}),
  32: dict({
  'name': 'seated_alternating_dumbbell_biceps_curl',
  'value': 32,
}),
  33: dict({
  'name': 'seated_dumbbell_biceps_curl',
  'value': 33,
}),
  34: dict({
  'name': 'seated_reverse_dumbbell_curl',
  'value': 34,
}),
  35: dict({
  'name': 'split_stance_offset_pinky_dumbbell_curl',
  'value': 35,
}),
  36: dict({
  'name': 'standing_alternating_dumbbell_curls',
  'value': 36,
}),
  37: dict({
  'name': 'standing_dumbbell_biceps_curl',
  'value': 37,
}),
  38: dict({
  'name': 'standing_ez_bar_biceps_curl',
  'value': 38,
}),
  39: dict({
  'name': 'static_curl',
  'value': 39,
}),
  40: dict({
  'name': 'swiss_ball_dumbbell_overhead_triceps_extension',
  'value': 40,
}),
  41: dict({
  'name': 'swiss_ball_ez_bar_preacher_curl',
  'value': 41,
}),
  42: dict({
  'name': 'twisting_standing_dumbbell_biceps_curl',
  'value': 42,
}),
  43: dict({
  'name': 'wide_grip_ez_bar_biceps_curl',
  'value': 43,
}),
}),
}),
  'deadlift_exercise_name': dict({
  'name': 'deadlift_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'barbell_deadlift',
  'value': 0,
}),
  1: dict({
  'name': 'barbell_straight_leg_deadlift',
  'value': 1,
}),
  2: dict({
  'name': 'dumbbell_deadlift',
  'value': 2,
}),
  3: dict({
  'name': 'dumbbell_single_leg_deadlift_to_row',
  'value': 3,
}),
  4: dict({
  'name': 'dumbbell_straight_leg_deadlift',
  'value': 4,
}),
  5: dict({
  'name': 'kettlebell_floor_to_shelf',
  'value': 5,
}),
  6: dict({
  'name': 'one_arm_one_leg_deadlift',
  'value': 6,
}),
  7: dict({
  'name': 'rack_pull',
  'value': 7,
}),
  8: dict({
  'name': 'rotational_dumbbell_straight_leg_deadlift',
  'value': 8,
}),
  9: dict({
  'name': 'single_arm_deadlift',
  'value': 9,
}),
  10: dict({
  'name': 'single_leg_barbell_deadlift',
  'value': 10,
}),
  11: dict({
  'name': 'single_leg_barbell_straight_leg_deadlift',
  'value': 11,
}),
  12: dict({
  'name': 'single_leg_deadlift_with_barbell',
  'value': 12,
}),
  13: dict({
  'name': 'single_leg_rdl_circuit',
  'value': 13,
}),
  14: dict({
  'name': 'single_leg_romanian_deadlift_with_dumbbell',
  'value': 14,
}),
  15: dict({
  'name': 'sumo_deadlift',
  'value': 15,
}),
  16: dict({
  'name': 'sumo_deadlift_high_pull',
  'value': 16,
}),
  17: dict({
  'name': 'trap_bar_deadlift',
  'value': 17,
}),
  18: dict({
  'name': 'wide_grip_barbell_deadlift',
  'value': 18,
}),
}),
}),
  'flye_exercise_name': dict({
  'name': 'flye_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'cable_crossover',
  'value': 0,
}),
  1: dict({
  'name': 'decline_dumbbell_flye',
  'value': 1,
}),
  2: dict({
  'name': 'dumbbell_flye',
  'value': 2,
}),
  3: dict({
  'name': 'incline_dumbbell_flye',
  'value': 3,
}),
  4: dict({
  'name': 'kettlebell_flye',
  'value': 4,
}),
  5: dict({
  'name': 'kneeling_rear_flye',
  'value': 5,
}),
  6: dict({
  'name': 'single_arm_standing_cable_reverse_flye',
  'value': 6,
}),
  7: dict({
  'name': 'swiss_ball_dumbbell_flye',
  'value': 7,
}),
  8: dict({
  'name': 'arm_rotations',
  'value': 8,
}),
  9: dict({
  'name': 'hug_a_tree',
  'value': 9,
}),
}),
}),
  'hip_raise_exercise_name': dict({
  'name': 'hip_raise_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'barbell_hip_thrust_on_floor',
  'value': 0,
}),
  1: dict({
  'name': 'barbell_hip_thrust_with_bench',
  'value': 1,
}),
  2: dict({
  'name': 'bent_knee_swiss_ball_reverse_hip_raise',
  'value': 2,
}),
  3: dict({
  'name': 'weighted_bent_knee_swiss_ball_reverse_hip_raise',
  'value': 3,
}),
  4: dict({
  'name': 'bridge_with_leg_extension',
  'value': 4,
}),
  5: dict({
  'name': 'weighted_bridge_with_leg_extension',
  'value': 5,
}),
  6: dict({
  'name': 'clam_bridge',
  'value': 6,
}),
  7: dict({
  'name': 'front_kick_tabletop',
  'value': 7,
}),
  8: dict({
  'name': 'weighted_front_kick_tabletop',
  'value': 8,
}),
  9: dict({
  'name': 'hip_extension_and_cross',
  'value': 9,
}),
  10: dict({
  'name': 'weighted_hip_extension_and_cross',
  'value': 10,
}),
  11: dict({
  'name': 'hip_raise',
  'value': 11,
}),
  12: dict({
  'name': 'weighted_hip_raise',
  'value': 12,
}),
  13: dict({
  'name': 'hip_raise_with_feet_on_swiss_ball',
  'value': 13,
}),
  14: dict({
  'name': 'weighted_hip_raise_with_feet_on_swiss_ball',
  'value': 14,
}),
  15: dict({
  'name': 'hip_raise_with_head_on_bosu_ball',
  'value': 15,
}),
  16: dict({
  'name': 'weighted_hip_raise_with_head_on_bosu_ball',
  'value': 16,
}),
  17: dict({
  'name': 'hip_raise_with_head_on_swiss_ball',
  'value': 17,
}),
  18: dict({
  'name': 'weighted_hip_raise_with_head_on_swiss_ball',
  'value': 18,
}),
  19: dict({
  'name': 'hip_raise_with_knee_squeeze',
  'value': 19,
}),
  20: dict({
  'name': 'weighted_hip_raise_with_knee_squeeze',
  'value': 20,
}),
  21: dict({
  'name': 'incline_rear_leg_extension',
  'value': 21,
}),
  22: dict({
  'name': 'weighted_incline_rear_leg_extension',
  'value': 22,
}),
  23: dict({
  'name': 'kettlebell_swing',
  'value': 23,
}),
  24: dict({
  'name': 'marching_hip_raise',
  'value': 24,
}),
  25: dict({
  'name': 'weighted_marching_hip_raise',
  'value': 25,
}),
  26: dict({
  'name': 'marching_hip_raise_with_feet_on_a_swiss_ball',
  'value': 26,
}),
  27: dict({
  'name': 'weighted_marching_hip_raise_with_feet_on_a_swiss_ball',
  'value': 27,
}),
  28: dict({
  'name': 'reverse_hip_raise',
  'value': 28,
}),
  29: dict({
  'name': 'weighted_reverse_hip_raise',
  'value': 29,
}),
  30: dict({
  'name': 'single_leg_hip_raise',
  'value': 30,
}),
  31: dict({
  'name': 'weighted_single_leg_hip_raise',
  'value': 31,
}),
  32: dict({
  'name': 'single_leg_hip_raise_with_foot_on_bench',
  'value': 32,
}),
  33: dict({
  'name': 'weighted_single_leg_hip_raise_with_foot_on_bench',
  'value': 33,
}),
  34: dict({
  'name': 'single_leg_hip_raise_with_foot_on_bosu_ball',
  'value': 34,
}),
  35: dict({
  'name': 'weighted_single_leg_hip_raise_with_foot_on_bosu_ball',
  'value': 35,
}),
  36: dict({
  'name': 'single_leg_hip_raise_with_foot_on_foam_roller',
  'value': 36,
}),
  37: dict({
  'name': 'weighted_single_leg_hip_raise_with_foot_on_foam_roller',
  'value': 37,
}),
  38: dict({
  'name': 'single_leg_hip_raise_with_foot_on_medicine_ball',
  'value': 38,
}),
  39: dict({
  'name': 'weighted_single_leg_hip_raise_with_foot_on_medicine_ball',
  'value': 39,
}),
  40: dict({
  'name': 'single_leg_hip_raise_with_head_on_bosu_ball',
  'value': 40,
}),
  41: dict({
  'name': 'weighted_single_leg_hip_raise_with_head_on_bosu_ball',
  'value': 41,
}),
  42: dict({
  'name': 'weighted_clam_bridge',
  'value': 42,
}),
  43: dict({
  'name': 'single_leg_swiss_ball_hip_raise_and_leg_curl',
  'value': 43,
}),
  44: dict({
  'name': 'clams',
  'value': 44,
}),
  45: dict({
  'name': 'inner_thigh_circles',
  'value': 45,
  'comment': 'Deprecated do not use',
}),
  46: dict({
  'name': 'inner_thigh_side_lift',
  'value': 46,
  'comment': 'Deprecated do not use',
}),
  47: dict({
  'name': 'leg_circles',
  'value': 47,
}),
  48: dict({
  'name': 'leg_lift',
  'value': 48,
}),
  49: dict({
  'name': 'leg_lift_in_external_rotation',
  'value': 49,
}),
}),
}),
  'hip_stability_exercise_name': dict({
  'name': 'hip_stability_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'band_side_lying_leg_raise',
  'value': 0,
}),
  1: dict({
  'name': 'dead_bug',
  'value': 1,
}),
  2: dict({
  'name': 'weighted_dead_bug',
  'value': 2,
}),
  3: dict({
  'name': 'external_hip_raise',
  'value': 3,
}),
  4: dict({
  'name': 'weighted_external_hip_raise',
  'value': 4,
}),
  5: dict({
  'name': 'fire_hydrant_kicks',
  'value': 5,
}),
  6: dict({
  'name': 'weighted_fire_hydrant_kicks',
  'value': 6,
}),
  7: dict({
  'name': 'hip_circles',
  'value': 7,
}),
  8: dict({
  'name': 'weighted_hip_circles',
  'value': 8,
}),
  9: dict({
  'name': 'inner_thigh_lift',
  'value': 9,
}),
  10: dict({
  'name': 'weighted_inner_thigh_lift',
  'value': 10,
}),
  11: dict({
  'name': 'lateral_walks_with_band_at_ankles',
  'value': 11,
}),
  12: dict({
  'name': 'pretzel_side_kick',
  'value': 12,
}),
  13: dict({
  'name': 'weighted_pretzel_side_kick',
  'value': 13,
}),
  14: dict({
  'name': 'prone_hip_internal_rotation',
  'value': 14,
}),
  15: dict({
  'name': 'weighted_prone_hip_internal_rotation',
  'value': 15,
}),
  16: dict({
  'name': 'quadruped',
  'value': 16,
}),
  17: dict({
  'name': 'quadruped_hip_extension',
  'value': 17,
}),
  18: dict({
  'name': 'weighted_quadruped_hip_extension',
  'value': 18,
}),
  19: dict({
  'name': 'quadruped_with_leg_lift',
  'value': 19,
}),
  20: dict({
  'name': 'weighted_quadruped_with_leg_lift',
  'value': 20,
}),
  21: dict({
  'name': 'side_lying_leg_raise',
  'value': 21,
}),
  22: dict({
  'name': 'weighted_side_lying_leg_raise',
  'value': 22,
}),
  23: dict({
  'name': 'sliding_hip_adduction',
  'value': 23,
}),
  24: dict({
  'name': 'weighted_sliding_hip_adduction',
  'value': 24,
}),
  25: dict({
  'name': 'standing_adduction',
  'value': 25,
}),
  26: dict({
  'name': 'weighted_standing_adduction',
  'value': 26,
}),
  27: dict({
  'name': 'standing_cable_hip_abduction',
  'value': 27,
}),
  28: dict({
  'name': 'standing_hip_abduction',
  'value': 28,
}),
  29: dict({
  'name': 'weighted_standing_hip_abduction',
  'value': 29,
}),
  30: dict({
  'name': 'standing_rear_leg_raise',
  'value': 30,
}),
  31: dict({
  'name': 'weighted_standing_rear_leg_raise',
  'value': 31,
}),
  32: dict({
  'name': 'supine_hip_internal_rotation',
  'value': 32,
}),
  33: dict({
  'name': 'weighted_supine_hip_internal_rotation',
  'value': 33,
}),
}),
}),
  'hip_swing_exercise_name': dict({
  'name': 'hip_swing_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'single_arm_kettlebell_swing',
  'value': 0,
}),
  1: dict({
  'name': 'single_arm_dumbbell_swing',
  'value': 1,
}),
  2: dict({
  'name': 'step_out_swing',
  'value': 2,
}),
}),
}),
  'hyperextension_exercise_name': dict({
  'name': 'hyperextension_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'back_extension_with_opposite_arm_and_leg_reach',
  'value': 0,
}),
  1: dict({
  'name': 'weighted_back_extension_with_opposite_arm_and_leg_reach',
  'value': 1,
}),
  2: dict({
  'name': 'base_rotations',
  'value': 2,
}),
  3: dict({
  'name': 'weighted_base_rotations',
  'value': 3,
}),
  4: dict({
  'name': 'bent_knee_reverse_hyperextension',
  'value': 4,
}),
  5: dict({
  'name': 'weighted_bent_knee_reverse_hyperextension',
  'value': 5,
}),
  6: dict({
  'name': 'hollow_hold_and_roll',
  'value': 6,
}),
  7: dict({
  'name': 'weighted_hollow_hold_and_roll',
  'value': 7,
}),
  8: dict({
  'name': 'kicks',
  'value': 8,
}),
  9: dict({
  'name': 'weighted_kicks',
  'value': 9,
}),
  10: dict({
  'name': 'knee_raises',
  'value': 10,
}),
  11: dict({
  'name': 'weighted_knee_raises',
  'value': 11,
}),
  12: dict({
  'name': 'kneeling_superman',
  'value': 12,
}),
  13: dict({
  'name': 'weighted_kneeling_superman',
  'value': 13,
}),
  14: dict({
  'name': 'lat_pull_down_with_row',
  'value': 14,
}),
  15: dict({
  'name': 'medicine_ball_deadlift_to_reach',
  'value': 15,
}),
  16: dict({
  'name': 'one_arm_one_leg_row',
  'value': 16,
}),
  17: dict({
  'name': 'one_arm_row_with_band',
  'value': 17,
}),
  18: dict({
  'name': 'overhead_lunge_with_medicine_ball',
  'value': 18,
}),
  19: dict({
  'name': 'plank_knee_tucks',
  'value': 19,
}),
  20: dict({
  'name': 'weighted_plank_knee_tucks',
  'value': 20,
}),
  21: dict({
  'name': 'side_step',
  'value': 21,
}),
  22: dict({
  'name': 'weighted_side_step',
  'value': 22,
}),
  23: dict({
  'name': 'single_leg_back_extension',
  'value': 23,
}),
  24: dict({
  'name': 'weighted_single_leg_back_extension',
  'value': 24,
}),
  25: dict({
  'name': 'spine_extension',
  'value': 25,
}),
  26: dict({
  'name': 'weighted_spine_extension',
  'value': 26,
}),
  27: dict({
  'name': 'static_back_extension',
  'value': 27,
}),
  28: dict({
  'name': 'weighted_static_back_extension',
  'value': 28,
}),
  29: dict({
  'name': 'superman_from_floor',
  'value': 29,
}),
  30: dict({
  'name': 'weighted_superman_from_floor',
  'value': 30,
}),
  31: dict({
  'name': 'swiss_ball_back_extension',
  'value': 31,
}),
  32: dict({
  'name': 'weighted_swiss_ball_back_extension',
  'value': 32,
}),
  33: dict({
  'name': 'swiss_ball_hyperextension',
  'value': 33,
}),
  34: dict({
  'name': 'weighted_swiss_ball_hyperextension',
  'value': 34,
}),
  35: dict({
  'name': 'swiss_ball_opposite_arm_and_leg_lift',
  'value': 35,
}),
  36: dict({
  'name': 'weighted_swiss_ball_opposite_arm_and_leg_lift',
  'value': 36,
}),
  37: dict({
  'name': 'superman_on_swiss_ball',
  'value': 37,
}),
  38: dict({
  'name': 'cobra',
  'value': 38,
}),
  39: dict({
  'name': 'supine_floor_barre',
  'value': 39,
  'comment': 'Deprecated do not use',
}),
}),
}),
  'lateral_raise_exercise_name': dict({
  'name': 'lateral_raise_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': '45_degree_cable_external_rotation',
  'value': 0,
}),
  1: dict({
  'name': 'alternating_lateral_raise_with_static_hold',
  'value': 1,
}),
  2: dict({
  'name': 'bar_muscle_up',
  'value': 2,
}),
  3: dict({
  'name': 'bent_over_lateral_raise',
  'value': 3,
}),
  4: dict({
  'name': 'cable_diagonal_raise',
  'value': 4,
}),
  5: dict({
  'name': 'cable_front_raise',
  'value': 5,
}),
  6: dict({
  'name': 'calorie_row',
  'value': 6,
}),
  7: dict({
  'name': 'combo_shoulder_raise',
  'value': 7,
}),
  8: dict({
  'name': 'dumbbell_diagonal_raise',
  'value': 8,
}),
  9: dict({
  'name': 'dumbbell_v_raise',
  'value': 9,
}),
  10: dict({
  'name': 'front_raise',
  'value': 10,
}),
  11: dict({
  'name': 'leaning_dumbbell_lateral_raise',
  'value': 11,
}),
  12: dict({
  'name': 'lying_dumbbell_raise',
  'value': 12,
}),
  13: dict({
  'name': 'muscle_up',
  'value': 13,
}),
  14: dict({
  'name': 'one_arm_cable_lateral_raise',
  'value': 14,
}),
  15: dict({
  'name': 'overhand_grip_rear_lateral_raise',
  'value': 15,
}),
  16: dict({
  'name': 'plate_raises',
  'value': 16,
}),
  17: dict({
  'name': 'ring_dip',
  'value': 17,
}),
  18: dict({
  'name': 'weighted_ring_dip',
  'value': 18,
}),
  19: dict({
  'name': 'ring_muscle_up',
  'value': 19,
}),
  20: dict({
  'name': 'weighted_ring_muscle_up',
  'value': 20,
}),
  21: dict({
  'name': 'rope_climb',
  'value': 21,
}),
  22: dict({
  'name': 'weighted_rope_climb',
  'value': 22,
}),
  23: dict({
  'name': 'scaption',
  'value': 23,
}),
  24: dict({
  'name': 'seated_lateral_raise',
  'value': 24,
}),
  25: dict({
  'name': 'seated_rear_lateral_raise',
  'value': 25,
}),
  26: dict({
  'name': 'side_lying_lateral_raise',
  'value': 26,
}),
  27: dict({
  'name': 'standing_lift',
  'value': 27,
}),
  28: dict({
  'name': 'suspended_row',
  'value': 28,
}),
  29: dict({
  'name': 'underhand_grip_rear_lateral_raise',
  'value': 29,
}),
  30: dict({
  'name': 'wall_slide',
  'value': 30,
}),
  31: dict({
  'name': 'weighted_wall_slide',
  'value': 31,
}),
  32: dict({
  'name': 'arm_circles',
  'value': 32,
}),
  33: dict({
  'name': 'shaving_the_head',
  'value': 33,
}),
}),
}),
  'leg_curl_exercise_name': dict({
  'name': 'leg_curl_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'leg_curl',
  'value': 0,
}),
  1: dict({
  'name': 'weighted_leg_curl',
  'value': 1,
}),
  2: dict({
  'name': 'good_morning',
  'value': 2,
}),
  3: dict({
  'name': 'seated_barbell_good_morning',
  'value': 3,
}),
  4: dict({
  'name': 'single_leg_barbell_good_morning',
  'value': 4,
}),
  5: dict({
  'name': 'single_leg_sliding_leg_curl',
  'value': 5,
}),
  6: dict({
  'name': 'sliding_leg_curl',
  'value': 6,
}),
  7: dict({
  'name': 'split_barbell_good_morning',
  'value': 7,
}),
  8: dict({
  'name': 'split_stance_extension',
  'value': 8,
}),
  9: dict({
  'name': 'staggered_stance_good_morning',
  'value': 9,
}),
  10: dict({
  'name': 'swiss_ball_hip_raise_and_leg_curl',
  'value': 10,
}),
  11: dict({
  'name': 'zercher_good_morning',
  'value': 11,
}),
}),
}),
  'leg_raise_exercise_name': dict({
  'name': 'leg_raise_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'hanging_knee_raise',
  'value': 0,
}),
  1: dict({
  'name': 'hanging_leg_raise',
  'value': 1,
}),
  2: dict({
  'name': 'weighted_hanging_leg_raise',
  'value': 2,
}),
  3: dict({
  'name': 'hanging_single_leg_raise',
  'value': 3,
}),
  4: dict({
  'name': 'weighted_hanging_single_leg_raise',
  'value': 4,
}),
  5: dict({
  'name': 'kettlebell_leg_raises',
  'value': 5,
}),
  6: dict({
  'name': 'leg_lowering_drill',
  'value': 6,
}),
  7: dict({
  'name': 'weighted_leg_lowering_drill',
  'value': 7,
}),
  8: dict({
  'name': 'lying_straight_leg_raise',
  'value': 8,
}),
  9: dict({
  'name': 'weighted_lying_straight_leg_raise',
  'value': 9,
}),
  10: dict({
  'name': 'medicine_ball_leg_drops',
  'value': 10,
}),
  11: dict({
  'name': 'quadruped_leg_raise',
  'value': 11,
}),
  12: dict({
  'name': 'weighted_quadruped_leg_raise',
  'value': 12,
}),
  13: dict({
  'name': 'reverse_leg_raise',
  'value': 13,
}),
  14: dict({
  'name': 'weighted_reverse_leg_raise',
  'value': 14,
}),
  15: dict({
  'name': 'reverse_leg_raise_on_swiss_ball',
  'value': 15,
}),
  16: dict({
  'name': 'weighted_reverse_leg_raise_on_swiss_ball',
  'value': 16,
}),
  17: dict({
  'name': 'single_leg_lowering_drill',
  'value': 17,
}),
  18: dict({
  'name': 'weighted_single_leg_lowering_drill',
  'value': 18,
}),
  19: dict({
  'name': 'weighted_hanging_knee_raise',
  'value': 19,
}),
  20: dict({
  'name': 'lateral_stepover',
  'value': 20,
}),
  21: dict({
  'name': 'weighted_lateral_stepover',
  'value': 21,
}),
}),
}),
  'lunge_exercise_name': dict({
  'name': 'lunge_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'overhead_lunge',
  'value': 0,
}),
  1: dict({
  'name': 'lunge_matrix',
  'value': 1,
}),
  2: dict({
  'name': 'weighted_lunge_matrix',
  'value': 2,
}),
  3: dict({
  'name': 'alternating_barbell_forward_lunge',
  'value': 3,
}),
  4: dict({
  'name': 'alternating_dumbbell_lunge_with_reach',
  'value': 4,
}),
  5: dict({
  'name': 'back_foot_elevated_dumbbell_split_squat',
  'value': 5,
}),
  6: dict({
  'name': 'barbell_box_lunge',
  'value': 6,
}),
  7: dict({
  'name': 'barbell_bulgarian_split_squat',
  'value': 7,
}),
  8: dict({
  'name': 'barbell_crossover_lunge',
  'value': 8,
}),
  9: dict({
  'name': 'barbell_front_split_squat',
  'value': 9,
}),
  10: dict({
  'name': 'barbell_lunge',
  'value': 10,
}),
  11: dict({
  'name': 'barbell_reverse_lunge',
  'value': 11,
}),
  12: dict({
  'name': 'barbell_side_lunge',
  'value': 12,
}),
  13: dict({
  'name': 'barbell_split_squat',
  'value': 13,
}),
  14: dict({
  'name': 'core_control_rear_lunge',
  'value': 14,
}),
  15: dict({
  'name': 'diagonal_lunge',
  'value': 15,
}),
  16: dict({
  'name': 'drop_lunge',
  'value': 16,
}),
  17: dict({
  'name': 'dumbbell_box_lunge',
  'value': 17,
}),
  18: dict({
  'name': 'dumbbell_bulgarian_split_squat',
  'value': 18,
}),
  19: dict({
  'name': 'dumbbell_crossover_lunge',
  'value': 19,
}),
  20: dict({
  'name': 'dumbbell_diagonal_lunge',
  'value': 20,
}),
  21: dict({
  'name': 'dumbbell_lunge',
  'value': 21,
}),
  22: dict({
  'name': 'dumbbell_lunge_and_rotation',
  'value': 22,
}),
  23: dict({
  'name': 'dumbbell_overhead_bulgarian_split_squat',
  'value': 23,
}),
  24: dict({
  'name': 'dumbbell_reverse_lunge_to_high_knee_and_press',
  'value': 24,
}),
  25: dict({
  'name': 'dumbbell_side_lunge',
  'value': 25,
}),
  26: dict({
  'name': 'elevated_front_foot_barbell_split_squat',
  'value': 26,
}),
  27: dict({
  'name': 'front_foot_elevated_dumbbell_split_squat',
  'value': 27,
}),
  28: dict({
  'name': 'gunslinger_lunge',
  'value': 28,
}),
  29: dict({
  'name': 'lawnmower_lunge',
  'value': 29,
}),
  30: dict({
  'name': 'low_lunge_with_isometric_adduction',
  'value': 30,
}),
  31: dict({
  'name': 'low_side_to_side_lunge',
  'value': 31,
}),
  32: dict({
  'name': 'lunge',
  'value': 32,
}),
  33: dict({
  'name': 'weighted_lunge',
  'value': 33,
}),
  34: dict({
  'name': 'lunge_with_arm_reach',
  'value': 34,
}),
  35: dict({
  'name': 'lunge_with_diagonal_reach',
  'value': 35,
}),
  36: dict({
  'name': 'lunge_with_side_bend',
  'value': 36,
}),
  37: dict({
  'name': 'offset_dumbbell_lunge',
  'value': 37,
}),
  38: dict({
  'name': 'offset_dumbbell_reverse_lunge',
  'value': 38,
}),
  39: dict({
  'name': 'overhead_bulgarian_split_squat',
  'value': 39,
}),
  40: dict({
  'name': 'overhead_dumbbell_reverse_lunge',
  'value': 40,
}),
  41: dict({
  'name': 'overhead_dumbbell_split_squat',
  'value': 41,
}),
  42: dict({
  'name': 'overhead_lunge_with_rotation',
  'value': 42,
}),
  43: dict({
  'name': 'reverse_barbell_box_lunge',
  'value': 43,
}),
  44: dict({
  'name': 'reverse_box_lunge',
  'value': 44,
}),
  45: dict({
  'name': 'reverse_dumbbell_box_lunge',
  'value': 45,
}),
  46: dict({
  'name': 'reverse_dumbbell_crossover_lunge',
  'value': 46,
}),
  47: dict({
  'name': 'reverse_dumbbell_diagonal_lunge',
  'value': 47,
}),
  48: dict({
  'name': 'reverse_lunge_with_reach_back',
  'value': 48,
}),
  49: dict({
  'name': 'weighted_reverse_lunge_with_reach_back',
  'value': 49,
}),
  50: dict({
  'name': 'reverse_lunge_with_twist_and_overhead_reach',
  'value': 50,
}),
  51: dict({
  'name': 'weighted_reverse_lunge_with_twist_and_overhead_reach',
  'value': 51,
}),
  52: dict({
  'name': 'reverse_sliding_box_lunge',
  'value': 52,
}),
  53: dict({
  'name': 'weighted_reverse_sliding_box_lunge',
  'value': 53,
}),
  54: dict({
  'name': 'reverse_sliding_lunge',
  'value': 54,
}),
  55: dict({
  'name': 'weighted_reverse_sliding_lunge',
  'value': 55,
}),
  56: dict({
  'name': 'runners_lunge_to_balance',
  'value': 56,
}),
  57: dict({
  'name': 'weighted_runners_lunge_to_balance',
  'value': 57,
}),
  58: dict({
  'name': 'shifting_side_lunge',
  'value': 58,
}),
  59: dict({
  'name': 'side_and_crossover_lunge',
  'value': 59,
}),
  60: dict({
  'name': 'weighted_side_and_crossover_lunge',
  'value': 60,
}),
  61: dict({
  'name': 'side_lunge',
  'value': 61,
}),
  62: dict({
  'name': 'weighted_side_lunge',
  'value': 62,
}),
  63: dict({
  'name': 'side_lunge_and_press',
  'value': 63,
}),
  64: dict({
  'name': 'side_lunge_jump_off',
  'value': 64,
}),
  65: dict({
  'name': 'side_lunge_sweep',
  'value': 65,
}),
  66: dict({
  'name': 'weighted_side_lunge_sweep',
  'value': 66,
}),
  67: dict({
  'name': 'side_lunge_to_crossover_tap',
  'value': 67,
}),
  68: dict({
  'name': 'weighted_side_lunge_to_crossover_tap',
  'value': 68,
}),
  69: dict({
  'name': 'side_to_side_lunge_chops',
  'value': 69,
}),
  70: dict({
  'name': 'weighted_side_to_side_lunge_chops',
  'value': 70,
}),
  71: dict({
  'name': 'siff_jump_lunge',
  'value': 71,
}),
  72: dict({
  'name': 'weighted_siff_jump_lunge',
  'value': 72,
}),
  73: dict({
  'name': 'single_arm_reverse_lunge_and_press',
  'value': 73,
}),
  74: dict({
  'name': 'sliding_lateral_lunge',
  'value': 74,
}),
  75: dict({
  'name': 'weighted_sliding_lateral_lunge',
  'value': 75,
}),
  76: dict({
  'name': 'walking_barbell_lunge',
  'value': 76,
}),
  77: dict({
  'name': 'walking_dumbbell_lunge',
  'value': 77,
}),
  78: dict({
  'name': 'walking_lunge',
  'value': 78,
}),
  79: dict({
  'name': 'weighted_walking_lunge',
  'value': 79,
}),
  80: dict({
  'name': 'wide_grip_overhead_barbell_split_squat',
  'value': 80,
}),
}),
}),
  'olympic_lift_exercise_name': dict({
  'name': 'olympic_lift_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'barbell_hang_power_clean',
  'value': 0,
}),
  1: dict({
  'name': 'barbell_hang_squat_clean',
  'value': 1,
}),
  2: dict({
  'name': 'barbell_power_clean',
  'value': 2,
}),
  3: dict({
  'name': 'barbell_power_snatch',
  'value': 3,
}),
  4: dict({
  'name': 'barbell_squat_clean',
  'value': 4,
}),
  5: dict({
  'name': 'clean_and_jerk',
  'value': 5,
}),
  6: dict({
  'name': 'barbell_hang_power_snatch',
  'value': 6,
}),
  7: dict({
  'name': 'barbell_hang_pull',
  'value': 7,
}),
  8: dict({
  'name': 'barbell_high_pull',
  'value': 8,
}),
  9: dict({
  'name': 'barbell_snatch',
  'value': 9,
}),
  10: dict({
  'name': 'barbell_split_jerk',
  'value': 10,
}),
  11: dict({
  'name': 'clean',
  'value': 11,
}),
  12: dict({
  'name': 'dumbbell_clean',
  'value': 12,
}),
  13: dict({
  'name': 'dumbbell_hang_pull',
  'value': 13,
}),
  14: dict({
  'name': 'one_hand_dumbbell_split_snatch',
  'value': 14,
}),
  15: dict({
  'name': 'push_jerk',
  'value': 15,
}),
  16: dict({
  'name': 'single_arm_dumbbell_snatch',
  'value': 16,
}),
  17: dict({
  'name': 'single_arm_hang_snatch',
  'value': 17,
}),
  18: dict({
  'name': 'single_arm_kettlebell_snatch',
  'value': 18,
}),
  19: dict({
  'name': 'split_jerk',
  'value': 19,
}),
  20: dict({
  'name': 'squat_clean_and_jerk',
  'value': 20,
}),
}),
}),
  'plank_exercise_name': dict({
  'name': 'plank_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': '45_degree_plank',
  'value': 0,
}),
  1: dict({
  'name': 'weighted_45_degree_plank',
  'value': 1,
}),
  2: dict({
  'name': '90_degree_static_hold',
  'value': 2,
}),
  3: dict({
  'name': 'weighted_90_degree_static_hold',
  'value': 3,
}),
  4: dict({
  'name': 'bear_crawl',
  'value': 4,
}),
  5: dict({
  'name': 'weighted_bear_crawl',
  'value': 5,
}),
  6: dict({
  'name': 'cross_body_mountain_climber',
  'value': 6,
}),
  7: dict({
  'name': 'weighted_cross_body_mountain_climber',
  'value': 7,
}),
  8: dict({
  'name': 'elbow_plank_pike_jacks',
  'value': 8,
}),
  9: dict({
  'name': 'weighted_elbow_plank_pike_jacks',
  'value': 9,
}),
  10: dict({
  'name': 'elevated_feet_plank',
  'value': 10,
}),
  11: dict({
  'name': 'weighted_elevated_feet_plank',
  'value': 11,
}),
  12: dict({
  'name': 'elevator_abs',
  'value': 12,
}),
  13: dict({
  'name': 'weighted_elevator_abs',
  'value': 13,
}),
  14: dict({
  'name': 'extended_plank',
  'value': 14,
}),
  15: dict({
  'name': 'weighted_extended_plank',
  'value': 15,
}),
  16: dict({
  'name': 'full_plank_passe_twist',
  'value': 16,
}),
  17: dict({
  'name': 'weighted_full_plank_passe_twist',
  'value': 17,
}),
  18: dict({
  'name': 'inching_elbow_plank',
  'value': 18,
}),
  19: dict({
  'name': 'weighted_inching_elbow_plank',
  'value': 19,
}),
  20: dict({
  'name': 'inchworm_to_side_plank',
  'value': 20,
}),
  21: dict({
  'name': 'weighted_inchworm_to_side_plank',
  'value': 21,
}),
  22: dict({
  'name': 'kneeling_plank',
  'value': 22,
}),
  23: dict({
  'name': 'weighted_kneeling_plank',
  'value': 23,
}),
  24: dict({
  'name': 'kneeling_side_plank_with_leg_lift',
  'value': 24,
}),
  25: dict({
  'name': 'weighted_kneeling_side_plank_with_leg_lift',
  'value': 25,
}),
  26: dict({
  'name': 'lateral_roll',
  'value': 26,
}),
  27: dict({
  'name': 'weighted_lateral_roll',
  'value': 27,
}),
  28: dict({
  'name': 'lying_reverse_plank',
  'value': 28,
}),
  29: dict({
  'name': 'weighted_lying_reverse_plank',
  'value': 29,
}),
  30: dict({
  'name': 'medicine_ball_mountain_climber',
  'value': 30,
}),
  31: dict({
  'name': 'weighted_medicine_ball_mountain_climber',
  'value': 31,
}),
  32: dict({
  'name': 'modified_mountain_climber_and_extension',
  'value': 32,
}),
  33: dict({
  'name': 'weighted_modified_mountain_climber_and_extension',
  'value': 33,
}),
  34: dict({
  'name': 'mountain_climber',
  'value': 34,
}),
  35: dict({
  'name': 'weighted_mountain_climber',
  'value': 35,
}),
  36: dict({
  'name': 'mountain_climber_on_sliding_discs',
  'value': 36,
}),
  37: dict({
  'name': 'weighted_mountain_climber_on_sliding_discs',
  'value': 37,
}),
  38: dict({
  'name': 'mountain_climber_with_feet_on_bosu_ball',
  'value': 38,
}),
  39: dict({
  'name': 'weighted_mountain_climber_with_feet_on_bosu_ball',
  'value': 39,
}),
  40: dict({
  'name': 'mountain_climber_with_hands_on_bench',
  'value': 40,
}),
  41: dict({
  'name': 'mountain_climber_with_hands_on_swiss_ball',
  'value': 41,
}),
  42: dict({
  'name': 'weighted_mountain_climber_with_hands_on_swiss_ball',
  'value': 42,
}),
  43: dict({
  'name': 'plank',
  'value': 43,
}),
  44: dict({
  'name': 'plank_jacks_with_feet_on_sliding_discs',
  'value': 44,
}),
  45: dict({
  'name': 'weighted_plank_jacks_with_feet_on_sliding_discs',
  'value': 45,
}),
  46: dict({
  'name': 'plank_knee_twist',
  'value': 46,
}),
  47: dict({
  'name': 'weighted_plank_knee_twist',
  'value': 47,
}),
  48: dict({
  'name': 'plank_pike_jumps',
  'value': 48,
}),
  49: dict({
  'name': 'weighted_plank_pike_jumps',
  'value': 49,
}),
  50: dict({
  'name': 'plank_pikes',
  'value': 50,
}),
  51: dict({
  'name': 'weighted_plank_pikes',
  'value': 51,
}),
  52: dict({
  'name': 'plank_to_stand_up',
  'value': 52,
}),
  53: dict({
  'name': 'weighted_plank_to_stand_up',
  'value': 53,
}),
  54: dict({
  'name': 'plank_with_arm_raise',
  'value': 54,
}),
  55: dict({
  'name': 'weighted_plank_with_arm_raise',
  'value': 55,
}),
  56: dict({
  'name': 'plank_with_knee_to_elbow',
  'value': 56,
}),
  57: dict({
  'name': 'weighted_plank_with_knee_to_elbow',
  'value': 57,
}),
  58: dict({
  'name': 'plank_with_oblique_crunch',
  'value': 58,
}),
  59: dict({
  'name': 'weighted_plank_with_oblique_crunch',
  'value': 59,
}),
  60: dict({
  'name': 'plyometric_side_plank',
  'value': 60,
}),
  61: dict({
  'name': 'weighted_plyometric_side_plank',
  'value': 61,
}),
  62: dict({
  'name': 'rolling_side_plank',
  'value': 62,
}),
  63: dict({
  'name': 'weighted_rolling_side_plank',
  'value': 63,
}),
  64: dict({
  'name': 'side_kick_plank',
  'value': 64,
}),
  65: dict({
  'name': 'weighted_side_kick_plank',
  'value': 65,
}),
  66: dict({
  'name': 'side_plank',
  'value': 66,
}),
  67: dict({
  'name': 'weighted_side_plank',
  'value': 67,
}),
  68: dict({
  'name': 'side_plank_and_row',
  'value': 68,
}),
  69: dict({
  'name': 'weighted_side_plank_and_row',
  'value': 69,
}),
  70: dict({
  'name': 'side_plank_lift',
  'value': 70,
}),
  71: dict({
  'name': 'weighted_side_plank_lift',
  'value': 71,
}),
  72: dict({
  'name': 'side_plank_with_elbow_on_bosu_ball',
  'value': 72,
}),
  73: dict({
  'name': 'weighted_side_plank_with_elbow_on_bosu_ball',
  'value': 73,
}),
  74: dict({
  'name': 'side_plank_with_feet_on_bench',
  'value': 74,
}),
  75: dict({
  'name': 'weighted_side_plank_with_feet_on_bench',
  'value': 75,
}),
  76: dict({
  'name': 'side_plank_with_knee_circle',
  'value': 76,
}),
  77: dict({
  'name': 'weighted_side_plank_with_knee_circle',
  'value': 77,
}),
  78: dict({
  'name': 'side_plank_with_knee_tuck',
  'value': 78,
}),
  79: dict({
  'name': 'weighted_side_plank_with_knee_tuck',
  'value': 79,
}),
  80: dict({
  'name': 'side_plank_with_leg_lift',
  'value': 80,
}),
  81: dict({
  'name': 'weighted_side_plank_with_leg_lift',
  'value': 81,
}),
  82: dict({
  'name': 'side_plank_with_reach_under',
  'value': 82,
}),
  83: dict({
  'name': 'weighted_side_plank_with_reach_under',
  'value': 83,
}),
  84: dict({
  'name': 'single_leg_elevated_feet_plank',
  'value': 84,
}),
  85: dict({
  'name': 'weighted_single_leg_elevated_feet_plank',
  'value': 85,
}),
  86: dict({
  'name': 'single_leg_flex_and_extend',
  'value': 86,
}),
  87: dict({
  'name': 'weighted_single_leg_flex_and_extend',
  'value': 87,
}),
  88: dict({
  'name': 'single_leg_side_plank',
  'value': 88,
}),
  89: dict({
  'name': 'weighted_single_leg_side_plank',
  'value': 89,
}),
  90: dict({
  'name': 'spiderman_plank',
  'value': 90,
}),
  91: dict({
  'name': 'weighted_spiderman_plank',
  'value': 91,
}),
  92: dict({
  'name': 'straight_arm_plank',
  'value': 92,
}),
  93: dict({
  'name': 'weighted_straight_arm_plank',
  'value': 93,
}),
  94: dict({
  'name': 'straight_arm_plank_with_shoulder_touch',
  'value': 94,
}),
  95: dict({
  'name': 'weighted_straight_arm_plank_with_shoulder_touch',
  'value': 95,
}),
  96: dict({
  'name': 'swiss_ball_plank',
  'value': 96,
}),
  97: dict({
  'name': 'weighted_swiss_ball_plank',
  'value': 97,
}),
  98: dict({
  'name': 'swiss_ball_plank_leg_lift',
  'value': 98,
}),
  99: dict({
  'name': 'weighted_swiss_ball_plank_leg_lift',
  'value': 99,
}),
  100: dict({
  'name': 'swiss_ball_plank_leg_lift_and_hold',
  'value': 100,
}),
  101: dict({
  'name': 'swiss_ball_plank_with_feet_on_bench',
  'value': 101,
}),
  102: dict({
  'name': 'weighted_swiss_ball_plank_with_feet_on_bench',
  'value': 102,
}),
  103: dict({
  'name': 'swiss_ball_prone_jackknife',
  'value': 103,
}),
  104: dict({
  'name': 'weighted_swiss_ball_prone_jackknife',
  'value': 104,
}),
  105: dict({
  'name': 'swiss_ball_side_plank',
  'value': 105,
}),
  106: dict({
  'name': 'weighted_swiss_ball_side_plank',
  'value': 106,
}),
  107: dict({
  'name': 'three_way_plank',
  'value': 107,
}),
  108: dict({
  'name': 'weighted_three_way_plank',
  'value': 108,
}),
  109: dict({
  'name': 'towel_plank_and_knee_in',
  'value': 109,
}),
  110: dict({
  'name': 'weighted_towel_plank_and_knee_in',
  'value': 110,
}),
  111: dict({
  'name': 't_stabilization',
  'value': 111,
}),
  112: dict({
  'name': 'weighted_t_stabilization',
  'value': 112,
}),
  113: dict({
  'name': 'turkish_get_up_to_side_plank',
  'value': 113,
}),
  114: dict({
  'name': 'weighted_turkish_get_up_to_side_plank',
  'value': 114,
}),
  115: dict({
  'name': 'two_point_plank',
  'value': 115,
}),
  116: dict({
  'name': 'weighted_two_point_plank',
  'value': 116,
}),
  117: dict({
  'name': 'weighted_plank',
  'value': 117,
}),
  118: dict({
  'name': 'wide_stance_plank_with_diagonal_arm_lift',
  'value': 118,
}),
  119: dict({
  'name': 'weighted_wide_stance_plank_with_diagonal_arm_lift',
  'value': 119,
}),
  120: dict({
  'name': 'wide_stance_plank_with_diagonal_leg_lift',
  'value': 120,
}),
  121: dict({
  'name': 'weighted_wide_stance_plank_with_diagonal_leg_lift',
  'value': 121,
}),
  122: dict({
  'name': 'wide_stance_plank_with_leg_lift',
  'value': 122,
}),
  123: dict({
  'name': 'weighted_wide_stance_plank_with_leg_lift',
  'value': 123,
}),
  124: dict({
  'name': 'wide_stance_plank_with_opposite_arm_and_leg_lift',
  'value': 124,
}),
  125: dict({
  'name': 'weighted_mountain_climber_with_hands_on_bench',
  'value': 125,
}),
  126: dict({
  'name': 'weighted_swiss_ball_plank_leg_lift_and_hold',
  'value': 126,
}),
  127: dict({
  'name': 'weighted_wide_stance_plank_with_opposite_arm_and_leg_lift',
  'value': 127,
}),
  128: dict({
  'name': 'plank_with_feet_on_swiss_ball',
  'value': 128,
}),
  129: dict({
  'name': 'side_plank_to_plank_with_reach_under',
  'value': 129,
}),
  130: dict({
  'name': 'bridge_with_glute_lower_lift',
  'value': 130,
}),
  131: dict({
  'name': 'bridge_one_leg_bridge',
  'value': 131,
}),
  132: dict({
  'name': 'plank_with_arm_variations',
  'value': 132,
}),
  133: dict({
  'name': 'plank_with_leg_lift',
  'value': 133,
}),
  134: dict({
  'name': 'reverse_plank_with_leg_pull',
  'value': 134,
}),
}),
}),
  'plyo_exercise_name': dict({
  'name': 'plyo_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'alternating_jump_lunge',
  'value': 0,
}),
  1: dict({
  'name': 'weighted_alternating_jump_lunge',
  'value': 1,
}),
  2: dict({
  'name': 'barbell_jump_squat',
  'value': 2,
}),
  3: dict({
  'name': 'body_weight_jump_squat',
  'value': 3,
}),
  4: dict({
  'name': 'weighted_jump_squat',
  'value': 4,
}),
  5: dict({
  'name': 'cross_knee_strike',
  'value': 5,
}),
  6: dict({
  'name': 'weighted_cross_knee_strike',
  'value': 6,
}),
  7: dict({
  'name': 'depth_jump',
  'value': 7,
}),
  8: dict({
  'name': 'weighted_depth_jump',
  'value': 8,
}),
  9: dict({
  'name': 'dumbbell_jump_squat',
  'value': 9,
}),
  10: dict({
  'name': 'dumbbell_split_jump',
  'value': 10,
}),
  11: dict({
  'name': 'front_knee_strike',
  'value': 11,
}),
  12: dict({
  'name': 'weighted_front_knee_strike',
  'value': 12,
}),
  13: dict({
  'name': 'high_box_jump',
  'value': 13,
}),
  14: dict({
  'name': 'weighted_high_box_jump',
  'value': 14,
}),
  15: dict({
  'name': 'isometric_explosive_body_weight_jump_squat',
  'value': 15,
}),
  16: dict({
  'name': 'weighted_isometric_explosive_jump_squat',
  'value': 16,
}),
  17: dict({
  'name': 'lateral_leap_and_hop',
  'value': 17,
}),
  18: dict({
  'name': 'weighted_lateral_leap_and_hop',
  'value': 18,
}),
  19: dict({
  'name': 'lateral_plyo_squats',
  'value': 19,
}),
  20: dict({
  'name': 'weighted_lateral_plyo_squats',
  'value': 20,
}),
  21: dict({
  'name': 'lateral_slide',
  'value': 21,
}),
  22: dict({
  'name': 'weighted_lateral_slide',
  'value': 22,
}),
  23: dict({
  'name': 'medicine_ball_overhead_throws',
  'value': 23,
}),
  24: dict({
  'name': 'medicine_ball_side_throw',
  'value': 24,
}),
  25: dict({
  'name': 'medicine_ball_slam',
  'value': 25,
}),
  26: dict({
  'name': 'side_to_side_medicine_ball_throws',
  'value': 26,
}),
  27: dict({
  'name': 'side_to_side_shuffle_jump',
  'value': 27,
}),
  28: dict({
  'name': 'weighted_side_to_side_shuffle_jump',
  'value': 28,
}),
  29: dict({
  'name': 'squat_jump_onto_box',
  'value': 29,
}),
  30: dict({
  'name': 'weighted_squat_jump_onto_box',
  'value': 30,
}),
  31: dict({
  'name': 'squat_jumps_in_and_out',
  'value': 31,
}),
  32: dict({
  'name': 'weighted_squat_jumps_in_and_out',
  'value': 32,
}),
}),
}),
  'pull_up_exercise_name': dict({
  'name': 'pull_up_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'banded_pull_ups',
  'value': 0,
}),
  1: dict({
  'name': '30_degree_lat_pulldown',
  'value': 1,
}),
  2: dict({
  'name': 'band_assisted_chin_up',
  'value': 2,
}),
  3: dict({
  'name': 'close_grip_chin_up',
  'value': 3,
}),
  4: dict({
  'name': 'weighted_close_grip_chin_up',
  'value': 4,
}),
  5: dict({
  'name': 'close_grip_lat_pulldown',
  'value': 5,
}),
  6: dict({
  'name': 'crossover_chin_up',
  'value': 6,
}),
  7: dict({
  'name': 'weighted_crossover_chin_up',
  'value': 7,
}),
  8: dict({
  'name': 'ez_bar_pullover',
  'value': 8,
}),
  9: dict({
  'name': 'hanging_hurdle',
  'value': 9,
}),
  10: dict({
  'name': 'weighted_hanging_hurdle',
  'value': 10,
}),
  11: dict({
  'name': 'kneeling_lat_pulldown',
  'value': 11,
}),
  12: dict({
  'name': 'kneeling_underhand_grip_lat_pulldown',
  'value': 12,
}),
  13: dict({
  'name': 'lat_pulldown',
  'value': 13,
}),
  14: dict({
  'name': 'mixed_grip_chin_up',
  'value': 14,
}),
  15: dict({
  'name': 'weighted_mixed_grip_chin_up',
  'value': 15,
}),
  16: dict({
  'name': 'mixed_grip_pull_up',
  'value': 16,
}),
  17: dict({
  'name': 'weighted_mixed_grip_pull_up',
  'value': 17,
}),
  18: dict({
  'name': 'reverse_grip_pulldown',
  'value': 18,
}),
  19: dict({
  'name': 'standing_cable_pullover',
  'value': 19,
}),
  20: dict({
  'name': 'straight_arm_pulldown',
  'value': 20,
}),
  21: dict({
  'name': 'swiss_ball_ez_bar_pullover',
  'value': 21,
}),
  22: dict({
  'name': 'towel_pull_up',
  'value': 22,
}),
  23: dict({
  'name': 'weighted_towel_pull_up',
  'value': 23,
}),
  24: dict({
  'name': 'weighted_pull_up',
  'value': 24,
}),
  25: dict({
  'name': 'wide_grip_lat_pulldown',
  'value': 25,
}),
  26: dict({
  'name': 'wide_grip_pull_up',
  'value': 26,
}),
  27: dict({
  'name': 'weighted_wide_grip_pull_up',
  'value': 27,
}),
  28: dict({
  'name': 'burpee_pull_up',
  'value': 28,
}),
  29: dict({
  'name': 'weighted_burpee_pull_up',
  'value': 29,
}),
  30: dict({
  'name': 'jumping_pull_ups',
  'value': 30,
}),
  31: dict({
  'name': 'weighted_jumping_pull_ups',
  'value': 31,
}),
  32: dict({
  'name': 'kipping_pull_up',
  'value': 32,
}),
  33: dict({
  'name': 'weighted_kipping_pull_up',
  'value': 33,
}),
  34: dict({
  'name': 'l_pull_up',
  'value': 34,
}),
  35: dict({
  'name': 'weighted_l_pull_up',
  'value': 35,
}),
  36: dict({
  'name': 'suspended_chin_up',
  'value': 36,
}),
  37: dict({
  'name': 'weighted_suspended_chin_up',
  'value': 37,
}),
  38: dict({
  'name': 'pull_up',
  'value': 38,
}),
}),
}),
  'push_up_exercise_name': dict({
  'name': 'push_up_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'chest_press_with_band',
  'value': 0,
}),
  1: dict({
  'name': 'alternating_staggered_push_up',
  'value': 1,
}),
  2: dict({
  'name': 'weighted_alternating_staggered_push_up',
  'value': 2,
}),
  3: dict({
  'name': 'alternating_hands_medicine_ball_push_up',
  'value': 3,
}),
  4: dict({
  'name': 'weighted_alternating_hands_medicine_ball_push_up',
  'value': 4,
}),
  5: dict({
  'name': 'bosu_ball_push_up',
  'value': 5,
}),
  6: dict({
  'name': 'weighted_bosu_ball_push_up',
  'value': 6,
}),
  7: dict({
  'name': 'clapping_push_up',
  'value': 7,
}),
  8: dict({
  'name': 'weighted_clapping_push_up',
  'value': 8,
}),
  9: dict({
  'name': 'close_grip_medicine_ball_push_up',
  'value': 9,
}),
  10: dict({
  'name': 'weighted_close_grip_medicine_ball_push_up',
  'value': 10,
}),
  11: dict({
  'name': 'close_hands_push_up',
  'value': 11,
}),
  12: dict({
  'name': 'weighted_close_hands_push_up',
  'value': 12,
}),
  13: dict({
  'name': 'decline_push_up',
  'value': 13,
}),
  14: dict({
  'name': 'weighted_decline_push_up',
  'value': 14,
}),
  15: dict({
  'name': 'diamond_push_up',
  'value': 15,
}),
  16: dict({
  'name': 'weighted_diamond_push_up',
  'value': 16,
}),
  17: dict({
  'name': 'explosive_crossover_push_up',
  'value': 17,
}),
  18: dict({
  'name': 'weighted_explosive_crossover_push_up',
  'value': 18,
}),
  19: dict({
  'name': 'explosive_push_up',
  'value': 19,
}),
  20: dict({
  'name': 'weighted_explosive_push_up',
  'value': 20,
}),
  21: dict({
  'name': 'feet_elevated_side_to_side_push_up',
  'value': 21,
}),
  22: dict({
  'name': 'weighted_feet_elevated_side_to_side_push_up',
  'value': 22,
}),
  23: dict({
  'name': 'hand_release_push_up',
  'value': 23,
}),
  24: dict({
  'name': 'weighted_hand_release_push_up',
  'value': 24,
}),
  25: dict({
  'name': 'handstand_push_up',
  'value': 25,
}),
  26: dict({
  'name': 'weighted_handstand_push_up',
  'value': 26,
}),
  27: dict({
  'name': 'incline_push_up',
  'value': 27,
}),
  28: dict({
  'name': 'weighted_incline_push_up',
  'value': 28,
}),
  29: dict({
  'name': 'isometric_explosive_push_up',
  'value': 29,
}),
  30: dict({
  'name': 'weighted_isometric_explosive_push_up',
  'value': 30,
}),
  31: dict({
  'name': 'judo_push_up',
  'value': 31,
}),
  32: dict({
  'name': 'weighted_judo_push_up',
  'value': 32,
}),
  33: dict({
  'name': 'kneeling_push_up',
  'value': 33,
}),
  34: dict({
  'name': 'weighted_kneeling_push_up',
  'value': 34,
}),
  35: dict({
  'name': 'medicine_ball_chest_pass',
  'value': 35,
}),
  36: dict({
  'name': 'medicine_ball_push_up',
  'value': 36,
}),
  37: dict({
  'name': 'weighted_medicine_ball_push_up',
  'value': 37,
}),
  38: dict({
  'name': 'one_arm_push_up',
  'value': 38,
}),
  39: dict({
  'name': 'weighted_one_arm_push_up',
  'value': 39,
}),
  40: dict({
  'name': 'weighted_push_up',
  'value': 40,
}),
  41: dict({
  'name': 'push_up_and_row',
  'value': 41,
}),
  42: dict({
  'name': 'weighted_push_up_and_row',
  'value': 42,
}),
  43: dict({
  'name': 'push_up_plus',
  'value': 43,
}),
  44: dict({
  'name': 'weighted_push_up_plus',
  'value': 44,
}),
  45: dict({
  'name': 'push_up_with_feet_on_swiss_ball',
  'value': 45,
}),
  46: dict({
  'name': 'weighted_push_up_with_feet_on_swiss_ball',
  'value': 46,
}),
  47: dict({
  'name': 'push_up_with_one_hand_on_medicine_ball',
  'value': 47,
}),
  48: dict({
  'name': 'weighted_push_up_with_one_hand_on_medicine_ball',
  'value': 48,
}),
  49: dict({
  'name': 'shoulder_push_up',
  'value': 49,
}),
  50: dict({
  'name': 'weighted_shoulder_push_up',
  'value': 50,
}),
  51: dict({
  'name': 'single_arm_medicine_ball_push_up',
  'value': 51,
}),
  52: dict({
  'name': 'weighted_single_arm_medicine_ball_push_up',
  'value': 52,
}),
  53: dict({
  'name': 'spiderman_push_up',
  'value': 53,
}),
  54: dict({
  'name': 'weighted_spiderman_push_up',
  'value': 54,
}),
  55: dict({
  'name': 'stacked_feet_push_up',
  'value': 55,
}),
  56: dict({
  'name': 'weighted_stacked_feet_push_up',
  'value': 56,
}),
  57: dict({
  'name': 'staggered_hands_push_up',
  'value': 57,
}),
  58: dict({
  'name': 'weighted_staggered_hands_push_up',
  'value': 58,
}),
  59: dict({
  'name': 'suspended_push_up',
  'value': 59,
}),
  60: dict({
  'name': 'weighted_suspended_push_up',
  'value': 60,
}),
  61: dict({
  'name': 'swiss_ball_push_up',
  'value': 61,
}),
  62: dict({
  'name': 'weighted_swiss_ball_push_up',
  'value': 62,
}),
  63: dict({
  'name': 'swiss_ball_push_up_plus',
  'value': 63,
}),
  64: dict({
  'name': 'weighted_swiss_ball_push_up_plus',
  'value': 64,
}),
  65: dict({
  'name': 't_push_up',
  'value': 65,
}),
  66: dict({
  'name': 'weighted_t_push_up',
  'value': 66,
}),
  67: dict({
  'name': 'triple_stop_push_up',
  'value': 67,
}),
  68: dict({
  'name': 'weighted_triple_stop_push_up',
  'value': 68,
}),
  69: dict({
  'name': 'wide_hands_push_up',
  'value': 69,
}),
  70: dict({
  'name': 'weighted_wide_hands_push_up',
  'value': 70,
}),
  71: dict({
  'name': 'parallette_handstand_push_up',
  'value': 71,
}),
  72: dict({
  'name': 'weighted_parallette_handstand_push_up',
  'value': 72,
}),
  73: dict({
  'name': 'ring_handstand_push_up',
  'value': 73,
}),
  74: dict({
  'name': 'weighted_ring_handstand_push_up',
  'value': 74,
}),
  75: dict({
  'name': 'ring_push_up',
  'value': 75,
}),
  76: dict({
  'name': 'weighted_ring_push_up',
  'value': 76,
}),
  77: dict({
  'name': 'push_up',
  'value': 77,
}),
  78: dict({
  'name': 'pilates_pushup',
  'value': 78,
}),
}),
}),
  'row_exercise_name': dict({
  'name': 'row_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'barbell_straight_leg_deadlift_to_row',
  'value': 0,
}),
  1: dict({
  'name': 'cable_row_standing',
  'value': 1,
}),
  2: dict({
  'name': 'dumbbell_row',
  'value': 2,
}),
  3: dict({
  'name': 'elevated_feet_inverted_row',
  'value': 3,
}),
  4: dict({
  'name': 'weighted_elevated_feet_inverted_row',
  'value': 4,
}),
  5: dict({
  'name': 'face_pull',
  'value': 5,
}),
  6: dict({
  'name': 'face_pull_with_external_rotation',
  'value': 6,
}),
  7: dict({
  'name': 'inverted_row_with_feet_on_swiss_ball',
  'value': 7,
}),
  8: dict({
  'name': 'weighted_inverted_row_with_feet_on_swiss_ball',
  'value': 8,
}),
  9: dict({
  'name': 'kettlebell_row',
  'value': 9,
}),
  10: dict({
  'name': 'modified_inverted_row',
  'value': 10,
}),
  11: dict({
  'name': 'weighted_modified_inverted_row',
  'value': 11,
}),
  12: dict({
  'name': 'neutral_grip_alternating_dumbbell_row',
  'value': 12,
}),
  13: dict({
  'name': 'one_arm_bent_over_row',
  'value': 13,
}),
  14: dict({
  'name': 'one_legged_dumbbell_row',
  'value': 14,
}),
  15: dict({
  'name': 'renegade_row',
  'value': 15,
}),
  16: dict({
  'name': 'reverse_grip_barbell_row',
  'value': 16,
}),
  17: dict({
  'name': 'rope_handle_cable_row',
  'value': 17,
}),
  18: dict({
  'name': 'seated_cable_row',
  'value': 18,
}),
  19: dict({
  'name': 'seated_dumbbell_row',
  'value': 19,
}),
  20: dict({
  'name': 'single_arm_cable_row',
  'value': 20,
}),
  21: dict({
  'name': 'single_arm_cable_row_and_rotation',
  'value': 21,
}),
  22: dict({
  'name': 'single_arm_inverted_row',
  'value': 22,
}),
  23: dict({
  'name': 'weighted_single_arm_inverted_row',
  'value': 23,
}),
  24: dict({
  'name': 'single_arm_neutral_grip_dumbbell_row',
  'value': 24,
}),
  25: dict({
  'name': 'single_arm_neutral_grip_dumbbell_row_and_rotation',
  'value': 25,
}),
  26: dict({
  'name': 'suspended_inverted_row',
  'value': 26,
}),
  27: dict({
  'name': 'weighted_suspended_inverted_row',
  'value': 27,
}),
  28: dict({
  'name': 't_bar_row',
  'value': 28,
}),
  29: dict({
  'name': 'towel_grip_inverted_row',
  'value': 29,
}),
  30: dict({
  'name': 'weighted_towel_grip_inverted_row',
  'value': 30,
}),
  31: dict({
  'name': 'underhand_grip_cable_row',
  'value': 31,
}),
  32: dict({
  'name': 'v_grip_cable_row',
  'value': 32,
}),
  33: dict({
  'name': 'wide_grip_seated_cable_row',
  'value': 33,
}),
}),
}),
  'shoulder_press_exercise_name': dict({
  'name': 'shoulder_press_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'alternating_dumbbell_shoulder_press',
  'value': 0,
}),
  1: dict({
  'name': 'arnold_press',
  'value': 1,
}),
  2: dict({
  'name': 'barbell_front_squat_to_push_press',
  'value': 2,
}),
  3: dict({
  'name': 'barbell_push_press',
  'value': 3,
}),
  4: dict({
  'name': 'barbell_shoulder_press',
  'value': 4,
}),
  5: dict({
  'name': 'dead_curl_press',
  'value': 5,
}),
  6: dict({
  'name': 'dumbbell_alternating_shoulder_press_and_twist',
  'value': 6,
}),
  7: dict({
  'name': 'dumbbell_hammer_curl_to_lunge_to_press',
  'value': 7,
}),
  8: dict({
  'name': 'dumbbell_push_press',
  'value': 8,
}),
  9: dict({
  'name': 'floor_inverted_shoulder_press',
  'value': 9,
}),
  10: dict({
  'name': 'weighted_floor_inverted_shoulder_press',
  'value': 10,
}),
  11: dict({
  'name': 'inverted_shoulder_press',
  'value': 11,
}),
  12: dict({
  'name': 'weighted_inverted_shoulder_press',
  'value': 12,
}),
  13: dict({
  'name': 'one_arm_push_press',
  'value': 13,
}),
  14: dict({
  'name': 'overhead_barbell_press',
  'value': 14,
}),
  15: dict({
  'name': 'overhead_dumbbell_press',
  'value': 15,
}),
  16: dict({
  'name': 'seated_barbell_shoulder_press',
  'value': 16,
}),
  17: dict({
  'name': 'seated_dumbbell_shoulder_press',
  'value': 17,
}),
  18: dict({
  'name': 'single_arm_dumbbell_shoulder_press',
  'value': 18,
}),
  19: dict({
  'name': 'single_arm_step_up_and_press',
  'value': 19,
}),
  20: dict({
  'name': 'smith_machine_overhead_press',
  'value': 20,
}),
  21: dict({
  'name': 'split_stance_hammer_curl_to_press',
  'value': 21,
}),
  22: dict({
  'name': 'swiss_ball_dumbbell_shoulder_press',
  'value': 22,
}),
  23: dict({
  'name': 'weight_plate_front_raise',
  'value': 23,
}),
}),
}),
  'shoulder_stability_exercise_name': dict({
  'name': 'shoulder_stability_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': '90_degree_cable_external_rotation',
  'value': 0,
}),
  1: dict({
  'name': 'band_external_rotation',
  'value': 1,
}),
  2: dict({
  'name': 'band_internal_rotation',
  'value': 2,
}),
  3: dict({
  'name': 'bent_arm_lateral_raise_and_external_rotation',
  'value': 3,
}),
  4: dict({
  'name': 'cable_external_rotation',
  'value': 4,
}),
  5: dict({
  'name': 'dumbbell_face_pull_with_external_rotation',
  'value': 5,
}),
  6: dict({
  'name': 'floor_i_raise',
  'value': 6,
}),
  7: dict({
  'name': 'weighted_floor_i_raise',
  'value': 7,
}),
  8: dict({
  'name': 'floor_t_raise',
  'value': 8,
}),
  9: dict({
  'name': 'weighted_floor_t_raise',
  'value': 9,
}),
  10: dict({
  'name': 'floor_y_raise',
  'value': 10,
}),
  11: dict({
  'name': 'weighted_floor_y_raise',
  'value': 11,
}),
  12: dict({
  'name': 'incline_i_raise',
  'value': 12,
}),
  13: dict({
  'name': 'weighted_incline_i_raise',
  'value': 13,
}),
  14: dict({
  'name': 'incline_l_raise',
  'value': 14,
}),
  15: dict({
  'name': 'weighted_incline_l_raise',
  'value': 15,
}),
  16: dict({
  'name': 'incline_t_raise',
  'value': 16,
}),
  17: dict({
  'name': 'weighted_incline_t_raise',
  'value': 17,
}),
  18: dict({
  'name': 'incline_w_raise',
  'value': 18,
}),
  19: dict({
  'name': 'weighted_incline_w_raise',
  'value': 19,
}),
  20: dict({
  'name': 'incline_y_raise',
  'value': 20,
}),
  21: dict({
  'name': 'weighted_incline_y_raise',
  'value': 21,
}),
  22: dict({
  'name': 'lying_external_rotation',
  'value': 22,
}),
  23: dict({
  'name': 'seated_dumbbell_external_rotation',
  'value': 23,
}),
  24: dict({
  'name': 'standing_l_raise',
  'value': 24,
}),
  25: dict({
  'name': 'swiss_ball_i_raise',
  'value': 25,
}),
  26: dict({
  'name': 'weighted_swiss_ball_i_raise',
  'value': 26,
}),
  27: dict({
  'name': 'swiss_ball_t_raise',
  'value': 27,
}),
  28: dict({
  'name': 'weighted_swiss_ball_t_raise',
  'value': 28,
}),
  29: dict({
  'name': 'swiss_ball_w_raise',
  'value': 29,
}),
  30: dict({
  'name': 'weighted_swiss_ball_w_raise',
  'value': 30,
}),
  31: dict({
  'name': 'swiss_ball_y_raise',
  'value': 31,
}),
  32: dict({
  'name': 'weighted_swiss_ball_y_raise',
  'value': 32,
}),
}),
}),
  'shrug_exercise_name': dict({
  'name': 'shrug_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'barbell_jump_shrug',
  'value': 0,
}),
  1: dict({
  'name': 'barbell_shrug',
  'value': 1,
}),
  2: dict({
  'name': 'barbell_upright_row',
  'value': 2,
}),
  3: dict({
  'name': 'behind_the_back_smith_machine_shrug',
  'value': 3,
}),
  4: dict({
  'name': 'dumbbell_jump_shrug',
  'value': 4,
}),
  5: dict({
  'name': 'dumbbell_shrug',
  'value': 5,
}),
  6: dict({
  'name': 'dumbbell_upright_row',
  'value': 6,
}),
  7: dict({
  'name': 'incline_dumbbell_shrug',
  'value': 7,
}),
  8: dict({
  'name': 'overhead_barbell_shrug',
  'value': 8,
}),
  9: dict({
  'name': 'overhead_dumbbell_shrug',
  'value': 9,
}),
  10: dict({
  'name': 'scaption_and_shrug',
  'value': 10,
}),
  11: dict({
  'name': 'scapular_retraction',
  'value': 11,
}),
  12: dict({
  'name': 'serratus_chair_shrug',
  'value': 12,
}),
  13: dict({
  'name': 'weighted_serratus_chair_shrug',
  'value': 13,
}),
  14: dict({
  'name': 'serratus_shrug',
  'value': 14,
}),
  15: dict({
  'name': 'weighted_serratus_shrug',
  'value': 15,
}),
  16: dict({
  'name': 'wide_grip_jump_shrug',
  'value': 16,
}),
}),
}),
  'sit_up_exercise_name': dict({
  'name': 'sit_up_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'alternating_sit_up',
  'value': 0,
}),
  1: dict({
  'name': 'weighted_alternating_sit_up',
  'value': 1,
}),
  2: dict({
  'name': 'bent_knee_v_up',
  'value': 2,
}),
  3: dict({
  'name': 'weighted_bent_knee_v_up',
  'value': 3,
}),
  4: dict({
  'name': 'butterfly_sit_up',
  'value': 4,
}),
  5: dict({
  'name': 'weighted_butterfly_situp',
  'value': 5,
}),
  6: dict({
  'name': 'cross_punch_roll_up',
  'value': 6,
}),
  7: dict({
  'name': 'weighted_cross_punch_roll_up',
  'value': 7,
}),
  8: dict({
  'name': 'crossed_arms_sit_up',
  'value': 8,
}),
  9: dict({
  'name': 'weighted_crossed_arms_sit_up',
  'value': 9,
}),
  10: dict({
  'name': 'get_up_sit_up',
  'value': 10,
}),
  11: dict({
  'name': 'weighted_get_up_sit_up',
  'value': 11,
}),
  12: dict({
  'name': 'hovering_sit_up',
  'value': 12,
}),
  13: dict({
  'name': 'weighted_hovering_sit_up',
  'value': 13,
}),
  14: dict({
  'name': 'kettlebell_sit_up',
  'value': 14,
}),
  15: dict({
  'name': 'medicine_ball_alternating_v_up',
  'value': 15,
}),
  16: dict({
  'name': 'medicine_ball_sit_up',
  'value': 16,
}),
  17: dict({
  'name': 'medicine_ball_v_up',
  'value': 17,
}),
  18: dict({
  'name': 'modified_sit_up',
  'value': 18,
}),
  19: dict({
  'name': 'negative_sit_up',
  'value': 19,
}),
  20: dict({
  'name': 'one_arm_full_sit_up',
  'value': 20,
}),
  21: dict({
  'name': 'reclining_circle',
  'value': 21,
}),
  22: dict({
  'name': 'weighted_reclining_circle',
  'value': 22,
}),
  23: dict({
  'name': 'reverse_curl_up',
  'value': 23,
}),
  24: dict({
  'name': 'weighted_reverse_curl_up',
  'value': 24,
}),
  25: dict({
  'name': 'single_leg_swiss_ball_jackknife',
  'value': 25,
}),
  26: dict({
  'name': 'weighted_single_leg_swiss_ball_jackknife',
  'value': 26,
}),
  27: dict({
  'name': 'the_teaser',
  'value': 27,
}),
  28: dict({
  'name': 'the_teaser_weighted',
  'value': 28,
}),
  29: dict({
  'name': 'three_part_roll_down',
  'value': 29,
}),
  30: dict({
  'name': 'weighted_three_part_roll_down',
  'value': 30,
}),
  31: dict({
  'name': 'v_up',
  'value': 31,
}),
  32: dict({
  'name': 'weighted_v_up',
  'value': 32,
}),
  33: dict({
  'name': 'weighted_russian_twist_on_swiss_ball',
  'value': 33,
}),
  34: dict({
  'name': 'weighted_sit_up',
  'value': 34,
}),
  35: dict({
  'name': 'x_abs',
  'value': 35,
}),
  36: dict({
  'name': 'weighted_x_abs',
  'value': 36,
}),
  37: dict({
  'name': 'sit_up',
  'value': 37,
}),
}),
}),
  'squat_exercise_name': dict({
  'name': 'squat_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'leg_press',
  'value': 0,
}),
  1: dict({
  'name': 'back_squat_with_body_bar',
  'value': 1,
}),
  2: dict({
  'name': 'back_squats',
  'value': 2,
}),
  3: dict({
  'name': 'weighted_back_squats',
  'value': 3,
}),
  4: dict({
  'name': 'balancing_squat',
  'value': 4,
}),
  5: dict({
  'name': 'weighted_balancing_squat',
  'value': 5,
}),
  6: dict({
  'name': 'barbell_back_squat',
  'value': 6,
}),
  7: dict({
  'name': 'barbell_box_squat',
  'value': 7,
}),
  8: dict({
  'name': 'barbell_front_squat',
  'value': 8,
}),
  9: dict({
  'name': 'barbell_hack_squat',
  'value': 9,
}),
  10: dict({
  'name': 'barbell_hang_squat_snatch',
  'value': 10,
}),
  11: dict({
  'name': 'barbell_lateral_step_up',
  'value': 11,
}),
  12: dict({
  'name': 'barbell_quarter_squat',
  'value': 12,
}),
  13: dict({
  'name': 'barbell_siff_squat',
  'value': 13,
}),
  14: dict({
  'name': 'barbell_squat_snatch',
  'value': 14,
}),
  15: dict({
  'name': 'barbell_squat_with_heels_raised',
  'value': 15,
}),
  16: dict({
  'name': 'barbell_stepover',
  'value': 16,
}),
  17: dict({
  'name': 'barbell_step_up',
  'value': 17,
}),
  18: dict({
  'name': 'bench_squat_with_rotational_chop',
  'value': 18,
}),
  19: dict({
  'name': 'weighted_bench_squat_with_rotational_chop',
  'value': 19,
}),
  20: dict({
  'name': 'body_weight_wall_squat',
  'value': 20,
}),
  21: dict({
  'name': 'weighted_wall_squat',
  'value': 21,
}),
  22: dict({
  'name': 'box_step_squat',
  'value': 22,
}),
  23: dict({
  'name': 'weighted_box_step_squat',
  'value': 23,
}),
  24: dict({
  'name': 'braced_squat',
  'value': 24,
}),
  25: dict({
  'name': 'crossed_arm_barbell_front_squat',
  'value': 25,
}),
  26: dict({
  'name': 'crossover_dumbbell_step_up',
  'value': 26,
}),
  27: dict({
  'name': 'dumbbell_front_squat',
  'value': 27,
}),
  28: dict({
  'name': 'dumbbell_split_squat',
  'value': 28,
}),
  29: dict({
  'name': 'dumbbell_squat',
  'value': 29,
}),
  30: dict({
  'name': 'dumbbell_squat_clean',
  'value': 30,
}),
  31: dict({
  'name': 'dumbbell_stepover',
  'value': 31,
}),
  32: dict({
  'name': 'dumbbell_step_up',
  'value': 32,
}),
  33: dict({
  'name': 'elevated_single_leg_squat',
  'value': 33,
}),
  34: dict({
  'name': 'weighted_elevated_single_leg_squat',
  'value': 34,
}),
  35: dict({
  'name': 'figure_four_squats',
  'value': 35,
}),
  36: dict({
  'name': 'weighted_figure_four_squats',
  'value': 36,
}),
  37: dict({
  'name': 'goblet_squat',
  'value': 37,
}),
  38: dict({
  'name': 'kettlebell_squat',
  'value': 38,
}),
  39: dict({
  'name': 'kettlebell_swing_overhead',
  'value': 39,
}),
  40: dict({
  'name': 'kettlebell_swing_with_flip_to_squat',
  'value': 40,
}),
  41: dict({
  'name': 'lateral_dumbbell_step_up',
  'value': 41,
}),
  42: dict({
  'name': 'one_legged_squat',
  'value': 42,
}),
  43: dict({
  'name': 'overhead_dumbbell_squat',
  'value': 43,
}),
  44: dict({
  'name': 'overhead_squat',
  'value': 44,
}),
  45: dict({
  'name': 'partial_single_leg_squat',
  'value': 45,
}),
  46: dict({
  'name': 'weighted_partial_single_leg_squat',
  'value': 46,
}),
  47: dict({
  'name': 'pistol_squat',
  'value': 47,
}),
  48: dict({
  'name': 'weighted_pistol_squat',
  'value': 48,
}),
  49: dict({
  'name': 'plie_slides',
  'value': 49,
}),
  50: dict({
  'name': 'weighted_plie_slides',
  'value': 50,
}),
  51: dict({
  'name': 'plie_squat',
  'value': 51,
}),
  52: dict({
  'name': 'weighted_plie_squat',
  'value': 52,
}),
  53: dict({
  'name': 'prisoner_squat',
  'value': 53,
}),
  54: dict({
  'name': 'weighted_prisoner_squat',
  'value': 54,
}),
  55: dict({
  'name': 'single_leg_bench_get_up',
  'value': 55,
}),
  56: dict({
  'name': 'weighted_single_leg_bench_get_up',
  'value': 56,
}),
  57: dict({
  'name': 'single_leg_bench_squat',
  'value': 57,
}),
  58: dict({
  'name': 'weighted_single_leg_bench_squat',
  'value': 58,
}),
  59: dict({
  'name': 'single_leg_squat_on_swiss_ball',
  'value': 59,
}),
  60: dict({
  'name': 'weighted_single_leg_squat_on_swiss_ball',
  'value': 60,
}),
  61: dict({
  'name': 'squat',
  'value': 61,
}),
  62: dict({
  'name': 'weighted_squat',
  'value': 62,
}),
  63: dict({
  'name': 'squats_with_band',
  'value': 63,
}),
  64: dict({
  'name': 'staggered_squat',
  'value': 64,
}),
  65: dict({
  'name': 'weighted_staggered_squat',
  'value': 65,
}),
  66: dict({
  'name': 'step_up',
  'value': 66,
}),
  67: dict({
  'name': 'weighted_step_up',
  'value': 67,
}),
  68: dict({
  'name': 'suitcase_squats',
  'value': 68,
}),
  69: dict({
  'name': 'sumo_squat',
  'value': 69,
}),
  70: dict({
  'name': 'sumo_squat_slide_in',
  'value': 70,
}),
  71: dict({
  'name': 'weighted_sumo_squat_slide_in',
  'value': 71,
}),
  72: dict({
  'name': 'sumo_squat_to_high_pull',
  'value': 72,
}),
  73: dict({
  'name': 'sumo_squat_to_stand',
  'value': 73,
}),
  74: dict({
  'name': 'weighted_sumo_squat_to_stand',
  'value': 74,
}),
  75: dict({
  'name': 'sumo_squat_with_rotation',
  'value': 75,
}),
  76: dict({
  'name': 'weighted_sumo_squat_with_rotation',
  'value': 76,
}),
  77: dict({
  'name': 'swiss_ball_body_weight_wall_squat',
  'value': 77,
}),
  78: dict({
  'name': 'weighted_swiss_ball_wall_squat',
  'value': 78,
}),
  79: dict({
  'name': 'thrusters',
  'value': 79,
}),
  80: dict({
  'name': 'uneven_squat',
  'value': 80,
}),
  81: dict({
  'name': 'weighted_uneven_squat',
  'value': 81,
}),
  82: dict({
  'name': 'waist_slimming_squat',
  'value': 82,
}),
  83: dict({
  'name': 'wall_ball',
  'value': 83,
}),
  84: dict({
  'name': 'wide_stance_barbell_squat',
  'value': 84,
}),
  85: dict({
  'name': 'wide_stance_goblet_squat',
  'value': 85,
}),
  86: dict({
  'name': 'zercher_squat',
  'value': 86,
}),
  87: dict({
  'name': 'kbs_overhead',
  'value': 87,
  'comment': 'Deprecated do not use',
}),
  88: dict({
  'name': 'squat_and_side_kick',
  'value': 88,
}),
  89: dict({
  'name': 'squat_jumps_in_n_out',
  'value': 89,
}),
  90: dict({
  'name': 'pilates_plie_squats_parallel_turned_out_flat_and_heels',
  'value': 90,
}),
  91: dict({
  'name': 'releve_straight_leg_and_knee_bent_with_one_leg_variation',
  'value': 91,
}),
}),
}),
  'total_body_exercise_name': dict({
  'name': 'total_body_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'burpee',
  'value': 0,
}),
  1: dict({
  'name': 'weighted_burpee',
  'value': 1,
}),
  2: dict({
  'name': 'burpee_box_jump',
  'value': 2,
}),
  3: dict({
  'name': 'weighted_burpee_box_jump',
  'value': 3,
}),
  4: dict({
  'name': 'high_pull_burpee',
  'value': 4,
}),
  5: dict({
  'name': 'man_makers',
  'value': 5,
}),
  6: dict({
  'name': 'one_arm_burpee',
  'value': 6,
}),
  7: dict({
  'name': 'squat_thrusts',
  'value': 7,
}),
  8: dict({
  'name': 'weighted_squat_thrusts',
  'value': 8,
}),
  9: dict({
  'name': 'squat_plank_push_up',
  'value': 9,
}),
  10: dict({
  'name': 'weighted_squat_plank_push_up',
  'value': 10,
}),
  11: dict({
  'name': 'standing_t_rotation_balance',
  'value': 11,
}),
  12: dict({
  'name': 'weighted_standing_t_rotation_balance',
  'value': 12,
}),
}),
}),
  'triceps_extension_exercise_name': dict({
  'name': 'triceps_extension_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'bench_dip',
  'value': 0,
}),
  1: dict({
  'name': 'weighted_bench_dip',
  'value': 1,
}),
  2: dict({
  'name': 'body_weight_dip',
  'value': 2,
}),
  3: dict({
  'name': 'cable_kickback',
  'value': 3,
}),
  4: dict({
  'name': 'cable_lying_triceps_extension',
  'value': 4,
}),
  5: dict({
  'name': 'cable_overhead_triceps_extension',
  'value': 5,
}),
  6: dict({
  'name': 'dumbbell_kickback',
  'value': 6,
}),
  7: dict({
  'name': 'dumbbell_lying_triceps_extension',
  'value': 7,
}),
  8: dict({
  'name': 'ez_bar_overhead_triceps_extension',
  'value': 8,
}),
  9: dict({
  'name': 'incline_dip',
  'value': 9,
}),
  10: dict({
  'name': 'weighted_incline_dip',
  'value': 10,
}),
  11: dict({
  'name': 'incline_ez_bar_lying_triceps_extension',
  'value': 11,
}),
  12: dict({
  'name': 'lying_dumbbell_pullover_to_extension',
  'value': 12,
}),
  13: dict({
  'name': 'lying_ez_bar_triceps_extension',
  'value': 13,
}),
  14: dict({
  'name': 'lying_triceps_extension_to_close_grip_bench_press',
  'value': 14,
}),
  15: dict({
  'name': 'overhead_dumbbell_triceps_extension',
  'value': 15,
}),
  16: dict({
  'name': 'reclining_triceps_press',
  'value': 16,
}),
  17: dict({
  'name': 'reverse_grip_pressdown',
  'value': 17,
}),
  18: dict({
  'name': 'reverse_grip_triceps_pressdown',
  'value': 18,
}),
  19: dict({
  'name': 'rope_pressdown',
  'value': 19,
}),
  20: dict({
  'name': 'seated_barbell_overhead_triceps_extension',
  'value': 20,
}),
  21: dict({
  'name': 'seated_dumbbell_overhead_triceps_extension',
  'value': 21,
}),
  22: dict({
  'name': 'seated_ez_bar_overhead_triceps_extension',
  'value': 22,
}),
  23: dict({
  'name': 'seated_single_arm_overhead_dumbbell_extension',
  'value': 23,
}),
  24: dict({
  'name': 'single_arm_dumbbell_overhead_triceps_extension',
  'value': 24,
}),
  25: dict({
  'name': 'single_dumbbell_seated_overhead_triceps_extension',
  'value': 25,
}),
  26: dict({
  'name': 'single_leg_bench_dip_and_kick',
  'value': 26,
}),
  27: dict({
  'name': 'weighted_single_leg_bench_dip_and_kick',
  'value': 27,
}),
  28: dict({
  'name': 'single_leg_dip',
  'value': 28,
}),
  29: dict({
  'name': 'weighted_single_leg_dip',
  'value': 29,
}),
  30: dict({
  'name': 'static_lying_triceps_extension',
  'value': 30,
}),
  31: dict({
  'name': 'suspended_dip',
  'value': 31,
}),
  32: dict({
  'name': 'weighted_suspended_dip',
  'value': 32,
}),
  33: dict({
  'name': 'swiss_ball_dumbbell_lying_triceps_extension',
  'value': 33,
}),
  34: dict({
  'name': 'swiss_ball_ez_bar_lying_triceps_extension',
  'value': 34,
}),
  35: dict({
  'name': 'swiss_ball_ez_bar_overhead_triceps_extension',
  'value': 35,
}),
  36: dict({
  'name': 'tabletop_dip',
  'value': 36,
}),
  37: dict({
  'name': 'weighted_tabletop_dip',
  'value': 37,
}),
  38: dict({
  'name': 'triceps_extension_on_floor',
  'value': 38,
}),
  39: dict({
  'name': 'triceps_pressdown',
  'value': 39,
}),
  40: dict({
  'name': 'weighted_dip',
  'value': 40,
}),
}),
}),
  'warm_up_exercise_name': dict({
  'name': 'warm_up_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'quadruped_rocking',
  'value': 0,
}),
  1: dict({
  'name': 'neck_tilts',
  'value': 1,
}),
  2: dict({
  'name': 'ankle_circles',
  'value': 2,
}),
  3: dict({
  'name': 'ankle_dorsiflexion_with_band',
  'value': 3,
}),
  4: dict({
  'name': 'ankle_internal_rotation',
  'value': 4,
}),
  5: dict({
  'name': 'arm_circles',
  'value': 5,
}),
  6: dict({
  'name': 'bent_over_reach_to_sky',
  'value': 6,
}),
  7: dict({
  'name': 'cat_camel',
  'value': 7,
}),
  8: dict({
  'name': 'elbow_to_foot_lunge',
  'value': 8,
}),
  9: dict({
  'name': 'forward_and_backward_leg_swings',
  'value': 9,
}),
  10: dict({
  'name': 'groiners',
  'value': 10,
}),
  11: dict({
  'name': 'inverted_hamstring_stretch',
  'value': 11,
}),
  12: dict({
  'name': 'lateral_duck_under',
  'value': 12,
}),
  13: dict({
  'name': 'neck_rotations',
  'value': 13,
}),
  14: dict({
  'name': 'opposite_arm_and_leg_balance',
  'value': 14,
}),
  15: dict({
  'name': 'reach_roll_and_lift',
  'value': 15,
}),
  16: dict({
  'name': 'scorpion',
  'value': 16,
  'comment': 'Deprecated do not use',
}),
  17: dict({
  'name': 'shoulder_circles',
  'value': 17,
}),
  18: dict({
  'name': 'side_to_side_leg_swings',
  'value': 18,
}),
  19: dict({
  'name': 'sleeper_stretch',
  'value': 19,
}),
  20: dict({
  'name': 'slide_out',
  'value': 20,
}),
  21: dict({
  'name': 'swiss_ball_hip_crossover',
  'value': 21,
}),
  22: dict({
  'name': 'swiss_ball_reach_roll_and_lift',
  'value': 22,
}),
  23: dict({
  'name': 'swiss_ball_windshield_wipers',
  'value': 23,
}),
  24: dict({
  'name': 'thoracic_rotation',
  'value': 24,
}),
  25: dict({
  'name': 'walking_high_kicks',
  'value': 25,
}),
  26: dict({
  'name': 'walking_high_knees',
  'value': 26,
}),
  27: dict({
  'name': 'walking_knee_hugs',
  'value': 27,
}),
  28: dict({
  'name': 'walking_leg_cradles',
  'value': 28,
}),
  29: dict({
  'name': 'walkout',
  'value': 29,
}),
  30: dict({
  'name': 'walkout_from_push_up_position',
  'value': 30,
}),
}),
}),
  'run_exercise_name': dict({
  'name': 'run_exercise_name',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'run',
  'value': 0,
}),
  1: dict({
  'name': 'walk',
  'value': 1,
}),
  2: dict({
  'name': 'jog',
  'value': 2,
}),
  3: dict({
  'name': 'sprint',
  'value': 3,
}),
}),
}),
  'water_type': dict({
  'name': 'water_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'fresh',
  'value': 0,
}),
  1: dict({
  'name': 'salt',
  'value': 1,
}),
  2: dict({
  'name': 'en13319',
  'value': 2,
}),
  3: dict({
  'name': 'custom',
  'value': 3,
}),
}),
}),
  'tissue_model_type': dict({
  'name': 'tissue_model_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'zhl_16c',
  'value': 0,
  'comment': "Buhlmann's decompression algorithm, version C",
}),
}),
}),
  'dive_gas_status': dict({
  'name': 'dive_gas_status',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'disabled',
  'value': 0,
}),
  1: dict({
  'name': 'enabled',
  'value': 1,
}),
  2: dict({
  'name': 'backup_only',
  'value': 2,
}),
}),
}),
  'dive_alarm_type': dict({
  'name': 'dive_alarm_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'depth',
  'value': 0,
}),
  1: dict({
  'name': 'time',
  'value': 1,
}),
}),
}),
  'dive_backlight_mode': dict({
  'name': 'dive_backlight_mode',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'at_depth',
  'value': 0,
}),
  1: dict({
  'name': 'always_on',
  'value': 1,
}),
}),
}),
  'favero_product': dict({
  'name': 'favero_product',
  'base_type': 'uint16',
  'parser': resolve,
  'values': dict({
  10: dict({
  'name': 'assioma_uno',
  'value': 10,
}),
  12: dict({
  'name': 'assioma_duo',
  'value': 12,
}),
}),
}),
  'climb_pro_event': dict({
  'name': 'climb_pro_event',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'approach',
  'value': 0,
}),
  1: dict({
  'name': 'start',
  'value': 1,
}),
  2: dict({
  'name': 'complete',
  'value': 2,
}),
}),
}),
  'tap_sensitivity': dict({
  'name': 'tap_sensitivity',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'high',
  'value': 0,
}),
  1: dict({
  'name': 'medium',
  'value': 1,
}),
  2: dict({
  'name': 'low',
  'value': 2,
}),
}),
}),
  'radar_threat_level_type': dict({
  'name': 'radar_threat_level_type',
  'base_type': 'enum',
  'parser': resolve,
  'values': dict({
  0: dict({
  'name': 'threat_unknown',
  'value': 0,
}),
  1: dict({
  'name': 'threat_none',
  'value': 1,
}),
  2: dict({
  'name': 'threat_approaching',
  'value': 2,
}),
  3: dict({
  'name': 'threat_approaching_fast',
  'value': 3,
}),
}),
}),
})
messages = dict({
  0: dict({
  'name': 'file_id',
  'global_number': 0,
  'group_name': 'Common Messages',
  'fields': dict({
  0: dict({
  'name': 'type',
  'type': 'file',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'manufacturer',
  'type': 'manufacturer',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'product',
  'type': 'uint16',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'favero_product',
  'type': 'favero_product',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'manufacturer',
  'value': 'favero_electronics',
  'def_num': 1,
  'raw_value': 263,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'garmin_product',
  'type': 'garmin_product',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'manufacturer',
  'value': 'garmin',
  'def_num': 1,
  'raw_value': 1,
}),
  dict({
  'name': 'manufacturer',
  'value': 'dynastream',
  'def_num': 1,
  'raw_value': 15,
}),
  dict({
  'name': 'manufacturer',
  'value': 'dynastream_oem',
  'def_num': 1,
  'raw_value': 13,
}),
  dict({
  'name': 'manufacturer',
  'value': 'tacx',
  'def_num': 1,
  'raw_value': 89,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'serial_number',
  'type': 'uint32z',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'time_created',
  'type': 'date_time',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Only set for files that are can be created/erased.',
}),
  5: dict({
  'name': 'number',
  'type': 'uint16',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Only set for files that are not created/erased.',
}),
  8: dict({
  'name': 'product_name',
  'type': 'string',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Optional free form string to indicate the devices name or model',
}),
}),
  'comment': 'Must be first message in file.',
}),
  1: dict({
  'name': 'capabilities',
  'global_number': 1,
  'group_name': 'Device File Messages',
  'fields': dict({
  0: dict({
  'name': 'languages',
  'type': 'uint8z',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Use language_bits_x types where x is index of array.',
}),
  1: dict({
  'name': 'sports',
  'type': 'sport_bits_0',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Use sport_bits_x types where x is index of array.',
}),
  21: dict({
  'name': 'workouts_supported',
  'type': 'workout_capabilities',
  'def_num': 21,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  23: dict({
  'name': 'connectivity_supported',
  'type': 'connectivity_capabilities',
  'def_num': 23,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  2: dict({
  'name': 'device_settings',
  'global_number': 2,
  'group_name': 'Settings File Messages',
  'fields': dict({
  0: dict({
  'name': 'active_time_zone',
  'type': 'uint8',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Index into time zone arrays.',
}),
  1: dict({
  'name': 'utc_offset',
  'type': 'uint32',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Offset from system time. Required to convert timestamp from system time to UTC.',
}),
  2: dict({
  'name': 'time_offset',
  'type': 'uint32',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Offset from system time.',
}),
  4: dict({
  'name': 'time_mode',
  'type': 'time_mode',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Display mode for the time',
}),
  5: dict({
  'name': 'time_zone_offset',
  'type': 'sint8',
  'def_num': 5,
  'scale': 4,
  'offset': None,
  'units': 'hr',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'timezone offset in 1/4 hour increments',
}),
  12: dict({
  'name': 'backlight_mode',
  'type': 'backlight_mode',
  'def_num': 12,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Mode for backlight',
}),
  36: dict({
  'name': 'activity_tracker_enabled',
  'type': 'bool',
  'def_num': 36,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Enabled state of the activity tracker functionality',
}),
  39: dict({
  'name': 'clock_time',
  'type': 'date_time',
  'def_num': 39,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'UTC timestamp used to set the devices clock and date',
}),
  40: dict({
  'name': 'pages_enabled',
  'type': 'uint16',
  'def_num': 40,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Bitfield  to configure enabled screens for each supported loop',
}),
  46: dict({
  'name': 'move_alert_enabled',
  'type': 'bool',
  'def_num': 46,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Enabled state of the move alert',
}),
  47: dict({
  'name': 'date_mode',
  'type': 'date_mode',
  'def_num': 47,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Display mode for the date',
}),
  55: dict({
  'name': 'display_orientation',
  'type': 'display_orientation',
  'def_num': 55,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  56: dict({
  'name': 'mounting_side',
  'type': 'side',
  'def_num': 56,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  57: dict({
  'name': 'default_page',
  'type': 'uint16',
  'def_num': 57,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Bitfield to indicate one page as default for each supported loop',
}),
  58: dict({
  'name': 'autosync_min_steps',
  'type': 'uint16',
  'def_num': 58,
  'scale': None,
  'offset': None,
  'units': 'steps',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Minimum steps before an autosync can occur',
}),
  59: dict({
  'name': 'autosync_min_time',
  'type': 'uint16',
  'def_num': 59,
  'scale': None,
  'offset': None,
  'units': 'minutes',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Minimum minutes before an autosync can occur',
}),
  80: dict({
  'name': 'lactate_threshold_autodetect_enabled',
  'type': 'bool',
  'def_num': 80,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Enable auto-detect setting for the lactate threshold feature.',
}),
  86: dict({
  'name': 'ble_auto_upload_enabled',
  'type': 'bool',
  'def_num': 86,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Automatically upload using BLE',
}),
  89: dict({
  'name': 'auto_sync_frequency',
  'type': 'auto_sync_frequency',
  'def_num': 89,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Helps to conserve battery by changing modes',
}),
  90: dict({
  'name': 'auto_activity_detect',
  'type': 'auto_activity_detect',
  'def_num': 90,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Allows setting specific activities auto-activity detect enabled/disabled settings',
}),
  94: dict({
  'name': 'number_of_screens',
  'type': 'uint8',
  'def_num': 94,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Number of screens configured to display',
}),
  95: dict({
  'name': 'smart_notification_display_orientation',
  'type': 'display_orientation',
  'def_num': 95,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Smart Notification display orientation',
}),
  134: dict({
  'name': 'tap_interface',
  'type': 'switch',
  'def_num': 134,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  174: dict({
  'name': 'tap_sensitivity',
  'type': 'tap_sensitivity',
  'def_num': 174,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Used to hold the tap threshold setting',
}),
}),
  'comment': None,
}),
  3: dict({
  'name': 'user_profile',
  'global_number': 3,
  'group_name': 'Settings File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'friendly_name',
  'type': 'string',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'gender',
  'type': 'gender',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'age',
  'type': 'uint8',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'years',
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'height',
  'type': 'uint8',
  'def_num': 3,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'weight',
  'type': 'uint16',
  'def_num': 4,
  'scale': 10,
  'offset': None,
  'units': 'kg',
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'language',
  'type': 'language',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'elev_setting',
  'type': 'display_measure',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'weight_setting',
  'type': 'display_measure',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'resting_heart_rate',
  'type': 'uint8',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'default_max_running_heart_rate',
  'type': 'uint8',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'default_max_biking_heart_rate',
  'type': 'uint8',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'default_max_heart_rate',
  'type': 'uint8',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  12: dict({
  'name': 'hr_setting',
  'type': 'display_heart',
  'def_num': 12,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  13: dict({
  'name': 'speed_setting',
  'type': 'display_measure',
  'def_num': 13,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  14: dict({
  'name': 'dist_setting',
  'type': 'display_measure',
  'def_num': 14,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  16: dict({
  'name': 'power_setting',
  'type': 'display_power',
  'def_num': 16,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  17: dict({
  'name': 'activity_class',
  'type': 'activity_class',
  'def_num': 17,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  18: dict({
  'name': 'position_setting',
  'type': 'display_position',
  'def_num': 18,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  21: dict({
  'name': 'temperature_setting',
  'type': 'display_measure',
  'def_num': 21,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  22: dict({
  'name': 'local_id',
  'type': 'user_local_id',
  'def_num': 22,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  23: dict({
  'name': 'global_id',
  'type': 'byte',
  'def_num': 23,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  28: dict({
  'name': 'wake_time',
  'type': 'localtime_into_day',
  'def_num': 28,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Typical wake time',
}),
  29: dict({
  'name': 'sleep_time',
  'type': 'localtime_into_day',
  'def_num': 29,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Typical bed time',
}),
  30: dict({
  'name': 'height_setting',
  'type': 'display_measure',
  'def_num': 30,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  31: dict({
  'name': 'user_running_step_length',
  'type': 'uint16',
  'def_num': 31,
  'scale': 1000,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'User defined running step length set to 0 for auto length',
}),
  32: dict({
  'name': 'user_walking_step_length',
  'type': 'uint16',
  'def_num': 32,
  'scale': 1000,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'User defined walking step length set to 0 for auto length',
}),
  47: dict({
  'name': 'depth_setting',
  'type': 'display_measure',
  'def_num': 47,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  49: dict({
  'name': 'dive_count',
  'type': 'uint32',
  'def_num': 49,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  4: dict({
  'name': 'hrm_profile',
  'global_number': 4,
  'group_name': 'Settings File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'enabled',
  'type': 'bool',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'hrm_ant_id',
  'type': 'uint16z',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'log_hrv',
  'type': 'bool',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'hrm_ant_id_trans_type',
  'type': 'uint8z',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  5: dict({
  'name': 'sdm_profile',
  'global_number': 5,
  'group_name': 'Settings File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'enabled',
  'type': 'bool',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'sdm_ant_id',
  'type': 'uint16z',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'sdm_cal_factor',
  'type': 'uint16',
  'def_num': 2,
  'scale': 10,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'odometer',
  'type': 'uint32',
  'def_num': 3,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'speed_source',
  'type': 'bool',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Use footpod for speed source instead of GPS',
}),
  5: dict({
  'name': 'sdm_ant_id_trans_type',
  'type': 'uint8z',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'odometer_rollover',
  'type': 'uint8',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Rollover counter that can be used to extend the odometer',
}),
}),
  'comment': None,
}),
  6: dict({
  'name': 'bike_profile',
  'global_number': 6,
  'group_name': 'Settings File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'name',
  'type': 'string',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'sport',
  'type': 'sport',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'sub_sport',
  'type': 'sub_sport',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'odometer',
  'type': 'uint32',
  'def_num': 3,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'bike_spd_ant_id',
  'type': 'uint16z',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'bike_cad_ant_id',
  'type': 'uint16z',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'bike_spdcad_ant_id',
  'type': 'uint16z',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'bike_power_ant_id',
  'type': 'uint16z',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'custom_wheelsize',
  'type': 'uint16',
  'def_num': 8,
  'scale': 1000,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'auto_wheelsize',
  'type': 'uint16',
  'def_num': 9,
  'scale': 1000,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'bike_weight',
  'type': 'uint16',
  'def_num': 10,
  'scale': 10,
  'offset': None,
  'units': 'kg',
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'power_cal_factor',
  'type': 'uint16',
  'def_num': 11,
  'scale': 10,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  12: dict({
  'name': 'auto_wheel_cal',
  'type': 'bool',
  'def_num': 12,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  13: dict({
  'name': 'auto_power_zero',
  'type': 'bool',
  'def_num': 13,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  14: dict({
  'name': 'id',
  'type': 'uint8',
  'def_num': 14,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  15: dict({
  'name': 'spd_enabled',
  'type': 'bool',
  'def_num': 15,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  16: dict({
  'name': 'cad_enabled',
  'type': 'bool',
  'def_num': 16,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  17: dict({
  'name': 'spdcad_enabled',
  'type': 'bool',
  'def_num': 17,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  18: dict({
  'name': 'power_enabled',
  'type': 'bool',
  'def_num': 18,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  19: dict({
  'name': 'crank_length',
  'type': 'uint8',
  'def_num': 19,
  'scale': 2,
  'offset': '-110',
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
}),
  20: dict({
  'name': 'enabled',
  'type': 'bool',
  'def_num': 20,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  21: dict({
  'name': 'bike_spd_ant_id_trans_type',
  'type': 'uint8z',
  'def_num': 21,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  22: dict({
  'name': 'bike_cad_ant_id_trans_type',
  'type': 'uint8z',
  'def_num': 22,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  23: dict({
  'name': 'bike_spdcad_ant_id_trans_type',
  'type': 'uint8z',
  'def_num': 23,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  24: dict({
  'name': 'bike_power_ant_id_trans_type',
  'type': 'uint8z',
  'def_num': 24,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  37: dict({
  'name': 'odometer_rollover',
  'type': 'uint8',
  'def_num': 37,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Rollover counter that can be used to extend the odometer',
}),
  38: dict({
  'name': 'front_gear_num',
  'type': 'uint8z',
  'def_num': 38,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Number of front gears',
}),
  39: dict({
  'name': 'front_gear',
  'type': 'uint8z',
  'def_num': 39,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Number of teeth on each gear 0 is innermost',
}),
  40: dict({
  'name': 'rear_gear_num',
  'type': 'uint8z',
  'def_num': 40,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Number of rear gears',
}),
  41: dict({
  'name': 'rear_gear',
  'type': 'uint8z',
  'def_num': 41,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Number of teeth on each gear 0 is innermost',
}),
  44: dict({
  'name': 'shimano_di2_enabled',
  'type': 'bool',
  'def_num': 44,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  7: dict({
  'name': 'zones_target',
  'global_number': 7,
  'group_name': 'Sport Settings File Messages',
  'fields': dict({
  1: dict({
  'name': 'max_heart_rate',
  'type': 'uint8',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'threshold_heart_rate',
  'type': 'uint8',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'functional_threshold_power',
  'type': 'uint16',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'hr_calc_type',
  'type': 'hr_zone_calc',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'pwr_calc_type',
  'type': 'pwr_zone_calc',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  8: dict({
  'name': 'hr_zone',
  'global_number': 8,
  'group_name': 'Sport Settings File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'high_bpm',
  'type': 'uint8',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'name',
  'type': 'string',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  9: dict({
  'name': 'power_zone',
  'global_number': 9,
  'group_name': 'Sport Settings File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'high_value',
  'type': 'uint16',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'name',
  'type': 'string',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  10: dict({
  'name': 'met_zone',
  'global_number': 10,
  'group_name': 'Sport Settings File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'high_bpm',
  'type': 'uint8',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'calories',
  'type': 'uint16',
  'def_num': 2,
  'scale': 10,
  'offset': None,
  'units': 'kcal/min',
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'fat_calories',
  'type': 'uint8',
  'def_num': 3,
  'scale': 10,
  'offset': None,
  'units': 'kcal/min',
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  12: dict({
  'name': 'sport',
  'global_number': 12,
  'group_name': 'Sport Settings File Messages',
  'fields': dict({
  0: dict({
  'name': 'sport',
  'type': 'sport',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'sub_sport',
  'type': 'sub_sport',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'name',
  'type': 'string',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  15: dict({
  'name': 'goal',
  'global_number': 15,
  'group_name': 'Goals File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'sport',
  'type': 'sport',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'sub_sport',
  'type': 'sub_sport',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'start_date',
  'type': 'date_time',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'end_date',
  'type': 'date_time',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'type',
  'type': 'goal',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'value',
  'type': 'uint32',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'repeat',
  'type': 'bool',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'target_value',
  'type': 'uint32',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'recurrence',
  'type': 'goal_recurrence',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'recurrence_value',
  'type': 'uint16',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'enabled',
  'type': 'bool',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'source',
  'type': 'goal_source',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  18: dict({
  'name': 'session',
  'global_number': 18,
  'group_name': 'Activity File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Selected bit is set for the current session.',
}),
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Sesson end time.',
}),
  0: dict({
  'name': 'event',
  'type': 'event',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'session',
}),
  1: dict({
  'name': 'event_type',
  'type': 'event_type',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'stop',
}),
  2: dict({
  'name': 'start_time',
  'type': 'date_time',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'start_position_lat',
  'type': 'sint32',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'start_position_long',
  'type': 'sint32',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'sport',
  'type': 'sport',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'sub_sport',
  'type': 'sub_sport',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'total_elapsed_time',
  'type': 'uint32',
  'def_num': 7,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Time (includes pauses)',
}),
  8: dict({
  'name': 'total_timer_time',
  'type': 'uint32',
  'def_num': 8,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Timer Time (excludes pauses)',
}),
  9: dict({
  'name': 'total_distance',
  'type': 'uint32',
  'def_num': 9,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'total_cycles',
  'type': 'uint32',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': 'cycles',
  'subfields': list([
  dict({
  'name': 'total_strides',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'strides',
  'reference_fields': list([
  dict({
  'name': 'sport',
  'value': 'running',
  'def_num': 5,
  'raw_value': 1,
}),
  dict({
  'name': 'sport',
  'value': 'walking',
  'def_num': 5,
  'raw_value': 11,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'total_strokes',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'strokes',
  'reference_fields': list([
  dict({
  'name': 'sport',
  'value': 'cycling',
  'def_num': 5,
  'raw_value': 2,
}),
  dict({
  'name': 'sport',
  'value': 'swimming',
  'def_num': 5,
  'raw_value': 5,
}),
  dict({
  'name': 'sport',
  'value': 'rowing',
  'def_num': 5,
  'raw_value': 15,
}),
  dict({
  'name': 'sport',
  'value': 'stand_up_paddleboarding',
  'def_num': 5,
  'raw_value': 37,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'total_calories',
  'type': 'uint16',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': 'kcal',
  'subfields': list([
]),
  'components': list([
]),
}),
  13: dict({
  'name': 'total_fat_calories',
  'type': 'uint16',
  'def_num': 13,
  'scale': None,
  'offset': None,
  'units': 'kcal',
  'subfields': list([
]),
  'components': list([
]),
}),
  14: dict({
  'name': 'avg_speed',
  'type': 'uint16',
  'def_num': 14,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'enhanced_avg_speed',
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'bits': 16,
  'accumulate': False,
  'num': 124,
  'bit_offset': 0,
}),
]),
  'comment': 'total_distance / total_timer_time',
}),
  15: dict({
  'name': 'max_speed',
  'type': 'uint16',
  'def_num': 15,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'enhanced_max_speed',
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'bits': 16,
  'accumulate': False,
  'num': 125,
  'bit_offset': 0,
}),
]),
}),
  16: dict({
  'name': 'avg_heart_rate',
  'type': 'uint8',
  'def_num': 16,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'average heart rate (excludes pause time)',
}),
  17: dict({
  'name': 'max_heart_rate',
  'type': 'uint8',
  'def_num': 17,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  18: dict({
  'name': 'avg_cadence',
  'type': 'uint8',
  'def_num': 18,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
  dict({
  'name': 'avg_running_cadence',
  'type': 'uint8',
  'scale': None,
  'offset': None,
  'units': 'strides/min',
  'reference_fields': list([
  dict({
  'name': 'sport',
  'value': 'running',
  'def_num': 5,
  'raw_value': 1,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
  'comment': 'total_cycles / total_timer_time if non_zero_avg_cadence otherwise total_cycles / total_elapsed_time',
}),
  19: dict({
  'name': 'max_cadence',
  'type': 'uint8',
  'def_num': 19,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
  dict({
  'name': 'max_running_cadence',
  'type': 'uint8',
  'scale': None,
  'offset': None,
  'units': 'strides/min',
  'reference_fields': list([
  dict({
  'name': 'sport',
  'value': 'running',
  'def_num': 5,
  'raw_value': 1,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
  20: dict({
  'name': 'avg_power',
  'type': 'uint16',
  'def_num': 20,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'total_power / total_timer_time if non_zero_avg_power otherwise total_power / total_elapsed_time',
}),
  21: dict({
  'name': 'max_power',
  'type': 'uint16',
  'def_num': 21,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
}),
  22: dict({
  'name': 'total_ascent',
  'type': 'uint16',
  'def_num': 22,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  23: dict({
  'name': 'total_descent',
  'type': 'uint16',
  'def_num': 23,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  24: dict({
  'name': 'total_training_effect',
  'type': 'uint8',
  'def_num': 24,
  'scale': 10,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  25: dict({
  'name': 'first_lap_index',
  'type': 'uint16',
  'def_num': 25,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  26: dict({
  'name': 'num_laps',
  'type': 'uint16',
  'def_num': 26,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  27: dict({
  'name': 'event_group',
  'type': 'uint8',
  'def_num': 27,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  28: dict({
  'name': 'trigger',
  'type': 'session_trigger',
  'def_num': 28,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  29: dict({
  'name': 'nec_lat',
  'type': 'sint32',
  'def_num': 29,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'North east corner latitude',
}),
  30: dict({
  'name': 'nec_long',
  'type': 'sint32',
  'def_num': 30,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'North east corner longitude',
}),
  31: dict({
  'name': 'swc_lat',
  'type': 'sint32',
  'def_num': 31,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'South west corner latitude',
}),
  32: dict({
  'name': 'swc_long',
  'type': 'sint32',
  'def_num': 32,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'South west corner longitude',
}),
  33: dict({
  'name': 'num_lengths',
  'type': 'uint16',
  'def_num': 33,
  'scale': None,
  'offset': None,
  'units': 'lengths',
  'subfields': list([
]),
  'components': list([
]),
  'comment': '# of lengths of swim pool',
}),
  34: dict({
  'name': 'normalized_power',
  'type': 'uint16',
  'def_num': 34,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
}),
  35: dict({
  'name': 'training_stress_score',
  'type': 'uint16',
  'def_num': 35,
  'scale': 10,
  'offset': None,
  'units': 'tss',
  'subfields': list([
]),
  'components': list([
]),
}),
  36: dict({
  'name': 'intensity_factor',
  'type': 'uint16',
  'def_num': 36,
  'scale': 1000,
  'offset': None,
  'units': 'if',
  'subfields': list([
]),
  'components': list([
]),
}),
  37: dict({
  'name': 'left_right_balance',
  'type': 'left_right_balance_100',
  'def_num': 37,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  41: dict({
  'name': 'avg_stroke_count',
  'type': 'uint32',
  'def_num': 41,
  'scale': 10,
  'offset': None,
  'units': 'strokes/lap',
  'subfields': list([
]),
  'components': list([
]),
}),
  42: dict({
  'name': 'avg_stroke_distance',
  'type': 'uint16',
  'def_num': 42,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  43: dict({
  'name': 'swim_stroke',
  'type': 'swim_stroke',
  'def_num': 43,
  'scale': None,
  'offset': None,
  'units': 'swim_stroke',
  'subfields': list([
]),
  'components': list([
]),
}),
  44: dict({
  'name': 'pool_length',
  'type': 'uint16',
  'def_num': 44,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  45: dict({
  'name': 'threshold_power',
  'type': 'uint16',
  'def_num': 45,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
}),
  46: dict({
  'name': 'pool_length_unit',
  'type': 'display_measure',
  'def_num': 46,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  47: dict({
  'name': 'num_active_lengths',
  'type': 'uint16',
  'def_num': 47,
  'scale': None,
  'offset': None,
  'units': 'lengths',
  'subfields': list([
]),
  'components': list([
]),
  'comment': '# of active lengths of swim pool',
}),
  48: dict({
  'name': 'total_work',
  'type': 'uint32',
  'def_num': 48,
  'scale': None,
  'offset': None,
  'units': 'J',
  'subfields': list([
]),
  'components': list([
]),
}),
  49: dict({
  'name': 'avg_altitude',
  'type': 'uint16',
  'def_num': 49,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'enhanced_avg_altitude',
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'bits': 16,
  'accumulate': False,
  'num': 126,
  'bit_offset': 0,
}),
]),
}),
  50: dict({
  'name': 'max_altitude',
  'type': 'uint16',
  'def_num': 50,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'enhanced_max_altitude',
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'bits': 16,
  'accumulate': False,
  'num': 128,
  'bit_offset': 0,
}),
]),
}),
  51: dict({
  'name': 'gps_accuracy',
  'type': 'uint8',
  'def_num': 51,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  52: dict({
  'name': 'avg_grade',
  'type': 'sint16',
  'def_num': 52,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  53: dict({
  'name': 'avg_pos_grade',
  'type': 'sint16',
  'def_num': 53,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  54: dict({
  'name': 'avg_neg_grade',
  'type': 'sint16',
  'def_num': 54,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  55: dict({
  'name': 'max_pos_grade',
  'type': 'sint16',
  'def_num': 55,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  56: dict({
  'name': 'max_neg_grade',
  'type': 'sint16',
  'def_num': 56,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  57: dict({
  'name': 'avg_temperature',
  'type': 'sint8',
  'def_num': 57,
  'scale': None,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
  58: dict({
  'name': 'max_temperature',
  'type': 'sint8',
  'def_num': 58,
  'scale': None,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
  59: dict({
  'name': 'total_moving_time',
  'type': 'uint32',
  'def_num': 59,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  60: dict({
  'name': 'avg_pos_vertical_speed',
  'type': 'sint16',
  'def_num': 60,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  61: dict({
  'name': 'avg_neg_vertical_speed',
  'type': 'sint16',
  'def_num': 61,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  62: dict({
  'name': 'max_pos_vertical_speed',
  'type': 'sint16',
  'def_num': 62,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  63: dict({
  'name': 'max_neg_vertical_speed',
  'type': 'sint16',
  'def_num': 63,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  64: dict({
  'name': 'min_heart_rate',
  'type': 'uint8',
  'def_num': 64,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  65: dict({
  'name': 'time_in_hr_zone',
  'type': 'uint32',
  'def_num': 65,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  66: dict({
  'name': 'time_in_speed_zone',
  'type': 'uint32',
  'def_num': 66,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  67: dict({
  'name': 'time_in_cadence_zone',
  'type': 'uint32',
  'def_num': 67,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  68: dict({
  'name': 'time_in_power_zone',
  'type': 'uint32',
  'def_num': 68,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  69: dict({
  'name': 'avg_lap_time',
  'type': 'uint32',
  'def_num': 69,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  70: dict({
  'name': 'best_lap_index',
  'type': 'uint16',
  'def_num': 70,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  71: dict({
  'name': 'min_altitude',
  'type': 'uint16',
  'def_num': 71,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'enhanced_min_altitude',
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'bits': 16,
  'accumulate': False,
  'num': 127,
  'bit_offset': 0,
}),
]),
}),
  82: dict({
  'name': 'player_score',
  'type': 'uint16',
  'def_num': 82,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  83: dict({
  'name': 'opponent_score',
  'type': 'uint16',
  'def_num': 83,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  84: dict({
  'name': 'opponent_name',
  'type': 'string',
  'def_num': 84,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  85: dict({
  'name': 'stroke_count',
  'type': 'uint16',
  'def_num': 85,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'stroke_type enum used as the index',
}),
  86: dict({
  'name': 'zone_count',
  'type': 'uint16',
  'def_num': 86,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'zone number used as the index',
}),
  87: dict({
  'name': 'max_ball_speed',
  'type': 'uint16',
  'def_num': 87,
  'scale': 100,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  88: dict({
  'name': 'avg_ball_speed',
  'type': 'uint16',
  'def_num': 88,
  'scale': 100,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  89: dict({
  'name': 'avg_vertical_oscillation',
  'type': 'uint16',
  'def_num': 89,
  'scale': 10,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
}),
  90: dict({
  'name': 'avg_stance_time_percent',
  'type': 'uint16',
  'def_num': 90,
  'scale': 100,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  91: dict({
  'name': 'avg_stance_time',
  'type': 'uint16',
  'def_num': 91,
  'scale': 10,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
}),
  92: dict({
  'name': 'avg_fractional_cadence',
  'type': 'uint8',
  'def_num': 92,
  'scale': 128,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of the avg_cadence',
}),
  93: dict({
  'name': 'max_fractional_cadence',
  'type': 'uint8',
  'def_num': 93,
  'scale': 128,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of the max_cadence',
}),
  94: dict({
  'name': 'total_fractional_cycles',
  'type': 'uint8',
  'def_num': 94,
  'scale': 128,
  'offset': None,
  'units': 'cycles',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of the total_cycles',
}),
  95: dict({
  'name': 'avg_total_hemoglobin_conc',
  'type': 'uint16',
  'def_num': 95,
  'scale': 100,
  'offset': None,
  'units': 'g/dL',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Avg saturated and unsaturated hemoglobin',
}),
  96: dict({
  'name': 'min_total_hemoglobin_conc',
  'type': 'uint16',
  'def_num': 96,
  'scale': 100,
  'offset': None,
  'units': 'g/dL',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Min saturated and unsaturated hemoglobin',
}),
  97: dict({
  'name': 'max_total_hemoglobin_conc',
  'type': 'uint16',
  'def_num': 97,
  'scale': 100,
  'offset': None,
  'units': 'g/dL',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Max saturated and unsaturated hemoglobin',
}),
  98: dict({
  'name': 'avg_saturated_hemoglobin_percent',
  'type': 'uint16',
  'def_num': 98,
  'scale': 10,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Avg percentage of hemoglobin saturated with oxygen',
}),
  99: dict({
  'name': 'min_saturated_hemoglobin_percent',
  'type': 'uint16',
  'def_num': 99,
  'scale': 10,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Min percentage of hemoglobin saturated with oxygen',
}),
  100: dict({
  'name': 'max_saturated_hemoglobin_percent',
  'type': 'uint16',
  'def_num': 100,
  'scale': 10,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Max percentage of hemoglobin saturated with oxygen',
}),
  101: dict({
  'name': 'avg_left_torque_effectiveness',
  'type': 'uint8',
  'def_num': 101,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  102: dict({
  'name': 'avg_right_torque_effectiveness',
  'type': 'uint8',
  'def_num': 102,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  103: dict({
  'name': 'avg_left_pedal_smoothness',
  'type': 'uint8',
  'def_num': 103,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  104: dict({
  'name': 'avg_right_pedal_smoothness',
  'type': 'uint8',
  'def_num': 104,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  105: dict({
  'name': 'avg_combined_pedal_smoothness',
  'type': 'uint8',
  'def_num': 105,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  111: dict({
  'name': 'sport_index',
  'type': 'uint8',
  'def_num': 111,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  112: dict({
  'name': 'time_standing',
  'type': 'uint32',
  'def_num': 112,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Total time spend in the standing position',
}),
  113: dict({
  'name': 'stand_count',
  'type': 'uint16',
  'def_num': 113,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Number of transitions to the standing state',
}),
  114: dict({
  'name': 'avg_left_pco',
  'type': 'sint8',
  'def_num': 114,
  'scale': None,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average platform center offset Left',
}),
  115: dict({
  'name': 'avg_right_pco',
  'type': 'sint8',
  'def_num': 115,
  'scale': None,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average platform center offset Right',
}),
  116: dict({
  'name': 'avg_left_power_phase',
  'type': 'uint8',
  'def_num': 116,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average left power phase angles. Indexes defined by power_phase_type.',
}),
  117: dict({
  'name': 'avg_left_power_phase_peak',
  'type': 'uint8',
  'def_num': 117,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average left power phase peak angles. Data value indexes defined by power_phase_type.',
}),
  118: dict({
  'name': 'avg_right_power_phase',
  'type': 'uint8',
  'def_num': 118,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average right power phase angles. Data value indexes defined by power_phase_type.',
}),
  119: dict({
  'name': 'avg_right_power_phase_peak',
  'type': 'uint8',
  'def_num': 119,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average right power phase peak angles data value indexes  defined by power_phase_type.',
}),
  120: dict({
  'name': 'avg_power_position',
  'type': 'uint16',
  'def_num': 120,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average power by position. Data value indexes defined by rider_position_type.',
}),
  121: dict({
  'name': 'max_power_position',
  'type': 'uint16',
  'def_num': 121,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Maximum power by position. Data value indexes defined by rider_position_type.',
}),
  122: dict({
  'name': 'avg_cadence_position',
  'type': 'uint8',
  'def_num': 122,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average cadence by position. Data value indexes defined by rider_position_type.',
}),
  123: dict({
  'name': 'max_cadence_position',
  'type': 'uint8',
  'def_num': 123,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Maximum cadence by position. Data value indexes defined by rider_position_type.',
}),
  124: dict({
  'name': 'enhanced_avg_speed',
  'type': 'uint32',
  'def_num': 124,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'total_distance / total_timer_time',
}),
  125: dict({
  'name': 'enhanced_max_speed',
  'type': 'uint32',
  'def_num': 125,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  126: dict({
  'name': 'enhanced_avg_altitude',
  'type': 'uint32',
  'def_num': 126,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  127: dict({
  'name': 'enhanced_min_altitude',
  'type': 'uint32',
  'def_num': 127,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  128: dict({
  'name': 'enhanced_max_altitude',
  'type': 'uint32',
  'def_num': 128,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  129: dict({
  'name': 'avg_lev_motor_power',
  'type': 'uint16',
  'def_num': 129,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'lev average motor power during session',
}),
  130: dict({
  'name': 'max_lev_motor_power',
  'type': 'uint16',
  'def_num': 130,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'lev maximum motor power during session',
}),
  131: dict({
  'name': 'lev_battery_consumption',
  'type': 'uint8',
  'def_num': 131,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'lev battery consumption during session',
}),
  132: dict({
  'name': 'avg_vertical_ratio',
  'type': 'uint16',
  'def_num': 132,
  'scale': 100,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  133: dict({
  'name': 'avg_stance_time_balance',
  'type': 'uint16',
  'def_num': 133,
  'scale': 100,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  134: dict({
  'name': 'avg_step_length',
  'type': 'uint16',
  'def_num': 134,
  'scale': 10,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
}),
  137: dict({
  'name': 'total_anaerobic_training_effect',
  'type': 'uint8',
  'def_num': 137,
  'scale': 10,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  139: dict({
  'name': 'avg_vam',
  'type': 'uint16',
  'def_num': 139,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  181: dict({
  'name': 'total_grit',
  'type': 'float32',
  'def_num': 181,
  'scale': None,
  'offset': None,
  'units': 'kGrit',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
}),
  182: dict({
  'name': 'total_flow',
  'type': 'float32',
  'def_num': 182,
  'scale': None,
  'offset': None,
  'units': 'Flow',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
}),
  183: dict({
  'name': 'jump_count',
  'type': 'uint16',
  'def_num': 183,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  186: dict({
  'name': 'avg_grit',
  'type': 'float32',
  'def_num': 186,
  'scale': None,
  'offset': None,
  'units': 'kGrit',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
}),
  187: dict({
  'name': 'avg_flow',
  'type': 'float32',
  'def_num': 187,
  'scale': None,
  'offset': None,
  'units': 'Flow',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
}),
  199: dict({
  'name': 'total_fractional_ascent',
  'type': 'uint8',
  'def_num': 199,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of total_ascent',
}),
  200: dict({
  'name': 'total_fractional_descent',
  'type': 'uint8',
  'def_num': 200,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of total_descent',
}),
  208: dict({
  'name': 'avg_core_temperature',
  'type': 'uint16',
  'def_num': 208,
  'scale': 100,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
  209: dict({
  'name': 'min_core_temperature',
  'type': 'uint16',
  'def_num': 209,
  'scale': 100,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
  210: dict({
  'name': 'max_core_temperature',
  'type': 'uint16',
  'def_num': 210,
  'scale': 100,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  19: dict({
  'name': 'lap',
  'global_number': 19,
  'group_name': 'Activity File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Lap end time.',
}),
  0: dict({
  'name': 'event',
  'type': 'event',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'event_type',
  'type': 'event_type',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'start_time',
  'type': 'date_time',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'start_position_lat',
  'type': 'sint32',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'start_position_long',
  'type': 'sint32',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'end_position_lat',
  'type': 'sint32',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'end_position_long',
  'type': 'sint32',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'total_elapsed_time',
  'type': 'uint32',
  'def_num': 7,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Time (includes pauses)',
}),
  8: dict({
  'name': 'total_timer_time',
  'type': 'uint32',
  'def_num': 8,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Timer Time (excludes pauses)',
}),
  9: dict({
  'name': 'total_distance',
  'type': 'uint32',
  'def_num': 9,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'total_cycles',
  'type': 'uint32',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': 'cycles',
  'subfields': list([
  dict({
  'name': 'total_strides',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'strides',
  'reference_fields': list([
  dict({
  'name': 'sport',
  'value': 'running',
  'def_num': 25,
  'raw_value': 1,
}),
  dict({
  'name': 'sport',
  'value': 'walking',
  'def_num': 25,
  'raw_value': 11,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'total_strokes',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'strokes',
  'reference_fields': list([
  dict({
  'name': 'sport',
  'value': 'cycling',
  'def_num': 25,
  'raw_value': 2,
}),
  dict({
  'name': 'sport',
  'value': 'swimming',
  'def_num': 25,
  'raw_value': 5,
}),
  dict({
  'name': 'sport',
  'value': 'rowing',
  'def_num': 25,
  'raw_value': 15,
}),
  dict({
  'name': 'sport',
  'value': 'stand_up_paddleboarding',
  'def_num': 25,
  'raw_value': 37,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'total_calories',
  'type': 'uint16',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': 'kcal',
  'subfields': list([
]),
  'components': list([
]),
}),
  12: dict({
  'name': 'total_fat_calories',
  'type': 'uint16',
  'def_num': 12,
  'scale': None,
  'offset': None,
  'units': 'kcal',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'If New Leaf',
}),
  13: dict({
  'name': 'avg_speed',
  'type': 'uint16',
  'def_num': 13,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'enhanced_avg_speed',
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'bits': 16,
  'accumulate': False,
  'num': 110,
  'bit_offset': 0,
}),
]),
}),
  14: dict({
  'name': 'max_speed',
  'type': 'uint16',
  'def_num': 14,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'enhanced_max_speed',
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'bits': 16,
  'accumulate': False,
  'num': 111,
  'bit_offset': 0,
}),
]),
}),
  15: dict({
  'name': 'avg_heart_rate',
  'type': 'uint8',
  'def_num': 15,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  16: dict({
  'name': 'max_heart_rate',
  'type': 'uint8',
  'def_num': 16,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  17: dict({
  'name': 'avg_cadence',
  'type': 'uint8',
  'def_num': 17,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
  dict({
  'name': 'avg_running_cadence',
  'type': 'uint8',
  'scale': None,
  'offset': None,
  'units': 'strides/min',
  'reference_fields': list([
  dict({
  'name': 'sport',
  'value': 'running',
  'def_num': 25,
  'raw_value': 1,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
  'comment': 'total_cycles / total_timer_time if non_zero_avg_cadence otherwise total_cycles / total_elapsed_time',
}),
  18: dict({
  'name': 'max_cadence',
  'type': 'uint8',
  'def_num': 18,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
  dict({
  'name': 'max_running_cadence',
  'type': 'uint8',
  'scale': None,
  'offset': None,
  'units': 'strides/min',
  'reference_fields': list([
  dict({
  'name': 'sport',
  'value': 'running',
  'def_num': 25,
  'raw_value': 1,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
  19: dict({
  'name': 'avg_power',
  'type': 'uint16',
  'def_num': 19,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'total_power / total_timer_time if non_zero_avg_power otherwise total_power / total_elapsed_time',
}),
  20: dict({
  'name': 'max_power',
  'type': 'uint16',
  'def_num': 20,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
}),
  21: dict({
  'name': 'total_ascent',
  'type': 'uint16',
  'def_num': 21,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  22: dict({
  'name': 'total_descent',
  'type': 'uint16',
  'def_num': 22,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  23: dict({
  'name': 'intensity',
  'type': 'intensity',
  'def_num': 23,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  24: dict({
  'name': 'lap_trigger',
  'type': 'lap_trigger',
  'def_num': 24,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  25: dict({
  'name': 'sport',
  'type': 'sport',
  'def_num': 25,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  26: dict({
  'name': 'event_group',
  'type': 'uint8',
  'def_num': 26,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  32: dict({
  'name': 'num_lengths',
  'type': 'uint16',
  'def_num': 32,
  'scale': None,
  'offset': None,
  'units': 'lengths',
  'subfields': list([
]),
  'components': list([
]),
  'comment': '# of lengths of swim pool',
}),
  33: dict({
  'name': 'normalized_power',
  'type': 'uint16',
  'def_num': 33,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
}),
  34: dict({
  'name': 'left_right_balance',
  'type': 'left_right_balance_100',
  'def_num': 34,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  35: dict({
  'name': 'first_length_index',
  'type': 'uint16',
  'def_num': 35,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  37: dict({
  'name': 'avg_stroke_distance',
  'type': 'uint16',
  'def_num': 37,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  38: dict({
  'name': 'swim_stroke',
  'type': 'swim_stroke',
  'def_num': 38,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  39: dict({
  'name': 'sub_sport',
  'type': 'sub_sport',
  'def_num': 39,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  40: dict({
  'name': 'num_active_lengths',
  'type': 'uint16',
  'def_num': 40,
  'scale': None,
  'offset': None,
  'units': 'lengths',
  'subfields': list([
]),
  'components': list([
]),
  'comment': '# of active lengths of swim pool',
}),
  41: dict({
  'name': 'total_work',
  'type': 'uint32',
  'def_num': 41,
  'scale': None,
  'offset': None,
  'units': 'J',
  'subfields': list([
]),
  'components': list([
]),
}),
  42: dict({
  'name': 'avg_altitude',
  'type': 'uint16',
  'def_num': 42,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'enhanced_avg_altitude',
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'bits': 16,
  'accumulate': False,
  'num': 112,
  'bit_offset': 0,
}),
]),
}),
  43: dict({
  'name': 'max_altitude',
  'type': 'uint16',
  'def_num': 43,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'enhanced_max_altitude',
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'bits': 16,
  'accumulate': False,
  'num': 114,
  'bit_offset': 0,
}),
]),
}),
  44: dict({
  'name': 'gps_accuracy',
  'type': 'uint8',
  'def_num': 44,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  45: dict({
  'name': 'avg_grade',
  'type': 'sint16',
  'def_num': 45,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  46: dict({
  'name': 'avg_pos_grade',
  'type': 'sint16',
  'def_num': 46,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  47: dict({
  'name': 'avg_neg_grade',
  'type': 'sint16',
  'def_num': 47,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  48: dict({
  'name': 'max_pos_grade',
  'type': 'sint16',
  'def_num': 48,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  49: dict({
  'name': 'max_neg_grade',
  'type': 'sint16',
  'def_num': 49,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  50: dict({
  'name': 'avg_temperature',
  'type': 'sint8',
  'def_num': 50,
  'scale': None,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
  51: dict({
  'name': 'max_temperature',
  'type': 'sint8',
  'def_num': 51,
  'scale': None,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
  52: dict({
  'name': 'total_moving_time',
  'type': 'uint32',
  'def_num': 52,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  53: dict({
  'name': 'avg_pos_vertical_speed',
  'type': 'sint16',
  'def_num': 53,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  54: dict({
  'name': 'avg_neg_vertical_speed',
  'type': 'sint16',
  'def_num': 54,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  55: dict({
  'name': 'max_pos_vertical_speed',
  'type': 'sint16',
  'def_num': 55,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  56: dict({
  'name': 'max_neg_vertical_speed',
  'type': 'sint16',
  'def_num': 56,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  57: dict({
  'name': 'time_in_hr_zone',
  'type': 'uint32',
  'def_num': 57,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  58: dict({
  'name': 'time_in_speed_zone',
  'type': 'uint32',
  'def_num': 58,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  59: dict({
  'name': 'time_in_cadence_zone',
  'type': 'uint32',
  'def_num': 59,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  60: dict({
  'name': 'time_in_power_zone',
  'type': 'uint32',
  'def_num': 60,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  61: dict({
  'name': 'repetition_num',
  'type': 'uint16',
  'def_num': 61,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  62: dict({
  'name': 'min_altitude',
  'type': 'uint16',
  'def_num': 62,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'enhanced_min_altitude',
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'bits': 16,
  'accumulate': False,
  'num': 113,
  'bit_offset': 0,
}),
]),
}),
  63: dict({
  'name': 'min_heart_rate',
  'type': 'uint8',
  'def_num': 63,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  71: dict({
  'name': 'wkt_step_index',
  'type': 'message_index',
  'def_num': 71,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  74: dict({
  'name': 'opponent_score',
  'type': 'uint16',
  'def_num': 74,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  75: dict({
  'name': 'stroke_count',
  'type': 'uint16',
  'def_num': 75,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'stroke_type enum used as the index',
}),
  76: dict({
  'name': 'zone_count',
  'type': 'uint16',
  'def_num': 76,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'zone number used as the index',
}),
  77: dict({
  'name': 'avg_vertical_oscillation',
  'type': 'uint16',
  'def_num': 77,
  'scale': 10,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
}),
  78: dict({
  'name': 'avg_stance_time_percent',
  'type': 'uint16',
  'def_num': 78,
  'scale': 100,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  79: dict({
  'name': 'avg_stance_time',
  'type': 'uint16',
  'def_num': 79,
  'scale': 10,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
}),
  80: dict({
  'name': 'avg_fractional_cadence',
  'type': 'uint8',
  'def_num': 80,
  'scale': 128,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of the avg_cadence',
}),
  81: dict({
  'name': 'max_fractional_cadence',
  'type': 'uint8',
  'def_num': 81,
  'scale': 128,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of the max_cadence',
}),
  82: dict({
  'name': 'total_fractional_cycles',
  'type': 'uint8',
  'def_num': 82,
  'scale': 128,
  'offset': None,
  'units': 'cycles',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of the total_cycles',
}),
  83: dict({
  'name': 'player_score',
  'type': 'uint16',
  'def_num': 83,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  84: dict({
  'name': 'avg_total_hemoglobin_conc',
  'type': 'uint16',
  'def_num': 84,
  'scale': 100,
  'offset': None,
  'units': 'g/dL',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Avg saturated and unsaturated hemoglobin',
}),
  85: dict({
  'name': 'min_total_hemoglobin_conc',
  'type': 'uint16',
  'def_num': 85,
  'scale': 100,
  'offset': None,
  'units': 'g/dL',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Min saturated and unsaturated hemoglobin',
}),
  86: dict({
  'name': 'max_total_hemoglobin_conc',
  'type': 'uint16',
  'def_num': 86,
  'scale': 100,
  'offset': None,
  'units': 'g/dL',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Max saturated and unsaturated hemoglobin',
}),
  87: dict({
  'name': 'avg_saturated_hemoglobin_percent',
  'type': 'uint16',
  'def_num': 87,
  'scale': 10,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Avg percentage of hemoglobin saturated with oxygen',
}),
  88: dict({
  'name': 'min_saturated_hemoglobin_percent',
  'type': 'uint16',
  'def_num': 88,
  'scale': 10,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Min percentage of hemoglobin saturated with oxygen',
}),
  89: dict({
  'name': 'max_saturated_hemoglobin_percent',
  'type': 'uint16',
  'def_num': 89,
  'scale': 10,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Max percentage of hemoglobin saturated with oxygen',
}),
  91: dict({
  'name': 'avg_left_torque_effectiveness',
  'type': 'uint8',
  'def_num': 91,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  92: dict({
  'name': 'avg_right_torque_effectiveness',
  'type': 'uint8',
  'def_num': 92,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  93: dict({
  'name': 'avg_left_pedal_smoothness',
  'type': 'uint8',
  'def_num': 93,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  94: dict({
  'name': 'avg_right_pedal_smoothness',
  'type': 'uint8',
  'def_num': 94,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  95: dict({
  'name': 'avg_combined_pedal_smoothness',
  'type': 'uint8',
  'def_num': 95,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  98: dict({
  'name': 'time_standing',
  'type': 'uint32',
  'def_num': 98,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Total time spent in the standing position',
}),
  99: dict({
  'name': 'stand_count',
  'type': 'uint16',
  'def_num': 99,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Number of transitions to the standing state',
}),
  100: dict({
  'name': 'avg_left_pco',
  'type': 'sint8',
  'def_num': 100,
  'scale': None,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average left platform center offset',
}),
  101: dict({
  'name': 'avg_right_pco',
  'type': 'sint8',
  'def_num': 101,
  'scale': None,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average right platform center offset',
}),
  102: dict({
  'name': 'avg_left_power_phase',
  'type': 'uint8',
  'def_num': 102,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average left power phase angles. Data value indexes defined by power_phase_type.',
}),
  103: dict({
  'name': 'avg_left_power_phase_peak',
  'type': 'uint8',
  'def_num': 103,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average left power phase peak angles. Data value indexes  defined by power_phase_type.',
}),
  104: dict({
  'name': 'avg_right_power_phase',
  'type': 'uint8',
  'def_num': 104,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average right power phase angles. Data value indexes defined by power_phase_type.',
}),
  105: dict({
  'name': 'avg_right_power_phase_peak',
  'type': 'uint8',
  'def_num': 105,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average right power phase peak angles. Data value indexes  defined by power_phase_type.',
}),
  106: dict({
  'name': 'avg_power_position',
  'type': 'uint16',
  'def_num': 106,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average power by position. Data value indexes defined by rider_position_type.',
}),
  107: dict({
  'name': 'max_power_position',
  'type': 'uint16',
  'def_num': 107,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Maximum power by position. Data value indexes defined by rider_position_type.',
}),
  108: dict({
  'name': 'avg_cadence_position',
  'type': 'uint8',
  'def_num': 108,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average cadence by position. Data value indexes defined by rider_position_type.',
}),
  109: dict({
  'name': 'max_cadence_position',
  'type': 'uint8',
  'def_num': 109,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Maximum cadence by position. Data value indexes defined by rider_position_type.',
}),
  110: dict({
  'name': 'enhanced_avg_speed',
  'type': 'uint32',
  'def_num': 110,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  111: dict({
  'name': 'enhanced_max_speed',
  'type': 'uint32',
  'def_num': 111,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  112: dict({
  'name': 'enhanced_avg_altitude',
  'type': 'uint32',
  'def_num': 112,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  113: dict({
  'name': 'enhanced_min_altitude',
  'type': 'uint32',
  'def_num': 113,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  114: dict({
  'name': 'enhanced_max_altitude',
  'type': 'uint32',
  'def_num': 114,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  115: dict({
  'name': 'avg_lev_motor_power',
  'type': 'uint16',
  'def_num': 115,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'lev average motor power during lap',
}),
  116: dict({
  'name': 'max_lev_motor_power',
  'type': 'uint16',
  'def_num': 116,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'lev maximum motor power during lap',
}),
  117: dict({
  'name': 'lev_battery_consumption',
  'type': 'uint8',
  'def_num': 117,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'lev battery consumption during lap',
}),
  118: dict({
  'name': 'avg_vertical_ratio',
  'type': 'uint16',
  'def_num': 118,
  'scale': 100,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  119: dict({
  'name': 'avg_stance_time_balance',
  'type': 'uint16',
  'def_num': 119,
  'scale': 100,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  120: dict({
  'name': 'avg_step_length',
  'type': 'uint16',
  'def_num': 120,
  'scale': 10,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
}),
  121: dict({
  'name': 'avg_vam',
  'type': 'uint16',
  'def_num': 121,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  149: dict({
  'name': 'total_grit',
  'type': 'float32',
  'def_num': 149,
  'scale': None,
  'offset': None,
  'units': 'kGrit',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
}),
  150: dict({
  'name': 'total_flow',
  'type': 'float32',
  'def_num': 150,
  'scale': None,
  'offset': None,
  'units': 'Flow',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
}),
  151: dict({
  'name': 'jump_count',
  'type': 'uint16',
  'def_num': 151,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  153: dict({
  'name': 'avg_grit',
  'type': 'float32',
  'def_num': 153,
  'scale': None,
  'offset': None,
  'units': 'kGrit',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
}),
  154: dict({
  'name': 'avg_flow',
  'type': 'float32',
  'def_num': 154,
  'scale': None,
  'offset': None,
  'units': 'Flow',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
}),
  156: dict({
  'name': 'total_fractional_ascent',
  'type': 'uint8',
  'def_num': 156,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of total_ascent',
}),
  157: dict({
  'name': 'total_fractional_descent',
  'type': 'uint8',
  'def_num': 157,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of total_descent',
}),
  158: dict({
  'name': 'avg_core_temperature',
  'type': 'uint16',
  'def_num': 158,
  'scale': 100,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
  159: dict({
  'name': 'min_core_temperature',
  'type': 'uint16',
  'def_num': 159,
  'scale': 100,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
  160: dict({
  'name': 'max_core_temperature',
  'type': 'uint16',
  'def_num': 160,
  'scale': 100,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  20: dict({
  'name': 'record',
  'global_number': 20,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'position_lat',
  'type': 'sint32',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'position_long',
  'type': 'sint32',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'altitude',
  'type': 'uint16',
  'def_num': 2,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'enhanced_altitude',
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'bits': 16,
  'accumulate': False,
  'num': 78,
  'bit_offset': 0,
}),
]),
}),
  3: dict({
  'name': 'heart_rate',
  'type': 'uint8',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'cadence',
  'type': 'uint8',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'distance',
  'type': 'uint32',
  'def_num': 5,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'speed',
  'type': 'uint16',
  'def_num': 6,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'enhanced_speed',
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'bits': 16,
  'accumulate': False,
  'num': 73,
  'bit_offset': 0,
}),
]),
}),
  7: dict({
  'name': 'power',
  'type': 'uint16',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'compressed_speed_distance',
  'type': 'byte',
  'def_num': 8,
  'scale': '100,\n16',
  'offset': None,
  'units': 'm/s,\nm',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'speed',
  'scale': 100,
  'offset': None,
  'units': 'm/s',
  'bits': 12,
  'accumulate': False,
  'num': 6,
  'bit_offset': 0,
}),
  dict({
  'name': 'distance',
  'scale': 16,
  'offset': None,
  'units': 'm',
  'bits': 12,
  'accumulate': True,
  'num': 5,
  'bit_offset': 12,
}),
]),
}),
  9: dict({
  'name': 'grade',
  'type': 'sint16',
  'def_num': 9,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'resistance',
  'type': 'uint8',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Relative. 0 is none  254 is Max.',
}),
  11: dict({
  'name': 'time_from_course',
  'type': 'sint32',
  'def_num': 11,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  12: dict({
  'name': 'cycle_length',
  'type': 'uint8',
  'def_num': 12,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  13: dict({
  'name': 'temperature',
  'type': 'sint8',
  'def_num': 13,
  'scale': None,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
  17: dict({
  'name': 'speed_1s',
  'type': 'uint8',
  'def_num': 17,
  'scale': 16,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Speed at 1s intervals.  Timestamp field indicates time of last array element.',
}),
  18: dict({
  'name': 'cycles',
  'type': 'uint8',
  'def_num': 18,
  'scale': None,
  'offset': None,
  'units': 'cycles',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'total_cycles',
  'scale': None,
  'offset': None,
  'units': 'cycles',
  'bits': 8,
  'accumulate': True,
  'num': 19,
  'bit_offset': 0,
}),
]),
}),
  19: dict({
  'name': 'total_cycles',
  'type': 'uint32',
  'def_num': 19,
  'scale': None,
  'offset': None,
  'units': 'cycles',
  'subfields': list([
]),
  'components': list([
]),
}),
  28: dict({
  'name': 'compressed_accumulated_power',
  'type': 'uint16',
  'def_num': 28,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'accumulated_power',
  'scale': None,
  'offset': None,
  'units': 'watts',
  'bits': 16,
  'accumulate': True,
  'num': 29,
  'bit_offset': 0,
}),
]),
}),
  29: dict({
  'name': 'accumulated_power',
  'type': 'uint32',
  'def_num': 29,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
}),
  30: dict({
  'name': 'left_right_balance',
  'type': 'left_right_balance',
  'def_num': 30,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  31: dict({
  'name': 'gps_accuracy',
  'type': 'uint8',
  'def_num': 31,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  32: dict({
  'name': 'vertical_speed',
  'type': 'sint16',
  'def_num': 32,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  33: dict({
  'name': 'calories',
  'type': 'uint16',
  'def_num': 33,
  'scale': None,
  'offset': None,
  'units': 'kcal',
  'subfields': list([
]),
  'components': list([
]),
}),
  39: dict({
  'name': 'vertical_oscillation',
  'type': 'uint16',
  'def_num': 39,
  'scale': 10,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
}),
  40: dict({
  'name': 'stance_time_percent',
  'type': 'uint16',
  'def_num': 40,
  'scale': 100,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  41: dict({
  'name': 'stance_time',
  'type': 'uint16',
  'def_num': 41,
  'scale': 10,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
}),
  42: dict({
  'name': 'activity_type',
  'type': 'activity_type',
  'def_num': 42,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  43: dict({
  'name': 'left_torque_effectiveness',
  'type': 'uint8',
  'def_num': 43,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  44: dict({
  'name': 'right_torque_effectiveness',
  'type': 'uint8',
  'def_num': 44,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  45: dict({
  'name': 'left_pedal_smoothness',
  'type': 'uint8',
  'def_num': 45,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  46: dict({
  'name': 'right_pedal_smoothness',
  'type': 'uint8',
  'def_num': 46,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  47: dict({
  'name': 'combined_pedal_smoothness',
  'type': 'uint8',
  'def_num': 47,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  48: dict({
  'name': 'time128',
  'type': 'uint8',
  'def_num': 48,
  'scale': 128,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  49: dict({
  'name': 'stroke_type',
  'type': 'stroke_type',
  'def_num': 49,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  50: dict({
  'name': 'zone',
  'type': 'uint8',
  'def_num': 50,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  51: dict({
  'name': 'ball_speed',
  'type': 'uint16',
  'def_num': 51,
  'scale': 100,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  52: dict({
  'name': 'cadence256',
  'type': 'uint16',
  'def_num': 52,
  'scale': 256,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Log cadence and fractional cadence for backwards compatability',
}),
  53: dict({
  'name': 'fractional_cadence',
  'type': 'uint8',
  'def_num': 53,
  'scale': 128,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  54: dict({
  'name': 'total_hemoglobin_conc',
  'type': 'uint16',
  'def_num': 54,
  'scale': 100,
  'offset': None,
  'units': 'g/dL',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Total saturated and unsaturated hemoglobin',
}),
  55: dict({
  'name': 'total_hemoglobin_conc_min',
  'type': 'uint16',
  'def_num': 55,
  'scale': 100,
  'offset': None,
  'units': 'g/dL',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Min saturated and unsaturated hemoglobin',
}),
  56: dict({
  'name': 'total_hemoglobin_conc_max',
  'type': 'uint16',
  'def_num': 56,
  'scale': 100,
  'offset': None,
  'units': 'g/dL',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Max saturated and unsaturated hemoglobin',
}),
  57: dict({
  'name': 'saturated_hemoglobin_percent',
  'type': 'uint16',
  'def_num': 57,
  'scale': 10,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Percentage of hemoglobin saturated with oxygen',
}),
  58: dict({
  'name': 'saturated_hemoglobin_percent_min',
  'type': 'uint16',
  'def_num': 58,
  'scale': 10,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Min percentage of hemoglobin saturated with oxygen',
}),
  59: dict({
  'name': 'saturated_hemoglobin_percent_max',
  'type': 'uint16',
  'def_num': 59,
  'scale': 10,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Max percentage of hemoglobin saturated with oxygen',
}),
  62: dict({
  'name': 'device_index',
  'type': 'device_index',
  'def_num': 62,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  67: dict({
  'name': 'left_pco',
  'type': 'sint8',
  'def_num': 67,
  'scale': None,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Left platform center offset',
}),
  68: dict({
  'name': 'right_pco',
  'type': 'sint8',
  'def_num': 68,
  'scale': None,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Right platform center offset',
}),
  69: dict({
  'name': 'left_power_phase',
  'type': 'uint8',
  'def_num': 69,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Left power phase angles. Data value indexes defined by power_phase_type.',
}),
  70: dict({
  'name': 'left_power_phase_peak',
  'type': 'uint8',
  'def_num': 70,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Left power phase peak angles. Data value indexes defined by power_phase_type.',
}),
  71: dict({
  'name': 'right_power_phase',
  'type': 'uint8',
  'def_num': 71,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Right power phase angles. Data value indexes defined by power_phase_type.',
}),
  72: dict({
  'name': 'right_power_phase_peak',
  'type': 'uint8',
  'def_num': 72,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Right power phase peak angles. Data value indexes defined by power_phase_type.',
}),
  73: dict({
  'name': 'enhanced_speed',
  'type': 'uint32',
  'def_num': 73,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  78: dict({
  'name': 'enhanced_altitude',
  'type': 'uint32',
  'def_num': 78,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  81: dict({
  'name': 'battery_soc',
  'type': 'uint8',
  'def_num': 81,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'lev battery state of charge',
}),
  82: dict({
  'name': 'motor_power',
  'type': 'uint16',
  'def_num': 82,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'lev motor power',
}),
  83: dict({
  'name': 'vertical_ratio',
  'type': 'uint16',
  'def_num': 83,
  'scale': 100,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  84: dict({
  'name': 'stance_time_balance',
  'type': 'uint16',
  'def_num': 84,
  'scale': 100,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  85: dict({
  'name': 'step_length',
  'type': 'uint16',
  'def_num': 85,
  'scale': 10,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
}),
  91: dict({
  'name': 'absolute_pressure',
  'type': 'uint32',
  'def_num': 91,
  'scale': None,
  'offset': None,
  'units': 'Pa',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Includes atmospheric pressure',
}),
  92: dict({
  'name': 'depth',
  'type': 'uint32',
  'def_num': 92,
  'scale': 1000,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': '0 if above water',
}),
  93: dict({
  'name': 'next_stop_depth',
  'type': 'uint32',
  'def_num': 93,
  'scale': 1000,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': '0 if above water',
}),
  94: dict({
  'name': 'next_stop_time',
  'type': 'uint32',
  'def_num': 94,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  95: dict({
  'name': 'time_to_surface',
  'type': 'uint32',
  'def_num': 95,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  96: dict({
  'name': 'ndl_time',
  'type': 'uint32',
  'def_num': 96,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  97: dict({
  'name': 'cns_load',
  'type': 'uint8',
  'def_num': 97,
  'scale': None,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  98: dict({
  'name': 'n2_load',
  'type': 'uint16',
  'def_num': 98,
  'scale': None,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  114: dict({
  'name': 'grit',
  'type': 'float32',
  'def_num': 114,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
}),
  115: dict({
  'name': 'flow',
  'type': 'float32',
  'def_num': 115,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
}),
  117: dict({
  'name': 'ebike_travel_range',
  'type': 'uint16',
  'def_num': 117,
  'scale': None,
  'offset': None,
  'units': 'km',
  'subfields': list([
]),
  'components': list([
]),
}),
  118: dict({
  'name': 'ebike_battery_level',
  'type': 'uint8',
  'def_num': 118,
  'scale': None,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  119: dict({
  'name': 'ebike_assist_mode',
  'type': 'uint8',
  'def_num': 119,
  'scale': None,
  'offset': None,
  'units': 'depends on sensor',
  'subfields': list([
]),
  'components': list([
]),
}),
  120: dict({
  'name': 'ebike_assist_level_percent',
  'type': 'uint8',
  'def_num': 120,
  'scale': None,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  139: dict({
  'name': 'core_temperature',
  'type': 'uint16',
  'def_num': 139,
  'scale': 100,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  21: dict({
  'name': 'event',
  'global_number': 21,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'event',
  'type': 'event',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'event_type',
  'type': 'event_type',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'data16',
  'type': 'uint16',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 16,
  'accumulate': False,
  'num': 3,
  'bit_offset': 0,
}),
]),
}),
  3: dict({
  'name': 'data',
  'type': 'uint32',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'timer_trigger',
  'type': 'timer_trigger',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'timer',
  'def_num': 0,
  'raw_value': 0,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'course_point_index',
  'type': 'message_index',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'course_point',
  'def_num': 0,
  'raw_value': 10,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'battery_level',
  'type': 'uint16',
  'scale': 1000,
  'offset': None,
  'units': 'V',
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'battery',
  'def_num': 0,
  'raw_value': 11,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'virtual_partner_speed',
  'type': 'uint16',
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'virtual_partner_pace',
  'def_num': 0,
  'raw_value': 12,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'hr_high_alert',
  'type': 'uint8',
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'hr_high_alert',
  'def_num': 0,
  'raw_value': 13,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'hr_low_alert',
  'type': 'uint8',
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'hr_low_alert',
  'def_num': 0,
  'raw_value': 14,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'speed_high_alert',
  'type': 'uint32',
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'speed_high_alert',
  'def_num': 0,
  'raw_value': 15,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'speed_low_alert',
  'type': 'uint32',
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'speed_low_alert',
  'def_num': 0,
  'raw_value': 16,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'cad_high_alert',
  'type': 'uint16',
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'cad_high_alert',
  'def_num': 0,
  'raw_value': 17,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'cad_low_alert',
  'type': 'uint16',
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'cad_low_alert',
  'def_num': 0,
  'raw_value': 18,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'power_high_alert',
  'type': 'uint16',
  'scale': None,
  'offset': None,
  'units': 'watts',
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'power_high_alert',
  'def_num': 0,
  'raw_value': 19,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'power_low_alert',
  'type': 'uint16',
  'scale': None,
  'offset': None,
  'units': 'watts',
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'power_low_alert',
  'def_num': 0,
  'raw_value': 20,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'time_duration_alert',
  'type': 'uint32',
  'scale': 1000,
  'offset': None,
  'units': 's',
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'time_duration_alert',
  'def_num': 0,
  'raw_value': 23,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'distance_duration_alert',
  'type': 'uint32',
  'scale': 100,
  'offset': None,
  'units': 'm',
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'distance_duration_alert',
  'def_num': 0,
  'raw_value': 24,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'calorie_duration_alert',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'calories',
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'calorie_duration_alert',
  'def_num': 0,
  'raw_value': 25,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'fitness_equipment_state',
  'type': 'fitness_equipment_state',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'fitness_equipment',
  'def_num': 0,
  'raw_value': 27,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'sport_point',
  'type': 'uint32',
  'scale': '1,1',
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'sport_point',
  'def_num': 0,
  'raw_value': 33,
}),
]),
  'components': list([
  dict({
  'name': 'score',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 16,
  'accumulate': False,
  'num': 7,
  'bit_offset': 0,
}),
  dict({
  'name': 'opponent_score',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 16,
  'accumulate': False,
  'num': 8,
  'bit_offset': 16,
}),
]),
}),
  dict({
  'name': 'gear_change_data',
  'type': 'uint32',
  'scale': '1,1,1,1',
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'front_gear_change',
  'def_num': 0,
  'raw_value': 42,
}),
  dict({
  'name': 'event',
  'value': 'rear_gear_change',
  'def_num': 0,
  'raw_value': 43,
}),
]),
  'components': list([
  dict({
  'name': 'rear_gear_num',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 11,
  'bit_offset': 0,
}),
  dict({
  'name': 'rear_gear',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 12,
  'bit_offset': 8,
}),
  dict({
  'name': 'front_gear_num',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 9,
  'bit_offset': 16,
}),
  dict({
  'name': 'front_gear',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 10,
  'bit_offset': 24,
}),
]),
}),
  dict({
  'name': 'rider_position',
  'type': 'rider_position_type',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'rider_position_change',
  'def_num': 0,
  'raw_value': 44,
}),
]),
  'components': list([
]),
  'comment': 'Indicates the rider position value.',
}),
  dict({
  'name': 'comm_timeout',
  'type': 'comm_timeout_type',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'comm_timeout',
  'def_num': 0,
  'raw_value': 47,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'radar_threat_alert',
  'type': 'uint32',
  'scale': '1,1',
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'event',
  'value': 'radar_threat_alert',
  'def_num': 0,
  'raw_value': 75,
}),
]),
  'components': list([
  dict({
  'name': 'radar_threat_level_max',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 21,
  'bit_offset': 0,
}),
  dict({
  'name': 'radar_threat_count',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 22,
  'bit_offset': 8,
}),
]),
  'comment': 'The\xa0first\xa0byte\xa0is\xa0the\xa0radar_threat_level_max, the\xa0second\xa0byte\xa0is\xa0the\xa0radar_threat_count, and the\xa0last\xa016\xa0bits\xa0are\xa0reserved\xa0for\xa0future\xa0use\xa0and\xa0should\xa0be\xa0set\xa0to\xa0FFFF.',
}),
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'event_group',
  'type': 'uint8',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'score',
  'type': 'uint16',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Do not populate directly. Autogenerated by decoder for sport_point subfield components',
}),
  8: dict({
  'name': 'opponent_score',
  'type': 'uint16',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Do not populate directly. Autogenerated by decoder for sport_point subfield components',
}),
  9: dict({
  'name': 'front_gear_num',
  'type': 'uint8z',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Do not populate directly. Autogenerated by decoder for gear_change subfield components.  Front gear number. 1 is innermost.',
}),
  10: dict({
  'name': 'front_gear',
  'type': 'uint8z',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Do not populate directly. Autogenerated by decoder for gear_change subfield components.  Number of front teeth.',
}),
  11: dict({
  'name': 'rear_gear_num',
  'type': 'uint8z',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Do not populate directly. Autogenerated by decoder for gear_change subfield components.  Rear gear number. 1 is innermost.',
}),
  12: dict({
  'name': 'rear_gear',
  'type': 'uint8z',
  'def_num': 12,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Do not populate directly. Autogenerated by decoder for gear_change subfield components.  Number of rear teeth.',
}),
  13: dict({
  'name': 'device_index',
  'type': 'device_index',
  'def_num': 13,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  21: dict({
  'name': 'radar_threat_level_max',
  'type': 'radar_threat_level_type',
  'def_num': 21,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Do not populate directly. Autogenerated by decoder for threat_alert subfield components.',
}),
  22: dict({
  'name': 'radar_threat_count',
  'type': 'uint8',
  'def_num': 22,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Do not populate directly. Autogenerated by decoder for threat_alert subfield components.',
}),
}),
  'comment': None,
}),
  23: dict({
  'name': 'device_info',
  'global_number': 23,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'device_index',
  'type': 'device_index',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'device_type',
  'type': 'uint8',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'antplus_device_type',
  'type': 'antplus_device_type',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'source_type',
  'value': 'antplus',
  'def_num': 25,
  'raw_value': 1,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'ant_device_type',
  'type': 'uint8',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'source_type',
  'value': 'ant',
  'def_num': 25,
  'raw_value': 0,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'manufacturer',
  'type': 'manufacturer',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'serial_number',
  'type': 'uint32z',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'product',
  'type': 'uint16',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'favero_product',
  'type': 'favero_product',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'manufacturer',
  'value': 'favero_electronics',
  'def_num': 2,
  'raw_value': 263,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'garmin_product',
  'type': 'garmin_product',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'manufacturer',
  'value': 'garmin',
  'def_num': 2,
  'raw_value': 1,
}),
  dict({
  'name': 'manufacturer',
  'value': 'dynastream',
  'def_num': 2,
  'raw_value': 15,
}),
  dict({
  'name': 'manufacturer',
  'value': 'dynastream_oem',
  'def_num': 2,
  'raw_value': 13,
}),
  dict({
  'name': 'manufacturer',
  'value': 'tacx',
  'def_num': 2,
  'raw_value': 89,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'software_version',
  'type': 'uint16',
  'def_num': 5,
  'scale': 100,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'hardware_version',
  'type': 'uint8',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'cum_operating_time',
  'type': 'uint32',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Reset by new battery or charge.',
}),
  10: dict({
  'name': 'battery_voltage',
  'type': 'uint16',
  'def_num': 10,
  'scale': 256,
  'offset': None,
  'units': 'V',
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'battery_status',
  'type': 'battery_status',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  18: dict({
  'name': 'sensor_position',
  'type': 'body_location',
  'def_num': 18,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Indicates the location of the sensor',
}),
  19: dict({
  'name': 'descriptor',
  'type': 'string',
  'def_num': 19,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Used to describe the sensor or location',
}),
  20: dict({
  'name': 'ant_transmission_type',
  'type': 'uint8z',
  'def_num': 20,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  21: dict({
  'name': 'ant_device_number',
  'type': 'uint16z',
  'def_num': 21,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  22: dict({
  'name': 'ant_network',
  'type': 'ant_network',
  'def_num': 22,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  25: dict({
  'name': 'source_type',
  'type': 'source_type',
  'def_num': 25,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  27: dict({
  'name': 'product_name',
  'type': 'string',
  'def_num': 27,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Optional free form string to indicate the devices name or model',
}),
}),
  'comment': None,
}),
  26: dict({
  'name': 'workout',
  'global_number': 26,
  'group_name': 'Workout File Messages',
  'fields': dict({
  4: dict({
  'name': 'sport',
  'type': 'sport',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'capabilities',
  'type': 'workout_capabilities',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'num_valid_steps',
  'type': 'uint16',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'number of valid steps',
}),
  8: dict({
  'name': 'wkt_name',
  'type': 'string',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'sub_sport',
  'type': 'sub_sport',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  14: dict({
  'name': 'pool_length',
  'type': 'uint16',
  'def_num': 14,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  15: dict({
  'name': 'pool_length_unit',
  'type': 'display_measure',
  'def_num': 15,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  27: dict({
  'name': 'workout_step',
  'global_number': 27,
  'group_name': 'Workout File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'wkt_step_name',
  'type': 'string',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'duration_type',
  'type': 'wkt_step_duration',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'duration_value',
  'type': 'uint32',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'duration_time',
  'type': 'uint32',
  'scale': 1000,
  'offset': None,
  'units': 's',
  'reference_fields': list([
  dict({
  'name': 'duration_type',
  'value': 'time',
  'def_num': 1,
  'raw_value': 0,
}),
  dict({
  'name': 'duration_type',
  'value': 'repetition_time',
  'def_num': 1,
  'raw_value': 28,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'duration_distance',
  'type': 'uint32',
  'scale': 100,
  'offset': None,
  'units': 'm',
  'reference_fields': list([
  dict({
  'name': 'duration_type',
  'value': 'distance',
  'def_num': 1,
  'raw_value': 1,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'duration_hr',
  'type': 'workout_hr',
  'scale': None,
  'offset': None,
  'units': '% or bpm',
  'reference_fields': list([
  dict({
  'name': 'duration_type',
  'value': 'hr_less_than',
  'def_num': 1,
  'raw_value': 2,
}),
  dict({
  'name': 'duration_type',
  'value': 'hr_greater_than',
  'def_num': 1,
  'raw_value': 3,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'duration_calories',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'calories',
  'reference_fields': list([
  dict({
  'name': 'duration_type',
  'value': 'calories',
  'def_num': 1,
  'raw_value': 4,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'duration_step',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_steps_cmplt',
  'def_num': 1,
  'raw_value': 6,
}),
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_time',
  'def_num': 1,
  'raw_value': 7,
}),
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_distance',
  'def_num': 1,
  'raw_value': 8,
}),
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_calories',
  'def_num': 1,
  'raw_value': 9,
}),
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_hr_less_than',
  'def_num': 1,
  'raw_value': 10,
}),
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_hr_greater_than',
  'def_num': 1,
  'raw_value': 11,
}),
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_power_less_than',
  'def_num': 1,
  'raw_value': 12,
}),
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_power_greater_than',
  'def_num': 1,
  'raw_value': 13,
}),
]),
  'components': list([
]),
  'comment': 'message_index of step to loop back to. Steps are assumed to be in the order by message_index. custom_name and intensity members are undefined for this duration type.',
}),
  dict({
  'name': 'duration_power',
  'type': 'workout_power',
  'scale': None,
  'offset': None,
  'units': '% or watts',
  'reference_fields': list([
  dict({
  'name': 'duration_type',
  'value': 'power_less_than',
  'def_num': 1,
  'raw_value': 14,
}),
  dict({
  'name': 'duration_type',
  'value': 'power_greater_than',
  'def_num': 1,
  'raw_value': 15,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'duration_reps',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'duration_type',
  'value': 'reps',
  'def_num': 1,
  'raw_value': 29,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'target_type',
  'type': 'wkt_step_target',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'target_value',
  'type': 'uint32',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'target_speed_zone',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'target_type',
  'value': 'speed',
  'def_num': 3,
  'raw_value': 0,
}),
]),
  'components': list([
]),
  'comment': 'speed zone (1-10);Custom =0;',
}),
  dict({
  'name': 'target_hr_zone',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'target_type',
  'value': 'heart_rate',
  'def_num': 3,
  'raw_value': 1,
}),
]),
  'components': list([
]),
  'comment': 'hr zone (1-5);Custom =0;',
}),
  dict({
  'name': 'target_cadence_zone',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'target_type',
  'value': 'cadence',
  'def_num': 3,
  'raw_value': 3,
}),
]),
  'components': list([
]),
  'comment': 'Zone (1-?); Custom = 0;',
}),
  dict({
  'name': 'target_power_zone',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'target_type',
  'value': 'power',
  'def_num': 3,
  'raw_value': 4,
}),
]),
  'components': list([
]),
  'comment': 'Power Zone ( 1-7); Custom = 0;',
}),
  dict({
  'name': 'repeat_steps',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_steps_cmplt',
  'def_num': 1,
  'raw_value': 6,
}),
]),
  'components': list([
]),
  'comment': '# of repetitions',
}),
  dict({
  'name': 'repeat_time',
  'type': 'uint32',
  'scale': 1000,
  'offset': None,
  'units': 's',
  'reference_fields': list([
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_time',
  'def_num': 1,
  'raw_value': 7,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'repeat_distance',
  'type': 'uint32',
  'scale': 100,
  'offset': None,
  'units': 'm',
  'reference_fields': list([
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_distance',
  'def_num': 1,
  'raw_value': 8,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'repeat_calories',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'calories',
  'reference_fields': list([
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_calories',
  'def_num': 1,
  'raw_value': 9,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'repeat_hr',
  'type': 'workout_hr',
  'scale': None,
  'offset': None,
  'units': '% or bpm',
  'reference_fields': list([
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_hr_less_than',
  'def_num': 1,
  'raw_value': 10,
}),
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_hr_greater_than',
  'def_num': 1,
  'raw_value': 11,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'repeat_power',
  'type': 'workout_power',
  'scale': None,
  'offset': None,
  'units': '% or watts',
  'reference_fields': list([
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_power_less_than',
  'def_num': 1,
  'raw_value': 12,
}),
  dict({
  'name': 'duration_type',
  'value': 'repeat_until_power_greater_than',
  'def_num': 1,
  'raw_value': 13,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'target_stroke_type',
  'type': 'swim_stroke',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'target_type',
  'value': 'swim_stroke',
  'def_num': 3,
  'raw_value': 11,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'custom_target_value_low',
  'type': 'uint32',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'custom_target_speed_low',
  'type': 'uint32',
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'reference_fields': list([
  dict({
  'name': 'target_type',
  'value': 'speed',
  'def_num': 3,
  'raw_value': 0,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'custom_target_heart_rate_low',
  'type': 'workout_hr',
  'scale': None,
  'offset': None,
  'units': '% or bpm',
  'reference_fields': list([
  dict({
  'name': 'target_type',
  'value': 'heart_rate',
  'def_num': 3,
  'raw_value': 1,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'custom_target_cadence_low',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'reference_fields': list([
  dict({
  'name': 'target_type',
  'value': 'cadence',
  'def_num': 3,
  'raw_value': 3,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'custom_target_power_low',
  'type': 'workout_power',
  'scale': None,
  'offset': None,
  'units': '% or watts',
  'reference_fields': list([
  dict({
  'name': 'target_type',
  'value': 'power',
  'def_num': 3,
  'raw_value': 4,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'custom_target_value_high',
  'type': 'uint32',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'custom_target_speed_high',
  'type': 'uint32',
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'reference_fields': list([
  dict({
  'name': 'target_type',
  'value': 'speed',
  'def_num': 3,
  'raw_value': 0,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'custom_target_heart_rate_high',
  'type': 'workout_hr',
  'scale': None,
  'offset': None,
  'units': '% or bpm',
  'reference_fields': list([
  dict({
  'name': 'target_type',
  'value': 'heart_rate',
  'def_num': 3,
  'raw_value': 1,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'custom_target_cadence_high',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'reference_fields': list([
  dict({
  'name': 'target_type',
  'value': 'cadence',
  'def_num': 3,
  'raw_value': 3,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'custom_target_power_high',
  'type': 'workout_power',
  'scale': None,
  'offset': None,
  'units': '% or watts',
  'reference_fields': list([
  dict({
  'name': 'target_type',
  'value': 'power',
  'def_num': 3,
  'raw_value': 4,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'intensity',
  'type': 'intensity',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'notes',
  'type': 'string',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'equipment',
  'type': 'workout_equipment',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'exercise_category',
  'type': 'exercise_category',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'exercise_name',
  'type': 'uint16',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  12: dict({
  'name': 'exercise_weight',
  'type': 'uint16',
  'def_num': 12,
  'scale': 100,
  'offset': None,
  'units': 'kg',
  'subfields': list([
]),
  'components': list([
]),
}),
  13: dict({
  'name': 'weight_display_unit',
  'type': 'fit_base_unit',
  'def_num': 13,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  28: dict({
  'name': 'schedule',
  'global_number': 28,
  'group_name': 'Schedule File Messages',
  'fields': dict({
  0: dict({
  'name': 'manufacturer',
  'type': 'manufacturer',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Corresponds to file_id of scheduled workout / course.',
}),
  1: dict({
  'name': 'product',
  'type': 'uint16',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'favero_product',
  'type': 'favero_product',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'manufacturer',
  'value': 'favero_electronics',
  'def_num': 0,
  'raw_value': 263,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'garmin_product',
  'type': 'garmin_product',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'manufacturer',
  'value': 'garmin',
  'def_num': 0,
  'raw_value': 1,
}),
  dict({
  'name': 'manufacturer',
  'value': 'dynastream',
  'def_num': 0,
  'raw_value': 15,
}),
  dict({
  'name': 'manufacturer',
  'value': 'dynastream_oem',
  'def_num': 0,
  'raw_value': 13,
}),
  dict({
  'name': 'manufacturer',
  'value': 'tacx',
  'def_num': 0,
  'raw_value': 89,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
  'comment': 'Corresponds to file_id of scheduled workout / course.',
}),
  2: dict({
  'name': 'serial_number',
  'type': 'uint32z',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Corresponds to file_id of scheduled workout / course.',
}),
  3: dict({
  'name': 'time_created',
  'type': 'date_time',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Corresponds to file_id of scheduled workout / course.',
}),
  4: dict({
  'name': 'completed',
  'type': 'bool',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'TRUE if this activity has been started',
}),
  5: dict({
  'name': 'type',
  'type': 'schedule',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'scheduled_time',
  'type': 'local_date_time',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  30: dict({
  'name': 'weight_scale',
  'global_number': 30,
  'group_name': 'Weight Scale File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'weight',
  'type': 'weight',
  'def_num': 0,
  'scale': 100,
  'offset': None,
  'units': 'kg',
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'percent_fat',
  'type': 'uint16',
  'def_num': 1,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'percent_hydration',
  'type': 'uint16',
  'def_num': 2,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'visceral_fat_mass',
  'type': 'uint16',
  'def_num': 3,
  'scale': 100,
  'offset': None,
  'units': 'kg',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'bone_mass',
  'type': 'uint16',
  'def_num': 4,
  'scale': 100,
  'offset': None,
  'units': 'kg',
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'muscle_mass',
  'type': 'uint16',
  'def_num': 5,
  'scale': 100,
  'offset': None,
  'units': 'kg',
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'basal_met',
  'type': 'uint16',
  'def_num': 7,
  'scale': 4,
  'offset': None,
  'units': 'kcal/day',
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'physique_rating',
  'type': 'uint8',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'active_met',
  'type': 'uint16',
  'def_num': 9,
  'scale': 4,
  'offset': None,
  'units': 'kcal/day',
  'subfields': list([
]),
  'components': list([
]),
  'comment': '~4kJ per kcal, 0.25 allows max 16384 kcal',
}),
  10: dict({
  'name': 'metabolic_age',
  'type': 'uint8',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': 'years',
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'visceral_fat_rating',
  'type': 'uint8',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  12: dict({
  'name': 'user_profile_index',
  'type': 'message_index',
  'def_num': 12,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Associates this weight scale message to a user.  This corresponds to the index of the user profile message in the weight scale file.',
}),
}),
  'comment': None,
}),
  31: dict({
  'name': 'course',
  'global_number': 31,
  'group_name': 'Course File Messages',
  'fields': dict({
  4: dict({
  'name': 'sport',
  'type': 'sport',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'name',
  'type': 'string',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'capabilities',
  'type': 'course_capabilities',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'sub_sport',
  'type': 'sub_sport',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  32: dict({
  'name': 'course_point',
  'global_number': 32,
  'group_name': 'Course File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'position_lat',
  'type': 'sint32',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'position_long',
  'type': 'sint32',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'distance',
  'type': 'uint32',
  'def_num': 4,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'type',
  'type': 'course_point',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'name',
  'type': 'string',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'favorite',
  'type': 'bool',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  33: dict({
  'name': 'totals',
  'global_number': 33,
  'group_name': 'Totals File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'timer_time',
  'type': 'uint32',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Excludes pauses',
}),
  1: dict({
  'name': 'distance',
  'type': 'uint32',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'calories',
  'type': 'uint32',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'kcal',
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'sport',
  'type': 'sport',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'elapsed_time',
  'type': 'uint32',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Includes pauses',
}),
  5: dict({
  'name': 'sessions',
  'type': 'uint16',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'active_time',
  'type': 'uint32',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'sport_index',
  'type': 'uint8',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  34: dict({
  'name': 'activity',
  'global_number': 34,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'total_timer_time',
  'type': 'uint32',
  'def_num': 0,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Exclude pauses',
}),
  1: dict({
  'name': 'num_sessions',
  'type': 'uint16',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'type',
  'type': 'activity',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'event',
  'type': 'event',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'event_type',
  'type': 'event_type',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'local_timestamp',
  'type': 'local_date_time',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'timestamp epoch expressed in local time, used to convert activity timestamps to local time ',
}),
  6: dict({
  'name': 'event_group',
  'type': 'uint8',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  35: dict({
  'name': 'software',
  'global_number': 35,
  'group_name': 'Device File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'version',
  'type': 'uint16',
  'def_num': 3,
  'scale': 100,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'part_number',
  'type': 'string',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  37: dict({
  'name': 'file_capabilities',
  'global_number': 37,
  'group_name': 'Device File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'type',
  'type': 'file',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'flags',
  'type': 'file_flags',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'directory',
  'type': 'string',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'max_count',
  'type': 'uint16',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'max_size',
  'type': 'uint32',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': 'bytes',
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  38: dict({
  'name': 'mesg_capabilities',
  'global_number': 38,
  'group_name': 'Device File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'file',
  'type': 'file',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'mesg_num',
  'type': 'mesg_num',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'count_type',
  'type': 'mesg_count',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'count',
  'type': 'uint16',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'num_per_file',
  'type': 'uint16',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'count_type',
  'value': 'num_per_file',
  'def_num': 2,
  'raw_value': 0,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'max_per_file',
  'type': 'uint16',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'count_type',
  'value': 'max_per_file',
  'def_num': 2,
  'raw_value': 1,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'max_per_file_type',
  'type': 'uint16',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'count_type',
  'value': 'max_per_file_type',
  'def_num': 2,
  'raw_value': 2,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  39: dict({
  'name': 'field_capabilities',
  'global_number': 39,
  'group_name': 'Device File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'file',
  'type': 'file',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'mesg_num',
  'type': 'mesg_num',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'field_num',
  'type': 'uint8',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'count',
  'type': 'uint16',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  49: dict({
  'name': 'file_creator',
  'global_number': 49,
  'group_name': 'Common Messages',
  'fields': dict({
  0: dict({
  'name': 'software_version',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'hardware_version',
  'type': 'uint8',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  51: dict({
  'name': 'blood_pressure',
  'global_number': 51,
  'group_name': 'Blood Pressure File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'systolic_pressure',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'mmHg',
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'diastolic_pressure',
  'type': 'uint16',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'mmHg',
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'mean_arterial_pressure',
  'type': 'uint16',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'mmHg',
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'map_3_sample_mean',
  'type': 'uint16',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': 'mmHg',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'map_morning_values',
  'type': 'uint16',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': 'mmHg',
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'map_evening_values',
  'type': 'uint16',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': 'mmHg',
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'heart_rate',
  'type': 'uint8',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'heart_rate_type',
  'type': 'hr_type',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'status',
  'type': 'bp_status',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'user_profile_index',
  'type': 'message_index',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Associates this blood pressure message to a user.  This corresponds to the index of the user profile message in the blood pressure file.',
}),
}),
  'comment': None,
}),
  53: dict({
  'name': 'speed_zone',
  'global_number': 53,
  'group_name': 'Sport Settings File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'high_value',
  'type': 'uint16',
  'def_num': 0,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'name',
  'type': 'string',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  55: dict({
  'name': 'monitoring',
  'global_number': 55,
  'group_name': 'Monitoring File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Must align to logging interval, for example, time must be 00:00:00 for daily log.',
}),
  0: dict({
  'name': 'device_index',
  'type': 'device_index',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Associates this data to device_info message.  Not required for file with single device (sensor).',
}),
  1: dict({
  'name': 'calories',
  'type': 'uint16',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'kcal',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Accumulated total calories.  Maintained by MonitoringReader for each activity_type.  See SDK documentation',
}),
  2: dict({
  'name': 'distance',
  'type': 'uint32',
  'def_num': 2,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Accumulated distance.  Maintained by MonitoringReader for each activity_type.  See SDK documentation.',
}),
  3: dict({
  'name': 'cycles',
  'type': 'uint32',
  'def_num': 3,
  'scale': 2,
  'offset': None,
  'units': 'cycles',
  'subfields': list([
  dict({
  'name': 'steps',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'steps',
  'reference_fields': list([
  dict({
  'name': 'activity_type',
  'value': 'walking',
  'def_num': 5,
  'raw_value': 6,
}),
  dict({
  'name': 'activity_type',
  'value': 'running',
  'def_num': 5,
  'raw_value': 1,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'strokes',
  'type': 'uint32',
  'scale': 2,
  'offset': None,
  'units': 'strokes',
  'reference_fields': list([
  dict({
  'name': 'activity_type',
  'value': 'cycling',
  'def_num': 5,
  'raw_value': 2,
}),
  dict({
  'name': 'activity_type',
  'value': 'swimming',
  'def_num': 5,
  'raw_value': 5,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
  'comment': 'Accumulated cycles.  Maintained by MonitoringReader for each activity_type.  See SDK documentation.',
}),
  4: dict({
  'name': 'active_time',
  'type': 'uint32',
  'def_num': 4,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'activity_type',
  'type': 'activity_type',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'activity_subtype',
  'type': 'activity_subtype',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'activity_level',
  'type': 'activity_level',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'distance_16',
  'type': 'uint16',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': '100*m',
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'cycles_16',
  'type': 'uint16',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': '2*cycles or steps',
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'active_time_16',
  'type': 'uint16',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'local_timestamp',
  'type': 'local_date_time',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Must align to logging interval, for example, time must be 00:00:00 for daily log.',
}),
  12: dict({
  'name': 'temperature',
  'type': 'sint16',
  'def_num': 12,
  'scale': 100,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Avg temperature during the logging interval ended at timestamp',
}),
  14: dict({
  'name': 'temperature_min',
  'type': 'sint16',
  'def_num': 14,
  'scale': 100,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Min temperature during the logging interval ended at timestamp',
}),
  15: dict({
  'name': 'temperature_max',
  'type': 'sint16',
  'def_num': 15,
  'scale': 100,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Max temperature during the logging interval ended at timestamp',
}),
  16: dict({
  'name': 'activity_time',
  'type': 'uint16',
  'def_num': 16,
  'scale': None,
  'offset': None,
  'units': 'minutes',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Indexed using minute_activity_level enum',
}),
  19: dict({
  'name': 'active_calories',
  'type': 'uint16',
  'def_num': 19,
  'scale': None,
  'offset': None,
  'units': 'kcal',
  'subfields': list([
]),
  'components': list([
]),
}),
  24: dict({
  'name': 'current_activity_type_intensity',
  'type': 'byte',
  'def_num': 24,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'activity_type',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 5,
  'accumulate': False,
  'num': 5,
  'bit_offset': 0,
}),
  dict({
  'name': 'intensity',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 3,
  'accumulate': False,
  'num': 28,
  'bit_offset': 5,
}),
]),
  'comment': 'Indicates single type / intensity for duration since last monitoring message.',
}),
  25: dict({
  'name': 'timestamp_min_8',
  'type': 'uint8',
  'def_num': 25,
  'scale': None,
  'offset': None,
  'units': 'min',
  'subfields': list([
]),
  'components': list([
]),
}),
  26: dict({
  'name': 'timestamp_16',
  'type': 'uint16',
  'def_num': 26,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  27: dict({
  'name': 'heart_rate',
  'type': 'uint8',
  'def_num': 27,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  28: dict({
  'name': 'intensity',
  'type': 'uint8',
  'def_num': 28,
  'scale': 10,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  29: dict({
  'name': 'duration_min',
  'type': 'uint16',
  'def_num': 29,
  'scale': None,
  'offset': None,
  'units': 'min',
  'subfields': list([
]),
  'components': list([
]),
}),
  30: dict({
  'name': 'duration',
  'type': 'uint32',
  'def_num': 30,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  31: dict({
  'name': 'ascent',
  'type': 'uint32',
  'def_num': 31,
  'scale': 1000,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  32: dict({
  'name': 'descent',
  'type': 'uint32',
  'def_num': 32,
  'scale': 1000,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  33: dict({
  'name': 'moderate_activity_minutes',
  'type': 'uint16',
  'def_num': 33,
  'scale': None,
  'offset': None,
  'units': 'minutes',
  'subfields': list([
]),
  'components': list([
]),
}),
  34: dict({
  'name': 'vigorous_activity_minutes',
  'type': 'uint16',
  'def_num': 34,
  'scale': None,
  'offset': None,
  'units': 'minutes',
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  72: dict({
  'name': 'training_file',
  'global_number': 72,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'type',
  'type': 'file',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'manufacturer',
  'type': 'manufacturer',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'product',
  'type': 'uint16',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'favero_product',
  'type': 'favero_product',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'manufacturer',
  'value': 'favero_electronics',
  'def_num': 1,
  'raw_value': 263,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'garmin_product',
  'type': 'garmin_product',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'manufacturer',
  'value': 'garmin',
  'def_num': 1,
  'raw_value': 1,
}),
  dict({
  'name': 'manufacturer',
  'value': 'dynastream',
  'def_num': 1,
  'raw_value': 15,
}),
  dict({
  'name': 'manufacturer',
  'value': 'dynastream_oem',
  'def_num': 1,
  'raw_value': 13,
}),
  dict({
  'name': 'manufacturer',
  'value': 'tacx',
  'def_num': 1,
  'raw_value': 89,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'serial_number',
  'type': 'uint32z',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'time_created',
  'type': 'date_time',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': 'Corresponds to file_id of workout or course.',
}),
  78: dict({
  'name': 'hrv',
  'global_number': 78,
  'group_name': 'Other Messages',
  'fields': dict({
  0: dict({
  'name': 'time',
  'type': 'uint16',
  'def_num': 0,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Time between beats',
}),
}),
  'comment': 'Heart rate variability',
}),
  80: dict({
  'name': 'ant_rx',
  'global_number': 80,
  'group_name': 'Other Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'fractional_timestamp',
  'type': 'uint16',
  'def_num': 0,
  'scale': 32768,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'mesg_id',
  'type': 'byte',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'mesg_data',
  'type': 'byte',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'channel_number',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 3,
  'bit_offset': 0,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 8,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 16,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 24,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 32,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 40,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 48,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 56,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 64,
}),
]),
}),
  3: dict({
  'name': 'channel_number',
  'type': 'uint8',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'data',
  'type': 'byte',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  81: dict({
  'name': 'ant_tx',
  'global_number': 81,
  'group_name': 'Other Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'fractional_timestamp',
  'type': 'uint16',
  'def_num': 0,
  'scale': 32768,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'mesg_id',
  'type': 'byte',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'mesg_data',
  'type': 'byte',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'channel_number',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 3,
  'bit_offset': 0,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 8,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 16,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 24,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 32,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 40,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 48,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 56,
}),
  dict({
  'name': 'data',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 8,
  'accumulate': False,
  'num': 4,
  'bit_offset': 64,
}),
]),
}),
  3: dict({
  'name': 'channel_number',
  'type': 'uint8',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'data',
  'type': 'byte',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  82: dict({
  'name': 'ant_channel_id',
  'global_number': 82,
  'group_name': 'Other Messages',
  'fields': dict({
  0: dict({
  'name': 'channel_number',
  'type': 'uint8',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'device_type',
  'type': 'uint8z',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'device_number',
  'type': 'uint16z',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'transmission_type',
  'type': 'uint8z',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'device_index',
  'type': 'device_index',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  101: dict({
  'name': 'length',
  'global_number': 101,
  'group_name': 'Activity File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'event',
  'type': 'event',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'event_type',
  'type': 'event_type',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'start_time',
  'type': 'date_time',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'total_elapsed_time',
  'type': 'uint32',
  'def_num': 3,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'total_timer_time',
  'type': 'uint32',
  'def_num': 4,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'total_strokes',
  'type': 'uint16',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': 'strokes',
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'avg_speed',
  'type': 'uint16',
  'def_num': 6,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'swim_stroke',
  'type': 'swim_stroke',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': 'swim_stroke',
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'avg_swimming_cadence',
  'type': 'uint8',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': 'strokes/min',
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'event_group',
  'type': 'uint8',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'total_calories',
  'type': 'uint16',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': 'kcal',
  'subfields': list([
]),
  'components': list([
]),
}),
  12: dict({
  'name': 'length_type',
  'type': 'length_type',
  'def_num': 12,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  18: dict({
  'name': 'player_score',
  'type': 'uint16',
  'def_num': 18,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  19: dict({
  'name': 'opponent_score',
  'type': 'uint16',
  'def_num': 19,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  20: dict({
  'name': 'stroke_count',
  'type': 'uint16',
  'def_num': 20,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'stroke_type enum used as the index',
}),
  21: dict({
  'name': 'zone_count',
  'type': 'uint16',
  'def_num': 21,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'zone number used as the index',
}),
}),
  'comment': None,
}),
  103: dict({
  'name': 'monitoring_info',
  'global_number': 103,
  'group_name': 'Monitoring File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'local_timestamp',
  'type': 'local_date_time',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Use to convert activity timestamps to local time if device does not support time zone and daylight savings time correction.',
}),
  1: dict({
  'name': 'activity_type',
  'type': 'activity_type',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'cycles_to_distance',
  'type': 'uint16',
  'def_num': 3,
  'scale': 5000,
  'offset': None,
  'units': 'm/cycle',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Indexed by activity_type',
}),
  4: dict({
  'name': 'cycles_to_calories',
  'type': 'uint16',
  'def_num': 4,
  'scale': 5000,
  'offset': None,
  'units': 'kcal/cycle',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Indexed by activity_type',
}),
  5: dict({
  'name': 'resting_metabolic_rate',
  'type': 'uint16',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': 'kcal/day',
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  106: dict({
  'name': 'slave_device',
  'global_number': 106,
  'group_name': 'Device File Messages',
  'fields': dict({
  0: dict({
  'name': 'manufacturer',
  'type': 'manufacturer',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'product',
  'type': 'uint16',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'favero_product',
  'type': 'favero_product',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'manufacturer',
  'value': 'favero_electronics',
  'def_num': 0,
  'raw_value': 263,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'garmin_product',
  'type': 'garmin_product',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'manufacturer',
  'value': 'garmin',
  'def_num': 0,
  'raw_value': 1,
}),
  dict({
  'name': 'manufacturer',
  'value': 'dynastream',
  'def_num': 0,
  'raw_value': 15,
}),
  dict({
  'name': 'manufacturer',
  'value': 'dynastream_oem',
  'def_num': 0,
  'raw_value': 13,
}),
  dict({
  'name': 'manufacturer',
  'value': 'tacx',
  'def_num': 0,
  'raw_value': 89,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  127: dict({
  'name': 'connectivity',
  'global_number': 127,
  'group_name': 'Settings File Messages',
  'fields': dict({
  0: dict({
  'name': 'bluetooth_enabled',
  'type': 'bool',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Use Bluetooth for connectivity features',
}),
  1: dict({
  'name': 'bluetooth_le_enabled',
  'type': 'bool',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Use Bluetooth Low Energy for connectivity features',
}),
  2: dict({
  'name': 'ant_enabled',
  'type': 'bool',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Use ANT for connectivity features',
}),
  3: dict({
  'name': 'name',
  'type': 'string',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'live_tracking_enabled',
  'type': 'bool',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'weather_conditions_enabled',
  'type': 'bool',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'weather_alerts_enabled',
  'type': 'bool',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'auto_activity_upload_enabled',
  'type': 'bool',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'course_download_enabled',
  'type': 'bool',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'workout_download_enabled',
  'type': 'bool',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'gps_ephemeris_download_enabled',
  'type': 'bool',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'incident_detection_enabled',
  'type': 'bool',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  12: dict({
  'name': 'grouptrack_enabled',
  'type': 'bool',
  'def_num': 12,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  128: dict({
  'name': 'weather_conditions',
  'global_number': 128,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'time of update for current conditions, else forecast time',
}),
  0: dict({
  'name': 'weather_report',
  'type': 'weather_report',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Current or forecast',
}),
  1: dict({
  'name': 'temperature',
  'type': 'sint8',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'condition',
  'type': 'weather_status',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Corresponds to GSC Response weatherIcon field',
}),
  3: dict({
  'name': 'wind_direction',
  'type': 'uint16',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'wind_speed',
  'type': 'uint16',
  'def_num': 4,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'precipitation_probability',
  'type': 'uint8',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'range 0-100',
}),
  6: dict({
  'name': 'temperature_feels_like',
  'type': 'sint8',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Heat Index if  GCS heatIdx above or equal to 90F or wind chill if GCS windChill below or equal to 32F',
}),
  7: dict({
  'name': 'relative_humidity',
  'type': 'uint8',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'location',
  'type': 'string',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'string corresponding to GCS response location string',
}),
  9: dict({
  'name': 'observed_at_time',
  'type': 'date_time',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'observed_location_lat',
  'type': 'sint32',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'observed_location_long',
  'type': 'sint32',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  12: dict({
  'name': 'day_of_week',
  'type': 'day_of_week',
  'def_num': 12,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  13: dict({
  'name': 'high_temperature',
  'type': 'sint8',
  'def_num': 13,
  'scale': None,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
  14: dict({
  'name': 'low_temperature',
  'type': 'sint8',
  'def_num': 14,
  'scale': None,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  129: dict({
  'name': 'weather_alert',
  'global_number': 129,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'report_id',
  'type': 'string',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Unique identifier from GCS report ID string, length is 12',
}),
  1: dict({
  'name': 'issue_time',
  'type': 'date_time',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Time alert was issued',
}),
  2: dict({
  'name': 'expire_time',
  'type': 'date_time',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Time alert expires',
}),
  3: dict({
  'name': 'severity',
  'type': 'weather_severity',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Warning, Watch, Advisory, Statement',
}),
  4: dict({
  'name': 'type',
  'type': 'weather_severe_type',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Tornado, Severe Thunderstorm, etc.',
}),
}),
  'comment': None,
}),
  131: dict({
  'name': 'cadence_zone',
  'global_number': 131,
  'group_name': 'Sport Settings File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'high_value',
  'type': 'uint8',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'name',
  'type': 'string',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  132: dict({
  'name': 'hr',
  'global_number': 132,
  'group_name': 'Monitoring File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'fractional_timestamp',
  'type': 'uint16',
  'def_num': 0,
  'scale': 32768,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'time256',
  'type': 'uint8',
  'def_num': 1,
  'scale': 256,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'fractional_timestamp',
  'scale': 256,
  'offset': None,
  'units': 's',
  'bits': 8,
  'accumulate': False,
  'num': 0,
  'bit_offset': 0,
}),
]),
}),
  6: dict({
  'name': 'filtered_bpm',
  'type': 'uint8',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'event_timestamp',
  'type': 'uint32',
  'def_num': 9,
  'scale': 1024,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'event_timestamp_12',
  'type': 'byte',
  'def_num': 10,
  'scale': '1024,\n1024,\n1024,\n1024,\n1024,\n1024,\n1024,\n1024,\n1024,\n1024',
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'event_timestamp',
  'scale': 1024,
  'offset': None,
  'units': 's',
  'bits': 12,
  'accumulate': True,
  'num': 9,
  'bit_offset': 0,
}),
  dict({
  'name': 'event_timestamp',
  'scale': 1024,
  'offset': None,
  'units': 's',
  'bits': 12,
  'accumulate': True,
  'num': 9,
  'bit_offset': 12,
}),
  dict({
  'name': 'event_timestamp',
  'scale': 1024,
  'offset': None,
  'units': 's',
  'bits': 12,
  'accumulate': True,
  'num': 9,
  'bit_offset': 24,
}),
  dict({
  'name': 'event_timestamp',
  'scale': 1024,
  'offset': None,
  'units': 's',
  'bits': 12,
  'accumulate': True,
  'num': 9,
  'bit_offset': 36,
}),
  dict({
  'name': 'event_timestamp',
  'scale': 1024,
  'offset': None,
  'units': 's',
  'bits': 12,
  'accumulate': True,
  'num': 9,
  'bit_offset': 48,
}),
  dict({
  'name': 'event_timestamp',
  'scale': 1024,
  'offset': None,
  'units': 's',
  'bits': 12,
  'accumulate': True,
  'num': 9,
  'bit_offset': 60,
}),
  dict({
  'name': 'event_timestamp',
  'scale': 1024,
  'offset': None,
  'units': 's',
  'bits': 12,
  'accumulate': True,
  'num': 9,
  'bit_offset': 72,
}),
  dict({
  'name': 'event_timestamp',
  'scale': 1024,
  'offset': None,
  'units': 's',
  'bits': 12,
  'accumulate': True,
  'num': 9,
  'bit_offset': 84,
}),
  dict({
  'name': 'event_timestamp',
  'scale': 1024,
  'offset': None,
  'units': 's',
  'bits': 12,
  'accumulate': True,
  'num': 9,
  'bit_offset': 96,
}),
  dict({
  'name': 'event_timestamp',
  'scale': 1024,
  'offset': None,
  'units': 's',
  'bits': 12,
  'accumulate': True,
  'num': 9,
  'bit_offset': 108,
}),
]),
}),
}),
  'comment': None,
}),
  142: dict({
  'name': 'segment_lap',
  'global_number': 142,
  'group_name': 'Segment File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Lap end time.',
}),
  0: dict({
  'name': 'event',
  'type': 'event',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'event_type',
  'type': 'event_type',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'start_time',
  'type': 'date_time',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'start_position_lat',
  'type': 'sint32',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'start_position_long',
  'type': 'sint32',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'end_position_lat',
  'type': 'sint32',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'end_position_long',
  'type': 'sint32',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'total_elapsed_time',
  'type': 'uint32',
  'def_num': 7,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Time (includes pauses)',
}),
  8: dict({
  'name': 'total_timer_time',
  'type': 'uint32',
  'def_num': 8,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Timer Time (excludes pauses)',
}),
  9: dict({
  'name': 'total_distance',
  'type': 'uint32',
  'def_num': 9,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'total_cycles',
  'type': 'uint32',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': 'cycles',
  'subfields': list([
  dict({
  'name': 'total_strokes',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'strokes',
  'reference_fields': list([
  dict({
  'name': 'sport',
  'value': 'cycling',
  'def_num': 23,
  'raw_value': 2,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'total_calories',
  'type': 'uint16',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': 'kcal',
  'subfields': list([
]),
  'components': list([
]),
}),
  12: dict({
  'name': 'total_fat_calories',
  'type': 'uint16',
  'def_num': 12,
  'scale': None,
  'offset': None,
  'units': 'kcal',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'If New Leaf',
}),
  13: dict({
  'name': 'avg_speed',
  'type': 'uint16',
  'def_num': 13,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  14: dict({
  'name': 'max_speed',
  'type': 'uint16',
  'def_num': 14,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  15: dict({
  'name': 'avg_heart_rate',
  'type': 'uint8',
  'def_num': 15,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  16: dict({
  'name': 'max_heart_rate',
  'type': 'uint8',
  'def_num': 16,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  17: dict({
  'name': 'avg_cadence',
  'type': 'uint8',
  'def_num': 17,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'total_cycles / total_timer_time if non_zero_avg_cadence otherwise total_cycles / total_elapsed_time',
}),
  18: dict({
  'name': 'max_cadence',
  'type': 'uint8',
  'def_num': 18,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  19: dict({
  'name': 'avg_power',
  'type': 'uint16',
  'def_num': 19,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'total_power / total_timer_time if non_zero_avg_power otherwise total_power / total_elapsed_time',
}),
  20: dict({
  'name': 'max_power',
  'type': 'uint16',
  'def_num': 20,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
}),
  21: dict({
  'name': 'total_ascent',
  'type': 'uint16',
  'def_num': 21,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  22: dict({
  'name': 'total_descent',
  'type': 'uint16',
  'def_num': 22,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  23: dict({
  'name': 'sport',
  'type': 'sport',
  'def_num': 23,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  24: dict({
  'name': 'event_group',
  'type': 'uint8',
  'def_num': 24,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  25: dict({
  'name': 'nec_lat',
  'type': 'sint32',
  'def_num': 25,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'North east corner latitude.',
}),
  26: dict({
  'name': 'nec_long',
  'type': 'sint32',
  'def_num': 26,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'North east corner longitude.',
}),
  27: dict({
  'name': 'swc_lat',
  'type': 'sint32',
  'def_num': 27,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'South west corner latitude.',
}),
  28: dict({
  'name': 'swc_long',
  'type': 'sint32',
  'def_num': 28,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'South west corner latitude.',
}),
  29: dict({
  'name': 'name',
  'type': 'string',
  'def_num': 29,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  30: dict({
  'name': 'normalized_power',
  'type': 'uint16',
  'def_num': 30,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
}),
  31: dict({
  'name': 'left_right_balance',
  'type': 'left_right_balance_100',
  'def_num': 31,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  32: dict({
  'name': 'sub_sport',
  'type': 'sub_sport',
  'def_num': 32,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  33: dict({
  'name': 'total_work',
  'type': 'uint32',
  'def_num': 33,
  'scale': None,
  'offset': None,
  'units': 'J',
  'subfields': list([
]),
  'components': list([
]),
}),
  34: dict({
  'name': 'avg_altitude',
  'type': 'uint16',
  'def_num': 34,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  35: dict({
  'name': 'max_altitude',
  'type': 'uint16',
  'def_num': 35,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  36: dict({
  'name': 'gps_accuracy',
  'type': 'uint8',
  'def_num': 36,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  37: dict({
  'name': 'avg_grade',
  'type': 'sint16',
  'def_num': 37,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  38: dict({
  'name': 'avg_pos_grade',
  'type': 'sint16',
  'def_num': 38,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  39: dict({
  'name': 'avg_neg_grade',
  'type': 'sint16',
  'def_num': 39,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  40: dict({
  'name': 'max_pos_grade',
  'type': 'sint16',
  'def_num': 40,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  41: dict({
  'name': 'max_neg_grade',
  'type': 'sint16',
  'def_num': 41,
  'scale': 100,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
}),
  42: dict({
  'name': 'avg_temperature',
  'type': 'sint8',
  'def_num': 42,
  'scale': None,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
  43: dict({
  'name': 'max_temperature',
  'type': 'sint8',
  'def_num': 43,
  'scale': None,
  'offset': None,
  'units': 'C',
  'subfields': list([
]),
  'components': list([
]),
}),
  44: dict({
  'name': 'total_moving_time',
  'type': 'uint32',
  'def_num': 44,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  45: dict({
  'name': 'avg_pos_vertical_speed',
  'type': 'sint16',
  'def_num': 45,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  46: dict({
  'name': 'avg_neg_vertical_speed',
  'type': 'sint16',
  'def_num': 46,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  47: dict({
  'name': 'max_pos_vertical_speed',
  'type': 'sint16',
  'def_num': 47,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  48: dict({
  'name': 'max_neg_vertical_speed',
  'type': 'sint16',
  'def_num': 48,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  49: dict({
  'name': 'time_in_hr_zone',
  'type': 'uint32',
  'def_num': 49,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  50: dict({
  'name': 'time_in_speed_zone',
  'type': 'uint32',
  'def_num': 50,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  51: dict({
  'name': 'time_in_cadence_zone',
  'type': 'uint32',
  'def_num': 51,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  52: dict({
  'name': 'time_in_power_zone',
  'type': 'uint32',
  'def_num': 52,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  53: dict({
  'name': 'repetition_num',
  'type': 'uint16',
  'def_num': 53,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  54: dict({
  'name': 'min_altitude',
  'type': 'uint16',
  'def_num': 54,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  55: dict({
  'name': 'min_heart_rate',
  'type': 'uint8',
  'def_num': 55,
  'scale': None,
  'offset': None,
  'units': 'bpm',
  'subfields': list([
]),
  'components': list([
]),
}),
  56: dict({
  'name': 'active_time',
  'type': 'uint32',
  'def_num': 56,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  57: dict({
  'name': 'wkt_step_index',
  'type': 'message_index',
  'def_num': 57,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  58: dict({
  'name': 'sport_event',
  'type': 'sport_event',
  'def_num': 58,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  59: dict({
  'name': 'avg_left_torque_effectiveness',
  'type': 'uint8',
  'def_num': 59,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  60: dict({
  'name': 'avg_right_torque_effectiveness',
  'type': 'uint8',
  'def_num': 60,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  61: dict({
  'name': 'avg_left_pedal_smoothness',
  'type': 'uint8',
  'def_num': 61,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  62: dict({
  'name': 'avg_right_pedal_smoothness',
  'type': 'uint8',
  'def_num': 62,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  63: dict({
  'name': 'avg_combined_pedal_smoothness',
  'type': 'uint8',
  'def_num': 63,
  'scale': 2,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  64: dict({
  'name': 'status',
  'type': 'segment_lap_status',
  'def_num': 64,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  65: dict({
  'name': 'uuid',
  'type': 'string',
  'def_num': 65,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  66: dict({
  'name': 'avg_fractional_cadence',
  'type': 'uint8',
  'def_num': 66,
  'scale': 128,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of the avg_cadence',
}),
  67: dict({
  'name': 'max_fractional_cadence',
  'type': 'uint8',
  'def_num': 67,
  'scale': 128,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of the max_cadence',
}),
  68: dict({
  'name': 'total_fractional_cycles',
  'type': 'uint8',
  'def_num': 68,
  'scale': 128,
  'offset': None,
  'units': 'cycles',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of the total_cycles',
}),
  69: dict({
  'name': 'front_gear_shift_count',
  'type': 'uint16',
  'def_num': 69,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  70: dict({
  'name': 'rear_gear_shift_count',
  'type': 'uint16',
  'def_num': 70,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  71: dict({
  'name': 'time_standing',
  'type': 'uint32',
  'def_num': 71,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Total time spent in the standing position',
}),
  72: dict({
  'name': 'stand_count',
  'type': 'uint16',
  'def_num': 72,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Number of transitions to the standing state',
}),
  73: dict({
  'name': 'avg_left_pco',
  'type': 'sint8',
  'def_num': 73,
  'scale': None,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average left platform center offset',
}),
  74: dict({
  'name': 'avg_right_pco',
  'type': 'sint8',
  'def_num': 74,
  'scale': None,
  'offset': None,
  'units': 'mm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average right platform center offset',
}),
  75: dict({
  'name': 'avg_left_power_phase',
  'type': 'uint8',
  'def_num': 75,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average left power phase angles. Data value indexes defined by power_phase_type.',
}),
  76: dict({
  'name': 'avg_left_power_phase_peak',
  'type': 'uint8',
  'def_num': 76,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average left power phase peak angles. Data value indexes defined by power_phase_type.',
}),
  77: dict({
  'name': 'avg_right_power_phase',
  'type': 'uint8',
  'def_num': 77,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average right power phase angles. Data value indexes defined by power_phase_type.',
}),
  78: dict({
  'name': 'avg_right_power_phase_peak',
  'type': 'uint8',
  'def_num': 78,
  'scale': 0.7111111,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average right power phase peak angles. Data value indexes defined by power_phase_type.',
}),
  79: dict({
  'name': 'avg_power_position',
  'type': 'uint16',
  'def_num': 79,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average power by position. Data value indexes defined by rider_position_type.',
}),
  80: dict({
  'name': 'max_power_position',
  'type': 'uint16',
  'def_num': 80,
  'scale': None,
  'offset': None,
  'units': 'watts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Maximum power by position. Data value indexes defined by rider_position_type.',
}),
  81: dict({
  'name': 'avg_cadence_position',
  'type': 'uint8',
  'def_num': 81,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average cadence by position. Data value indexes defined by rider_position_type.',
}),
  82: dict({
  'name': 'max_cadence_position',
  'type': 'uint8',
  'def_num': 82,
  'scale': None,
  'offset': None,
  'units': 'rpm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Maximum cadence by position. Data value indexes defined by rider_position_type.',
}),
  83: dict({
  'name': 'manufacturer',
  'type': 'manufacturer',
  'def_num': 83,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Manufacturer that produced the segment',
}),
  84: dict({
  'name': 'total_grit',
  'type': 'float32',
  'def_num': 84,
  'scale': None,
  'offset': None,
  'units': 'kGrit',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
}),
  85: dict({
  'name': 'total_flow',
  'type': 'float32',
  'def_num': 85,
  'scale': None,
  'offset': None,
  'units': 'Flow',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
}),
  86: dict({
  'name': 'avg_grit',
  'type': 'float32',
  'def_num': 86,
  'scale': None,
  'offset': None,
  'units': 'kGrit',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The grit score estimates how challenging a route could be for a cyclist in terms of time spent going over sharp turns or large grade slopes.',
}),
  87: dict({
  'name': 'avg_flow',
  'type': 'float32',
  'def_num': 87,
  'scale': None,
  'offset': None,
  'units': 'Flow',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The flow score estimates how long distance wise a cyclist deaccelerates over intervals where deacceleration is unnecessary such as smooth turns or small grade angle intervals.',
}),
  89: dict({
  'name': 'total_fractional_ascent',
  'type': 'uint8',
  'def_num': 89,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of total_ascent',
}),
  90: dict({
  'name': 'total_fractional_descent',
  'type': 'uint8',
  'def_num': 90,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'fractional part of total_descent',
}),
}),
  'comment': None,
}),
  145: dict({
  'name': 'memo_glob',
  'global_number': 145,
  'group_name': 'Other Messages',
  'fields': dict({
  250: dict({
  'name': 'part_index',
  'type': 'uint32',
  'def_num': 250,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Sequence number of memo blocks',
}),
  0: dict({
  'name': 'memo',
  'type': 'byte',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Block of utf8 bytes',
}),
  1: dict({
  'name': 'message_number',
  'type': 'uint16',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Allows relating glob to another mesg  If used only required for first part of each memo_glob',
}),
  2: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Index of external mesg',
}),
}),
  'comment': None,
}),
  148: dict({
  'name': 'segment_id',
  'global_number': 148,
  'group_name': 'Segment File Messages',
  'fields': dict({
  0: dict({
  'name': 'name',
  'type': 'string',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Friendly name assigned to segment',
}),
  1: dict({
  'name': 'uuid',
  'type': 'string',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'UUID of the segment',
}),
  2: dict({
  'name': 'sport',
  'type': 'sport',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Sport associated with the segment',
}),
  3: dict({
  'name': 'enabled',
  'type': 'bool',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Segment enabled for evaluation',
}),
  4: dict({
  'name': 'user_profile_primary_key',
  'type': 'uint32',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Primary key of the user that created the segment',
}),
  5: dict({
  'name': 'device_id',
  'type': 'uint32',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'ID of the device that created the segment',
}),
  6: dict({
  'name': 'default_race_leader',
  'type': 'uint8',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Index for the Leader Board entry selected as the default race participant',
}),
  7: dict({
  'name': 'delete_status',
  'type': 'segment_delete_status',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Indicates if any segments should be deleted',
}),
  8: dict({
  'name': 'selection_type',
  'type': 'segment_selection_type',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Indicates how the segment was selected to be sent to the device',
}),
}),
  'comment': 'Unique Identification data for a segment file',
}),
  149: dict({
  'name': 'segment_leaderboard_entry',
  'global_number': 149,
  'group_name': 'Segment File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'name',
  'type': 'string',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Friendly name assigned to leader',
}),
  1: dict({
  'name': 'type',
  'type': 'segment_leaderboard_type',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Leader classification',
}),
  2: dict({
  'name': 'group_primary_key',
  'type': 'uint32',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Primary user ID of this leader',
}),
  3: dict({
  'name': 'activity_id',
  'type': 'uint32',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'ID of the activity associated with this leader time',
}),
  4: dict({
  'name': 'segment_time',
  'type': 'uint32',
  'def_num': 4,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Segment Time (includes pauses)',
}),
  5: dict({
  'name': 'activity_id_string',
  'type': 'string',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'String version of the activity_id. 21 characters long, express in decimal',
}),
}),
  'comment': 'Unique Identification data for an individual segment leader within a segment file',
}),
  150: dict({
  'name': 'segment_point',
  'global_number': 150,
  'group_name': 'Segment File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'position_lat',
  'type': 'sint32',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'position_long',
  'type': 'sint32',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'distance',
  'type': 'uint32',
  'def_num': 3,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Accumulated distance along the segment at the described point',
}),
  4: dict({
  'name': 'altitude',
  'type': 'uint16',
  'def_num': 4,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Accumulated altitude along the segment at the described point',
}),
  5: dict({
  'name': 'leader_time',
  'type': 'uint32',
  'def_num': 5,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Accumualted time each leader board member required to reach the described point. This value is zero for all leader board members at the starting point of the segment.',
}),
}),
  'comment': 'Navigation and race evaluation point for a segment decribing a point along the segment path and time it took each segment leader to reach that point',
}),
  151: dict({
  'name': 'segment_file',
  'global_number': 151,
  'group_name': 'Segment File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'file_uuid',
  'type': 'string',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'UUID of the segment file',
}),
  3: dict({
  'name': 'enabled',
  'type': 'bool',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Enabled state of the segment file',
}),
  4: dict({
  'name': 'user_profile_primary_key',
  'type': 'uint32',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Primary key of the user that created the segment file',
}),
  7: dict({
  'name': 'leader_type',
  'type': 'segment_leaderboard_type',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Leader type of each leader in the segment file',
}),
  8: dict({
  'name': 'leader_group_primary_key',
  'type': 'uint32',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Group primary key of each leader in the segment file',
}),
  9: dict({
  'name': 'leader_activity_id',
  'type': 'uint32',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Activity ID of each leader in the segment file',
}),
  10: dict({
  'name': 'leader_activity_id_string',
  'type': 'string',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'String version of the activity ID of each leader in the segment file. 21 characters long for each ID, express in decimal',
}),
  11: dict({
  'name': 'default_race_leader',
  'type': 'uint8',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Index for the Leader Board entry selected as the default race participant',
}),
}),
  'comment': 'Summary of the unique segment and leaderboard information associated with a segment file. This message is used to compile a segment list file describing all segment files on a device. The segment list file is used when refreshing the contents of a segment file with the latest available leaderboard information.',
}),
  158: dict({
  'name': 'workout_session',
  'global_number': 158,
  'group_name': 'Workout File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'sport',
  'type': 'sport',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'sub_sport',
  'type': 'sub_sport',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'num_valid_steps',
  'type': 'uint16',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'first_step_index',
  'type': 'uint16',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'pool_length',
  'type': 'uint16',
  'def_num': 4,
  'scale': 100,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'pool_length_unit',
  'type': 'display_measure',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  159: dict({
  'name': 'watchface_settings',
  'global_number': 159,
  'group_name': 'Settings File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'mode',
  'type': 'watchface_mode',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'layout',
  'type': 'byte',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'digital_layout',
  'type': 'digital_watchface_layout',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'mode',
  'value': 'digital',
  'def_num': 0,
  'raw_value': 0,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'analog_layout',
  'type': 'analog_watchface_layout',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'mode',
  'value': 'analog',
  'def_num': 0,
  'raw_value': 1,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  160: dict({
  'name': 'gps_metadata',
  'global_number': 160,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Whole second part of the timestamp.',
}),
  0: dict({
  'name': 'timestamp_ms',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Millisecond part of the timestamp.',
}),
  1: dict({
  'name': 'position_lat',
  'type': 'sint32',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'position_long',
  'type': 'sint32',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'enhanced_altitude',
  'type': 'uint32',
  'def_num': 3,
  'scale': 5,
  'offset': 500,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'enhanced_speed',
  'type': 'uint32',
  'def_num': 4,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'heading',
  'type': 'uint16',
  'def_num': 5,
  'scale': 100,
  'offset': None,
  'units': 'degrees',
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'utc_timestamp',
  'type': 'date_time',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Used to correlate UTC to system time if the timestamp of the message is in system time.  This UTC time is derived from the GPS data.',
}),
  7: dict({
  'name': 'velocity',
  'type': 'sint16',
  'def_num': 7,
  'scale': 100,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'velocity[0] is lon velocity.  Velocity[1] is lat velocity.  Velocity[2] is altitude velocity.',
}),
}),
  'comment': None,
}),
  161: dict({
  'name': 'camera_event',
  'global_number': 161,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Whole second part of the timestamp.',
}),
  0: dict({
  'name': 'timestamp_ms',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Millisecond part of the timestamp.',
}),
  1: dict({
  'name': 'camera_event_type',
  'type': 'camera_event_type',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'camera_file_uuid',
  'type': 'string',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'camera_orientation',
  'type': 'camera_orientation_type',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  162: dict({
  'name': 'timestamp_correlation',
  'global_number': 162,
  'group_name': 'Common Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Whole second part of UTC timestamp at the time the system timestamp was recorded.',
}),
  0: dict({
  'name': 'fractional_timestamp',
  'type': 'uint16',
  'def_num': 0,
  'scale': 32768,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Fractional part of the UTC timestamp at the time the system timestamp was recorded.',
}),
  1: dict({
  'name': 'system_timestamp',
  'type': 'date_time',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Whole second part of the system timestamp',
}),
  2: dict({
  'name': 'fractional_system_timestamp',
  'type': 'uint16',
  'def_num': 2,
  'scale': 32768,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Fractional part of the system timestamp',
}),
  3: dict({
  'name': 'local_timestamp',
  'type': 'local_date_time',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'timestamp epoch expressed in local time used to convert timestamps to local time',
}),
  4: dict({
  'name': 'timestamp_ms',
  'type': 'uint16',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Millisecond part of the UTC timestamp at the time the system timestamp was recorded.',
}),
  5: dict({
  'name': 'system_timestamp_ms',
  'type': 'uint16',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Millisecond part of the system timestamp',
}),
}),
  'comment': None,
}),
  164: dict({
  'name': 'gyroscope_data',
  'global_number': 164,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Whole second part of the timestamp',
}),
  0: dict({
  'name': 'timestamp_ms',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Millisecond part of the timestamp.',
}),
  1: dict({
  'name': 'sample_time_offset',
  'type': 'uint16',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Each time in the array describes the time at which the gyro sample with the corrosponding index was taken. Limited to 30 samples in each message. The samples may span across seconds. Array size must match the number of samples in gyro_x and gyro_y and gyro_z',
}),
  2: dict({
  'name': 'gyro_x',
  'type': 'uint16',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
}),
  3: dict({
  'name': 'gyro_y',
  'type': 'uint16',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
}),
  4: dict({
  'name': 'gyro_z',
  'type': 'uint16',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
}),
  5: dict({
  'name': 'calibrated_gyro_x',
  'type': 'float32',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': 'deg/s',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibrated gyro reading',
}),
  6: dict({
  'name': 'calibrated_gyro_y',
  'type': 'float32',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': 'deg/s',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibrated gyro reading',
}),
  7: dict({
  'name': 'calibrated_gyro_z',
  'type': 'float32',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': 'deg/s',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibrated gyro reading',
}),
}),
  'comment': None,
}),
  165: dict({
  'name': 'accelerometer_data',
  'global_number': 165,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Whole second part of the timestamp',
}),
  0: dict({
  'name': 'timestamp_ms',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Millisecond part of the timestamp.',
}),
  1: dict({
  'name': 'sample_time_offset',
  'type': 'uint16',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Each time in the array describes the time at which the accelerometer sample with the corrosponding index was taken. Limited to 30 samples in each message. The samples may span across seconds. Array size must match the number of samples in accel_x and accel_y and accel_z',
}),
  2: dict({
  'name': 'accel_x',
  'type': 'uint16',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
}),
  3: dict({
  'name': 'accel_y',
  'type': 'uint16',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
}),
  4: dict({
  'name': 'accel_z',
  'type': 'uint16',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
}),
  5: dict({
  'name': 'calibrated_accel_x',
  'type': 'float32',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': 'g',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibrated accel reading',
}),
  6: dict({
  'name': 'calibrated_accel_y',
  'type': 'float32',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': 'g',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibrated accel reading',
}),
  7: dict({
  'name': 'calibrated_accel_z',
  'type': 'float32',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': 'g',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibrated accel reading',
}),
  8: dict({
  'name': 'compressed_calibrated_accel_x',
  'type': 'sint16',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': 'mG',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibrated accel reading',
}),
  9: dict({
  'name': 'compressed_calibrated_accel_y',
  'type': 'sint16',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': 'mG',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibrated accel reading',
}),
  10: dict({
  'name': 'compressed_calibrated_accel_z',
  'type': 'sint16',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': 'mG',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibrated accel reading',
}),
}),
  'comment': None,
}),
  167: dict({
  'name': 'three_d_sensor_calibration',
  'global_number': 167,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Whole second part of the timestamp',
}),
  0: dict({
  'name': 'sensor_type',
  'type': 'sensor_type',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Indicates which sensor the calibration is for',
}),
  1: dict({
  'name': 'calibration_factor',
  'type': 'uint32',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'accel_cal_factor',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'g',
  'reference_fields': list([
  dict({
  'name': 'sensor_type',
  'value': 'accelerometer',
  'def_num': 0,
  'raw_value': 0,
}),
]),
  'components': list([
]),
  'comment': 'Accelerometer calibration factor',
}),
  dict({
  'name': 'gyro_cal_factor',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'deg/s',
  'reference_fields': list([
  dict({
  'name': 'sensor_type',
  'value': 'gyroscope',
  'def_num': 0,
  'raw_value': 1,
}),
]),
  'components': list([
]),
  'comment': 'Gyro calibration factor',
}),
]),
  'components': list([
]),
  'comment': 'Calibration factor used to convert from raw ADC value to degrees, g,  etc.',
}),
  2: dict({
  'name': 'calibration_divisor',
  'type': 'uint32',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibration factor divisor',
}),
  3: dict({
  'name': 'level_shift',
  'type': 'uint32',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Level shift value used to shift the ADC value back into range',
}),
  4: dict({
  'name': 'offset_cal',
  'type': 'sint32',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Internal calibration factors, one for each: xy, yx, zx',
}),
  5: dict({
  'name': 'orientation_matrix',
  'type': 'sint32',
  'def_num': 5,
  'scale': 65535,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': '3 x 3 rotation matrix (row major)',
}),
}),
  'comment': None,
}),
  169: dict({
  'name': 'video_frame',
  'global_number': 169,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Whole second part of the timestamp',
}),
  0: dict({
  'name': 'timestamp_ms',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Millisecond part of the timestamp.',
}),
  1: dict({
  'name': 'frame_number',
  'type': 'uint32',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Number of the frame that the timestamp and timestamp_ms correlate to',
}),
}),
  'comment': None,
}),
  174: dict({
  'name': 'obdii_data',
  'global_number': 174,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Timestamp message was output',
}),
  0: dict({
  'name': 'timestamp_ms',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Fractional part of timestamp, added to timestamp',
}),
  1: dict({
  'name': 'time_offset',
  'type': 'uint16',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Offset of PID reading [i] from start_timestamp+start_timestamp_ms. Readings may span accross seconds.',
}),
  2: dict({
  'name': 'pid',
  'type': 'byte',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Parameter ID',
}),
  3: dict({
  'name': 'raw_data',
  'type': 'byte',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Raw parameter data',
}),
  4: dict({
  'name': 'pid_data_size',
  'type': 'uint8',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Optional, data size of PID[i].  If not specified refer to SAE J1979.',
}),
  5: dict({
  'name': 'system_time',
  'type': 'uint32',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'System time associated with sample expressed in ms, can be used instead of time_offset.  There will be a system_time value for each raw_data element.  For multibyte pids the system_time is repeated.',
}),
  6: dict({
  'name': 'start_timestamp',
  'type': 'date_time',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Timestamp of first sample recorded in the message.  Used with time_offset to generate time of each sample',
}),
  7: dict({
  'name': 'start_timestamp_ms',
  'type': 'uint16',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Fractional part of start_timestamp',
}),
}),
  'comment': None,
}),
  177: dict({
  'name': 'nmea_sentence',
  'global_number': 177,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Timestamp message was output',
}),
  0: dict({
  'name': 'timestamp_ms',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Fractional part of timestamp, added to timestamp',
}),
  1: dict({
  'name': 'sentence',
  'type': 'string',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'NMEA sentence',
}),
}),
  'comment': None,
}),
  178: dict({
  'name': 'aviation_attitude',
  'global_number': 178,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Timestamp message was output',
}),
  0: dict({
  'name': 'timestamp_ms',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Fractional part of timestamp, added to timestamp',
}),
  1: dict({
  'name': 'system_time',
  'type': 'uint32',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'System time associated with sample expressed in ms.',
}),
  2: dict({
  'name': 'pitch',
  'type': 'sint16',
  'def_num': 2,
  'scale': 10430.38,
  'offset': None,
  'units': 'radians',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Range -PI/2 to +PI/2',
}),
  3: dict({
  'name': 'roll',
  'type': 'sint16',
  'def_num': 3,
  'scale': 10430.38,
  'offset': None,
  'units': 'radians',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Range -PI to +PI',
}),
  4: dict({
  'name': 'accel_lateral',
  'type': 'sint16',
  'def_num': 4,
  'scale': 100,
  'offset': None,
  'units': 'm/s^2',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Range -78.4 to +78.4 (-8 Gs to 8 Gs)',
}),
  5: dict({
  'name': 'accel_normal',
  'type': 'sint16',
  'def_num': 5,
  'scale': 100,
  'offset': None,
  'units': 'm/s^2',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Range -78.4 to +78.4 (-8 Gs to 8 Gs)',
}),
  6: dict({
  'name': 'turn_rate',
  'type': 'sint16',
  'def_num': 6,
  'scale': 1024,
  'offset': None,
  'units': 'radians/second',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Range -8.727 to +8.727 (-500 degs/sec to +500 degs/sec)',
}),
  7: dict({
  'name': 'stage',
  'type': 'attitude_stage',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'attitude_stage_complete',
  'type': 'uint8',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': '%',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'The percent complete of the current attitude stage.  Set to 0 for attitude stages 0, 1 and 2 and to 100 for attitude stage 3 by AHRS modules that do not support it.  Range - 100',
}),
  9: dict({
  'name': 'track',
  'type': 'uint16',
  'def_num': 9,
  'scale': 10430.38,
  'offset': None,
  'units': 'radians',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Track Angle/Heading Range 0 - 2pi',
}),
  10: dict({
  'name': 'validity',
  'type': 'attitude_validity',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  184: dict({
  'name': 'video',
  'global_number': 184,
  'group_name': 'Activity File Messages',
  'fields': dict({
  0: dict({
  'name': 'url',
  'type': 'string',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'hosting_provider',
  'type': 'string',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'duration',
  'type': 'uint32',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Playback time of video',
}),
}),
  'comment': None,
}),
  185: dict({
  'name': 'video_title',
  'global_number': 185,
  'group_name': 'Activity File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Long titles will be split into multiple parts',
}),
  0: dict({
  'name': 'message_count',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Total number of title parts',
}),
  1: dict({
  'name': 'text',
  'type': 'string',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  186: dict({
  'name': 'video_description',
  'global_number': 186,
  'group_name': 'Activity File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Long descriptions will be split into multiple parts',
}),
  0: dict({
  'name': 'message_count',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Total number of description parts',
}),
  1: dict({
  'name': 'text',
  'type': 'string',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  187: dict({
  'name': 'video_clip',
  'global_number': 187,
  'group_name': 'Activity File Messages',
  'fields': dict({
  0: dict({
  'name': 'clip_number',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'start_timestamp',
  'type': 'date_time',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'start_timestamp_ms',
  'type': 'uint16',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'end_timestamp',
  'type': 'date_time',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'end_timestamp_ms',
  'type': 'uint16',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'clip_start',
  'type': 'uint32',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Start of clip in video time',
}),
  7: dict({
  'name': 'clip_end',
  'type': 'uint32',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'End of clip in video time',
}),
}),
  'comment': None,
}),
  188: dict({
  'name': 'ohr_settings',
  'global_number': 188,
  'group_name': 'Settings File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'enabled',
  'type': 'switch',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  200: dict({
  'name': 'exd_screen_configuration',
  'global_number': 200,
  'group_name': 'Other Messages',
  'fields': dict({
  0: dict({
  'name': 'screen_index',
  'type': 'uint8',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'field_count',
  'type': 'uint8',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'number of fields in screen',
}),
  2: dict({
  'name': 'layout',
  'type': 'exd_layout',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'screen_enabled',
  'type': 'bool',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  201: dict({
  'name': 'exd_data_field_configuration',
  'global_number': 201,
  'group_name': 'Other Messages',
  'fields': dict({
  0: dict({
  'name': 'screen_index',
  'type': 'uint8',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'concept_field',
  'type': 'byte',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'field_id',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 4,
  'accumulate': False,
  'num': 2,
  'bit_offset': 0,
}),
  dict({
  'name': 'concept_count',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 4,
  'accumulate': False,
  'num': 3,
  'bit_offset': 4,
}),
]),
}),
  2: dict({
  'name': 'field_id',
  'type': 'uint8',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'concept_count',
  'type': 'uint8',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'display_type',
  'type': 'exd_display_type',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'title',
  'type': 'string',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  202: dict({
  'name': 'exd_data_concept_configuration',
  'global_number': 202,
  'group_name': 'Other Messages',
  'fields': dict({
  0: dict({
  'name': 'screen_index',
  'type': 'uint8',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'concept_field',
  'type': 'byte',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'field_id',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 4,
  'accumulate': False,
  'num': 2,
  'bit_offset': 0,
}),
  dict({
  'name': 'concept_index',
  'scale': None,
  'offset': None,
  'units': None,
  'bits': 4,
  'accumulate': False,
  'num': 3,
  'bit_offset': 4,
}),
]),
}),
  2: dict({
  'name': 'field_id',
  'type': 'uint8',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'concept_index',
  'type': 'uint8',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'data_page',
  'type': 'uint8',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'concept_key',
  'type': 'uint8',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'scaling',
  'type': 'uint8',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'data_units',
  'type': 'exd_data_units',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'qualifier',
  'type': 'exd_qualifiers',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'descriptor',
  'type': 'exd_descriptors',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'is_signed',
  'type': 'bool',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  206: dict({
  'name': 'field_description',
  'global_number': 206,
  'group_name': 'Activity File Messages',
  'fields': dict({
  0: dict({
  'name': 'developer_data_index',
  'type': 'uint8',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'field_definition_number',
  'type': 'uint8',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'fit_base_type_id',
  'type': 'fit_base_type',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'field_name',
  'type': 'string',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'array',
  'type': 'uint8',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'components',
  'type': 'string',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'scale',
  'type': 'uint8',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'offset',
  'type': 'sint8',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'units',
  'type': 'string',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'bits',
  'type': 'string',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'accumulate',
  'type': 'string',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  13: dict({
  'name': 'fit_base_unit_id',
  'type': 'fit_base_unit',
  'def_num': 13,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  14: dict({
  'name': 'native_mesg_num',
  'type': 'mesg_num',
  'def_num': 14,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  15: dict({
  'name': 'native_field_num',
  'type': 'uint8',
  'def_num': 15,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': 'Must be logged before developer field is used',
}),
  207: dict({
  'name': 'developer_data_id',
  'global_number': 207,
  'group_name': 'Activity File Messages',
  'fields': dict({
  0: dict({
  'name': 'developer_id',
  'type': 'byte',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'application_id',
  'type': 'byte',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'manufacturer_id',
  'type': 'manufacturer',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'developer_data_index',
  'type': 'uint8',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'application_version',
  'type': 'uint32',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': 'Must be logged before field description',
}),
  208: dict({
  'name': 'magnetometer_data',
  'global_number': 208,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Whole second part of the timestamp',
}),
  0: dict({
  'name': 'timestamp_ms',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Millisecond part of the timestamp.',
}),
  1: dict({
  'name': 'sample_time_offset',
  'type': 'uint16',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Each time in the array describes the time at which the compass sample with the corrosponding index was taken. Limited to 30 samples in each message. The samples may span across seconds. Array size must match the number of samples in cmps_x and cmps_y and cmps_z',
}),
  2: dict({
  'name': 'mag_x',
  'type': 'uint16',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
}),
  3: dict({
  'name': 'mag_y',
  'type': 'uint16',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
}),
  4: dict({
  'name': 'mag_z',
  'type': 'uint16',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'These are the raw ADC reading. Maximum number of samples is 30 in each message. The samples may span across seconds. A conversion will need to be done on this data once read.',
}),
  5: dict({
  'name': 'calibrated_mag_x',
  'type': 'float32',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': 'G',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibrated Magnetometer reading',
}),
  6: dict({
  'name': 'calibrated_mag_y',
  'type': 'float32',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': 'G',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibrated Magnetometer reading',
}),
  7: dict({
  'name': 'calibrated_mag_z',
  'type': 'float32',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': 'G',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibrated Magnetometer reading',
}),
}),
  'comment': None,
}),
  209: dict({
  'name': 'barometer_data',
  'global_number': 209,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Whole second part of the timestamp',
}),
  0: dict({
  'name': 'timestamp_ms',
  'type': 'uint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Millisecond part of the timestamp.',
}),
  1: dict({
  'name': 'sample_time_offset',
  'type': 'uint16',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'ms',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Each time in the array describes the time at which the barometer sample with the corrosponding index was taken. The samples may span across seconds. Array size must match the number of samples in baro_cal',
}),
  2: dict({
  'name': 'baro_pres',
  'type': 'uint32',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'Pa',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'These are the raw ADC reading. The samples may span across seconds. A conversion will need to be done on this data once read.',
}),
}),
  'comment': None,
}),
  210: dict({
  'name': 'one_d_sensor_calibration',
  'global_number': 210,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Whole second part of the timestamp',
}),
  0: dict({
  'name': 'sensor_type',
  'type': 'sensor_type',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Indicates which sensor the calibration is for',
}),
  1: dict({
  'name': 'calibration_factor',
  'type': 'uint32',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'baro_cal_factor',
  'type': 'uint32',
  'scale': None,
  'offset': None,
  'units': 'Pa',
  'reference_fields': list([
  dict({
  'name': 'sensor_type',
  'value': 'barometer',
  'def_num': 0,
  'raw_value': 3,
}),
]),
  'components': list([
]),
  'comment': 'Barometer calibration factor',
}),
]),
  'components': list([
]),
  'comment': 'Calibration factor used to convert from raw ADC value to degrees, g,  etc.',
}),
  2: dict({
  'name': 'calibration_divisor',
  'type': 'uint32',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'counts',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Calibration factor divisor',
}),
  3: dict({
  'name': 'level_shift',
  'type': 'uint32',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Level shift value used to shift the ADC value back into range',
}),
  4: dict({
  'name': 'offset_cal',
  'type': 'sint32',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Internal Calibration factor',
}),
}),
  'comment': None,
}),
  225: dict({
  'name': 'set',
  'global_number': 225,
  'group_name': 'Activity File Messages',
  'fields': dict({
  254: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Timestamp of the set',
}),
  0: dict({
  'name': 'duration',
  'type': 'uint32',
  'def_num': 0,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'repetitions',
  'type': 'uint16',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': '# of repitions of the movement',
}),
  4: dict({
  'name': 'weight',
  'type': 'uint16',
  'def_num': 4,
  'scale': 16,
  'offset': None,
  'units': 'kg',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Amount of weight applied for the set',
}),
  5: dict({
  'name': 'set_type',
  'type': 'set_type',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'start_time',
  'type': 'date_time',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Start time of the set',
}),
  7: dict({
  'name': 'category',
  'type': 'exercise_category',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'category_subtype',
  'type': 'uint16',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Based on the associated category, see [category]_exercise_names',
}),
  9: dict({
  'name': 'weight_display_unit',
  'type': 'fit_base_unit',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'wkt_step_index',
  'type': 'message_index',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  227: dict({
  'name': 'stress_level',
  'global_number': 227,
  'group_name': 'Monitoring File Messages',
  'fields': dict({
  0: dict({
  'name': 'stress_level_value',
  'type': 'sint16',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'stress_level_time',
  'type': 'date_time',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Time stress score was calculated',
}),
}),
  'comment': 'Value from 1 to 100 calculated by FirstBeat',
}),
  258: dict({
  'name': 'dive_settings',
  'global_number': 258,
  'group_name': 'Sport Settings File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'name',
  'type': 'string',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'model',
  'type': 'tissue_model_type',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'gf_low',
  'type': 'uint8',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'gf_high',
  'type': 'uint8',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'water_type',
  'type': 'water_type',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'water_density',
  'type': 'float32',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': 'kg/m^3',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Fresh water is usually 1000; salt water is usually 1025',
}),
  6: dict({
  'name': 'po2_warn',
  'type': 'uint8',
  'def_num': 6,
  'scale': 100,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Typically 1.40',
}),
  7: dict({
  'name': 'po2_critical',
  'type': 'uint8',
  'def_num': 7,
  'scale': 100,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Typically 1.60',
}),
  8: dict({
  'name': 'po2_deco',
  'type': 'uint8',
  'def_num': 8,
  'scale': 100,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'safety_stop_enabled',
  'type': 'bool',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'bottom_depth',
  'type': 'float32',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'bottom_time',
  'type': 'uint32',
  'def_num': 11,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  12: dict({
  'name': 'apnea_countdown_enabled',
  'type': 'bool',
  'def_num': 12,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  13: dict({
  'name': 'apnea_countdown_time',
  'type': 'uint32',
  'def_num': 13,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  14: dict({
  'name': 'backlight_mode',
  'type': 'dive_backlight_mode',
  'def_num': 14,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  15: dict({
  'name': 'backlight_brightness',
  'type': 'uint8',
  'def_num': 15,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  16: dict({
  'name': 'backlight_timeout',
  'type': 'backlight_timeout',
  'def_num': 16,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  17: dict({
  'name': 'repeat_dive_interval',
  'type': 'uint16',
  'def_num': 17,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Time between surfacing and ending the activity',
}),
  18: dict({
  'name': 'safety_stop_time',
  'type': 'uint16',
  'def_num': 18,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Time at safety stop (if enabled)',
}),
  19: dict({
  'name': 'heart_rate_source_type',
  'type': 'source_type',
  'def_num': 19,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  20: dict({
  'name': 'heart_rate_source',
  'type': 'uint8',
  'def_num': 20,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
  dict({
  'name': 'heart_rate_antplus_device_type',
  'type': 'antplus_device_type',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'heart_rate_source_type',
  'value': 'antplus',
  'def_num': 19,
  'raw_value': 1,
}),
]),
  'components': list([
]),
}),
  dict({
  'name': 'heart_rate_local_device_type',
  'type': 'local_device_type',
  'scale': None,
  'offset': None,
  'units': None,
  'reference_fields': list([
  dict({
  'name': 'heart_rate_source_type',
  'value': 'local',
  'def_num': 19,
  'raw_value': 5,
}),
]),
  'components': list([
]),
}),
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  259: dict({
  'name': 'dive_gas',
  'global_number': 259,
  'group_name': 'Sport Settings File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'helium_content',
  'type': 'uint8',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'oxygen_content',
  'type': 'uint8',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'status',
  'type': 'dive_gas_status',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  262: dict({
  'name': 'dive_alarm',
  'global_number': 262,
  'group_name': 'Sport Settings File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Index of the alarm',
}),
  0: dict({
  'name': 'depth',
  'type': 'uint32',
  'def_num': 0,
  'scale': 1000,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'time',
  'type': 'sint32',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'enabled',
  'type': 'bool',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'alarm_type',
  'type': 'dive_alarm_type',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'sound',
  'type': 'tone',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'dive_types',
  'type': 'sub_sport',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  264: dict({
  'name': 'exercise_title',
  'global_number': 264,
  'group_name': 'Workout File Messages',
  'fields': dict({
  254: dict({
  'name': 'message_index',
  'type': 'message_index',
  'def_num': 254,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'exercise_category',
  'type': 'exercise_category',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'exercise_name',
  'type': 'uint16',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'wkt_step_name',
  'type': 'string',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  268: dict({
  'name': 'dive_summary',
  'global_number': 268,
  'group_name': 'Other Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'reference_mesg',
  'type': 'mesg_num',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'reference_index',
  'type': 'message_index',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'avg_depth',
  'type': 'uint32',
  'def_num': 2,
  'scale': 1000,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': '0 if above water',
}),
  3: dict({
  'name': 'max_depth',
  'type': 'uint32',
  'def_num': 3,
  'scale': 1000,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
  'comment': '0 if above water',
}),
  4: dict({
  'name': 'surface_interval',
  'type': 'uint32',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Time since end of last dive',
}),
  5: dict({
  'name': 'start_cns',
  'type': 'uint8',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'end_cns',
  'type': 'uint8',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'start_n2',
  'type': 'uint16',
  'def_num': 7,
  'scale': None,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  8: dict({
  'name': 'end_n2',
  'type': 'uint16',
  'def_num': 8,
  'scale': None,
  'offset': None,
  'units': 'percent',
  'subfields': list([
]),
  'components': list([
]),
}),
  9: dict({
  'name': 'o2_toxicity',
  'type': 'uint16',
  'def_num': 9,
  'scale': None,
  'offset': None,
  'units': 'OTUs',
  'subfields': list([
]),
  'components': list([
]),
}),
  10: dict({
  'name': 'dive_number',
  'type': 'uint32',
  'def_num': 10,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  11: dict({
  'name': 'bottom_time',
  'type': 'uint32',
  'def_num': 11,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  17: dict({
  'name': 'avg_ascent_rate',
  'type': 'sint32',
  'def_num': 17,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average ascent rate, not including descents or stops',
}),
  22: dict({
  'name': 'avg_descent_rate',
  'type': 'uint32',
  'def_num': 22,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Average descent rate, not including ascents or stops',
}),
  23: dict({
  'name': 'max_ascent_rate',
  'type': 'uint32',
  'def_num': 23,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Maximum ascent rate',
}),
  24: dict({
  'name': 'max_descent_rate',
  'type': 'uint32',
  'def_num': 24,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Maximum descent rate',
}),
  25: dict({
  'name': 'hang_time',
  'type': 'uint32',
  'def_num': 25,
  'scale': 1000,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'Time spent neither ascending nor descending',
}),
}),
  'comment': None,
}),
  285: dict({
  'name': 'jump',
  'global_number': 285,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'distance',
  'type': 'float32',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'height',
  'type': 'float32',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'rotations',
  'type': 'uint8',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'hang_time',
  'type': 'float32',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'score',
  'type': 'float32',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
  'comment': 'A score for a jump calculated based on hang time, rotations, and distance.',
}),
  5: dict({
  'name': 'position_lat',
  'type': 'sint32',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  6: dict({
  'name': 'position_long',
  'type': 'sint32',
  'def_num': 6,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  7: dict({
  'name': 'speed',
  'type': 'uint16',
  'def_num': 7,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
  dict({
  'name': 'enhanced_speed',
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'bits': 16,
  'accumulate': False,
  'num': 8,
  'bit_offset': 0,
}),
]),
}),
  8: dict({
  'name': 'enhanced_speed',
  'type': 'uint32',
  'def_num': 8,
  'scale': 1000,
  'offset': None,
  'units': 'm/s',
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
  317: dict({
  'name': 'climb_pro',
  'global_number': 317,
  'group_name': 'Activity File Messages',
  'fields': dict({
  253: dict({
  'name': 'timestamp',
  'type': 'date_time',
  'def_num': 253,
  'scale': None,
  'offset': None,
  'units': 's',
  'subfields': list([
]),
  'components': list([
]),
}),
  0: dict({
  'name': 'position_lat',
  'type': 'sint32',
  'def_num': 0,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  1: dict({
  'name': 'position_long',
  'type': 'sint32',
  'def_num': 1,
  'scale': None,
  'offset': None,
  'units': 'semicircles',
  'subfields': list([
]),
  'components': list([
]),
}),
  2: dict({
  'name': 'climb_pro_event',
  'type': 'climb_pro_event',
  'def_num': 2,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  3: dict({
  'name': 'climb_number',
  'type': 'uint16',
  'def_num': 3,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  4: dict({
  'name': 'climb_category',
  'type': 'uint8',
  'def_num': 4,
  'scale': None,
  'offset': None,
  'units': None,
  'subfields': list([
]),
  'components': list([
]),
}),
  5: dict({
  'name': 'current_dist',
  'type': 'float32',
  'def_num': 5,
  'scale': None,
  'offset': None,
  'units': 'm',
  'subfields': list([
]),
  'components': list([
]),
}),
}),
  'comment': None,
}),
})
