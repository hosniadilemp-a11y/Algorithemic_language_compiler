import json
import sys
sys.path.append('src')
from compiler.parser import compile_algo


code = """
Algorithme TestLire;
Var
    b : Entier;
Debut
    Lire(b);
Fin.
"""

# Compile
result, errors = compile_algo(code)
if errors:
    print("Compile errors:", errors)
else:
    print("Compiled successfully!")
    print(result)

    # Let's mock the execution like in app.py
    def mock_input():
        return "2.5"
    
    # We will use the exact _algo_read_typed from app_py logic
    def _algo_read_typed(current_val, raw_val, target_type_name='CHAINE'):
        type_to_check = target_type_name.upper()
        if 'ENTIER' in type_to_check or isinstance(current_val, int):
            try: 
                return int(raw_val)
            except: 
                raise ValueError(f"Type mismatch: '{raw_val}' n'est pas un Entier valide.")
        return str(raw_val)

    # Mock _algo_read
    def _algo_read():
        return mock_input()

    exec_globals = {
        '_algo_read': _algo_read,
        '_algo_read_typed': _algo_read_typed,
    }

    try:
        exec(result, exec_globals)
        print("Execution finished without error. b =", exec_globals['b'])
    except Exception as e:
        print("Execution raised error:", type(e), e)
