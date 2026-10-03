############
Server guide
############

This section is only relevant for administrators that want to run
an instance of `github:marcel-scherzinger/bast3st-web#bast3st-backend
<https://github.com/Marcel-Scherzinger/bast3st-web>`_ to host
specifications as exercises.


Installation
============

Cargo
-----

As the server is entirely written in Rust, you can compile the application
by using `cargo <https://doc.rust-lang.org/cargo/getting-started/installation.html>`_:

.. code-block:: console
    
    $ cargo install --git https://github.com/marcel-scherzinger/bast3st-web


.. _cargo: 

Nix
---

The repository also declares a `Flake <https://nixos.wiki/wiki/flakes>`_ for the `Nix package manager <https://nixos.org/>`_, so you can add it to your system packages or run the application directly with Nix:

.. code-block:: console

   $ nix run github:marcel-scherzinger/bast3st-web#bast3st-backend

Setup and configuration
=======================

When you run the application, it will probably output nothing,
as the default log level is `error`. To make it more verbose, set the
`RUST_LOG environment variable <https://docs.rs/env_logger/latest/env_logger/#enabling-logging>`_.

.. attention::
    It is highly adviced to at least **lower the logging level to warn**
    for logs that humans look at and set it to `debug` when you finally
    let it run alone on a server 24/7.
    Logs with level `warn` can help you during setup and will also warn
    you if someone uses the admin API.

.. code-block:: console

   $ RUST_LOG=warn bast3st-backend

Without any arguments, the server will default to a configuration that
you'll likely want to change. For this, create a new file (e. g. named
:code:`bast3st.toml`) where the following options can be set:

.. code-block:: toml

    # the section itself is required, even if it is empty
    [server]
    # port = ...                   # defaults to 42139
    # workers = ...                # defaults to 4

    # if section missing, count as `enable = false`
    [admin]
    # BE CAREFUL: read the chapter about the admin API
    enable = true
    # host = ...                   # defaults to "localhost"
    # port = ...                   # defaults to 42039
    # workers = ...                # defaults to 2


    [server.cors]
    allowed_origins = [
        "http://127.0.0.1",  # local testing
        "http://localhost",  # local testing
        "https://127.0.0.1", # local testing
        "https://localhost", # local testing
        # allowed frontends
    ]
    # allowed_headers = []         # defaults to []
    # max_age = ...                # defaults to unspecified

    # important for limiting size of program- and spec- uploads
    [server.limits]
    json = 102400                  
    form = 102400

    [database]
    host = "/var/run/postgresql"
    database = "bast3st"
    username = "bast3st" # same as Linux username here
    # not necessary if host is unix domain socket
    # password = 
    # port = 5432

.. code-block:: console

   $ RUST_LOG=warn bast3st-backend bast3st.toml

You will probably see something like this:

.. code-block:: console

   $ RUST_LOG=warn bast3st-backend bast3st.toml
   [2026-10-03T13:33:55Z WARN  bast3st_backend::settings] reading configuration from bast3st.toml
   [2026-10-03T13:33:56Z WARN  bast3st_backend] [admin-api] start admin server api on (localhost, 42039)
   [2026-10-03T13:33:56Z WARN  bast3st_backend] [admin-api] note that no network selector of bast3st-eval will be able to contact servers on port 42039


.. note::

   `CORS <https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS>`_
   only limits what the browser of a user will allow
   the frontend that tries to communicate with the API and what frontends
   the browser will allow at all. So setting this to your own domain will
   not prevent anyone else communicating with the server, it will only
   ask the browsers of your users to not allow other sites to use your
   API to prevent e. g. malicious frontends that do extra stuff.

.. _server-admin:

Admin API
=========

You should **never** make the admin API publicly available!
Everyone who can send messages to the API, can create new users and reset
the password of any other user without authentication.

By default, it will listen only on `localhost` and you shouldn't change
that. This way, only local programs can send requests to it, adding an
important level of security.
You can use the port-mapping-capabilities of SSH to access the API as
an administrator with SSH access to the server:

.. code-block::

   $ ssh -L 42039:localhost:42039 user@server

where `user@server` can also be an alias in your SSH config.
This will make the admin API available to *your* localhost as long as
the session is open.
You can also consider *deactivating the admin API* after you created all
required users, what is definitly the safest option.

.. _serveradmin-jailbreak:

Jailbreaking
------------

As the server allows users to do nearly arbitrary network requests,
one could also try to write the following test specification:

.. code-block:: python

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


As the normal server normally is on the same host as the admin API,
it is allowed to communicate to it on a network-level.
To prevent this jailbreak, the server will block all requests from
user specifications that try to access the same port that is used to
run the admin API. Without this protection, anyone with access to the
main server could run this jailbreak successfully.

.. note::
   This means that you make it more complicated for your users if you
   pick a port that is typically needed, but as the server permits only
   http and https connections, there shouldn't be a problem.
   The default port is a good choice and shouldn't ever cause problems.

   Never let the admin API run on one of the ports 80 or 443. That
   is not a good idea but could also allow bypassing the safety guard
   from above.

Using the admin API
-------------------

You can interact with the server like in :ref:`serveradmin-jailbreak`
by sending manual network requests (from your computer), but an easier
way might be to use `github:marcel-scherzinger/bast3st <https://github.com/marcel-scherzinger/bast3st>`_:

.. code-block:: console

    $ nix run github:marcel-scherzinger/bast3st -- admin users -h
    usage: bast3st admin users [-h] [-a {register,reset}] username

    positional arguments:
      username

    options:
      -h, --help            show this help message and exit
      -a, --action {register,reset}

To tell the CLI which server you want, you can explicitly set the 
environment variable :code:`BAST3ST_ADMIN_SERVER`. By default it will just
use `http://localhost:42039`, this should **always** be ok,
:ref:`right <server-admin>`?


.. code-block:: console

    $ nix run github:marcel-scherzinger/bast3st -- admin users -a register ferris
    Registered user 'ferris' with password: XuLLAtq3WcykatGZmDzkjEsFbWygccNz3qE8PgEKJ3

.. code-block:: console

    $ nix run github:marcel-scherzinger/bast3st -- admin users -a reset ferris
    The password of 'ferris' is now: gc2VVLQyw3MTgP2fGd22FCp9We4enNtdHZD85vsWMF

The passwords are selected randomly by the server and you have no way
to influence their value or length.
The passwords you see here were reset before this documentation went live.
**Never share your real passwords like this!**

If you see the following error, there is no server you can talk to:

.. code-block:: console

   $ nix run github:marcel-scherzinger/bast3st -- admin users -a register ferris
   ERROR:root:Admin server at 'http://localhost:42039' misbehaved: HTTPConnectionPool(host='localhost', port=42039): Max retries exceeded with url: /v2/api/admin/health (Caused by NewConnectionError("HTTPConnection(host='localhost', port=42039): Failed to establish a new connection: [Errno 111] Connection refused"))

.. code-block:: console

   $ ssh -L 42039:localhost:42039 user@server # this could help
