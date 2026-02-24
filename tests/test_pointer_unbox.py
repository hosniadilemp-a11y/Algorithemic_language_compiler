import sys
sys.path.append('src')
from compiler.parser import pointer_class_code

exec_globals = {}
exec(pointer_class_code, exec_globals)

Pointer = exec_globals['Pointer']

base = [None] * 50
p1 = Pointer("phrase", exec_globals, index=0, base_var=base)
p2 = Pointer("ptr", exec_globals, index=0, base_var=p1)

def unbox(source_val):
    if hasattr(source_val, "_get_target_container"):
        targ = source_val._get_target_container()
        while hasattr(targ, "_get_target_container"):
            targ = targ._get_target_container()
        return type(targ)
    return type(source_val)

print("Unboxed Type:", unbox(p2))
