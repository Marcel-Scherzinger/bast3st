import json
from typing import Any, Literal, Mapping

import dataclasses
import textwrap
from dataclasses import field
import pprint


type Relation = Literal["only", "top", "bottom", "inner", None]


def box_sym(rel: Relation, side: Literal["nw", "ne", "sw", "se", "-", "|"]):
    if side == "-":
        return "─"
    if side == "|":
        return "│"
    if rel in ("top", "only"):
        if side == "nw":
            return "┌"
        elif side == "ne":
            return "┐"
    if rel in ("bottom", "only"):
        if side == "nw":
            return "├"
        elif side == "ne":
            return "┤"
        elif side == "sw":
            return "└"
        elif side == "se":
            return "┘"
    if rel == "inner":
        if side == "nw":
            return "├"
        elif side == "ne":
            return "┤"
    return "*"


def indent(text: str, prefix: str, suffix: str = "", suffix_fill_width: int = 0):
    out = ""
    for line in text.splitlines():
        out += prefix + line.ljust(suffix_fill_width) + suffix + "\n"
    return out


def wrap(text: str, width: int, prefix: str = "", suffix: str = ""):
    out = ""
    for lines in textwrap.wrap(text, width=width, replace_whitespace=False):
        for line in lines.splitlines():
            out += prefix + line.ljust(width) + suffix + "\n"
    return out


def add_block(obj, label: str, width: int) -> str:
    if hasattr(obj, "to_pretty"):
        return label + ":\n" + indent(obj.to_pretty(width - 2), prefix=" " * 2)
    return label + ":\n" + wrap(str(obj), width=width - 2, prefix=" " * 2)


@dataclasses.dataclass(frozen=True, kw_only=True)
class RuntimeCriterion:
    is_fulfilled: bool
    failure_explaination: str | None = None
    inner: dict

    @classmethod
    def from_json(cls, val):
        f = val["fulfilled"]
        if "Err" in f:
            return RuntimeCriterion(
                is_fulfilled=False, failure_explaination=f["Err"], inner=val["inner"]
            )
        return RuntimeCriterion(is_fulfilled=True, inner=val["inner"])

    def to_pretty(self, width, relation: Relation = None):
        kind = self.inner.pop("t")
        status = "fulfilled" if self.is_fulfilled else "not fulfilled"

        attributes = (
            kind + ": " + ", ".join([f"{k}={v!r}" for (k, v) in self.inner.items()])
        )

        nw = box_sym("only", "nw")
        ne = box_sym("only", "ne")
        sw = box_sym("only", "sw")
        se = box_sym("only", "se")
        dash = box_sym("only", "-")
        bar = box_sym("only", "|")

        line = nw + dash + " " + status + " " + dash * (width - 5 - len(status)) + ne

        content = attributes + (
            f"\n{'-' * (width - 1)}\n{self.failure_explaination}"
            if self.failure_explaination is not None
            else ""
        )
        content = wrap(content, width=width - 4, prefix=bar + " ", suffix=" " + bar)
        content += sw + dash + dash * (width - 3) + se + "\n"

        return f"{line}\n{content}"

    pass


@dataclasses.dataclass(frozen=True, kw_only=True)
class Message:
    severity: str
    text: str

    @classmethod
    def from_json(cls, val):
        return Message(severity=val["severity"], text=val["text"])

    def to_pretty(self, width: int, relation: Relation = None):
        nw = box_sym(relation, "nw")
        ne = box_sym(relation, "ne")

        fill = width - len(self.severity) - 6
        text = f"{nw}─[{self.severity}]{'─' * fill}─{ne}\n" + wrap(
            self.text, width=width - 4, prefix="│ ", suffix=" │"
        )
        if relation in ("bottom", "only"):
            text += "└─" + ("─" * (width - 4)) + "─┘"

        return text


@dataclasses.dataclass(frozen=True, kw_only=True)
class TestStatus:
    is_fulfilled: bool
    fexp: str | None = None
    error: dict | None = None
    inner: dict

    @classmethod
    def from_json(cls, val: dict):
        if "criterion" not in val:
            if "just-fail-test-run" in val:
                return TestStatus(
                    is_fulfilled=False,
                    fexp=None,
                    error=val["just-fail-test-run"],
                    inner=val,
                )

        f = val["criterion"]["fulfilled"]
        i = val["criterion"]["inner"]
        if "Ok" in f:
            return cls(is_fulfilled=True, inner=i)
        else:
            return cls(is_fulfilled=False, inner=i, fexp=f.get("Err", None))

    def to_pretty(self, width: int) -> str:
        text = ""
        if self.is_fulfilled:
            text += "This test passed!\n"
        else:
            text += "This test failed :(  " + (self.fexp or "") + "\n"
        text += str(self.inner)
        return wrap(text, width)

    def __str__(self) -> str:
        return str(self.is_fulfilled) + f" || {self.fexp} || " + str(self.inner)


@dataclasses.dataclass(frozen=True, kw_only=True)
class Rundata:
    input: list
    output: list
    randoms: list
    lists: Mapping[str, list[Any]]
    variables: Mapping[str, Any]

    @classmethod
    def from_json(cls, val: dict):
        return cls(
            input=val.get("input", {}).get("val", []),
            output=val.get("output", {}).get("val", []),
            randoms=val.get("randoms", {}).get("val", []),
            lists=val.get("lists", {}).get("val", {}),
            variables=val.get("variables", {}).get("val", {}),
        )

    def to_pretty(self, width: int):
        text = ""
        if len(self.input):
            text += add_block(self.input, label="input", width=width)
        if len(self.output):
            text += add_block(self.output, label="output", width=width)
        if len(self.randoms):
            text += add_block(self.randoms, label="randoms", width=width)
        if len(self.lists):
            text += add_block(self.lists, label="lists", width=width)
        if len(self.variables):
            text += add_block(self.variables, label="variables", width=width)
        return text


@dataclasses.dataclass(frozen=True, kw_only=True)
class HookRes:
    is_ok: bool
    val: RuntimeCriterion | dict

    @classmethod
    def from_json(cls, val: dict):
        if v := val.get("Ok"):
            return cls(is_ok=True, val=RuntimeCriterion.from_json(v["criterion"]))
        return cls(is_ok=False, val=val["Err"])

    def to_pretty(self, width: int, relation: Relation = None):
        if self.is_ok:
            t = self.val.to_pretty(width)  # type: ignore
        else:
            t = f"error: {self.val}"
        return t

    pass


@dataclasses.dataclass(frozen=True, kw_only=True)
class AlternativeTestHooks:
    before_alt: list[HookRes] = field(default_factory=list)
    after_alt: list[HookRes] = field(default_factory=list)

    @classmethod
    def from_json(cls, val: dict):
        return AlternativeTestHooks(
            before_alt=list(map(HookRes.from_json, val.get("before-alt", []))),
            after_alt=list(map(HookRes.from_json, val.get("after-alt", []))),
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class MainTestHooks:
    before_main: list[HookRes] = field(default_factory=list)
    before_alternatives: list[HookRes] = field(default_factory=list)
    after_complete: list[HookRes] = field(default_factory=list)

    @classmethod
    def from_json(cls, val: dict):
        return MainTestHooks(
            before_main=list(map(HookRes.from_json, val.get("before-main", []))),
            before_alternatives=list(
                map(HookRes.from_json, val.get("before-alternatives", []))
            ),
            after_complete=list(map(HookRes.from_json, val.get("after-complete", []))),
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class CatHooks:
    before_all_tests: list[HookRes] = field(default_factory=list)
    after_all_tests: list[HookRes] = field(default_factory=list)

    @classmethod
    def from_json(cls, val: dict):
        return CatHooks(
            before_all_tests=list(
                map(HookRes.from_json, val.get("before-all-tests", []))
            ),
            after_all_tests=list(
                map(HookRes.from_json, val.get("after-all-tests", []))
            ),
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class SpecHooks:
    before_all_categories: list[HookRes] = field(default_factory=list)
    after_all_categories: list[HookRes] = field(default_factory=list)

    @classmethod
    def from_json(cls, val: dict):
        return SpecHooks(
            before_all_categories=list(
                map(HookRes.from_json, val.get("before-all-categories", []))
            ),
            after_all_categories=list(
                map(HookRes.from_json, val.get("after-all-categories", []))
            ),
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class AlternativeTest:
    title: str
    status: TestStatus
    messages: list[Message] = field(default_factory=list)
    alternatives: list[AlternativeTest] = field(default_factory=list)
    hooks: AlternativeTestHooks = field(default_factory=AlternativeTestHooks)
    data: Rundata | None = None

    @classmethod
    def from_json(cls, val: dict):
        return AlternativeTest(
            title=val["general"]["title"],
            status=TestStatus.from_json(val["general"]["status"]),
            messages=list(map(Message.from_json, val.get("messages", []))),
            data=Rundata.from_json(val["general"].get("data", {})),
            hooks=AlternativeTestHooks.from_json(val.get("hooks", {})),
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class MainTest:
    title: str
    status: TestStatus
    messages: list[Message] = field(default_factory=list)
    alternatives: list[AlternativeTest] = field(default_factory=list)
    hooks: MainTestHooks = field(default_factory=MainTestHooks)
    data: Rundata | None = None

    @classmethod
    def from_json(cls, val):
        return MainTest(
            title=val["general"]["title"],
            status=TestStatus.from_json(val["general"]["status"]),
            messages=list(map(Message.from_json, val.get("messages", []))),
            alternatives=list(
                map(AlternativeTest.from_json, val.get("alternatives", []))
            ),
            data=Rundata.from_json(val["general"].get("data", {})),
            hooks=MainTestHooks.from_json(val.get("hooks", {})),
        )

    def to_pretty(self, width: int, relation: Relation = None):
        nw = box_sym(relation, "nw")
        ne = box_sym(relation, "ne")
        lver = box_sym(relation, "|")
        rver = box_sym(relation, "|")

        if not self.status.is_fulfilled:
            lver = "█"

        text = f"{nw}─{'─' * (width - 4)}─{ne}\n" + indent(
            self._inner_to_pretty(width - 4),
            prefix=lver + " ",
            suffix=" " + rver,
            suffix_fill_width=width - 4,
        )
        if relation in ("bottom", "only"):
            text += "└─" + ("─" * (width - 4)) + "─┘"
        return text

    def _inner_to_pretty(self, width: int) -> str:
        text = wrap(self.title, width=width)
        # text += (" " if self.status.is_fulfilled else "!") * min(
        #     width, len(self.title)
        # ) + "\n"
        text += self.status.to_pretty(width)
        text += output_list(self.messages, width, label="messages")
        text += output_list(self.hooks.before_main, label="before-main", width=width)
        text += add_block(self.data, label="data", width=width)
        text += output_list(
            self.hooks.before_alternatives, label="before-alternatives", width=width
        )
        text += output_list(self.alternatives, width, label="alternatives")
        text += output_list(
            self.hooks.after_complete, label="after-complete", width=width
        )
        return text


@dataclasses.dataclass(frozen=True, kw_only=True)
class Category:
    title: str
    messages: list[Message] = field(default_factory=list)
    tests: list[MainTest] = field(default_factory=list)
    hooks: CatHooks = field(default_factory=CatHooks)

    @classmethod
    def from_json(cls, val: dict):
        return Category(
            title=val["title"],
            messages=list(map(Message.from_json, val.get("messages", []))),
            tests=list(map(MainTest.from_json, val.get("tests", []))),
            hooks=CatHooks.from_json(val.get("hooks", {})),
        )

    def to_pretty(self, width: int, _relation: Relation = None):
        text = "title:\n" + wrap(self.title, prefix="  ", width=width)
        text += output_list(self.messages, width=width, label="messages")
        text += output_list(
            self.hooks.before_all_tests, width=width, label="before-all-tests"
        )
        text += output_list(self.tests, width=width, label="tests")
        text += output_list(
            self.hooks.after_all_tests, width=width, label="after-all-tests"
        )
        return text

    pass


@dataclasses.dataclass(frozen=True, kw_only=True)
class SpecReport:
    title: str
    description: str | None = None
    messages: list[Message] = field(default_factory=list)
    categories: list[Category] = field(default_factory=list)
    hooks: SpecHooks = field(default_factory=SpecHooks)
    flags: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, value: dict):
        return SpecReport(
            title=value["title"],
            description=value.get("description", None),
            messages=list(map(Message.from_json, value.get("messages", []))),
            categories=list(map(Category.from_json, value.get("categories", []))),
            hooks=SpecHooks.from_json(value.get("hooks", {})),
            flags=value.get("flags", {}),
        )

    def to_pretty(self, width: int = 60) -> str:
        ind = " " * 4
        title = "title:\n" + "\n".join(
            [(ind + x) for x in textwrap.wrap(self.title, width)]
        )

        text = title + "\ndesc:\n"
        if desc := self.description:
            desc = "\n".join(textwrap.wrap(desc, width=width))
            text += textwrap.indent(desc, prefix=ind)
            text += "\n"
        text += output_list(self.messages, width=width, label="messages")
        text += output_list(
            self.hooks.before_all_categories, width=width, label="before-all-categories"
        )
        text += output_list(self.categories, width=width, label="categories")
        text += output_list(
            self.hooks.after_all_categories, width=width, label="after-all-categories"
        )

        text += "flags:\n" + wrap(
            pprint.pformat(self.flags, indent=2, width=width - 4),
            width=width,
            prefix="    ",
        )
        return text


def output_items(
    m: list, width: int, leading_indent: str = "- ", other_indent: str = "  "
) -> str:
    if len(m) == 0:
        return ""
    text = ""
    for index, item in enumerate(m):
        if len(m) == 1:
            relation = "only"
        elif index == 0:
            relation = "top"
        elif index == len(m) - 1:
            relation = "bottom"
        else:
            relation = "inner"

        pretty_item = indent(item.to_pretty(width - 2, relation), other_indent)
        text += leading_indent + pretty_item[len(other_indent) :]

    return text


def output_list(l: list, width: int, label: str):
    if l:
        return label + ":\n" + indent(output_items(l, width=width - 2), prefix="  ")
    return ""
