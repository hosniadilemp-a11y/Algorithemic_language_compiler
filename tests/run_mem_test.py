import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from compiler.parser import compile_algo

def test_mem_specs():
    with open('tests/verify_memory_specs.algo', 'r') as f:
        code = f.read()
    
    python_code, errors = compile_algo(code)
    
    if errors:
        print("Errors found:")
        for err in errors:
            print(f"- {err['message']} at line {err.get('line')}")
        return

    print("Compilation successful.")
    print("-" * 20)
    print(python_code)
    print("-" * 20)
    
    # Run the compiled code
    globals_dict = {}
    try:
        # Need to mock some builtins if needed, but ecrire/taille are defined in the code
        exec(python_code, globals_dict)
    except Exception as e:
        print(f"Runtime error: {e}")

if __name__ == "__main__":
    test_mem_specs()
