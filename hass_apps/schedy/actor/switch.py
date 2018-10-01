"""
This module implements a binary on/off switch, derived from the generic actor.
"""

import voluptuous as vol

from .generic import Generic


CONFIG_SCHEMA = vol.Schema(vol.All(
    lambda v: v.setdefault("states", {
        "on": {
            "service": "homeassistant/turn_on",
        },
        "off": {
            "service": "homeassistant/turn_off",
        },
    }) and False or v,
    Generic.config_schema,
))


class Switch(Generic):
    """A binary on/off switch actor for Schedy."""

    name = "switch"
    config_schema = CONFIG_SCHEMA
