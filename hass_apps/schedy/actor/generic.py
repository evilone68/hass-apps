"""
This module implements the generic actor.
"""

import typing as T

import copy
import json
import voluptuous as vol

from ... import common
from .base import Actor


STATE_DEF_SCHEMA = vol.Schema(vol.All(
    lambda v: v or {},
    {
        vol.Required("service"): vol.All(
            str,
            lambda v: v.replace(".", "/", 1),
        ),
        vol.Optional("service_data", default=dict): vol.All(
            lambda v: v or {},
            dict,
        ),
        vol.Optional("include_entity_id", default=True): bool,
    },
))

WILDCARD_STATE_NAME_SCHEMA = vol.Schema(vol.All(
    str, str.lower, "_other_",
))

CONFIG_SCHEMA = vol.Schema({
    vol.Optional("state_attr", default="state"): vol.Any(str, None),
    vol.Optional("states", default=dict): vol.All(
        lambda v: v or {},
        {vol.Any(WILDCARD_STATE_NAME_SCHEMA, vol.Extra): STATE_DEF_SCHEMA},
    ),
}, extra=True)


class Generic(Actor):
    """A configurable, generic actor for Schedy."""

    name = "generic"
    config_schema = CONFIG_SCHEMA

    def _get_state_cfg(self, state: str) -> T.Any:
        """Returns the state configuration for given state or None,
        if unknown. _other_ is respected as well."""

        try:
            return self.cfg["states"][state]
        except KeyError:
            return self.cfg["states"].get("_other_")

    @staticmethod
    def deserialize_value(value: str) -> T.Any:
        """Deserializes value from JSON."""

        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError) as err:
            raise ValueError("invalid JSON data: {}".format(repr(err)))

    def do_send(self) -> None:
        """Executes the service configured for self.wanted_value."""

        cfg = self._get_state_cfg(self.wanted_value)
        service = cfg["service"]
        service_data = copy.copy(cfg["service_data"])
        if cfg["include_entity_id"]:
            service_data.setdefault("entity_id", self.entity_id)

        self.log("Calling service {}, data = {}."
                 .format(repr(service), repr(service_data)),
                 level="DEBUG", prefix=common.LOG_PREFIX_OUTGOING)
        self.app.call_service(service, **service_data)

    def filter_set_value(self, value: T.Any) -> T.Any:
        """Checks whether the actor supports this state."""

        if self._get_state_cfg(value) is not None:
            return value

        self.log("State {} is not known by this generic actor, "
                 "ignoring request to set it."
                 .format(repr(value)),
                 level="WARNING")
        return None

    def notify_state_changed(self, attrs: dict) -> None:
        """Is called when the entity's state changes."""

        state_attr = self.cfg["state_attr"]
        if state_attr is None:
            return
        state = attrs.get(state_attr)
        self.log("Attribute {} is {}."
                 .format(repr(state_attr), repr(state)),
                 level="DEBUG", prefix=common.LOG_PREFIX_INCOMING)
        if state is None:
            self.log("Ignoring state of None.", level="DEBUG")
            return

        if state != self.current_value:
            self.log("Received state of {}."
                     .format(repr(state)),
                     prefix=common.LOG_PREFIX_INCOMING)
            self.current_value = state
            self.events.trigger("value_changed", self, state)

    @staticmethod
    def serialize_value(value: T.Any) -> str:
        """Serializes value to JSON."""

        try:
            return json.dumps(value)
        except TypeError as err:
            raise ValueError("can't serialize to JSON: {}".format(err))

    @staticmethod
    def validate_value(value: T.Any) -> T.Any:
        """Accepts any value."""

        return value
