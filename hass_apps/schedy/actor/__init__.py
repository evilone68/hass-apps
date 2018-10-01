"""
This package contains the various actor implementations.
"""

import typing as T

from .base import Actor
from .generic import Generic
from .switch import Switch
from .thermostat import Thermostat


__all__ = ["Actor", "Generic", "Switch", "Thermostat"]


def get_actor_types() -> T.Iterable[T.Type[Actor]]:
    """Yields available actor classes."""

    globs = globals()
    for actor_class_name in __all__:
        actor_type = globs.get(actor_class_name)
        if actor_type is not Actor and isinstance(actor_type, type) and \
           issubclass(actor_type, Actor):
            yield actor_type
