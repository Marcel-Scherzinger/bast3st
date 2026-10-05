from __future__ import annotations
import json
from typing import Literal, Mapping, Self

from bast3st.actions import send_error
from bast3st.decisions import (
    ALWAYS_FULFILLED,
    BLOCKCOUNT,
    Action,
    Criterion,
    IntoTextValue,
)
from bast3st.features import (
    PermittedFEAT_CondAltTestActAct,
    PermittedFEAT_CondAltTestActCrit,
    PermittedFEAT_CondCatActAct,
    PermittedFEAT_CondCatActCrit,
    PermittedFEAT_CondSpecActAct,
    PermittedFEAT_CondSpecActCrit,
    PermittedFEAT_CondTestActAct,
    PermittedFEAT_CondTestActCrit,
    PermittedFEAT_PassTestCrit,
)
from bast3st.ser import DecisionSerializer, _ser_post_process


class SpecEntity:
    def __init__(self) -> None:
        self._if_then_actions: list = []

    def _extra_hooks(self) -> list[tuple]:
        return []

    def _hooks_to_json_like(self, ser):
        hooks = {}
        for order, (criterion, action) in self._if_then_actions + self._extra_hooks():
            group = hooks.get(order, [])
            group.append([ser.register(criterion), ser.register(action)])

            hooks[order] = group
        return hooks

    def _ar(self, *args, **kwargs) -> str:
        """
        This should format custom arguments together with the ones of the base class
        into a comma-separated string, copied from DecisionEntity

        (stands for _arg_repr)
        """
        fmt_args = [repr(a) for a in args]
        fmt_kwargs = [f"{k}={v!r}" for (k, v) in kwargs.items() if v is not None]
        fmt_kwargs.sort()
        return ", ".join(fmt_args + fmt_kwargs)

    def _repr(self, *args, **kwargs) -> str:
        """Utility that returns a string of class-name(self._ar(*args, **kwargs))"""
        b = f"{self.__class__.__name__}({self._ar(*args, **kwargs)})"
        for order, (crit, act) in self._if_then_actions:
            b += f".if_criterion_then({crit!r}, {act!r}, order={order!r})"
        return b


class Bast3StSpec(SpecEntity):
    def __init__(self, title: str, *, description: str | None = None) -> None:
        super().__init__()
        self._title = title
        self._description = description
        self._categories = []
        self._limit = None

    def _extra_hooks(self) -> list[tuple]:
        return [self._limit] if self._limit is not None else []

    def set_block_count_limit(
        self,
        maximum: int,
        error_msg: IntoTextValue[PermittedFEAT_CondSpecActAct] | None = None,
    ):
        if error_msg is None:
            error_msg = (
                f"Sie verwenden zu viele Blöcke. Maximal erlaubt sind {maximum}."
            )
        self._limit = (
            "before-all-categories",
            (BLOCKCOUNT["total"] > maximum, send_error(error_msg)),
        )
        pass

    def new_category(self, title: str, *, description: str | None = None) -> Category:
        self._categories.append(Category(title=title, description=description))
        return self._categories[-1]

    def if_criterion_then(
        self,
        criterion: Criterion[PermittedFEAT_CondSpecActCrit],
        action: Action[PermittedFEAT_CondSpecActAct],
        order: Literal[
            "before-all-categories", "after-all-categories"
        ] = "after-all-categories",
    ) -> Self:
        self._if_then_actions.append((order, (criterion, action)))
        return self

    def run_action(
        self,
        action: Action[PermittedFEAT_CondSpecActAct],
        order: Literal[
            "before-all-categories", "after-all-categories"
        ] = "after-all-categories",
    ) -> Self:
        return self.if_criterion_then(ALWAYS_FULFILLED, action=action, order=order)

    def __repr__(self) -> str:
        return self._repr(title=self._title, description=self._description)

    def to_json(self, *, indent: int | None = None):
        ser = DecisionSerializer()
        base = self._to_json(ser)
        base["nodes"] = ser._final
        return json.dumps(base, indent=indent, default=_ser_post_process)

    def _node_dict(self):
        ser = DecisionSerializer()
        self._to_json(ser)
        return ser._final

    def _to_json(self, ser):
        base: dict = dict(
            title=self._title,
        )
        if self._description is not None:
            base["description"] = self._description
        if len(self._categories) > 0:
            base["categories"] = [x._to_json(ser) for x in self._categories]
        hooks = self._hooks_to_json_like(ser)
        if len(hooks) > 0:
            base["hooks"] = hooks

        return base

    pass


class Category(SpecEntity):
    def __init__(self, title, description) -> None:
        super().__init__()
        self._title = title
        self._description = description
        self._maintests: list = []

    def with_description(self, new_description: str | None) -> Self:
        self._description = new_description
        return self

    def new_test(
        self,
        title: str | None = None,
        *,
        criterion: Criterion[PermittedFEAT_PassTestCrit],
        input: list[str | int | float] | None = None,
        random_generation: bool | int | None = None,
        predefined_randoms: list[int | float] | None = None,
        initial_variables: Mapping[str, str | int | float] | None = None,
        initial_lists: Mapping[str, list[str | int | float]] | None = None,
    ) -> MainTest:
        self._maintests.append(
            MainTest(
                title=title,
                criterion=criterion,
                input=input,
                random_generation=random_generation,
                initial_variables=initial_variables,
                initial_lists=initial_lists,
                predefined_randoms=predefined_randoms,
            )
        )
        return self._maintests[-1]

    def if_criterion_then(
        self,
        criterion: Criterion[PermittedFEAT_CondCatActCrit],
        action: Action[PermittedFEAT_CondCatActAct],
        order: Literal["before-all-tests", "after-all-tests"] = "after-all-tests",
    ) -> Self:
        self._if_then_actions.append((order, (criterion, action)))
        return self

    def run_action(
        self,
        action: Action[PermittedFEAT_CondCatActAct],
        order: Literal["before-all-tests", "after-all-tests"] = "after-all-tests",
    ) -> Self:
        return self.if_criterion_then(ALWAYS_FULFILLED, action=action, order=order)

    def __repr__(self) -> str:
        return self._repr(title=self._title, description=self._description)

    def _to_json(self, ser):
        base = dict(
            title=self._title,
        )
        if self._description is not None:
            base["description"] = self._description
        if len(self._maintests) > 0:
            base["tests"] = [x._to_json(ser) for x in self._maintests]
        hooks = self._hooks_to_json_like(ser)
        if len(hooks) > 0:
            base["hooks"] = hooks
        return base

    pass


class AnyTest(SpecEntity):
    def __init__(
        self,
        *,
        title,
        criterion,
        input,
        random_generation,
        predefined_randoms,
        initial_variables,
        initial_lists,
    ) -> None:
        super().__init__()
        self._title = title
        self._criterion = criterion
        self._input = input
        self._random_generation = random_generation
        self._predefined_randoms = predefined_randoms
        self._initial_variables = initial_variables
        self._initial_lists = initial_lists

    def __repr__(self) -> str:
        return self._repr(
            title=self._title,
            criterion=self._criterion,
            input=self._input,
            random_generation=self._random_generation,
            predefined_randoms=self._predefined_randoms,
            initial_variables=self._initial_variables,
            initial_lists=self._initial_lists,
        )

    def _to_json(self, ser):
        base = dict(
            title=self._title,
            criterion=ser.register(self._criterion),
            input=self._input,
            random_generation=self._random_generation,
            initial_variables=self._initial_variables,
            initial_lists=self._initial_lists,
            hooks=self._hooks_to_json_like(ser),
        )
        return {
            k: v
            for (k, v) in base.items()
            if v is not None and not (isinstance(v, (list, dict)) and len(v) == 0)
        }


class MainTest(AnyTest):
    def __init__(
        self,
        *,
        title,
        criterion,
        input,
        random_generation,
        predefined_randoms,
        initial_variables,
        initial_lists,
    ) -> None:
        super().__init__(
            title=title,
            criterion=criterion,
            input=input,
            random_generation=random_generation,
            predefined_randoms=predefined_randoms,
            initial_variables=initial_variables,
            initial_lists=initial_lists,
        )
        self._alternatives: list = []

    def new_alternative_test(
        self,
        title: str | None = None,
        *,
        criterion: Criterion[PermittedFEAT_PassTestCrit],
        input: list[str | int | float] | None = None,
        random_generation: bool | int | None = None,
        predefined_randoms: list[int | float] | None = None,
        initial_variables: Mapping[str, str | int | float] | None = None,
        initial_lists: Mapping[str, list[str | int | float]] | None = None,
    ) -> AlternativeTest:
        self._alternatives.append(
            AlternativeTest(
                title=title,
                criterion=criterion,
                input=input,
                random_generation=random_generation,
                predefined_randoms=predefined_randoms,
                initial_variables=initial_variables,
                initial_lists=initial_lists,
            )
        )
        return self._alternatives[-1]

    def if_criterion_then(
        self,
        criterion: Criterion[PermittedFEAT_CondTestActCrit],
        action: Action[PermittedFEAT_CondTestActAct],
        order: Literal[
            "before-main", "before-alternatives", "after-complete"
        ] = "after-complete",
    ) -> Self:
        self._if_then_actions.append((order, (criterion, action)))
        return self

    def run_action(
        self,
        action: Action[PermittedFEAT_CondTestActAct],
        order: Literal[
            "before-main", "before-alternatives", "after-complete"
        ] = "after-complete",
    ) -> Self:
        return self.if_criterion_then(ALWAYS_FULFILLED, action=action, order=order)

    def _to_json(self, ser) -> dict:
        base: dict = super()._to_json(ser)
        if len(self._alternatives) > 0:
            base["alternatives"] = [a._to_json(ser) for a in self._alternatives]
        return base


class AlternativeTest(AnyTest):
    def if_criterion_then(
        self,
        criterion: Criterion[PermittedFEAT_CondAltTestActCrit],
        action: Action[PermittedFEAT_CondAltTestActAct],
        order: Literal["before-alt", "after-alt"] = "after-alt",
    ) -> Self:
        self._if_then_actions.append((order, (criterion, action)))
        return self

    def run_action(
        self,
        action: Action[PermittedFEAT_CondAltTestActAct],
        order: Literal["before-alt", "after-alt"] = "after-alt",
    ) -> Self:
        return self.if_criterion_then(ALWAYS_FULFILLED, action=action, order=order)
