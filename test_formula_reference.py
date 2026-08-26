from services.formula.reference import adjust_reference,adjust_formula

assert adjust_reference("A1",1,0)=="A2"
assert adjust_reference("A1",0,1)=="B1"
assert adjust_reference("Z1",0,1)=="AA1"
assert adjust_reference("AA1",0,1)=="AB1"
print("Basic reference adjustment: PASS")
assert adjust_reference("$A$1",5,5)=="$A$1"
assert adjust_reference("$A1",2,3)=="$A3"
assert adjust_reference("A$1",2,3)=="D$1"
assert adjust_reference("$B2",-1,0)=="$B1"
print("Absolute references: PASS")
assert adjust_formula("=A1+B1",1,0)=="=A2+B2"
assert adjust_formula("=A1*10",0,1)=="=B1*10"
assert adjust_formula("=SUM(A1:A5)",1,1)=="=SUM(B2:B6)"
assert adjust_formula("=A1+(B1*2)",2,1)=="=B3+(C3*2)"
print("Formula adjustment: PASS")
assert adjust_formula("=$A$1+B1",1,1)=="=$A$1+C2"
assert adjust_formula("=$A1+B$1",2,2)=="=$A3+D$1"
print("Mixed references: PASS")
assert adjust_formula("Hello",1,1)=="Hello"
assert adjust_formula(123,1,1)==123
print("Non-formula values: PASS")