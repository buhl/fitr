


class Map():
    def __init__(self, value_type, map_type=list, key_type=str, map=None):
        self._map = map_type() if map_type in [list, dict, set] else list()
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

            else:
                return method


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
            else:
                return method

        elif isinstance(self._map, set):
            if attr == "add":
                def add(value):
                    if not isinstance(value, self._value_type):
                        raise ValueError(f"'{self.__class__.__name__}' can only contain '{self._value_type.__class__.__name__}'")
                    return method(value)
                return add

            elif attr == "symmetric_difference_update":
                def symmetric_difference_update(value):
                    if not all(isinstance(v, self._value_type) for v in value):
                        raise ValueError(f"'{self.__class__.__name__}' can only contain '{self._value_type.__class__.__name__}'")
                    return method(value)
                return symmetric_difference_update
                
            elif attr.endswith("update"):
                def updates(*values):
                    for set_value in values:
                        if not all(isinstance(v, self._value_type) for v in set_value):
                            raise ValueError(f"'{self.__class__.__name__}' can only contain '{self._value_type.__class__.__name__}'")
                    return method(*values)
                return updates

            else:
                return method


        raise AttributeError(f"'{self.__class__.__name__}' object does not support attribute '{attr}'")

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

if __name__ == "__main__":
    class TypeValue():
        def __init__(self, name, value, comment=None):
            self.name = name
            self.value = value
            self.comment = comment


    mgb = TypeValue("mgb", 41)
    srg = TypeValue("srg", 36)
    grg = TypeValue("grg", 63)
    irg = TypeValue("irg", 64)

    lmap = Map(TypeValue)
    assert not lmap
    lmap.append(mgb)
    lmap.append(srg)
    lmap.extend([grg, irg])
    assert lmap

    try:
        lmap.append("test")
    except ValueError as e:
        ...

    assert lmap.pick(0) == mgb
    assert lmap.pick(name="srg") == 1
    assert lmap.pick(True, name="grg") == grg
    assert len(lmap) == 4
    assert list(lmap) == [mgb, srg, grg, irg]
    del lmap[2]
    assert len(lmap) == 3
    assert list(lmap) == [mgb, srg, irg]

    lmap = Map(TypeValue, map=[mgb, srg, grg, irg])
    assert lmap.pick(0) == mgb
    assert lmap.pick(name="srg") == 1
    assert lmap.pick(True, name="grg") == grg
    assert len(lmap) == 4
    assert list(lmap) == [mgb, srg, grg, irg]
    del lmap[2]
    assert len(lmap) == 3
    assert list(lmap) == [mgb, srg, irg]

    dmap = Map(TypeValue, dict)
    assert not dmap
    dmap["mgb"] = mgb
    dmap["srg"] = srg
    dmap.update({"grg": grg, "irg": irg})
    assert dmap
    assert dmap.pick("mgb") == mgb
    assert dmap.pick("notthere") == None
    assert dmap.pick(name="srg") == "srg"
    assert dmap.pick(name="notthere") == None
    assert dmap.pick(True, name="grg") == grg
    assert dmap.pick(True, name="notthere") == None
    assert len(dmap) == 4
    assert dict(dmap) == {"mgb": mgb, "srg": srg, "grg": grg, "irg": irg}
    del dmap["mgb"]
    assert len(dmap) == 3
    assert dict(dmap) == {"srg": srg, "grg": grg, "irg": irg}


    dmap = Map(TypeValue, dict, map={"mgb": mgb, "srg": srg, "grg": grg, "irg": irg})
    assert dmap
    assert dmap.pick("mgb") == mgb
    assert dmap.pick("notthere") == None
    assert dmap.pick(name="srg") == "srg"
    assert dmap.pick(name="notthere") == None
    assert dmap.pick(True, name="grg") == grg
    assert dmap.pick(True, name="notthere") == None
    assert len(dmap) == 4
    assert dict(dmap) == {"mgb": mgb, "srg": srg, "grg": grg, "irg": irg}
    del dmap["mgb"]
    assert len(dmap) == 3
    assert dict(dmap) == {"srg": srg, "grg": grg, "irg": irg}

    dimap = Map(TypeValue, dict, int)
    assert not dimap
    dimap[0] = mgb
    dimap[1] = srg
    dimap.update({2: grg, 0: irg})
    assert dimap
    assert dimap.pick(0) == irg
    assert dimap.pick(name="srg") == 1
    assert dimap.pick(True, name="mgb") == None
    assert dimap.pick(True, name="irg") == irg
    assert len(dimap) == 3
    assert dict(dimap) == {0: irg, 1: srg, 2: grg}
    del dimap[1]
    assert len(dimap) == 2
    assert dict(dimap) == {0: irg, 2: grg}

    dimap = Map(TypeValue, dict, int, map={0: irg, 1: srg, 2: grg})
    assert dimap
    assert dimap.pick(0) == irg
    assert dimap.pick(name="srg") == 1
    assert dimap.pick(True, name="mgb") == None
    assert dimap.pick(True, name="irg") == irg
    assert len(dimap) == 3
    assert dict(dimap) == {0: irg, 1: srg, 2: grg}
    del dimap[1]
    assert len(dimap) == 2
    assert dict(dimap) == {0: irg, 2: grg}

    smap = Map(TypeValue, set)
    assert not smap
    smap.add(mgb)
    smap.add(srg)
    smap.update([grg, irg])
    assert smap

    try:
        smap.add("test")
    except ValueError as e:
        ...

    assert smap.pick(0) == mgb
    assert smap.pick(name="srg") == 3
    assert smap.pick(True, name="grg") == grg
    assert len(smap) == 4
    assert set(smap) == {mgb, srg, grg, irg}
    smap.remove(grg)
    assert len(smap) == 3
    assert set(smap) == {mgb, srg, irg}

    smap = Map(TypeValue, set, map={mgb, srg, grg, irg})
    assert smap.pick(0) == mgb
    assert smap.pick(name="srg") == 3
    assert smap.pick(True, name="grg") == grg
    assert len(smap) == 4
    assert set(smap) == {mgb, srg, grg, irg}
    smap.remove(grg)
    assert len(smap) == 3
    assert set(smap) == {mgb, srg, irg}

