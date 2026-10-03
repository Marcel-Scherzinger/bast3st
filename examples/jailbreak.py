from bast3st import Bast3StSpec, main
from bast3st.actions import set_flag
from bast3st.decisions import NetworkRequest


register = True
part = "register" if register else "pwdreset"

spec = Bast3StSpec("Test if the network config allows to contact the admin api")
spec.run_action(
    set_flag(
        "flag",
        value=NetworkRequest(
            server="http://localhost:42039",
            route=f"/v2/api/admin/{part}",
            method="POST",
            allowed_status=(400, 200),
            json={"user": "jailbreak"},
        )["text"],
    )
)


if __name__ == "__main__":
    main(spec)
