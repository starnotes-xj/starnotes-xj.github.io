from typing import TypeVar


_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class LRUDict(dict[_KT, _VT]):
    def __init__(self, max_size: int):
        super().__init__()
        self.max_size = max_size
        self.lru: dict[_KT, int] = {}

    def __setitem__(self, key: _KT, value):
        if key not in self and len(self) >= self.max_size:
            least_used = sorted(self.lru.items(), key=lambda x: x[1])[0][0]
            del self[least_used]

        self.lru[key] = 0
        super().__setitem__(key, value)

    def __delitem__(self, key: _KT, /) -> None:
        del self.lru[key]
        return super().__delitem__(key)

    def __getitem__(self, key: _KT, /) -> _VT:
        self.lru[key] += 1
        return super().__getitem__(key)
