########
Concepts
########

Describing decisions
====================

There are multiple situations where you need to describe how a
submission should be evaluated and what is correct behaviour and what not.
This can include the following:

- Specify the success condition of a test case
- Trigger actions like showing warnings depending on the submission
- *Idea: Provide a formula for the allowed number of blocks (per type) a submission may use
  (requires selectors that are not implemented yet)*

This library thinks of decisions in the following way:

1. You :any:`select <Selector>` values that are currently unknown
   (as you don't know what submissions will be handed in in the future), ...
2. ... :any:`transform <Transformation>` these values with multiple operations, ...
3. ... and finally give them to a :any:`criterion <Criterion>`
   that decides if the condition is satisfied.

By using that model, this library only provides some predefined selectors,
transformations and criteria that can be plugged together in multiple ways.

.. _placeholders-in-future:

Placeholders live in the future
===============================

The created tree of multiple different selector-, transformation- and criterion-nodes
is then transformed to a JSON representation that can be stored or sent to a server.

.. warning::

   As this tree can only contain predefined stages plugged together,
   you **can't define new functionality** for evaluating submissions
   that can not be expressed by combining the predefined stages.
   The generated JSON will be interpreted at a later point in time by
   **another program that won't know anything about your modifications**
   and deviations from the normal specification format which will
   likely just cause errors.

Available decision components
=============================

.. _concept-selectors:

Selectors
---------

- :class:`Array indexing<bast3st.decisions.FutureArray>`:
  access a specific element of a :class:`FutureArray <bast3st.decisions.FutureArray>`

    - :func:`LIST("mylist")[number]<bast3st.decisions.LIST>`: select one of the items of the list `mylist` using the state after executing the program
    - :func:`INPUT[number]<bast3st.decisions.INPUT>`: select one of the inputs the submission received during the current test
    - :func:`OUTPUT[number]<bast3st.decisions.OUTPUT>`: select one of the outputs the submission received during the current test
    - :func:`RANDOMS[number] <bast3st.decisions.RANDOMS>`: select one of the random numbers the submission requested and received during the current test
- :class:`Array length<bast3st.decisions.FutureArray>`:
  number of elements in the respective :class:`FutureArray <bast3st.decisions.FutureArray>`

    - :func:`LIST("mylist").length <bast3st.decisions.LIST>`
    - :func:`INPUT.length <bast3st.decisions.INPUT>`
    - :func:`OUTPUT.length <bast3st.decisions.OUTPUT>`
    - :func:`RANDOMS.length <bast3st.decisions.RANDOMS>`
- :func:`VAR("myvar")<bast3st.decisions.VAR>`: value of a specific variable
- :func:`Value::first_capture <bast3st.decisions.Value.first_capture>`:
  :code:`value2 = value1.first_capture("^.(?P<sndLetter>).$")["sndLetter"]`
- :class:`NetworkRequest <bast3st.decisions.NetworkRequest>` (click for details)
- :obj:`FLAGS <bast3st.decisions.FLAGS>` see :ref:`concept-flags` for details
- :obj:`PARAM <bast3st.decisions.PARAM>` see :ref:`concept-param` for details

.. _concept-transformations:

Transformations
---------------

- :func:`concat<bast3st.decisions.concat>`: :code:`concat(value1, " + ", value2)`
    
    - :mod:`t-string<string.templatelib>`-version: :code:`t"{value1} + {value2}"`

      + :mod:`t-string<string.templatelib>` templates are accepted by everyting that takes :any:`IntoValue` or :any:`IntoTextValue`
      + :mod:`t-string<string.templatelib>` templates can be converted explicitly using :any:`Value.of(t"{value1} + {value2}") <Value.of>`:
- :meth:`Value::to_lower<bast3st.decisions.Value.to_lower>`
- :meth:`Value::to_upper<bast3st.decisions.Value.to_upper>`
- :meth:`Value::trim<bast3st.decisions.Value.trim>`
- :meth:`Value::trim_start<bast3st.decisions.Value.trim_start>`
- :meth:`Value::trim_end<bast3st.decisions.Value.trim_end>`
- :func:`if_then_else <bast3st.decisions.if_then_else>`: select one of two options depending on the acceptance state of a criterion

.. _concept-criteria:

Criteria
--------

- :func:`Value::contains_text <bast3st.decisions.Value.contains_text>`:
  :code:`value1.contains_text("hello")`
- :func:`Value::contains_this_number <bast3st.decisions.Value.contains_this_number>`:
  :code:`value1.contains_this_number(42)`
- :func:`Value::contains_only_this_number <bast3st.decisions.Value.contains_only_this_number>`:
  :code:`value1.contains_only_this_number(42)`
- :func:`Value::contains_with_gaps <bast3st.decisions.Value.contains_with_gaps>`:
  :code:`value1.contains_with_gaps("42", "is greater", "24")`
- :func:`Value::matches <bast3st.decisions.Value.matches>`:
  :code:`value1.matches("(?i)a+(?-i)b+")`
  (be aware that this is *not* Python-re's syntax)
- :class:`compare`: typically you can use the short-cut syntax :any:`Value`

  - :any:`compare.eq`: :code:`value1 == value2`
  - :any:`compare.neq`: :code:`value1 != value2`
  - :any:`compare.lt`: :code:`value1 <  value2`
  - :any:`compare.gt`: :code:`value1 >  value2`
  - :any:`compare.le`: :code:`value1 <= value2`
  - :any:`compare.ge`: :code:`value1 >= value2`
- :obj:`ALWAYS_FULFILLED<bast3st.decisions.ALWAYS_FULFILLED>`: a dummy
  criterion that is always successful
- :obj:`NEVER_FULFILLED<bast3st.decisions.NEVER_FULFILLED>`: a dummy
  criterion that is never successful and always fails
- :func:`if_then_else <bast3st.decisions.if_then_else>`: select one of two options depending on the acceptance state of a criterion

- Junctors

  - :func:`all_of(...) <bast3st.decisions.all_of>`:
    :code:`all_of(last_output_contains_A, last_output_contains_a, failure_explaination="Your last output should contain at least one lowercase and one uppercase a")`
  - :func:`any_of(...) <bast3st.decisions.any_of>`
    :code:`any_of(last_output_contains_A, last_output_contains_a, failure_explaination="Your last output should contain at least one a (lower or upper case)")`
  - :any:`Criterion::negate <bast3st.decisions.Criterion.negate>`
    :code:`last_output_contains_number.negate(failure_explaination="Your last output shouldn't contain any number")`


.. _catchable-errors:

Catchable errors
================

There are multiple situations in which decision entities
can encounter unexpected situations or failures.
One of the simplest can occur when selecting the first :any:`OUTPUT`
during a decision as there can be submissions that don't produce
any output at all.
As the term *Catchable errors* implies, one can still work with those
errors to procede the evaluation by *catching* them.

Normally, selectors, transformations and criteria work on the *happy path*::

                                      v catch
    (error path)       +--------------+
                      /                \
                     /                  \
    (happy path) ---+--------------------+----->
                    ^ error

When errors – that aren't severe enough to cancel the whole execution – occur,
the values move to the error path and further (normal) transformations
and criteria will be skipped to pass the error up.
By using a special method to `catch` the error, the execution can come
back to the happy path when the error is handled.

- catching for (transformed) values: :func:`Value::catch <bast3st.decisions.Value.catch>`
- catching for criteria: :func:`Criterion::catch <bast3st.decisions.Criterion.catch>`

Uncatched errors have different effects depending on the context in which they occur.

See :any:`err` for a list of available error kinds that can be catched.

.. _concept-actions:

Actions
=======

In addition to specifying if a test should pass or fail, :ref:`concept-criteria` can be used 
to trigger *actions* if there conditions are satisfied:

- generate a message that will be displayed
  to the student who has submitted a file for checking:

  - :func:`send_message<bast3st.actions.send_message>`
  - :func:`send_info<bast3st.actions.send_info>`
  - :func:`send_warning<bast3st.actions.send_warning>`
  - :func:`send_error<bast3st.actions.send_error>`

- :any:`pass_this_test_immediatly`: stop further checking of :ref:`concept-criteria`
  and mark the currently checked test as *passed*.
- :any:`fail_this_test_immediatly`: stop further checking of :ref:`concept-criteria`
  and mark the currently checked test as *failed*.
- :func:`if_then_else <bast3st.decisions.if_then_else>`: select one of two actions depending on the acceptance state of a criterion
- :func:`set_flag(at_least_one_key, *other_keys, value)<bast3st.actions.set_flag>`: see :ref:`concept-flags`


Test specification
==================

The top-level part of a specification is :class:`Bast3StSpec<bast3st.spec.Bast3StSpec>` which contains all categories and meta information about the point of the whole exercise.
A :class:`Bast3StSpec<bast3st.spec.Bast3StSpec>` object can contain
multiple :class:`Category<bast3st.spec.Category>` objects that group
tests by logical relation.
Each :class:`Category<bast3st.spec.Category>` has multiple
:class:`MainTest<bast3st.spec.MainTest>` instances each of them being
able to hold :class:`AlternativeTest<bast3st.spec.AlternativeTest>`
objects. These objects
(aside from :class:`Bast3StSpec<bast3st.spec.Bast3StSpec>`)
should mostly not be instantiated directly but through special
functions:

- :func:`Bast3StSpec::new_category<bast3st.spec.Bast3StSpec.new_category>`
- :func:`Category::new_test<bast3st.spec.Category.new_test>`
- :func:`MainTest::new_alternative_test<bast3st.spec.MainTest.new_alternative_test>`

See the functions for required arguments. All levels support extra hook
conditions to run actions if some criterion is suffied:

- :func:`Bast3StSpec::if_criterion_then<bast3st.spec.Bast3StSpec.if_criterion_then>`
- :func:`Category::if_criterion_then<bast3st.spec.Category.if_criterion_then>`
- :func:`MainTest::if_criterion_then<bast3st.spec.MainTest.if_criterion_then>`
- :func:`AlternativeTest::if_criterion_then<bast3st.spec.AlternativeTest.if_criterion_then>`

There are also those convenience functions which call the above with :obj:`ALWAYS_FULFILLED<bast3st.decisions.ALWAYS_FULFILLED>`:

- :func:`Bast3StSpec::run_action<bast3st.spec.Bast3StSpec.run_action>`
- :func:`Category::run_action<bast3st.spec.Category.run_action>`
- :func:`MainTest::run_action<bast3st.spec.MainTest.run_action>`
- :func:`AlternativeTest::run_action<bast3st.spec.AlternativeTest.run_action>`

Each of those functions specifies an *order* which decides when the
condition should be checked and the action be run. The following shows a typical flow

.. _concept-order:

Execution order of a test specification
---------------------------------------

1. *run hooks of* :class:`specification<bast3st.spec.Bast3StSpec>`
   *that should be run before all categories*
2. process each :class:`Category<bast3st.spec.Category>`:

    3. *run hooks of* :class:`Category<bast3st.spec.Category>`
       *that should be run before all tests of this category*
    4. process each :class:`MainTest<bast3st.spec.MainTest>`:

        5. *run hooks of* :class:`MainTest<bast3st.spec.MainTest>`
           *that should be run before the actual test*
        6. evaluate the main test's :class:`Criterion<bast3st.decisions.Criterion>`
           to decide if the test should be passed 
        7. *run hooks of* :class:`MainTest<bast3st.spec.MainTest>`
           that should be run *after the actual test*
        8. **If the main test failed**, *run hooks of*
           :class:`MainTest<bast3st.spec.MainTest>`
           *that should be run after the main test but before the*
           *alternative tests*
        9. **If the main test failed**, process each
           :class:`AlternativeTest<bast3st.spec.AlternativeTest>`
           in order until one passes or all were tried:
            
            10. *run hooks of* :class:`AlternativeTest<bast3st.spec.AlternativeTest>` *that should be run before the alternative test*
            11. evaluate the alternative test's :class:`Criterion<bast3st.decisions.Criterion>`
                to decide if the test should be passed.
                (if so, run 12 but proceed to 13 without trying 9 again)
            12. *run hooks of*
                :class:`AlternativeTest<bast3st.spec.AlternativeTest>`
                *that should be run after the alternative test*

        13. *run hooks of* :class:`MainTest<bast3st.spec.MainTest>`
            *that should be run after the main test and after the*
            *alternative tests*

    14. *run hooks of* :class:`Category<bast3st.spec.Category>`
        *that should be run after all tests of this category*

15. *run hooks of* :class:`specification<bast3st.spec.Bast3StSpec>`
    *that should be run after all categories*

.. note::

   This order of (hook) execution is important if you rely on
   results from other stages being present, like when you set
   flags or change the global state in other means.

   Categories of a specification and main tests of a category
   are computed independently from each other (maybe even in parallel).


.. _concept-flags:

Setting and reading flags
=========================

Flags are a way for the author of a test specification to store
values across stages and communicate them to external tools.
If you set the same flag in multiple stages or want to read a flag
that was set in another stage, you should consider the following about
flag visibility to ensure that the changes are really visible when
you expect them to be available:

1. Flag changes will never be visible during the same "atomic" step
   in which they were made, where "atomic" step means a single evaluation
   like checking if the criterion of a hook is valid, evaluating the
   action of a hook, ...

2. Different steps within a sequentially treated process can see all flag
   changes of their predecessors in the order they are specified in source.

    a. Different hooks of the same kind and entity
       (e. g. all `before main` hooks of a main test) are run sequentially.
       So every hook will see the flag-state its predecessor hook produced.
    b. The action of a hook is executed strictly after the criterion of the
       same hook, so the criterion can set flags that are then visible to
       the action
    c. Inside a main test (the main tests hooks, alternative tests and their
       hooks) are run sequentially in the order :ref:`concept-order` describes.

3. Parallel stages are all started with the same initial flag-view and
   operate independently from the flag-setting of others till they end.
   As soon as they have finished, their flags are *merged* in the order
   in which they occur in the specification file:

    a. All categories of a specification are run with the flag-state after
       the last `before all categories` hook. When they finished, their
       final flag values are merged sequentially. Afterwards this state
       is used as input to the first `after all categories` hook.
    b. All tests of a category are run with the flag-state after
       the last `before all tests` hook. When they finished, their
       final flag values are merged sequentially. Afterwards this state
       is used as input to the first `after all tests` hook.

.. _concet-flags-merge:

How flags are merged
--------------------

Flag-merging is non-commutative, so the order matters if there
are conflicting keys. The *left* or *old* flags name in the following
the flags from a predecessor step and *right* or *new* the flags from
the current step that need to be merged into the existing ones.

Flags allow only primitive values (texts and numbers), so no mappings
or arrays can be set here, but as flags *do* allow nested keys,
one can set multiple keys with the same prefix and then read them
at a later point as a mapping.

A simple example:

1. :code:`set_flag("points", "test1", value=4)` (after: :code:`{"points": {"test1": 4}}`)
2. :code:`set_flag("points", "test2", value=0)` (after: :code:`{"points": {"test1": 4, "test2": 0}}`)
3. :code:`set_flag("points", "test3", value=2)` (after: :code:`{"points": {"test1": 4, "test2": 0, "test3": 2}}`)
4. :code:`set_flag("points", value=FLAGS["points"].sum())` (after: :code:`{"points": 6}`)

The merging process can be described with pattern matching and recursion:

    match (old, new):
        (Mapping o, Mapping n) => 
            items with keys that occur in exactly one of the mappings are taken as they are,
            for conflicting keys the values are merged in the same order to get the key's new value.
        (Primitive o, Mapping n) =>
            the old value is treated as the mapping :code:`{"": o}` (empty string to normal value)
            and this value is then merged with the mapping :code:`n`, so it survives as long
            as :code:`n` doesn't contain :code:`""` as a key.
        (Mapping o, Primitive n) =>
            the new value (:code:`n`) wins and is kept instead of the whole mapping
        (Primitive o, Primitive n) =>
            the new value (:code:`n`) wins and is kept

.. _concept-param:

Parameters
==========

Parameters are similar to flags, but they are readonly for specifications and
can only be set from the outside. They are accessible through :obj:`PARAM<bast3st.decisions.PARAM>`
and are grouped into multi-level scopes::

    {
        "doc": {
            "blockcount": {
                "total": NUMBER,
                "opcode": {
                    opcode1: NUMBER,
                    opcode2: NUMBER,
                    ...
                }
            }
        },
    }

The `opcode` mapping contains a value for every block-kind the submission used.
See the Scratch wiki for a list of `official opcode-names <https://en.scratch-wiki.info/wiki/List_of_Block_Opcodes>`__
but be aware that only the ones from `scratch-test-model/BlockKindUnit <https://marcel-scherzinger.github.io/scratch-test-model/scratch_test_model/blocks/enum.BlockKindUnit.html>`__ and co are detected by the application.
(detected doesn't mean supported and unsupported blocks will just be skipped during execution of a program if possible or cancel execution if not.)
If you try to read an item from :code:`PARAM["doc", "blockcount", "opcode"]` that doesn't exist, you will receive 0 instead of an error.

:code:`PARAM["doc", "blockcount", "total"]` will be the same value as :code:`PARAM["doc", "blockcount", "opcode"].sum()` or :code:`PARAM["doc", "blockcount", "opcode"].values().sum()`.
