from dataclasses import dataclass
import json
import logging
import os
import pathlib
from typing import Literal
import urllib.parse

from bast3st.client.helpers import get_program_json, get_spec_json, send_request
from bast3st.client.report import SpecReport
from bast3st.spec import Bast3StSpec


@dataclass(frozen=True)
class DebugSpecError:
    kind: Literal["spec", "program", "unknown", "server"]
    data: object = None


@dataclass(frozen=True)
class PasswordResetError:
    kind: Literal["forbidden", "unknown", "server"]
    data: object = None


@dataclass(frozen=True)
class PasswordResetConfirmError:
    kind: Literal["forbidden", "unknown", "server", "conflict"]
    data: object = None


class Client:
    def __init__(self, url: str):
        url = url.rstrip("/")
        lower_url = url.lower()
        if not (lower_url.startswith("http://") or lower_url.startswith("https://")):
            url = "https://" + url
        self.parsed_url = urllib.parse.urlparse(url)

    @classmethod
    def new(cls, url: str | None = None) -> Client | None:
        url = url or os.environ.get("BAST3ST_SERVER", None)
        if url is None or url.strip() == "":
            return None
        client = Client(url)
        try:
            assert client.check_health() == 200, "couldn't find server-specific uri"
            return client
        except Exception as e:
            if not url.lower().startswith("http:"):
                extra = " (if you see a SSL error you maybe have to specify http:// as protocol, not https://)"
            else:
                extra = ""
            logging.error(f"Bast3St server at {url!r} misbehaved{extra}: {e}")

    @classmethod
    def require(cls, url: str | None = None) -> Client:
        c = cls.new(url)
        if c is None:
            raise ValueError(
                f"no client available, consider setting 'BAST3ST_SERVER' env-var: {url=}"
            )
        return c

    def check_health(self) -> int:
        resp = send_request(
            "get",
            urllib.parse.urljoin(self.parsed_url.geturl(), "/api/v2/health"),
        )
        return resp.status

    def debug_spec(
        self,
        *,
        program: dict | pathlib.Path | str,
        spec: dict | Bast3StSpec,
        agent: str = "cli",
        session: str | None = None,
    ) -> SpecReport | DebugSpecError:
        """Debug a specification with a scratch program"""
        program = get_program_json(program)
        spec = get_spec_json(spec)

        resp = send_request(
            "post",
            urllib.parse.urljoin(self.parsed_url.geturl(), "/api/v2/debug"),
            json_body={
                "program": program,
                "spec": spec,
                "agent": agent,
                "session": session,
            },
        )
        if resp.status == 200:
            return SpecReport.from_json(json.load(resp))
        if resp.status == 422:
            return DebugSpecError("program", resp.read())
        if resp.status == 424:
            return DebugSpecError("spec", resp.read())
        if resp.status == 500:
            return DebugSpecError("server", resp.read())
        return DebugSpecError(
            kind="unknown", data=dict(status=resp.status, data=resp.read())
        )

    def start_password_reset(
        self, username: str, password: str
    ) -> str | PasswordResetError:
        resp = send_request(
            "post",
            urllib.parse.urljoin(self.parsed_url.geturl(), "/api/v2/account/pwdreset"),
            json_body={"username": username, "password": password},
        )

        if resp.status == 200:
            return resp.read().decode("utf8")
        elif resp.status == 403:
            return PasswordResetError("forbidden", data=resp.read())
        elif resp.status == 500:
            return PasswordResetError("server", data=resp.read())
        else:
            return PasswordResetError("unknown", data=resp.read())

    def confirm_password_reset(
        self, username: str, password: str, new_password: str
    ) -> PasswordResetConfirmError | None:
        resp = send_request(
            "post",
            urllib.parse.urljoin(
                self.parsed_url.geturl(), "/api/v2/account/confirmreset"
            ),
            json_body={
                "username": username,
                "password": password,
                "new-password": new_password,
            },
        )

        if resp.status == 200:
            return None
        elif resp.status == 403:
            return PasswordResetConfirmError("forbidden", data=resp.read())
        elif resp.status == 409:
            return PasswordResetConfirmError("conflict", data=resp.read())
        elif resp.status == 500:
            return PasswordResetConfirmError("server", data=resp.read())
        else:
            return PasswordResetConfirmError("unknown", data=resp.read())
