from commands.history import History

class TestCommand:
    def __init__(self, state, value):
        self.state = state
        self.value = value
        self.previous = None

    def execute(self):
        self.previous = self.state["value"]
        self.state["value"] = self.value

    def undo(self):
        self.state["value"] = self.previous


state = {"value": 0}
history = History()

assert history.can_undo() is False
assert history.can_redo() is False
print("Empty history: PASS")


command1 = TestCommand(state, 10)
history.execute(command1)

assert state["value"] == 10
assert history.undo_count() == 1
assert history.redo_count() == 0
assert history.can_undo() is True
assert history.can_redo() is False
print("Execute command: PASS")


assert history.undo() is True
assert state["value"] == 0
assert history.undo_count() == 0
assert history.redo_count() == 1
print("Undo command: PASS")


assert history.redo() is True
assert state["value"] == 10
assert history.undo_count() == 1
assert history.redo_count() == 0
print("Redo command: PASS")


command2 = TestCommand(state, 20)
history.execute(command2)

assert state["value"] == 20
assert history.undo_count() == 2
assert history.redo_count() == 0
print("New command clears redo: PASS")


assert history.undo() is True
assert state["value"] == 10

assert history.undo() is True
assert state["value"] == 0

assert history.undo() is False
assert state["value"] == 0
print("Multiple undo operations: PASS")


assert history.redo() is True
assert state["value"] == 10

assert history.redo() is True
assert state["value"] == 20

assert history.redo() is False
assert state["value"] == 20
print("Multiple redo operations: PASS")


history.clear()

assert history.can_undo() is False
assert history.can_redo() is False
assert history.undo_count() == 0
assert history.redo_count() == 0
print("Clear history: PASS")