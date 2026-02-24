from compiler.parser import compile_algo

def debug_file(filepath):
    print(f"Compiling {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()
    
    result, errors = compile_algo(code)
    
    if errors:
        print("ERRORS FOUND:")
        for e in errors:
            print(e)
    else:
        print("COMPILATION SUCCESS")
        print("Generated Code:")
        print("--------------------------------------------------")
        print(result)
        print("--------------------------------------------------")
        
        # Try to exec it to see if it runs
        try:
            print("Executing...")
            exec(result)
            print("Execution Success")
        except Exception as e:
            print(f"Execution Failed: {e}")

if __name__ == "__main__":
    debug_file(r"debug_infinite.algo")
