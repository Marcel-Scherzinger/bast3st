from __future__ import annotations

from typing import Any, NoReturn, Literal
import abc
from string import templatelib
import itertools
import typing
import copy

from bast3st._general import ForceInline
from bast3st.catchable import err
from bast3st.features import (
    FS_read_rundata,
    Features,
    Features2,
    Features3,
    Features4,
)

type StdArrayScopeT = Literal["ior", "list"]
type ArrayScopeT = Literal["arrayview"] | StdArrayScopeT
type MapScopeT = Literal[
    "network",
    "first-capture",
    "read-input",
    "read-output",
    "read-lists",
    "read-randoms",
    "read-variables",
    "read-param",
    "read-flags",
    "mapitem",
    "view",
]
type RelationT = Literal["==", "!=", "<=", ">=", "<", ">"]
"""A comparison operator string to specify the desired relation"""

type SelectorOpcodeT = Literal["var", "arrayitem", "arrayprop", "mapitem", "mapprop"]
type ContainOpcodeT = Literal["contain-onlynum", "contain-num", "contain-text"]


NO_BOOL_ON_CRITERION = "A criterion shouldn't be used in Python boolean expressions, you can't use Pythons and, or and not keywords on it, but & (all_of(...)), | (any_of(...)) and ~ (.negated) work!"


class DecisionEntity(typing.Generic[Features], abc.ABC):
    def _ar(self, *args, **kwargs) -> str:
        """
        This should format custom arguments together with the ones of the base class
        into a comma-separated string

        (stands for _arg_repr)
        """
        fmt_args = [repr(a) for a in args]
        fmt_kwargs = [f"{k}={v!r}" for (k, v) in kwargs.items() if v is not None]
        fmt_kwargs.sort()
        return ", ".join(fmt_args + fmt_kwargs)

    def _repr(self, *args, **kwargs) -> str:
        """Utility that returns a string of class-name(self._ar(*args, **kwargs))"""
        return f"{self.__class__.__name__}({self._ar(*args, **kwargs)})"

    def __bool__(self) -> NoReturn:
        raise TypeError("You can't use bool(...) on decision entities")

    def __format__(self, _: str, /) -> NoReturn:
        raise TypeError(
            "Decision entities should never be used in format string, use Python 3.14 t-strings instead"
        )


################################
# Future values
################################


class Value(DecisionEntity[Features], abc.ABC):
    @typing.overload
    @classmethod
    def of(cls, val: IntoValue[Features]) -> Value[Features]: ...

    @typing.overload
    @classmethod
    def of(cls, val: IntoValue[Features] | None) -> Value[Features] | None: ...

    @classmethod
    def of(cls, val):
        """Exactly like :any:`ofStrict` but returns `None` if input is `None`"""
        if val is not None:
            return cls.ofStrict(val)
        return None

    @classmethod
    def ofStrict(cls, val: IntoValue[Features]) -> Value[Features]:
        """
        Converts a set of supported types into sub-classes of :class:`Value`

        :raise TypeError: If the input is of a not-supported type
        """
        if isinstance(val, Value):
            return val
        elif isinstance(val, (str, int, bool, float)):
            return LitValue(val)
        elif isinstance(val, templatelib.Template):
            return _concat_from_template(val)
        raise TypeError(
            f"Unknown type for Value.of: {type(val)}, maybe you shouln't use this as a value ({val!r})"
        )

    def __eq__(self, value: IntoValue[Features2], /) -> Criterion[Features | Features2]:  # type: ignore
        return compare.eq(self, value)

    def __ne__(self, value: IntoValue[Features2], /) -> Criterion[Features | Features2]:  # type: ignore
        return compare.neq(self, value)

    def __lt__(self, value: IntoValue[Features2], /) -> Criterion[Features | Features2]:
        return compare.lt(self, value)

    def __gt__(self, value: IntoValue[Features2], /) -> Criterion[Features | Features2]:
        return compare.gt(self, value)

    def __le__(self, value: IntoValue[Features2], /) -> Criterion[Features | Features2]:
        return compare.le(self, value)

    def __ge__(self, value: IntoValue[Features2], /) -> Criterion[Features | Features2]:
        return compare.ge(self, value)

    def __add__(
        self, other: IntoValue[Features2], /
    ) -> Value[Features | Features2 | Features2]:
        return SerVal("add", l=self, r=Value.ofStrict(other))

    def __sub__(self, other: IntoValue[Features2], /) -> Value[Features | Features2]:
        return SerVal("sub", l=self, r=Value.ofStrict(other))

    def __mul__(self, other: IntoValue[Features2], /) -> Value[Features | Features2]:
        return SerVal("mul", l=self, r=Value.ofStrict(other))

    def __truediv__(
        self, other: IntoValue[Features2], /
    ) -> Value[Features | Features2]:
        return SerVal("truediv", l=self, r=Value.ofStrict(other))

    def __floordiv__(
        self, other: IntoValue[Features2], /
    ) -> Value[Features | Features2]:
        # // operator (integer division)
        return SerVal("floordiv", l=self, r=Value.ofStrict(other))

    def __mod__(self, other: IntoValue[Features2], /) -> Value[Features | Features2]:
        return SerVal("mod", l=self, r=Value.ofStrict(other))

    def __pow__(self, other: IntoValue[Features2], /) -> Value[Features | Features2]:
        return SerVal("pow", l=self, r=Value.ofStrict(other))

    def __neg__(self, /) -> Value[Features]:
        return SerVal("neg", v=self)

    def __floor__(self, /) -> Value[Features]:
        return SerVal("floor", v=self)

    def __ceil__(self, /) -> Value[Features]:
        return SerVal("ceil", v=self)

    def __round__(self, /) -> Value[Features]:
        return SerVal("round", v=self)

    def __abs__(self, /) -> Value[Features]:
        return SerVal("abs", v=self)

    def contains_text(
        self,
        val: IntoTextValue[Features2],
        *,
        failure_explaination: IntoTextValue[Features3] | None = None,
    ) -> Criterion[Features | Features2 | Features3]:
        return Contained(
            sub=val,
            sup=self,
            mode="contain-text",
            failure_explaination=failure_explaination,
        )

    def contains_only_this_number(
        self,
        val: IntoValue[Features2],
        *,
        failure_explaination: IntoTextValue[Features3] | None = None,
    ) -> Criterion[Features | Features2 | Features3]:
        return Contained(
            sub=val,
            sup=self,
            mode="contain-onlynum",
            failure_explaination=failure_explaination,
        )

    def contains_with_gaps(
        self,
        *val: IntoValue[Features2],
        failure_explaination: IntoTextValue[Features3] | None = None,
    ) -> Criterion[Features | Features2 | Features3]:
        """If this contains a specific sequence of fragments, with arbitraty gaps inbetween"""
        return SerCrit(
            "contain-wgap",
            *val,
            sup=self,
            failure_explaination=failure_explaination,
        )

    def matches(
        self,
        pattern: IntoTextValue[Features2],
        failure_explaination: IntoTextValue[Features3] | None = None,
    ) -> Criterion[Features | Features2 | Features3]:
        """
        If this matches a *Rust regex* regular expression.

        .. warning::

            As :ref:`placeholders-in-future` the pattern will be evaluated **not** by the
            Python :mod:`re` regular expression library, but by the one that is used
            by the server implementation.
            The required syntax can be found in the
            `regex crate <https://docs.rs/regex/latest/regex/#syntax>`_

        """
        return SerCrit(
            "regex",
            pattern=pattern,
            sup=self,
            failure_explaination=failure_explaination,
        )

    def first_capture(
        self, pattern: IntoTextValue[Features2]
    ) -> FutureMapping[Features | Features2]:
        """
        Tries to match a *Rust regex* regular expression and returns
        a mapping of the first match that allows accessing the
        `captured parts <https://docs.rs/regex/latest/regex/#grouping-and-flags>`_.

        .. warning::

            As :ref:`placeholders-in-future` the pattern will be evaluated **not** by the
            Python :mod:`re` regular expression library, but by the one that is used
            by the server implementation.
            The required syntax can be found in the
            `regex crate <https://docs.rs/regex/latest/regex/#syntax>`_

        """
        return FirstPatternCapture(pattern, self)

    def contains_this_number(
        self,
        val: IntoValue[Features2],
        *,
        failure_explaination: IntoTextValue[Features3] | None = None,
    ) -> Criterion[Features | Features2 | Features3]:
        return Contained(
            sub=val,
            sup=self,
            mode="contain-num",
            failure_explaination=failure_explaination,
        )

    def text_is_contained_in(
        self,
        val: IntoTextValue[Features2],
        *,
        failure_explaination: IntoTextValue[Features3] | None = None,
    ) -> Criterion[Features | Features2 | Features3]:
        return Contained(
            sub=self,
            sup=val,
            mode="contain-text",
            failure_explaination=failure_explaination,
        )

    def pipe(
        self, *operations: Transformation[Features2]
    ) -> Value[Features | Features2]:
        """
        Execute a sequence of transformations in order on this value
        and return the final result. The value itself is the input to
        the first :class:`Transformation` and every further
        :class:`Transformation` gets the output of the last as input.
        The last :class:`Transformation`'s output will be returned.
        """
        val: Value[Features | Features2] = self
        for op in operations:
            val = op.on(val)
        return val

    def to_upper(self) -> Value[Features]:
        return self.pipe(to_upper)

    def to_lower(self) -> Value[Features]:
        return self.pipe(to_lower)

    def trim_start(self) -> Value[Features]:
        return self.pipe(trim_start)

    def trim_end(self) -> Value[Features]:
        return self.pipe(trim_end)

    def trim(self) -> Value[Features]:
        return self.pipe(trim)

    @typing.overload
    def catch(
        self,
        error: err,
        *,
        default_value: IntoValue[Features2],
        only_if: Criterion[Features3] | None = None,
    ) -> Value[Features | Features2 | Features3]: ...
    @typing.overload
    def catch(
        self,
        error: err,
        *,
        action: Action[Features2],
        only_if: Criterion[Features3] | None = None,
    ) -> Value[Features | Features2 | Features3]: ...
    @typing.overload
    def catch(
        self,
        error: err,
        *,
        only_if: Criterion[Features2] | None = None,
        default_value: IntoValue[Features3] | None,
        action: Action[Features4] | None,
    ) -> Value[Features | Features2 | Features3 | Features4]: ...

    def catch(
        self,
        error: err,
        *,
        only_if: Criterion[Features2] | None = None,
        default_value: IntoValue[Features3] | None = None,
        action: Action[Features4] | None = None,
    ) -> Value[Features | Features2 | Features3 | Features4]:
        return SerVal(
            "catch",
            v=self,
            error=error,
            only_if=only_if,
            default_value=Value.of(default_value),
            action=action,
        )._with_syntax("meth", as_args=["v"])


type IntoTextValue[Features] = str | templatelib.Template | Value[Features]
"""Any type that can be converted into a :class:`Value` and is likely a text"""

type IntoValue[Features] = IntoTextValue[Features] | float | int | bool
"""Any type that can be converted into a :class:`Value`"""


class LitValue(Value):
    def __init__(self, val: str | int | float | bool) -> None:
        super().__init__()
        self._val = val._val if isinstance(val, LitValue) else val

    def _to_json_able(self, _):
        return dict(op="lit", v=ForceInline(self._val))

    def __repr__(self) -> str:
        return "LitValue(" + repr(self._val) + ")"


################################
# Actions
################################

MsgSeverityT = Literal["info", "warning", "error"]


class Action(DecisionEntity[Features]):
    pass


class SerAct(Action[Features]):
    def __init__(self, opcode: str, *args, **kwargs) -> None:
        super().__init__()
        self.opcode = opcode
        self.args = args
        self.kwargs = kwargs
        self._syntax = "func"

    def _ar(self, *args, **kwargs) -> str:
        return super()._ar(*self.args, *args, **self.kwargs, **kwargs)

    def __repr__(self) -> str:
        if self._syntax == "meth":
            return f"{self.args[0]!r}.{self.opcode}({super()._ar(*self.args[1:], **self.kwargs)})"
        if self._syntax == "prop":
            extra = super()._ar(*self.args[1:], **self.kwargs)
            if len(extra) > 0:
                return f"{self.args[0]!r}.{self.opcode}({extra})"
            else:
                return f"{self.args[0]!r}.{self.opcode}"
        return f"{self.opcode}({self._ar()})"

    def _with_syntax(self, syntax: typing.Literal["func", "meth", "prop"]) -> SerAct:
        self._syntax = syntax
        return self

    def _to_json_able(self, ser):
        return dict(
            op=self.opcode,
            a=ser.register(self.args),
            **{k: ser.register(v) for (k, v) in self.kwargs.items()},
        )


################################
# Transformations
################################


class Transformation(DecisionEntity[Features], abc.ABC):
    def __init__(self) -> None:
        pass

    @abc.abstractmethod
    def on(self, value: IntoValue[Features2]) -> Value[Features | Features2]:
        pass


class SerVal(Value[Features]):
    def __init__(self, opcode: str, *args, **kwargs) -> None:
        super().__init__()
        self.opcode = opcode
        self.args = args
        self.kwargs = kwargs
        self._syntax = ("func", [])

    def _ar(self, *args, **kwargs) -> str:
        return super()._ar(*self.args, *args, **self.kwargs, **kwargs)

    def _to_json_able(self, ser):
        return dict(
            op=self.opcode,
            a=ser.register(self.args),
            **ser.registerDictStar(self.kwargs),
        )

    def __repr__(self) -> str:
        opcode = self.opcode.replace("-", "_")

        args = list(self.args)
        kwargs = dict(self.kwargs)
        for k in self._syntax[1]:
            args.append(kwargs.pop(k))

        if self._syntax[0] == "meth":
            return f"{args[0]!r}.{opcode}({super()._ar(*args[1:], **kwargs)})"
        if self._syntax[0] == "prop":
            extra = super()._ar(*args[1:], **kwargs)
            if len(extra) > 0:
                return f"{args[0]!r}.{opcode}({extra})"
            else:
                return f"{args[0]!r}.{opcode}"
        return f"{opcode}({super()._ar(args, kwargs)})"

    def _with_syntax(
        self,
        syntax: typing.Literal["func", "meth", "prop"],
        as_args: list[str] | None = None,
    ) -> SerVal:
        self._syntax = (syntax, as_args or [])
        return self


class TransformSingleNoParam(Transformation[Features]):
    def __init__(self, opcode: str) -> None:
        super().__init__()
        self.opcode = opcode

    def on(self, value: IntoValue[Features2]) -> Value[Features | Features2]:
        return SerVal(self.opcode, v=value)

    def __call__(self, value: IntoValue[Features2]) -> Value[Features | Features2]:
        return self.on(value)


to_upper = TransformSingleNoParam[Any]("to-upper")
""":class:`Transformation` converting a value to uppercase"""

to_lower = TransformSingleNoParam[Any]("to-lower")
""":class:`Transformation` converting a value to lowercase"""

trim = TransformSingleNoParam[Any]("trim")
""":class:`Transformation` removing all whitespace from start and end of the stringified value"""

trim_start = TransformSingleNoParam[Any]("trim-start")
""":class:`Transformation` removing all whitespace from the start of the stringified value"""

trim_end = TransformSingleNoParam[Any]("trim-end")
""":class:`Transformation` removing all whitespace from the end of the stringified value"""


def concat(*clauses: IntoValue[Features]) -> Value[Features]:
    return SerVal("concat", *[Value.of(c) for c in clauses])


def _concat_from_template(temp: templatelib.Template) -> Value:
    return concat(
        *tuple(
            x
            for pair in itertools.zip_longest(temp.strings, temp.values)
            for x in pair
            if not (isinstance(x, str) and x == "")
        )[:-1]
    )


################################
# Criteria
################################


class Criterion(DecisionEntity[Features]):
    def __init__(self, *, failure_explaination: IntoTextValue[Features] | None) -> None:
        super().__init__()
        self.failure_explaination = Value.of(failure_explaination)

    def __bool__(self) -> NoReturn:
        raise TypeError(NO_BOOL_ON_CRITERION + f" ({self!r})")

    def negate(
        self, *, failure_explaination: IntoTextValue[Features2] | None = None
    ) -> Criterion[Features | Features2]:
        """Create criterion with the success condition negated"""
        return negated(self, failure_explaination=failure_explaination)

    @property
    def negated(self) -> Criterion[Features]:
        """Criterion with the success condition negated"""
        return negated(self)

    def with_failure_explaination(
        self, val: IntoTextValue[Features2]
    ) -> Criterion[Features | Features2]:
        other: Criterion[Features | Features2] = copy.deepcopy(self)
        other.failure_explaination = Value[Features | Features2].of(val)
        return other

    def _ar(self, *args, **kwargs) -> str:
        extend: dict = {}
        if self.failure_explaination is not None:
            extend.update(failure_explaination=self.failure_explaination)
        return super()._ar(*args, **kwargs, **extend)

    @typing.overload
    def catch(
        self,
        error: err,
        *,
        fallback: Criterion[Features2],
        only_if: Criterion[Features3] | None = None,
    ) -> Criterion[Features | Features2 | Features3]: ...
    @typing.overload
    def catch(
        self,
        error: err,
        *,
        action: Action[Features2],
        only_if: Criterion[Features3] | None = None,
    ) -> Criterion[Features | Features2 | Features3]: ...
    @typing.overload
    def catch(
        self,
        error: err,
        *,
        only_if: Criterion[Features2] | None = None,
        fallback: Criterion[Features3] | None,
        action: Action[Features4] | None,
    ) -> Criterion[Features | Features2 | Features3 | Features4]: ...

    def catch(
        self,
        error: err,
        *,
        only_if: Criterion[Features2] | None = None,
        fallback: Criterion[Features3] | None = None,
        action: Action[Features4] | None = None,
    ) -> Criterion[Features | Features2 | Features3 | Features4]:
        return SerCrit(
            "catch",
            c=self,
            error=error,
            only_if=only_if,
            fallback=fallback,
            action=action,
        )


class SerCrit(Criterion[Features]):
    def __init__(
        self,
        opcode: str,
        *args,
        failure_explaination: IntoTextValue[Features] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(failure_explaination=Value.of(failure_explaination))
        self._consname = self.__class__.__name__
        self.opcode = opcode
        self._args = args
        self._kwargs = kwargs

    def _ar(self, *args, **kwargs) -> str:
        return super()._ar(
            *self._args,
            *args,
            **self._kwargs,
            **kwargs,
        )

    def __repr__(self) -> str:
        return f"{self._consname}({self._ar()})"

    def _to_json_able(self, ser):
        return {
            "op": self.opcode,
            "a": ser.register(self._args),
            "fexp": ser.register(self.failure_explaination),
            **ser.registerDictStar(self._kwargs),
        }


class _ConstantCrit(SerCrit):
    def __init__(self, opcode: str, label: str, **kwargs) -> None:
        super().__init__(opcode, **kwargs)
        self._label = label

    def __repr__(self) -> str:
        return str(self._label)


#: a special criterion that is always fulfilled
ALWAYS_FULFILLED: Criterion = _ConstantCrit(
    "special-crit", "ALWAYS_FULFILLED", v="fulfilled"
)

#: a special criterion that is never fulfilled
NEVER_FULFILLED: Criterion = _ConstantCrit(
    "special-crit", "NEVER_FULFILLED", v="not-fulfilled"
)


@typing.overload
def if_then_else(
    if_: Criterion[Features], then_: Criterion[Features2], else_: Criterion[Features3]
) -> Criterion[Features | Features2 | Features3]: ...
@typing.overload
def if_then_else(
    if_: Criterion[Features], then_: IntoValue[Features2], else_: IntoValue[Features3]
) -> Value[Features | Features2 | Features3]: ...
@typing.overload
def if_then_else(
    if_: Criterion[Features], then_: Action[Features2], else_: Action[Features3]
) -> Action[Features | Features2 | Features3]: ...


def if_then_else(if_, then_, else_):  # type: ignore
    if (
        isinstance(then_, Criterion) != isinstance(else_, Criterion)
        or isinstance(then_, Action) != isinstance(else_, Action)
        or isinstance(then_, Value) != isinstance(else_, Value)
    ):
        raise TypeError("Can't use if_then_else with mixed signature for then_/else_")

    if isinstance(then_, Criterion):
        return SerCrit("cifte", i=if_, t=then_, e=else_)
    elif isinstance(then_, Action):
        return SerAct("aifte", i=if_, t=then_, e=else_)
    else:
        return SerVal("vifte", i=if_, t=then_, e=else_)


class compare(SerCrit[Features | Features2 | Features3]):
    def __init__(
        self,
        left: IntoValue[Features],
        relation: RelationT,
        right: IntoValue[Features2],
        *,
        failure_explaination: IntoTextValue[Features3] | None = None,
    ) -> None:
        """
        Compare two future values with a given relation

        :param Value left: first future value
        :param RelationT relation: the comparison relation to use
        :param Value right: second future value
        """
        super().__init__(
            relation,
            l=Value.of(left),
            r=Value.of(right),
            failure_explaination=failure_explaination,
        )

    @property
    def relation(self):
        return self.opcode

    @property
    def left(self) -> Value[Features]:
        return self._kwargs["l"]

    @property
    def right(self) -> Value[Features2]:
        return self._kwargs["r"]

    def __repr__(self) -> str:
        return f"{self.left!r} {self.relation} {self.right!r}"

    @classmethod
    def eq(cls, left: IntoValue[Features], right: IntoValue[Features2]) -> compare:
        return cls(left, "==", right)

    @classmethod
    def neq(cls, left: IntoValue[Features], right: IntoValue[Features2]) -> compare:
        return cls(left, "!=", right)

    @classmethod
    def lt(cls, left: IntoValue[Features], right: IntoValue[Features2]) -> compare:
        return cls(left, "<", right)

    @classmethod
    def gt(cls, left: IntoValue[Features], right: IntoValue[Features2]) -> compare:
        return cls(left, ">", right)

    @classmethod
    def le(cls, left: IntoValue[Features], right: IntoValue[Features2]) -> compare:
        return cls(left, "<=", right)

    @classmethod
    def ge(cls, left: IntoValue[Features], right: IntoValue[Features2]) -> compare:
        return cls(left, ">=", right)


class Contained(SerCrit[Features | Features2 | Features3]):
    def __init__(
        self,
        *,
        sub: IntoValue[Features],
        sup: IntoTextValue[Features2],
        mode: ContainOpcodeT = "contain-text",
        failure_explaination: IntoTextValue[Features3] | None = None,
    ) -> None:
        super().__init__(
            mode,
            sub=Value.of(sub),
            sup=Value.of(sup),
            failure_explaination=failure_explaination,
        )

    @property
    def mode(self) -> ContainOpcodeT:
        return self.opcode  # type: ignore

    @property
    def sub(self) -> Value[Features]:
        return self._kwargs["sub"]

    @property
    def sup(self) -> Value[Features2]:
        return self._kwargs["sup"]

    def __repr__(self) -> str:
        kw = (
            f", failure_explaination={self.failure_explaination!r}"
            if self.failure_explaination is not None
            else ""
        )
        if self.mode == "contain-text":
            return f"{self.sup!r}.contains_text({Criterion._ar(self, self.sub)}{kw})"
        if self.mode == "contain-num":
            return f"{self.sup!r}.contains_this_number({Criterion._ar(self, self.sub)}{kw})"
        if self.mode == "contain-onlynum":
            return f"{self.sup!r}.contains_only_this_number({Criterion._ar(self, self.sub)}{kw})"
        raise TypeError(f"Unexpected contain mode: {self.mode}")


################################
# Criterion junctors
################################


def negated(
    criterion: Criterion[Features],
    *,
    failure_explaination: IntoTextValue[Features2] | None = None,
) -> Criterion[Features | Features2]:
    """Negate a criterion so that it accepts exactly when the original one didn't accept"""
    c: SerCrit[Features | Features2] = SerCrit(
        "negated", c=criterion, failure_explaination=failure_explaination
    )
    c._consname = "negated"
    return c


class all_of(SerCrit[Features | Features2]):
    def __init__(
        self,
        *clauses: Criterion[Features],
        failure_explaination: IntoTextValue[Features2] | None = None,
    ) -> None:
        _clauses: list[Criterion[Features]] = []
        for c in clauses:
            if isinstance(c, self.__class__):
                _clauses.extend(c._args)
            else:
                _clauses.append(c)

        super().__init__(
            self.__class__.__name__.replace("_", "-"),
            *_clauses,
            failure_explaination=failure_explaination,
        )

    pass


class any_of(SerCrit[Features | Features2]):
    def __init__(
        self,
        *clauses: Criterion[Features],
        failure_explaination: IntoTextValue[Features2] | None = None,
    ) -> None:
        _clauses: list[Criterion[Features]] = []
        for c in clauses:
            if isinstance(c, self.__class__):
                _clauses.extend(c._args)
            else:
                _clauses.append(c)

        super().__init__(
            self.__class__.__name__.replace("_", "-"),
            *_clauses,
            failure_explaination=failure_explaination,
        )


################################
# Selectors
################################


class Selector(Value[Features]):
    def __init__(self, opcode: SelectorOpcodeT, *args) -> None:
        Value.__init__(self)
        self._opcode = opcode
        self._args = args


class FutureArray(typing.Protocol[Features]):
    """
    A :class:`FutureArray` represents a specific source of multiple
    values that are available – somewhere in the future – during the
    evaluation of a submission.

    Examples are:
        - :any:`INPUT`: access the input a submission got in the current test
        - :any:`OUTPUT`: access the output a submission produced
        - :any:`LIST(name) <LIST>`: access the list with the provided name

    This type can be used similarily to a list of :class:`Selector`'s:

    >>> first_input = INPUT.first # or INPUT[0]
    >>> first_input
    INPUT[0]
    >>> last_output = OUTPUT.last # or OUTPUT[-1]
    >>> last_output
    OUTPUT[-1]
    >>> mylist = LIST("mylist")
    >>> second_item = mylist[1] # or mylist.index1(2)
    >>> second_item
    LIST("mylist")[1]
    >>> length_of_mylist = mylist.length # don't use len(mylist)
    >>> length_of_mylist
    LIST("mylist").length

    .. attention::

        The values you receive are special instances of :class:`Selector`
        and can be understood as placeholders.
        For more see :ref:`placeholders-in-future`.


    (This type should not be instantiated directly)
    """

    def sum(self) -> Value[Features]:
        """Sum all values of the mapping, texts and collections count as zeros"""
        ...

    def __getitem__(self, key: IntoValue[Features2]) -> Value[Features | Features2]: ...
    @property
    def last(self) -> Value[Features]: ...
    @property
    def length(self) -> Value[Features]: ...
    @property
    def first(self) -> Value[Features]: ...
    def from_start1(self, onebased_n: int) -> Value[Features]: ...
    def from_end1(self, onebased_n: int) -> Value[Features]: ...
    def index1(self, onebased_n: int) -> Value[Features]: ...


def LIST(name: str) -> FutureArray[FS_read_rundata]:
    return LISTS[name]


def VAR(name: str) -> Value[FS_read_rundata]:
    return VARIABLES[name]


class FutureMapping(DecisionEntity[Features]):
    """
    This is a key-value-mapping that lives in the future. (See :class:`FutureArray`)
    """

    def __init__(self, kind: MapScopeT, *args, **kwargs) -> None:
        super().__init__()
        self._kind: MapScopeT = kind
        self._args = args
        self._kwargs = kwargs
        self._definitly_array = False

    def _to_json_able(self, ser):
        return dict(
            op=self._kind,
            a=ser.register(self._args),
            **ser.registerDictStar(self._kwargs),
        )

    @property
    def kind(self) -> MapScopeT:
        return self._kind

    def __getitem__(
        self,
        key: IntoValue[Features2]
        | list[IntoValue[Features2]]
        | tuple[IntoValue[Features2], ...],
    ) -> FutureMapItem[Features, Features2]:
        """
        Get the item with the specified key.

        If the provided key is a sequence (tuple/list) of atomic key values,
        this is interpreted as accessing multiple nesting levels deep.
        This is important for JSON-like structures with multiple levels.
        """
        return FutureMapItem(self, key)

    @property
    def length(self) -> Value[Features]:
        """The number of items in the mapping"""
        return SerVal("property", p="length", v=self)._with_syntax(
            "prop", as_args=["v", "p"]
        )

    def keys(self) -> FutureArray[Features]:
        """Array of all keys of the mapping (indexed by numbers), in their sorting order"""
        return FutureViewMapping("view", "keys", self)

    def sum(self) -> Value[Features]:
        """Sum all values of the mapping, texts and collections count as zeros"""
        return SerVal("property", p="sum", v=self)._with_syntax(
            "prop", as_args=["v", "p"]
        )

    def values(self) -> FutureArray[Features]:
        """Array of all values of the mapping (indexed by numbers), in the order of the sorted keys"""
        return FutureViewMapping("view", "values", self)

    @property
    def last(self) -> Value[Features]:
        """
        On arrays this will return the last element (length-1),
        but on mappings this will be the element with the biggest key (sort order)
        """
        if self._definitly_array:
            return self[-1]
        return self.values()[-1]

    @property
    def first(self) -> Value[Features]:
        """
        On arrays this will return the first element (index 0),
        but on mappings this will be the element with the smallest key (sort order)
        """
        if self._definitly_array:
            return self[0]
        return self.values()[0]

    def from_start1(self, onebased_n: int) -> Value[Features]:
        assert onebased_n > 0, f"{onebased_n=} should be at least 1"
        return self[onebased_n - 1]

    def from_end1(self, onebased_n: int) -> Value[Features]:
        assert onebased_n > 0, f"{onebased_n=} should be at least 1"
        return self[-onebased_n]

    def index1(self, onebased_n: int) -> Value[Features]:
        assert onebased_n != 0, (
            "index1(1) means first element, index1(-1) last, but index1(0) is undefined"
        )
        if onebased_n > 0:
            return self[onebased_n - 1]
        return self[-onebased_n]

    def __repr__(self) -> str:
        return super()._repr(*self._args, **self._kwargs)

    def _format_item_repr(self, key: tuple[Value, ...], base: str | None = None) -> str:
        keys = "".join([f"[{k!r}]" for k in key])
        base = base if base is not None else repr(self)
        return f"{base}{keys}"


class FutureMapItem(
    Selector[Features | Features2], FutureMapping[Features | Features2]
):
    def __init__(
        self,
        mapping: FutureMapping[Features],
        key: IntoValue[Features2]
        | tuple[IntoValue[Features2], ...]
        | list[IntoValue[Features2]],
    ) -> None:
        if not isinstance(key, tuple) and not isinstance(key, list):
            key = (key,)
        if isinstance(mapping, FutureMapItem):
            key = (*mapping._my_key, *key)
            mapping = mapping._mapping
        key = tuple([Value.of(k) for k in key])
        # set both constructors to the same *args as both of them
        # set self._args. Thisway we know exactly what self._args will be
        FutureMapping.__init__(self, "mapitem", mapping, key)
        Selector.__init__(self, "mapitem", mapping, key)

    def _to_json_able(self, ser):
        if (sect := getattr(self._mapping, "_direct_section", None)) is not None:
            return dict(op="cmapitem", m=sect, k=ser.register(self._my_key))
        else:
            return dict(
                op="mapitem",
                m=ser.register(self._mapping),
                k=ser.register(self._my_key),
            )

    @property
    def _mapping(self):
        return self._args[0]

    @property
    def _my_key(self) -> tuple[Value, ...]:
        return self._args[1]

    def __repr__(self) -> str:
        return self._mapping._format_item_repr(self._my_key)


class FutureViewMapping(FutureMapping[Features]):
    @property
    def perspective(self):
        """The thing this view makes accessible"""
        return self._kwargs["p"]

    @property
    def inner_viewed(self):
        return self._kwargs["m"]

    def __init__(
        self,
        kind: Literal["view"],
        perspective: Literal["keys", "values"],
        mapping: FutureMapping[Features],
        /,
    ) -> None:
        super().__init__(kind, p=perspective, m=mapping)

    def __repr__(self) -> str:
        return f"{self.inner_viewed!r}.{self.perspective}()"

    pass


class FirstPatternCapture(FutureMapping[Features | Features2]):
    def __init__(
        self, pattern: IntoTextValue[Features], value: Value[Features2]
    ) -> None:
        super().__init__("first-capture", p=pattern, sup=value)

    def __repr__(self) -> str:
        return f"{self._kwargs['sup']!r}.first_capture({self._kwargs['p']}!r)"


class NetworkRequest(FutureMapping[Features | Features2 | Features3]):
    """
    A network request to a specific server.
    The server's domain has to be a static string and must be explicitly
    whitelisted by the server administrator

    .. todo:: name the error if not whitelisted

    .. todo:: explicit response attribute methods for selecting.

    :param str server: The server to contact
    :param str route: The part after the first slash that specifies the route on the server
    :param method: The `HTTP Method <https://developer.mozilla.org/en/docs/Web/HTTP/Reference/Methods>`_
        to use for the request. Only `GET` and `POST` are supported
    :param json: A :class:`dict` of values that should be sent as json to the specified url.
        The json attribute is **not** available for `GET` requests.
    :param allowed_status: The
        `HTTP status codes <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status>`_
        of the response that are considered normal behaviour of the API.
        This can be a single number or a :class:`tuple` of status codes.
        If the server responds with a code that isn't listed here, it will be considered
        one of the :ref:`catchable-errors`,
        but only if a map item is used that is expected to require a successful response.

    :ref:`catchable-errors`
    -----------------------

    - :any:`err.network_statusDisallowed`
    - :any:`err.network_respInvalid_notJson`
    - :any:`err.network`
    """

    @typing.overload
    def __init__(
        self,
        *,
        server: str,
        route: IntoTextValue[Features],
        method: Literal["GET"],
        allowed_status: int | tuple[int, ...] = 200,
    ) -> None: ...

    @typing.overload
    def __init__(
        self,
        *,
        server: str,
        route: IntoTextValue[Features],
        method: Literal["POST"],
        json: dict[str, IntoValue[Features3]]
        | list[tuple[IntoValue[Features2], IntoValue[Features3]]]
        | None = None,
        allowed_status: int | tuple[int, ...] = 200,
    ) -> None: ...

    def __init__(
        self,
        *,
        server: str,
        route: IntoTextValue[Features],
        method: Literal["GET", "POST"],
        json: dict[str, IntoValue[Features3]]
        | list[tuple[IntoValue[Features2], IntoValue[Features3]]]
        | None = None,
        allowed_status: int | tuple[int, ...] = 200,
    ) -> None:
        if isinstance(json, dict):
            json = [(k, Value.of(v)) for (k, v) in json.items()]
        elif isinstance(json, list):
            json = [(Value.of(k), Value.of(v)) for (k, v) in json]

        if isinstance(allowed_status, int):
            allowed_status = (allowed_status,)

        super().__init__(
            "network",
            server=server,
            route=Value.of(route),
            method=method,
            json=json,
            **{"allowed-status": [ForceInline(a) for a in allowed_status]},
        )


class _Data(FutureMapping[Features]):
    """
    :ref:`catchable-errors`
    -----------------------

    .. todo:: fill
    """

    def __init__(
        self,
        section: Literal["input", "output", "randoms", "lists", "variables", "flags"],
    ) -> None:
        super().__init__(
            "read-" + section,
        )
        self._section = section
        self._direct_section = section

    def __getitem__(  # type: ignore
        self, key
    ) -> FutureMapItem:
        return super().__getitem__(key)

    def __repr__(self) -> str:
        return self._section.upper()


class _Param(FutureMapping[Features]):
    def __init__(
        self,
    ) -> None:
        super().__init__("read-param")
        self._section = "param"
        self._direct_section = "param"

    def __getitem__(  # type: ignore
        self, key: tuple[Literal["my", "doc", "teststatus"], *tuple[IntoValue, ...]]
    ) -> FutureMapItem:
        return super().__getitem__(key)

    def my(self, *key: IntoValue) -> FutureMapItem:
        """
        Parameters that the user set in his account or specifically on the server
        for the specific url slot where this specification is registered.
        (they can't be changed during runtime.)
        """
        return self["my", *key]

    # @typing.overload
    # def doc(
    #     self, scope1: Literal["blockcount"], scope2: Literal["group"], group: str, /
    # ) -> Value: ...
    @typing.overload
    def doc(
        self, scope1: Literal["blockcount"], scope2: Literal["opcode"], opcode: str, /
    ) -> Value: ...
    @typing.overload
    def doc(
        self, scope1: Literal["blockcount"], scope2: Literal["total"], /
    ) -> Value: ...
    @typing.overload
    def doc(self, scope1: Literal["blockcount"], /) -> FutureMapItem: ...

    def doc(self, *key: IntoValue) -> FutureMapItem:  # type: ignore
        """
        Information about the scratch document that contains the submission.
        """
        return self["doc", *key]

    # def teststatus(self, *key: IntoValue):
    #     return self["teststatus", *key]

    def __repr__(self) -> str:
        return self._section.upper()


OUTPUT: FutureArray[FS_read_rundata] = _Data("output")
""":class:`FutureArray` that represents the output a submission produced during the current test"""

INPUT: FutureArray[FS_read_rundata] = _Data("input")
""":class:`FutureArray` that represents the output a submission got during the current test"""

RANDOMS: FutureArray[FS_read_rundata] = _Data("randoms")
""":class:`FutureArray` that represents the random numbers a submission requested and got during the current test"""

FLAGS: FutureMapping = _Data("flags")
""":class:`FutureMapping` that allows reading arbitraty flags, see :ref:`concept-flags` for details"""

LISTS: FutureMapping[FS_read_rundata] = _Data("lists")
VARIABLES: FutureArray[FS_read_rundata] = _Data("variables")

PARAM = _Param()  # type: ignore
""":class:`FutureMapping` that allows reading set parameters, see :ref:`concept-param` for details"""

BLOCKCOUNT: FutureMapping[Any] = PARAM.doc("blockcount")
