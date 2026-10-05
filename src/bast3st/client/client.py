from dataclasses import dataclass
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
class UploadSpecError:
    kind: Literal["password", "spec", "unknown", "server"]
    data: object = None


@dataclass(frozen=True)
class SubmitProgramError:
    kind: Literal["user/slot", "spec", "program", "unknown", "server"]
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
            logging.error(
                f"no client available, consider setting 'BAST3ST_SERVER' env-var: {url=}"
            )
            exit(13)
        return c

    def check_health(self) -> int:
        resp = send_request(
            "get",
            urllib.parse.urljoin(self.parsed_url.geturl(), "/v2/api/health"),
        )
        return resp.status_code

    def upload_spec(
        self, *, user: str, password: str, slot: str, spec: dict | Bast3StSpec
    ) -> UploadSpecError | None:
        spec = get_spec_json(spec)

        resp = send_request(
            "post",
            urllib.parse.urljoin(self.parsed_url.geturl(), "/v2/api/spec/upload"),
            json_body={
                "spec": spec,
                "username": user,
                "slot": slot,
                "password": password,
            },
        )
        status = resp.status_code
        if status == 201:
            return None
        if status == 403:
            return UploadSpecError("password", resp.text)
        if status == 424:
            return UploadSpecError("spec", resp.text)
        if status == 500:
            return UploadSpecError("server", resp.text)
        return UploadSpecError(kind="unknown", data=dict(status=status, data=resp.text))

    def debug_spec(
        self,
        *,
        program: dict | pathlib.Path | str,
        spec: dict | Bast3StSpec,
        agent: str = "cli",
        session: str | None = None,
        parse: bool = True,
    ) -> SpecReport | dict | DebugSpecError:
        """Debug a specification with a scratch program"""
        program = get_program_json(program)
        spec = get_spec_json(spec)

        resp = send_request(
            "post",
            urllib.parse.urljoin(self.parsed_url.geturl(), "/v2/api/spec/debug"),
            json_body={
                "program": program,
                "spec": spec,
                "agent": agent,
                "session": session,
            },
        )
        status = resp.status_code
        if status == 200:
            if parse:
                return SpecReport.from_json(resp.json())
            return resp.json()
        if status == 422:
            return DebugSpecError("program", resp.text)
        if status == 424:
            return DebugSpecError("spec", resp.text)
        if status == 500:
            return DebugSpecError("server", resp.text)
        return DebugSpecError(kind="unknown", data=dict(status=status, data=resp.text))

    def submit_program(
        self,
        *,
        user: str,
        slot: str,
        program: dict | pathlib.Path | str,
        agent: str = "cli",
        session: str | None = None,
        parse: bool = True,
    ) -> SpecReport | dict | SubmitProgramError:
        """Submit a program to a given user/slot"""
        program = get_program_json(program)

        resp = send_request(
            "post",
            urllib.parse.urljoin(self.parsed_url.geturl(), "/v2/api/program/run"),
            json_body={
                "program": program,
                "user": user,
                "slot": slot,
                "agent": agent,
                "session": session,
            },
        )
        status = resp.status_code
        if status == 200:
            if parse:
                return SpecReport.from_json(resp.json())
            return resp.json()
        if status == 400:
            return SubmitProgramError("user/slot", resp.text)
        if status == 422:
            return SubmitProgramError("program", resp.text)
        if status == 424:
            return SubmitProgramError("spec", resp.text)
        if status == 500:
            return SubmitProgramError("server", resp.text)
        return SubmitProgramError(
            kind="unknown", data=dict(status=status, data=resp.text)
        )

    def start_password_reset(
        self, username: str, password: str
    ) -> str | PasswordResetError:
        resp = send_request(
            "post",
            urllib.parse.urljoin(self.parsed_url.geturl(), "/v2/api/account/pwdreset"),
            json_body={"username": username, "password": password},
        )
        status = resp.status_code

        if status == 200:
            return resp.text
        elif status == 403:
            return PasswordResetError("forbidden", data=resp.text)
        elif status == 500:
            return PasswordResetError("server", data=resp.text)
        else:
            return PasswordResetError("unknown", data=resp.text)

    def confirm_password_reset(
        self, username: str, password: str, new_password: str
    ) -> PasswordResetConfirmError | None:
        resp = send_request(
            "post",
            urllib.parse.urljoin(
                self.parsed_url.geturl(), "/v2/api/account/confirmreset"
            ),
            json_body={
                "username": username,
                "password": password,
                "new-password": new_password,
            },
        )
        status = resp.status_code
        data = resp.text

        if status == 200:
            return None
        elif status == 403:
            return PasswordResetConfirmError("forbidden", data=data)
        elif status == 409:
            return PasswordResetConfirmError("conflict", data=data)
        elif status == 500:
            return PasswordResetConfirmError("server", data=data)
        else:
            return PasswordResetConfirmError("unknown", data=data)
