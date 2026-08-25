from services.formula.parser import Parser

def print_node(node,indent=0):
    prefix=" "*indent
    if hasattr(node,"value") and not hasattr(node,"operator"):
        print(prefix+f"{type(node).__name__}: {node.value}")
    elif hasattr(node,"operator"):
        print(prefix+f"Binary: {node.operator}")
        print_node(node.left,indent+2)
        print_node(node.right,indent+2)
    elif hasattr(node,"reference"):
        print(prefix+f"Cell: {node.reference}")
    elif hasattr(node,"name"):
        print(prefix+f"Function: {node.name}")
        for arg in node.args:
            print_node(arg,indent+2)
    elif hasattr(node,"start"):
        print(prefix+"Range")
        print_node(node.start,indent+2)
        print_node(node.end,indent+2)

parser=Parser()
tests=["=1+2","=A1+B1","=A1+(B1*2)","=SUM(A1:A5)"]
for formula in tests:
    print(formula)
    print_node(parser.parse(formula))
    print()