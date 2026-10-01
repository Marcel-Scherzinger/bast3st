import argparse
import urllib.parse
import http.client
import json
import pathlib
import zipfile

from bast3st.spec import Bast3StSpec


def send_request(method, uri: str, json_body: dict | None = None):
    url = urllib.parse.urlparse(uri)

    conn = http.client.HTTPConnection(url.hostname or "", port=url.port)
    conn.request(
        method.upper(),
        url.path,
        body=json.dumps(json_body) if json_body else None,
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    return resp


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
