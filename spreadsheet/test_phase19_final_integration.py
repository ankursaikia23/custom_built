from services.formula.recalculation import RecalculationManager


class Cell:
    def __init__(self, value=None):
        self.value = value


class Sheet:
    def __init__(self, name):
        self.name = name
        self.cells = {}

    def set_cell(self, reference, value):
        self.cells[reference] = Cell(value)

    def get_cell(self, reference):
        return self.cells.get(reference)


class Workbook:
    def __init__(self):
        self.sheets = {}

    def add_sheet(self, sheet):
        self.sheets[sheet.name] = sheet

    def get_sheet(self, name):
        return self.sheets.get(name)


def create_environment():
    workbook = Workbook()

    sheet1 = Sheet("Sheet1")
    sheet2 = Sheet("Sheet2")

    workbook.add_sheet(sheet1)
    workbook.add_sheet(sheet2)

    manager = RecalculationManager(
        sheet=sheet1,
        workbook=workbook
    )

    return manager, workbook, sheet1, sheet2


def register(manager, cell, formula, dependencies):
    manager.register_formula(
        cell,
        formula
    )

    manager.graph.set_dependencies(
        cell,
        dependencies
    )


# ==================================================
# 1. Basic dependency chain
#
# A1 -> B1 -> C1 -> D1
# ==================================================

manager, workbook, sheet1, sheet2 = (
    create_environment()
)

sheet1.set_cell("A1", 10)
sheet1.set_cell("B1", "=A1+5")
sheet1.set_cell("C1", "=B1*2")
sheet1.set_cell("D1", "=C1+10")

register(
    manager,
    "B1",
    "=A1+5",
    {"A1"}
)

register(
    manager,
    "C1",
    "=B1*2",
    {"B1"}
)

register(
    manager,
    "D1",
    "=C1+10",
    {"C1"}
)

order = manager.get_recalculation_order("A1")

assert set(order) == {
    "B1",
    "C1",
    "D1"
}

assert order.index("B1") < order.index("C1")
assert order.index("C1") < order.index("D1")

result = manager.recalculate("A1")

assert result["B1"] == 15
assert result["C1"] == 30
assert result["D1"] == 40

print("Basic dependency integration: PASS")


# ==================================================
# 2. Branching dependencies
#
#          -> B1 ->
# A1                D1
#          -> C1 ->
# ==================================================

sheet1.set_cell("B1", "=A1+5")
sheet1.set_cell("C1", "=A1*2")
sheet1.set_cell("D1", "=B1+C1")

register(
    manager,
    "B1",
    "=A1+5",
    {"A1"}
)

register(
    manager,
    "C1",
    "=A1*2",
    {"A1"}
)

register(
    manager,
    "D1",
    "=B1+C1",
    {"B1", "C1"}
)

order = manager.get_recalculation_order("A1")

assert set(order) == {
    "B1",
    "C1",
    "D1"
}

assert order.index("B1") < order.index("D1")
assert order.index("C1") < order.index("D1")

result = manager.recalculate("A1")

assert result["B1"] == 15
assert result["C1"] == 20
assert result["D1"] == 35

print("Branching integration: PASS")


# ==================================================
# 3. Range dependency
# ==================================================

sheet1.set_cell("A2", 10)
sheet1.set_cell("A3", 20)

sheet1.set_cell(
    "B2",
    "=SUM(A1:A3)"
)

register(
    manager,
    "B2",
    "=SUM(A1:A3)",
    {"A1:A3"}
)

assert manager.graph.get_dependencies(
    "B2"
) == {"A1:A3"}

print("Range integration: PASS")


# ==================================================
# 4. Function dependency
# ==================================================

sheet1.set_cell(
    "B3",
    "=ABS(A1)"
)

register(
    manager,
    "B3",
    "=ABS(A1)",
    {"A1"}
)

sheet1.get_cell("A1").value = -25

result = manager.recalculate("A1")

assert result["B3"] == 25

print("Function integration: PASS")


# ==================================================
# 5. Error propagation
# ==================================================

sheet1.set_cell(
    "B1",
    "=10/A1"
)

sheet1.set_cell(
    "C1",
    "=B1+5"
)

sheet1.set_cell(
    "D1",
    "=C1*2"
)

register(
    manager,
    "B1",
    "=10/A1",
    {"A1"}
)

register(
    manager,
    "C1",
    "=B1+5",
    {"B1"}
)

register(
    manager,
    "D1",
    "=C1*2",
    {"C1"}
)

sheet1.get_cell("A1").value = 0

result = manager.recalculate("A1")

assert result["B1"] == "#DIV/0!"
assert result["C1"] == "#DIV/0!"
assert result["D1"] == "#DIV/0!"

print("Error propagation integration: PASS")


# ==================================================
# 6. Error recovery
# ==================================================

sheet1.get_cell("A1").value = 20

result = manager.recalculate("A1")

assert result["B1"] == 0.5
assert result["C1"] == 5.5
assert result["D1"] == 11

print("Error recovery integration: PASS")


# ==================================================
# 7. VALUE error and recovery
# ==================================================

sheet1.get_cell("A1").value = "hello"

result = manager.recalculate("A1")

assert result["B1"] == "#VALUE!"
assert result["C1"] == "#VALUE!"
assert result["D1"] == "#VALUE!"

print("VALUE error integration: PASS")

sheet1.get_cell("A1").value = 40

result = manager.recalculate("A1")

assert result["B1"] == 0.25
assert result["C1"] == 5.25
assert result["D1"] == 10.5

print("VALUE recovery integration: PASS")


# ==================================================
# 8. NAME error and recovery
# ==================================================

sheet1.set_cell(
    "B1",
    "=UNKNOWN(A1)"
)

register(
    manager,
    "B1",
    "=UNKNOWN(A1)",
    {"A1"}
)

result = manager.recalculate("A1")

assert result["B1"] == "#NAME?"
assert result["C1"] == "#VALUE!" or result["C1"] == "#NAME?"
assert result["D1"] == "#VALUE!" or result["D1"] == "#NAME?"

print("NAME error integration: PASS")


sheet1.set_cell(
    "B1",
    "=10/A1"
)

register(
    manager,
    "B1",
    "=10/A1",
    {"A1"}
)

sheet1.get_cell("A1").value = 50

result = manager.recalculate("A1")

assert result["B1"] == 0.2

print("NAME recovery integration: PASS")


# ==================================================
# 9. IF lazy evaluation
# ==================================================

sheet1.set_cell(
    "B1",
    "=IF(A1=0,10,20)"
)

register(
    manager,
    "B1",
    "=IF(A1=0,10,20)",
    {"A1"}
)

sheet1.get_cell("A1").value = 0

result = manager.recalculate("A1")

assert result["B1"] == 10

sheet1.get_cell("A1").value = 5

result = manager.recalculate("A1")

assert result["B1"] == 20

print("IF integration: PASS")


# ==================================================
# 10. Cross-sheet dependency
# ==================================================

sheet1.set_cell("A1", 100)

sheet2.set_cell(
    "A1",
    "=Sheet1!A1/2"
)

register(
    manager,
    "Sheet2!A1",
    "=Sheet1!A1/2",
    {"Sheet1!A1"}
)

assert manager.graph.get_dependents(
    "Sheet1!A1"
) == {"Sheet2!A1"}

result = manager.recalculate(
    "Sheet1!A1"
)

assert result["Sheet2!A1"] == 50

print("Cross-sheet integration: PASS")


# ==================================================
# 11. Cross-sheet error and recovery
# ==================================================

sheet1.get_cell("A1").value = 0

result = manager.recalculate(
    "Sheet1!A1"
)

assert result["Sheet2!A1"] == "#DIV/0!"

print("Cross-sheet error propagation: PASS")


sheet1.get_cell("A1").value = 200

result = manager.recalculate(
    "Sheet1!A1"
)

assert result["Sheet2!A1"] == 100

print("Cross-sheet recovery: PASS")


# ==================================================
# 12. Formula mutation
# ==================================================

sheet1.set_cell(
    "B1",
    "=A1+100"
)

register(
    manager,
    "B1",
    "=A1+100",
    {"A1"}
)

assert manager.graph.get_dependencies(
    "B1"
) == {"A1"}

sheet1.set_cell(
    "B1",
    "=Sheet2!A1+100"
)

register(
    manager,
    "B1",
    "=Sheet2!A1+100",
    {"Sheet2!A1"}
)

assert manager.graph.get_dependencies(
    "B1"
) == {"Sheet2!A1"}

assert manager.graph.get_dependents(
    "A1"
) == {
    "Sheet2!A1"
}

assert manager.graph.get_dependents(
    "Sheet2!A1"
) == {
    "B1"
}

print("Formula mutation integration: PASS")


# ==================================================
# 13. Mutation recalculation
# ==================================================

sheet1.get_cell("A1").value = 300

result = manager.recalculate(
    "Sheet1!A1"
)

assert result["Sheet2!A1"] == 150
assert result["B1"] == 250

print("Mutation recalculation: PASS")


# ==================================================
# 14. Circular dependency detection
# ==================================================

circular_manager, circular_workbook, circular_sheet1, _ = (
    create_environment()
)

circular_sheet1.set_cell(
    "A1",
    "=B1+1"
)

circular_sheet1.set_cell(
    "B1",
    "=A1+1"
)

register(
    circular_manager,
    "A1",
    "=B1+1",
    {"B1"}
)

register(
    circular_manager,
    "B1",
    "=A1+1",
    {"A1"}
)

assert circular_manager.has_circular_dependency(
    "A1"
)

assert circular_manager.has_circular_dependency(
    "B1"
)

print("Circular dependency integration: PASS")


# ==================================================
# 15. Circular recovery after breaking cycle
# ==================================================

circular_sheet1.set_cell(
    "B1",
    "=10"
)

register(
    circular_manager,
    "B1",
    "=10",
    set()
)

assert not circular_manager.has_circular_dependency(
    "A1"
)

assert not circular_manager.has_circular_dependency(
    "B1"
)

print("Circular recovery integration: PASS")


# ==================================================
# 16. Dependency graph persistence
# ==================================================

assert manager.graph.get_dependencies(
    "Sheet2!A1"
) == {
    "Sheet1!A1"
}

assert manager.graph.get_dependencies(
    "B1"
) == {
    "Sheet2!A1"
}

assert manager.graph.get_dependents(
    "Sheet1!A1"
) == {
    "Sheet2!A1"
}

assert manager.graph.get_dependents(
    "Sheet2!A1"
) == {
    "B1"
}

print("Dependency graph persistence: PASS")


# ==================================================
# 17. Repeated recalculation stability
# ==================================================

sheet1.get_cell("A1").value = 500

for _ in range(10):

    result = manager.recalculate(
        "Sheet1!A1"
    )

    assert result["Sheet2!A1"] == 250
    assert result["B1"] == 350

print("Repeated recalculation stability: PASS")


# ==================================================
# 18. Final graph cleanup
# ==================================================

manager.remove_formula("B1")

assert manager.graph.get_dependencies(
    "B1"
) == set()

assert manager.graph.get_dependents(
    "Sheet2!A1"
) == set()

print("Final dependency cleanup: PASS")


# ==================================================
# 19. Final restoration
# ==================================================

sheet1.set_cell(
    "B1",
    "=Sheet2!A1+100"
)

register(
    manager,
    "B1",
    "=Sheet2!A1+100",
    {"Sheet2!A1"}
)

assert manager.graph.get_dependencies(
    "B1"
) == {
    "Sheet2!A1"
}

assert manager.graph.get_dependents(
    "Sheet2!A1"
) == {
    "B1"
}

sheet1.get_cell("A1").value = 600

result = manager.recalculate(
    "Sheet1!A1"
)

assert result["Sheet2!A1"] == 300
assert result["B1"] == 400

print("Final restoration: PASS")


# ==================================================
# 20. Final repeated error/recovery cycle
# ==================================================

for value in (
    0,
    10,
    100,
    0,
    50,
    0,
    200,
):

    sheet1.get_cell("A1").value = value

    result = manager.recalculate(
        "Sheet1!A1"
    )

    if value == 0:

        assert result["Sheet2!A1"] == "#DIV/0!"
        assert result["B1"] == "#DIV/0!"

    else:

        assert result["Sheet2!A1"] == value / 2
        assert result["B1"] == value / 2 + 100


print("Final error/recovery cycle: PASS")


# ==================================================
# FINAL PHASE 19 GATE
# ==================================================

print("========================================")
print("PHASE 19 PART 14: PASS")
print("========================================")
print("PHASE 19 COMPLETE")
print("========================================")