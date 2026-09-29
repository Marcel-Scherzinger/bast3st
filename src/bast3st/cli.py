import argparse

from bast3st.client.admin import AdminClient
import logging


EXIT_SERVER = 12
EXIT_ERROR = 13


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

    subparsers = parser.add_subparsers(required=True)

    sub_admin = subparsers.add_parser("admin")
    sub_admin.add_argument("-u", "--url", type=str, required=False)

    sub_admin_sub = sub_admin.add_subparsers(required=True)
    sub_admin_users = sub_admin_sub.add_parser("users")
    sub_admin_users.add_argument("username", type=str)
    sub_admin_users.add_argument("-a", "--action", choices=["register", "reset"])
    sub_admin_users.set_defaults(func=run_admin_users)

    parsed = parser.parse_args()
    exit(parsed.func(parsed))


if __name__ == "__main__":
    run()
