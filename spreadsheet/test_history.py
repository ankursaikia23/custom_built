from commands.base import Command
from commands.history import History

class TestCommand(Command):
    def __init__(self):
        self.value=0

    def execute(self):
        self.value+=1

    def undo(self):
        self.value-=1

command=TestCommand()
history=History()
history.execute(command)
print("After execute:",command.value)
history.undo()
print("After undo:",command.value)
history.redo()
print("After redo:",command.value)