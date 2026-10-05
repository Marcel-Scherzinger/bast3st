import argparse
import json
import pathlib
import shutil

from bast3st.client.admin import AdminClient
import logging
import os

from bast3st.client.client import Client
from bast3st.client.report import SpecReport


EXIT_SERVER = 12
EXIT_ERROR = 13


def run_reset_pwd(args) -> int:
    username = args.username or os.environ.get("BAST3ST_USERNAME", None)
    password = os.environ.get("BAST3ST_PASSWORD", None)

    if username is None:
        logging.error("you have to specify a username or set 'BAST3ST_USERNAME'")
        return EXIT_ERROR
    if password is None:
        logging.error("you have to set 'BAST3ST_PASSWORD'")
        return EXIT_ERROR

    client = Client.require(url=args.url)

    reset = client.start_password_reset(username, password)
    if not isinstance(reset, str):
        logging.error(f"password reset request failed: {reset}")
        return EXIT_ERROR

    if args.confirm:
        if args.quiet:
            print(reset)
            client.confirm_password_reset(username, password, new_password=reset)
        else:
            print(f"Your new password for user={username} is: {reset}")
            client.confirm_password_reset(username, password, new_password=reset)
    else:
        if args.quiet:
            answer = input(reset)
        else:
            answer = input(
                f"Confirm changing password of user={username} to: {reset} [y/N]: "
            )
        if answer.lower() == "y":
            if x := client.confirm_password_reset(
                username, password, new_password=reset
            ):
                logging.error(f"{x}")
            else:
                logging.info("Successfully changed password")
        else:
            logging.warning("Cancel password change")
    return 0


def run_admin_users(args) -> int:
    client = AdminClient.new(args.url)
    if client is None:
        return EXIT_SERVER
    if args.action == "register":
        resp = client.register_user(args.username)
        if isinstance(resp, str):
            if args.quiet:
                print(resp)
            else:
                print(f"Registered user {args.username!r} with password: {resp}")
            return 0
        else:
            logging.warning(f"Failed to register user {args.username!r}: {resp}")
            return 13
    elif args.action == "reset":
        resp = client.reset_user_password(args.username)
        if isinstance(resp, str):
            if args.quiet:
                print(resp)
            else:
                print(f"The password of {args.username!r} is now: {resp}")
            return 0
        else:
            logging.warning(
                f"Failed to reset password of user {args.username!r}: {resp}"
            )
            return 13
    return 13


def run_submit(args):
    user, slot = args.user, args.slot
    user = user or os.environ.get("BAST3ST_USERNAME", None)
    if user is None:
        logging.error("You have to provide --user or set BAST3ST_USERNAME")
        exit(13)
    client = Client.require(url=args.url)
    if args.format == "json":
        rep = client.submit_program(
            user=user, slot=slot, program=args.program, parse=False
        )
        if isinstance(rep, dict):
            print(json.dumps(rep))
        else:
            logging.error(f"{rep}")
            exit(13)
    else:
        rep = client.submit_program(user=user, slot=slot, program=args.program)
        if isinstance(rep, SpecReport):
            if args.format == "pretty":
                width = args.width or (shutil.get_terminal_size().columns)
                print(rep.to_pretty(width))
            else:
                print(repr(rep))
        else:
            logging.error(f"{rep}")
            exit(13)


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="quiet output on stdout, only data without labels",
    )
    parser.add_argument("--url", type=str, required=False)

    subparsers = parser.add_subparsers(required=True)

    sub_admin = subparsers.add_parser("admin")

    sub_admin_sub = sub_admin.add_subparsers(required=True)
    sub_admin_users = sub_admin_sub.add_parser("users")
    sub_admin_users.add_argument("username", type=str)
    sub_admin_users.add_argument("-a", "--action", choices=["register", "reset"])
    sub_admin_users.set_defaults(func=run_admin_users)

    sub_pwd = subparsers.add_parser("reset-password", help="reset own password")
    sub_pwd.add_argument("--username", type=str, help="defaults to 'BAST3ST_USERNAME'")
    sub_pwd.add_argument("--confirm", action="store_true")
    sub_pwd.set_defaults(func=run_reset_pwd)

    sub_submit = subparsers.add_parser(
        "submit", help="submit a program to a specific user/slot exercise"
    )
    sub_submit.add_argument(
        "-f",
        "--format",
        choices=["pretty", "repr", "json"],
        required=False,
        default="pretty",
    )
    sub_submit.add_argument(
        "--width", type=int, help="terminal width to use, defaults to available"
    )
    sub_submit.add_argument("program", type=pathlib.Path)
    sub_submit.add_argument("-u", "--user", type=str, required=False)
    sub_submit.add_argument("-s", "--slot", type=str, required=True)
    sub_submit.set_defaults(func=run_submit)

    parsed = parser.parse_args()
    exit(parsed.func(parsed))


if __name__ == "__main__":
    run()
