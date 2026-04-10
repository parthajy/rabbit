def __getattr__(name):
    if name == "MemoryStore":
        from rabbit.storage.memory_store import MemoryStore
        return MemoryStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["MemoryStore"]
