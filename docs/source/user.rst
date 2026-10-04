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


