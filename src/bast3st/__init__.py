from bast3st.decisions import (
    OUTPUT,
    INPUT,
    LIST,
    VAR,
    NetworkRequest,
    BLOCKCOUNT,
    PARAM,
    any_of,
    all_of,
    negated,
    if_then_else,
)
from bast3st.spec import Bast3StSpec, Category, AlternativeTest, MainTest
from bast3st.catchable import err
from bast3st.actions import (
    send_error,
    send_info,
    send_message,
    send_warning,
    pass_this_test_immediatly,
    end_this_test_immediatly,
    fail_this_test_immediatly,
)
from bast3st.client import main
