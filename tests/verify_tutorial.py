import sys
import os

# Add src to path
sys.path.append(os.path.abspath('src'))

from compiler.parser import compile_algo

# Read the updated tutorial
tutorial_path = 'examples/Dynamic_Allocation/00_Tutoriel_Allocation_Dynamique.algo'
with open(tutorial_path, 'r', encoding='utf-8') as f:
    code = f.read()

result, errors = compile_algo(code)
if errors:
    print("Compilation failed:")
    for err in errors:
        print(err)
    sys.exit(1)

# print("Generated code:")
# print(result)

# Mock environment
exec_globals = {
    '_algo_heap': {},
    '_algo_heap_next_addr': 50000,
    '_algo_vars_info': {},
    'builtins': __import__('builtins'),
    'sys': __import__('sys'),
}

# Run the generated code
print("Starting execution of tutorial...")
exec(result, exec_globals)
print("\nExecution finished successfully.")
