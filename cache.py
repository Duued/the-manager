from typing import Any


class CacheFullException(Exception):
    def __init__(self, msg="The cache is full."):
        self.msg = msg
        pass


class CacheEmptyException(Exception):
    def __init__(self, msg="The cache is empty."):
        self.msg = msg
        pass


class CacheEntryNotFound(Exception):
    def __init__(self, msg="The cache entry was not found."):
        self.msg = msg
        pass


class Cache:
    def __init__(self, limit: int = -1):
        self.limit = limit
        self.cache_dict: dict[Any, Any] = {}

    def get(self, key: str) -> Any:
        if key in self.cache_dict:
            return self.cache_dict[key]
        return None

    def add(self, key: str, value: Any) -> None:
        if self.limit != -1:
            if len(self.cache_dict) == self.limit:
                raise CacheFullException()
        self.cache_dict[key] = value

    def edit(self, key: str, value: Any) -> None:
        try:
            self.cache_dict[key] = value
        except KeyError:
            raise CacheEntryNotFound()

    def delete(self, key: str) -> None:
        try:
            self.cache_dict[key] = None
        except KeyError:
            raise CacheEntryNotFound()

    def clear(self) -> None:
        self.cache_dict = {}
