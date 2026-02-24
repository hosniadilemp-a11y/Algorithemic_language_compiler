from compiler.parser import parser

# Read the file
with open(r'examples/test_comprehensive.algo', 'r') as f:
    code = f.read()

try:
    python_code = parser.parse(code, debug=True)
    with open('debug_output.py', 'w', encoding='utf-8') as f:
        f.write(python_code)
    print("Code written to debug_output.py")
except Exception as e:
    print(f"Error: {e}")
