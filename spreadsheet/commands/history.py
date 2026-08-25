class History:
    def __init__(self):
        self.undo_stack=[]
        self.redo_stack=[]
    
    def execute(self,command):
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()
    
    def undo(self):
        if not self.undo_stack:
            return
        command=self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
    
    def redo(self):
        if not self.redo_stack:
            return
        command=self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)