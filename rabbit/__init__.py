"""
Rabbit — Memory infrastructure for the world.

Two operations: remember and ask.

Usage:
    from rabbit import Rabbit

    rab = Rabbit("rab_test_abc123")
    rab.remember("Sarah delayed the launch to March 15.", source="meeting")
    answer = rab.ask("When is the launch?")
    print(answer.text)
"""

__version__ = "0.1.0"

from rabbit.sdk.client import Rabbit, RabbitLocal, RabbitAnswer, RabbitMemory, RabbitAlert

__all__ = ["Rabbit", "RabbitLocal", "RabbitAnswer", "RabbitMemory", "RabbitAlert"]
