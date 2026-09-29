import argparse
import pathlib
import sys
import json
import zipfile
import http.client
from os import path
from pathlib import Path
from bast3st.client.report import SpecReport
from bast3st.spec import Bast3StSpec


def get_program_name():
    return path.basename(str(getattr(sys.modules["__main__"], "__file__", "")))


def get_server_url() -> tuple[str, int]:
    return ("localhost", 42139)


def run_export(spec: Bast3StSpec, args):
    file = args.file
    with open(file, mode="w", encoding="utf8") as f:
        f.write(spec.to_json(indent=args.indent))


def debug_spec(
    program: dict, spec: Bast3StSpec, program_name: str | None = None
) -> SpecReport:
    program_name = program_name or get_program_name()
    host, port = get_server_url()
    conn = http.client.HTTPConnection(host, port)
    conn.request(
        "POST",
        "/api/v2/debug",
        body=json.dumps(
            {
                "program": program,
                "agent": f"bast3st/{program_name}",
                "spec": json.loads(spec.to_json()),
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    response = conn.getresponse()
    read_body = response.read()
    read_json = json.loads(read_body)

    conn.close()

    return SpecReport.from_json(read_json)


def run_test(spec: Bast3StSpec, args):
    program_path: pathlib.Path = args.program

    if program_path.suffix == "json":
        with open(program_path, mode="r", encoding="utf8") as f:
            program = json.load(f)
    else:
        with zipfile.ZipFile(program_path) as f:
            program = f.read("project.json")
            program = json.loads(program)

    rep = debug_spec(program=program, spec=spec)
    if args.format == "pretty":
        print(rep.to_pretty(60))
    else:
        print(repr(rep))


def run_upload(spec, args):
    print(args)


def main(spec: Bast3StSpec, password_env=None):
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(required=True)
    ######################
    # Upload
    ######################
    sub_upload = subparsers.add_parser(
        "upload", help="upload the specification to the server"
    )
    sub_upload.set_defaults(func=lambda args: run_upload(spec, args))
    ######################
    # Test
    ######################
    sub_test = subparsers.add_parser(
        "test", help="test this spec with a sb3 file and print the report"
    )
    sub_test.set_defaults(func=lambda args: run_test(spec, args))
    sub_test.add_argument("program", type=Path, help="Path to *.sb3 or project.json")
    sub_test.add_argument(
        "-f", "--format", choices=["pretty", "repr"], required=False, default="pretty"
    )

    ######################
    # Export
    ######################
    sub_export = subparsers.add_parser("export", help="export this spec to json")
    sub_export.set_defaults(func=lambda args: run_export(spec, args))

    sub_export.add_argument("file", type=Path, help="the file to write the json to")
    sub_export.add_argument(
        "--indent",
        type=int,
        required=False,
        help="indentation of json, leave out for minimal",
    )

    ######################
    # Parse
    parsed = parser.parse_args()
    parsed.func(parsed)
