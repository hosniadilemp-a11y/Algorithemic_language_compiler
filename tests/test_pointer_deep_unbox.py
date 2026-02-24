import sys
sys.path.append('src')
from compiler.parser import pointer_class_code

exec_globals = {}
exec(pointer_class_code, exec_globals)

Pointer = exec_globals['Pointer']
base = ['P', 'o', 'i', 'n', 't', 'e', 'u', 'r', 's', '!', '\0'] + [None] * 39
p1 = Pointer("phrase", exec_globals, index=0, base_var=base)
p2 = Pointer("ptr", exec_globals, index=0, base_var=p1)

def _algo_to_string(val):
    if isinstance(val, bool): return "Vrai" if val else "Faux"
    if isinstance(val, list):
        res = ""
        for char in val:
            if char is None or char == "\0": break
            res += str(char)
        return res
    return str(val)

def _algo_assign_fixed_string(target_list, source_val):
    if not isinstance(target_list, list): return target_list
    limit = len(target_list)
    s_val = ''
    if hasattr(source_val, '_get_target_container'):
        targ = source_val._get_target_container()
        while hasattr(targ, '_get_target_container'):
            targ = targ._get_target_container()
            
        if isinstance(targ, list):
            s_val = _algo_to_string(targ[source_val.index:])
        else:
            s_val = str(source_val._get_string() if hasattr(source_val, '_get_string') else source_val._get())
    elif isinstance(source_val, list):
         s_val = _algo_to_string(source_val)
    else:
         s_val = str(source_val)
    
    if limit > 0:
        s_val = s_val[:limit-1]
        for i in range(len(s_val)):
            target_list[i] = s_val[i]
        target_list[len(s_val)] = '\0'
        for i in range(len(s_val)+1, limit):
            target_list[i] = None
    return target_list

target = [None] * 50
print("RESULT OF p1: ", "".join([c for c in _algo_assign_fixed_string(target.copy(), p1) if c is not None]))
print("RESULT OF p2: ", "".join([c for c in _algo_assign_fixed_string(target.copy(), p2) if c is not None]))
