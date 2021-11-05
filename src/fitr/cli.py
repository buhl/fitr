# -*- coding: utf-8 -*-

import sys

from .readers import FitFileMemory
from .fitfile import FitFile

class FitR():
    def __init__(self, fitfile):
        self._memory = FitFileMemory(fitfile)

    def get_fitfiles(self):
        while self._memory.tell() < len(self._memory):
            ff = FitFile(self._memory.copy())
            for message in ff.messages():
                #print(f"{message!r}")
                ...
            self._memory.seek(self._memory.tell() + ff.file_size)


def run():
    fitr = FitR(sys.argv[-1])
    fitr.get_fitfiles()
