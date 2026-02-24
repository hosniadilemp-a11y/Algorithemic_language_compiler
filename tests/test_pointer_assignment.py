import json
import sys
sys.path.append('src')
from compiler.parser import compile_algo

code = """
Algorithme TestDecay;
Var
    phrase[50] : Chaine;
    ptr_chaine : ^Chaine;
    temp_chaine[50] : Chaine;
Debut
    phrase := "Pointeurs!";
    ptr_chaine := &phrase;
    temp_chaine := ptr_chaine^;
Fin.
"""

result, errors = compile_algo(code)
if errors:
    print("Compile errors:", errors)
else:
    print("Compiled successfully!")
    
    def _algo_read():
        return ""

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
        print("source_val type:", type(source_val))
        print("hasattr:", hasattr(source_val, '_get_target_container'))
        
        if hasattr(source_val, '_get_target_container'):
            targ = source_val._get_target_container()
            print("INITIAL TARG TYPE:", type(targ))
            
            # Sub-pointers decay wrapper (chaine Pointers points to base_var=Pointer(...)
            while hasattr(targ, '_get_target_container'): 
                targ = targ._get_target_container()
                
            print("FINAL TARG TYPE:", type(targ))
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

    exec_globals = {
        '_algo_read': _algo_read,
        '_algo_to_string': _algo_to_string,
        '_algo_assign_fixed_string': _algo_assign_fixed_string,
    }

    # Remove the embedded _algo_assign_fixed_string to let our override run with prints
    result_parts = result.split('def _algo_assign_fixed_string(target_list, source_val):')
    if len(result_parts) > 1:
        rest = result_parts[1].split('def ', 1)[1]
        result = result_parts[0] + 'def ' + rest

    try:
        print("--- GENERATED CODE ---")
        print(result)
        print("----------------------")
        exec(result, exec_globals)
        print("Execution finished without error.")
        temp_chaine = exec_globals['temp_chaine']
        print("temp_chaine Content:", _algo_to_string(temp_chaine))
    except Exception as e:
        print("Execution raised error:", type(e), e)
