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


@contextlib.contextmanager
def ctxmng():
    Ctx.reset()
    Ctx.accumulators = profile.Map(model.Accumulator, dict, int)
    Ctx.message_definitions = profile.Map(model.MessageDefinition, dict, int)
    yield Ctx
