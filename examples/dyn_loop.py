from bast3st import Bast3StSpec, OUTPUT, main
from bast3st.actions import set_flag
from bast3st.decisions import FLAGS, PARAM
from bast3st.spec import Category


spec = Bast3StSpec(
    "Ausgabe des Doppelten der Summe der Quadrate von der ersten bis zur zweiten Eingabe"
)
spec.set_block_count_limit(30, "Sie verwenden zu viele Blöcke")


def correct_value(a, b):
    return sum([2 * i * i for i in range(min(a, b), max(a, b) + 1)])


def get_criterion(a, b):
    return OUTPUT.last.contains_only_this_number(
        correct_value(a, b)
    ).with_failure_explaination(t"Die korrekte Summe ist {correct_value(a, b)}")


def main_test_for(category: Category, a: int, b: int):
    criterion = get_criterion(a, b)
    mtest = category.new_test(f"{a} bis {b}", criterion=criterion, input=[b, a])
    mtest.if_criterion_then(criterion, set_flag("points", f"{a}#{b}", value=2))
    alt_test = mtest.new_alternative_test(
        "Funktioniert es, wenn ich die Eingaben vertausche?",
        criterion=criterion,
        input=[a, b],
    )
    alt_test.if_criterion_then(criterion, set_flag("points", f"{a}#{b}", value=1))
    return mtest


cat = spec.new_category("Positive Grenzen")

main_test_for(cat, 1, 5)
main_test_for(cat, 1, 10)
main_test_for(cat, 6, 20)

cat.run_action(set_flag("sum", value=FLAGS["points"].sum()))

if __name__ == "__main__":
    main(spec)
