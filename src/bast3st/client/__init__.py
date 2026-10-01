import argparse
import logging
import os
import pathlib
import shutil
import sys
from os import path
from pathlib import Path
from bast3st.cli import EXIT_ERROR
from bast3st.client.client import Client
from bast3st.client.helpers import get_program_json, parse_exercise_id
from bast3st.client.report import SpecReport
from bast3st.spec import Bast3StSpec


def get_program_name():
    return path.basename(str(getattr(sys.modules["__main__"], "__file__", "")))


def run_export(spec: Bast3StSpec, args):
    file = args.file
    with open(file, mode="w", encoding="utf8") as f:
        f.write(spec.to_json(indent=args.indent))


def debug_spec(
    program: dict, spec: Bast3StSpec, program_name: str | None = None, url=None
) -> SpecReport:
    program_name = program_name or get_program_name()

    client = Client.require(url)
    rep = client.debug_spec(program=program, spec=spec)
    if not isinstance(rep, SpecReport):
        raise ValueError(f"{rep!r}")

    return rep


def run_test(spec: Bast3StSpec, args):
    program_path: pathlib.Path = args.program
    program = get_program_json(program_path)

    rep = debug_spec(program=program, spec=spec, url=args.url)
    if args.format == "pretty":
        width = args.width or (shutil.get_terminal_size().columns)
        print(rep.to_pretty(width))
    else:
        print(repr(rep))


def run_upload(spec, args):
    user, slot = args.exercise
    client = Client.require(args.url)
    username = user or os.environ.get("BAST3ST_USERNAME", None)
    password = os.environ.get("BAST3ST_PASSWORD", None)

    if username is None:
        logging.error("you have to specify a username or set 'BAST3ST_USERNAME'")
        return EXIT_ERROR
    if password is None:
        logging.error("you have to set 'BAST3ST_PASSWORD'")
        return EXIT_ERROR

    resp = client.upload_spec(spec=spec, user=user, slot=slot, password=password)
    if resp is None:
        logging.info(f"Successfully uploaded specification to {user}/{slot}")
        return 0
    logging.error(repr(resp))
    return EXIT_ERROR


def main(spec: Bast3StSpec):
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", type=str, required=False)

    subparsers = parser.add_subparsers(required=True)
    ######################
    # Upload
    ######################
    sub_upload = subparsers.add_parser(
        "upload", help="upload the specification to the server"
    )
    sub_upload.add_argument(
        "-e", "--exercise", type=parse_exercise_id, metavar="USER/SLOT", required=True
    )
    sub_upload.set_defaults(func=lambda args: run_upload(spec, args))
    ######################
    # Debug
    ######################
    sub_test = subparsers.add_parser(
        "debug", help="debug this spec with a sb3 file and print the report"
    )
    sub_test.set_defaults(func=lambda args: run_test(spec, args))
    sub_test.add_argument("program", type=Path, help="Path to *.sb3 or project.json")
    sub_test.add_argument(
        "--width", type=int, help="terminal width to use, defaults to available"
    )
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
