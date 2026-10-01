from dataclasses import dataclass
import logging
import os
from typing import Literal
import urllib.parse

from bast3st.client.helpers import send_request


@dataclass(frozen=True)
class AdminRegisterUserError:
    kind: Literal["already-there", "unknown", "server"]
    data: object = None


@dataclass(frozen=True)
class AdminResetUserPwdError:
    kind: Literal["not-found", "unknown", "server"]
    data: object = None


class AdminClient:
    def __init__(self, url: str):
        url = url.rstrip("/")
        lower_url = url.lower()
        if not (lower_url.startswith("http://") or lower_url.startswith("https://")):
            url = "https://" + url
        self.parsed_url = urllib.parse.urlparse(url)

    @classmethod
    def new(cls, url: str | None = None) -> AdminClient | None:
        url = (
            url
            or os.environ.get("BAST3ST_ADMIN_SERVER", None)
            or "http://localhost:42039"
        )
        if url is None or url.strip() == "":
            return None
        client = AdminClient(url)
        try:
            assert client.check_health() == 200, (
                "couldn't find admin-server-specific uri"
            )
            return client
        except Exception as e:
            if not url.lower().startswith("http:"):
                extra = " (if you see a SSL error you maybe have to specify http:// as protocol, not https://)"
            else:
                extra = ""
            logging.error(f"Admin server at {url!r} misbehaved{extra}: {e}")

    def check_health(self) -> int:
        resp = send_request(
            "get",
            urllib.parse.urljoin(self.parsed_url.geturl(), "/v2/api/admin/health"),
        )
        return resp.status

    def register_user(self, username: str) -> str | AdminRegisterUserError:
        """Returns the created password for the user or an error"""
        resp = send_request(
            "post",
            urllib.parse.urljoin(self.parsed_url.geturl(), "/v2/api/admin/register"),
            json_body={"user": username},
        )
        if resp.status == 200:
            return resp.read().decode("utf8")
        if resp.status == 409:
            return AdminRegisterUserError(kind="already-there")
        if resp.status == 500:
            return AdminRegisterUserError(kind="server")
        return AdminRegisterUserError(
            kind="unknown", data=dict(status=resp.status, data=resp.read())
        )

    def reset_user_password(self, username: str) -> str | AdminResetUserPwdError:
        """Returns the new password for the user or an error"""
        resp = send_request(
            "post",
            urllib.parse.urljoin(self.parsed_url.geturl(), "/v2/api/admin/pwdreset"),
            json_body={"user": username},
        )
        if resp.status == 200:
            return resp.read().decode("utf8")
        if resp.status == 409:
            return AdminResetUserPwdError(kind="not-found")
        if resp.status == 500:
            return AdminResetUserPwdError(kind="server")
        return AdminResetUserPwdError(
            kind="unknown", data=dict(status=resp.status, data=resp.read())
        )
