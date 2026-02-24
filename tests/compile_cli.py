import sys
import os

# Add parent to path
# Add parent to path (tests/ -> root)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(root_dir, 'src'))

from compiler.parser import compile_algo

if len(sys.argv) < 2:
    print("Usage: python compile_cli.py <algo_file>")
    sys.exit(1)

filename = sys.argv[1]

try:
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()

    # compile_algo returns (code, errors)
    result = compile_algo(code)
    
    python_code = None
    if isinstance(result, tuple):
        python_code, errors = result
        if errors:
            print(f"FAIL: Compilation errors: {errors}")
            sys.exit(1)
    else:
        python_code = result # legacy fallback

    if python_code:
        # Write to file for debug
        with open("output.py", "w", encoding="utf-8") as f:
            f.write(python_code)
            
        # Check Python syntax
        compile(python_code, "output.py", 'exec')
        print("OK")
        sys.exit(0)
    else:
        print("FAIL: Transpilation failed (None)")
        sys.exit(1)

except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
