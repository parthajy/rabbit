def __getattr__(name):
    if name == "RabbitCore":
        from rabbit.core.engine import RabbitCore
        return RabbitCore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["RabbitCore"]
