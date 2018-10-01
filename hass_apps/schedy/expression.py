"""
Module containing functionality to evaluate expressions.
"""

import typing as T
if T.TYPE_CHECKING:
    # pylint: disable=cyclic-import,unused-import
    from . import schedule
    from .app import SchedyApp
import types

import datetime


__all__ = ["Abort", "Add", "Break", "IncludeSchedule", "Result", "Skip"]


# type of an evaluable expression
ExprType = T.Union[str, types.CodeType]


class AddibleMixin:
    """Mixin that marks an expression's result as addible."""

    def __init__(self, value: T.Any) -> None:
        self.value = value

    def __eq__(self, other: T.Any) -> bool:
        return type(self) is type(other) and self.value == other.value

class ResultBase:
    """Holds the result of an expression."""

    def __eq__(self, other: T.Any) -> bool:
        return type(self) is type(other)

class Result(ResultBase, AddibleMixin):
    """Final result of an expression."""

    def __repr__(self) -> str:
        return "Result({})".format(repr(self.value))

class Abort(ResultBase):
    """Result of an expression that should cause scheduling to be aborted
    and the value left unchanged."""

    def __repr__(self) -> str:
        return "Abort()"

class Add(ResultBase, AddibleMixin):
    """Result of an expression to which the result of a consequent
    expression should be added."""

    def __add__(self, other: ResultBase) -> ResultBase:
        if not isinstance(other, AddibleMixin):
            raise TypeError("can't add {} and {}"
                            .format(repr(type(self)), repr(type(other))))

        return type(other)(self.value + other.value)

    def __repr__(self) -> str:
        return "Add({})".format(repr(self.value))

class Break(ResultBase):
    """Result of an expression that should cause the rest of a
    sub-schedule to be skipped."""

    def __init__(self, levels: int = 1) -> None:
        if not isinstance(levels, int) or levels < 1:
            raise ValueError(
                "levels to break must be >= 1, but is {}".format(repr(levels))
            )
        self.levels = levels

    def __repr__(self) -> str:
        return "Break({})".format(self.levels if self.levels != 1 else "")

class IncludeSchedule(ResultBase):
    """Result that inserts a schedule in place for further processing."""

    def __init__(self, sched: "schedule.Schedule") -> None:
        self.schedule = sched

    def __repr__(self) -> str:
        return "IncludeSchedule({})".format(self.schedule)

class Skip(ResultBase):
    """Result of an expression which should be ignored."""

    def __repr__(self) -> str:
        return "Skip()"


def build_expr_env(app: "SchedyApp") -> T.Dict[str, T.Any]:
    """This function builds and returns an environment usable as globals
    for the evaluation of an expression. It will add all members
    of this module's __all__ to the environment. Additionally, some
    helpers will be constructed based on the SchedyApp object"""

    # use date/time provided by appdaemon to support time-traveling
    now = app.datetime()
    env = {
        "app": app,
        "schedule_snippets": app.cfg["schedule_snippets"],
        "datetime": datetime,
        "now": now,
        "date": now.date(),
        "time": now.time(),
        "state": app.get_state,
        "is_on":
            lambda entity_id: str(app.get_state(entity_id)).lower() == "on",
        "is_off":
            lambda entity_id: str(app.get_state(entity_id)).lower() == "off",
    }

    globs = globals()
    for name in __all__:
        env[name] = globs[name]

    env.update(app.expression_modules)

    return env

def eval_expr(
        expr: ExprType,
        app: "SchedyApp",
        extra_env: T.Optional[T.Dict[str, T.Any]] = None
) -> ResultBase:
    """This method evaluates the given expression. The evaluation result
    is returned. The items of the extra_env dict are added to the globals
    available during evaluation."""

    # pylint: disable=eval-used

    env = build_expr_env(app)
    if extra_env:
        env.update(extra_env)

    eval_result = eval(expr, env)

    if not isinstance(eval_result, ResultBase):
        return Result(eval_result)
    return eval_result
