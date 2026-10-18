##########
User guide
##########

After you received credentials for a user account (see :ref:`server` for setting one up yourself),
you need to install the library for creating specifications:

The CLI can be installed via `pip` or `uv` (or with Nix, but I assume you don't want to do this):

.. caution::

   The library supports Python t-strings and therefore requires at least Python version 3.14

.. note::

   The recommended way to use this library is inside a uv-project.
   See the `uv docs <https://docs.astral.sh/uv/>`_ for more information.
   You can also use uv to install the right Python version and manage your
   virtual environments

.. code-block:: console

   $ uvx bast3st  # if you have uv installed, you can run the cli this way

.. code-block:: console

   $ uv add bast3st  # use this to add bast3st as a library

.. code-block:: console

   $ pip install bast3st  # for normal Python installation


Providing credentials
=====================

The command-line-interface needs to know which server you want to
communicate to and how to login to your account. For some of this
information, you can add extra flags to the commands whenever you
execute one, but this option is not supported for the password
for security reasons.

The user-part of the program cares about three different environment
variables:

- :code:`BAST3ST_SERVER`
- :code:`BAST3ST_USERNAME`
- :code:`BAST3ST_PASSWORD`

If those environment variables are set, the program will fall back to
their values if they are not overwritten by the CLI.
If you use `direnv <https://direnv.net/>`_, you can add the values
of those variables in a file that you ignore from version control,
namely `.envrc` (or without direnv, your shell's rc-file)
with content like this:

.. code-block:: shell

    export BAST3ST_SERVER="https://homeserver.example.org/"
    export BAST3ST_USERNAME="ferris"
    export BAST3ST_PASSWORD=$(kwallet-query kdewallet --folder Bast3St -r password)

The last line uses a functionality of direnv to compute the value by
executing a command. The shown command accesses the standard
password manager of the `KDE desktop environment <https://kde.org>`_
so that the password isn't stored in the project directory.

Uploading a specification
=========================

First, you need a specification script that you want to upload.
Information for understanding the basics can be found in :ref:`concepts`.
The following shows a basic template with required aspects

.. code-block:: python

    from bast3st import Bast3StSpec, main

    # you need one object of `Bast3StSpec`
    spec = Bast3StSpec(
        "Template specification"
    )
    # just as an example of possible operations
    spec.set_block_count_limit(30, "You use too many blocks")

    # run the following only, if the specification is used as a CLI
    if __name__ == "__main__":
        # run the CLI, Bast3St includes specifically for specifications
        # and run it with the specification you just created
        main(spec)

You can then run your specification with a command like this:

.. code-block:: console

    $ uv run template.py -h
    usage: template.py [-h] [--url URL]
                       {upload,debug,export} ...

    positional arguments:
      {upload,debug,export}
        upload              upload the specification to the
                            server
        debug               debug this spec with a sb3 file and
                            print the report
        export              export this spec to json

    options:
      -h, --help            show this help message and exit
      --url URL

:code:`uv run` `FILENAME.py` :code:`debug` `PROGRAM.sb3`
--------------------------------------------------------

The `debug`-subcommand can be used to test your specification with
a Scratch file that can be your sample-solution or a file with a
specific mistake. It will send both to a server and print the report.
This won't care about username or password and could therefore be
blocked on servers that only allow authenticated users.
See :code:`uv run FILENAME.py debug -h` for further options like
output formats.

:code:`uv run` `FILENAME.py` :code:`upload --slot` `my-slot`
--------------------------------------------

The `upload`-subcommand sends the specification to a server and makes
it available under a specific path. This path is your username in the
first level and a slotname of your choice in the second level.
If the option :code:`--user` is not specified, the environment variable
`BAST3ST_USERNAME` is taken.
The exercise id can be shown in two parts or as `USER/SLOT` as neither
usernames nor slotnames should **ever** contain :code:`/`.

.. attention::

    Please try to not use special symbols or characters in slotnames.
    It is guaranteed that lowercase letters from :code:`a` to :code:`z`,
    digits from :code:`0` to :code:`9` and dashes :code:`-` will work.
    Normally, the server should be case-sensitive, but if you want to
    try uppercase or other characters, you're on your own if it causes
    problems from time to time.

:code:`uv run` `FILENAME.py` :code:`export` `OUT.json`
---------------------------

The `export`-subcommand converts the specification into a
`JSON representation <https://en.wikipedia.org/wiki/JSON>`__
and stores it in the provided out-file.

You can add the
:code:`--indent NUM` flag to export it with spaces and readable
indentation. This consumes extra memory and is not needed for machines.

Submitting a program to a specification
=======================================

The following commands are part of the main-program's CLI and independent
of specification files.

:code:`uvx bast3st submit -u` `USER` :code:`-s` `SLOT PROGRAM.sb3`
------------------------------------------------------------------

See :code:`uvx bast3st submit -h` for further options like
output formats.

.. note::

   By the time of writing this, there is no web-frontend for submitting
   files and inspecting the created report.
   If you don't want to write such a frontend yourself,
   you have to accept the usage of a CLI. You can also build on top of
   it or use Bast3St as a library to build a custom solution.

   You only need a tool that correctly reads and presents the format
   of test reports the server uses for its answers.
   Some information about the `output format <https://marcel-scherzinger.github.io/bast3st-eval/bast3st_eval/#output-format>`__
   (look also at the `Source code` of the definitions)
   can be found in the reference, but the JSON-structure might differ
   from the Rust-structs in subtle ways so you will still need to
   experiment.
