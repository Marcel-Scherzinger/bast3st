import argparse
import json
import pathlib
import zipfile
import requests

from bast3st.spec import Bast3StSpec
from bast3st.version import VERSION


def send_request(method, uri: str, json_body: dict | None = None):
    if method.lower() == "get":
        return requests.get(
            uri,
            headers={
                "User-Agent": f"bast3st/{VERSION}",
            },
        )
    elif method.lower() == "post":
        return requests.post(
            uri,
            json=json_body,
            headers={
                "User-Agent": f"bast3st/{VERSION}",
            },
        )
    assert False, "neither get nor post"


def get_program_json(doc: pathlib.Path | str | dict) -> dict:
    if isinstance(doc, dict):
        return doc
    if isinstance(doc, (str, pathlib.Path)):
        path = pathlib.Path(doc)
        if path.suffix == "json":
            with open(path, encoding="utf8") as f:
                return json.load(f)
        with zipfile.ZipFile(path) as f:
            program = f.read("project.json")
            return json.loads(program)
    raise TypeError(f"Invalid type for program: {type(doc)}")


def get_spec_json(doc: dict | Bast3StSpec) -> dict:
    if isinstance(doc, Bast3StSpec):
        return json.loads(doc.to_json())
    return doc


def parse_exercise_id(value: str):
    parts = value.split("/", 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("id has to have the form USER/SLOT")
    return tuple(parts)
