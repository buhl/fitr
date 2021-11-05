# -*- coding: utf-8 -*-

import contextlib
import contextvars

from . import profile
from . import model


class Meta(type):
    _vars = {}
    def __getattr__(self, attr):
        if attr not in self._vars:
            raise AttributeError(f"type object '{self.__qualname__}' has no attribute '{attr}'")
        return self._vars.get(attr).get()

    def __setattr__(self, attr, value):
        self._vars[attr] = self._vars.get(attr, contextvars.ContextVar(attr)).set(value).var

    def __copy__(self):
        return contextvars.copy_context()

    def keys(self):
        return self._vars.keys()

    def values(self):
        return (_.get() for _ in self._vars.values())

    def reset(self):
        for k in list(self.keys()):
            del self._vars[k]


class Ctx(metaclass=Meta):
    pass

class DevField(profile.Base):
    def __init__(self, dev_data_index, def_num, base_type, name, units, native_field_num):
       self.dev_data_index=dev_data_index
       self.def_num=def_num
       self.type=base_type
       self.name=name
       self.units=units
       self.native_field_num=native_field_num


class DevDataType(profile.Base):
    def __init__(self, developer_data_index, application_id=None, fields=None):
        self.developer_data_index = developer_data_index
        self.application_id = application_id
        self.fields = fields or profile.Map(DevField, dict, int)

@contextlib.contextmanager
def ctxmng():
    Ctx.reset()
    Ctx.developer_data_types = profile.Map(DevDataType, dict, int)
    Ctx.accumulators = profile.Map(model.Accumulator, dict, int)
    Ctx.message_definitions = profile.Map(model.MessageDefinition, dict, int)
    Ctx.compressed_ts_accumulator = None
    yield Ctx
