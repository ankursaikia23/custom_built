class History:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def execute(self, command):
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return False

        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        return True

    def redo(self):
        if not self.redo_stack:
            return False

        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)
        return True

    def can_undo(self):
        return bool(self.undo_stack)

    def can_redo(self):
        return bool(self.redo_stack)

    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()

    def undo_count(self):
        return len(self.undo_stack)

    def redo_count(self):
        return len(self.redo_stack)