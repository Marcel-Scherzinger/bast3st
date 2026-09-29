import argparse

from bast3st.client.admin import AdminClient
import logging
import os

from bast3st.client.client import Client


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
                f"Confirm chaning password of user={username} to: {reset} [y/N]: "
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


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Quiet output on stdout, only data without labels",
    )
    parser.add_argument("-u", "--url", type=str, required=False)

    subparsers = parser.add_subparsers(required=True)

    sub_admin = subparsers.add_parser("admin")

    sub_admin_sub = sub_admin.add_subparsers(required=True)
    sub_admin_users = sub_admin_sub.add_parser("users")
    sub_admin_users.add_argument("username", type=str)
    sub_admin_users.add_argument("-a", "--action", choices=["register", "reset"])
    sub_admin_users.set_defaults(func=run_admin_users)

    sub_pwd = subparsers.add_parser("reset-password")
    sub_pwd.add_argument("--username", type=str, help="defaults to 'BAST3ST_USERNAME'")
    sub_pwd.add_argument("--confirm", action="store_true")
    sub_pwd.set_defaults(func=run_reset_pwd)

    parsed = parser.parse_args()
    exit(parsed.func(parsed))


if __name__ == "__main__":
    run()
