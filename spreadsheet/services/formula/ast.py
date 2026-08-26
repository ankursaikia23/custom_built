class ErrorNode:
    def __init__(self, error):
        self.error = error

class NumberNode:
    def __init__(self,value):
        self.value=value
        
class CellNode:
    def __init__(self,reference):
        self.reference=reference

class BinaryOperationNode:
    def __init__(self,operator,left,right):
        self.operator=operator
        self.left=left
        self.right=right

class FunctionNode:
    def __init__(self,name,args):
        self.name=name
        self.args=args

class RangeNode:
    def __init__(self,start,end,sheet_name=None):
        self.start=start
        self.end=end
        self.sheet_name=sheet_name