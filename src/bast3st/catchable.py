import enum

from bast3st._general import ForceInline


class err(enum.Flag):
    """
    Collection of all :ref:`catchable-errors` that can occur in any situation.

    As described in :class:`enum.Flag`, you can use bitwise operations to combine
    the error names from this type. Thisway, you can filter out arbitrary combinations
    of different error causes.

    Never rely on the exact numeric values of the following constants.
    They are not stable and not considered part of the api.

    (You can click on the `[source]` button to see how compound flags are defined.)

    .. warning:: Compound error-values don't exist at the json level and are serialized
        as a :code:`|`-separated list of their parts, so if e. g. a new server version
        would introduce a new error kind, your previously (with an old version)
        serialized and uploaded specification won't catch this error even though it
        might belong to a group whose compound flag you used.
        You then have to use a new version of this library to re-serialize the spec.
    """

    #: the status that was reported isn't among the ones in the allow-list
    network_statusDisallowed = enum.auto()
    #: a selector tried to extract json from the response,
    #: but the response is not json
    network_respInvalid_notJson = enum.auto()
    #: the administrator doesn't allow contacting the specified server
    network_policy_serverNotAllowed = enum.auto()
    #: the administrator doesn't allow using the specified scheme (=https, http, file, ...)
    network_policy_schemeNotAllowed = enum.auto()
    #: the administrator doesn't allow the request for some reason
    network_policy_other = enum.auto()
    network_policy = (
        network_policy_serverNotAllowed
        | network_policy_schemeNotAllowed
        | network_policy_other
    )

    #: networking can always fail, this error indicates that the program tried to
    #: execute the request but something failed that wasn't in the program's control
    network_external = enum.auto()
    #: the combination of server + '/' + route can't be parsed as a valid url
    network_url_syntax = enum.auto()

    network = (
        network_respInvalid_notJson
        | network_statusDisallowed
        | network_policy
        | network_external
        | network_url_syntax
    )

    #: a variable was requested that is missing, e.g. no variable with the specified name exists
    missing_variable = enum.auto()
    #: a list was requested and the whole list is missing.
    #: If the list was requested by name, there is no list with this name.
    missing_list = enum.auto()
    missing = missing_list | missing_variable

    #: the syntax of the pattern is invalid
    regex_syntax = enum.auto()
    #: there is no match for the pattern in the specified text/array
    regex_noMatch = enum.auto()
    #: the thing in which the pattern should search is neither an array nor a text
    regex_invalidHaystack = enum.auto()
    #: the specified capture group doesn't exist
    regex_noGroup = enum.auto()
    regex = regex_syntax | regex_noMatch | regex_noGroup | regex_invalidHaystack

    #: a MapKey that was used to index an array is either not in range or not an int
    collection_keyInvalidForArray = enum.auto()
    #: the key doesn't belong to a value in the collection at hand
    collection_valueNotFound = enum.auto()
    collection = collection_keyInvalidForArray | collection_valueNotFound

    typing_notCollection_notArray = enum.auto()
    typing_notCollection_notMapping = enum.auto()
    typing_notCollection = (
        typing_notCollection_notArray | typing_notCollection_notMapping
    )

    typing_notAction = enum.auto()
    typing_notCriterion = enum.auto()
    typing_notValue = enum.auto()
    typing_notPrimitive = enum.auto()
    typing_notText = enum.auto()
    typing_notNumeric = enum.auto()
    typing_notMapkey = enum.auto()
    typing_notIterable = enum.auto()
    #: `typing` errors occur if a component needs an evaluated value to be of a specific
    #: shape while it isn't the case
    typing = (
        typing_notCollection
        | typing_notAction
        | typing_notCriterion
        | typing_notValue
        | typing_notPrimitive
        | typing_notText
        | typing_notNumeric
        | typing_notMapkey
        | typing_notIterable
    )

    any = missing | network | regex | collection | typing

    def _to_json_able(self, _):
        return ForceInline("|".join([x.name for x in list(self) if x.name is not None]))
