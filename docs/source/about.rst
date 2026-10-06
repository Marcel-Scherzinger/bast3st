#####
About
#####

This project was created for the
`Kontaktstudium Informatik <https://www.kontaktstudium-informatik.uni-konstanz.de/>`_
and provides a way to unit test programs written in the
`Scratch programming language <https://scratch.mit.edu/>`_
that are submitted by students to defined algorithmic exercises.

.. note::

    Algorithmic is important here as this project considers sounds,
    images, movement, other sensing functionality and
    concurrency (whose order is undefined in Scratch) out-of-scope,
    ignores it where possible and rejects whole files where
    ignoring is not possible.

Repositories
============

Bast3St is split into multiple repositories that build on each other, the most important ones are:

- `github:marcel-scherzinger/scratch-test-value <https://github.com/marcel-scherzinger/scratch-test-value>`_: implements how Scratch defines computations like arithmetic operations or coercions
- `github:marcel-scherzinger/scratch-test-model <https://github.com/marcel-scherzinger/scratch-test-model>`_: parses the Scratch-file-format :code:`sb3`
- `github:marcel-scherzinger/scratch-test-interpreter <https://github.com/marcel-scherzinger/scratch-test-interpreter>`_: allows running a parsed Scratch program with given inputs and defined limits
- `github:marcel-scherzinger/bast3st-eval <https://github.com/marcel-scherzinger/bast3st-eval>`_: takes JSON data that describes what a program should be tested for and creates a detailed report
- `github:marcel-scherzinger/bast3st-web <https://github.com/marcel-scherzinger/bast3st-web>`_: listens for requests to analyze programs, responds with reports and stores everyting in a Postgres-database
- `github:marcel-scherzinger/bast3st <https://github.com/marcel-scherzinger/bast3st>`_: Python library to generate JSON specifiactions by writing scripts with type hinting support and CLI program that allows interacting with a server

What's with the name?
=====================

.. raw:: html

   <table style="background:#1a3042;border-radius:1rem;color: white; margin-bottom: 0.5rem" width="100%">
   <tr>
   <td style="padding:0.5rem">
    <span style="color:#808080; text-shadow: 0 0 5px #808080">Bast3</span><span style="color:#f0ff00; text-shadow: 0 0 5px #f0ff00">S</span><span style="color:#808080; text-shadow: 0 0 5px #808080">t</span>
   </td>
   <td style="padding:0.5rem">The project is about Scratch and it starts with S</td>
   </tr>
   <tr>
   <td style="padding:0.5rem; padding-top: 0rem">
    <span style="color:#f0ff00; text-shadow: 0 0 5px #f0ff00">B</span><span style="color:#808080; text-shadow: 0 0 5px #808080">ast</span><span style="color:#f0ff00; text-shadow: 0 0 5px #f0ff00">3S</span><span style="color:#808080; text-shadow: 0 0 5px #808080">t</span>
   </td>
   <td style="padding:0.5rem; padding-top: 0rem">The file extension of Scratch is sb3</td>
   </tr>
   <tr>
   <td style="padding:0.5rem; padding-top: 0rem">
    <span style="color:#f0ff00; text-shadow: 0 0 5px #f0ff00">Baste</span><span style="color:#808080; text-shadow: 0 0 5px #808080">S</span><span style="color:#f0ff00; text-shadow: 0 0 5px #f0ff00">t</span>
   </td>
   <td style="padding:0.5rem; padding-top: 0rem">Bastet is the egyptian god of cats</td>
   </tr>
   <tr>
   <td style="padding:0.5rem; padding-top: 0rem">
    <span style="color:#808080; text-shadow: 0 0 5px #808080">Bas</span><span style="color:#f0ff00; text-shadow: 0 0 5px #f0ff00">teSt</span>
   </td>
   <td style="padding:0.5rem; padding-top: 0rem">This project is about testing</td>
   </tr>
   </table>
