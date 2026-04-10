def __getattr__(name):
    if name == "process_input":
        from rabbit.processors.router import process_input
        return process_input
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["process_input"]
