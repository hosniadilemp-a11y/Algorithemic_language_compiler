import os
import glob
import subprocess
import sys

def run_tests():
    examples_dir = "examples"
    algo_files = glob.glob(os.path.join(examples_dir, "**/*.algo"), recursive=True)
    algo_files.sort()
    
    passed = []
    failed = []
    
    # 50 lines of input "1" or "a" just in case the program wants to read something
    mock_input = "1\n" * 20 + "a\n" * 10 + "10\n" * 10
    
    for file in algo_files:
        print(f"Testing {file}...", end=" ", flush=True)
        try:
            # Run the compiled CLI test
            result = subprocess.run(
                [sys.executable, "tests/compile_cli.py", file],
                input=mock_input.encode('utf-8'),
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                print("PASSED")
                passed.append(file)
            else:
                print("FAILED")
                print("--- STDERR ---")
                print(result.stderr.decode('utf-8'))
                print("--- STDOUT ---")
                print(result.stdout.decode('utf-8'))
                failed.append((file, result.stderr.decode('utf-8')))
        except subprocess.TimeoutExpired:
            print("TIMEOUT (Likely waiting for more input or infinite loop)")
            failed.append((file, "Timeout"))
        except Exception as e:
            print(f"ERROR: {e}")
            failed.append((file, str(e)))
            
    print("\n" + "="*40)
    print(f"Total: {len(algo_files)}, Passed: {len(passed)}, Failed: {len(failed)}")
    if failed:
        print("\nFailed files:")
        for f, err in failed:
            print(f"  - {f}")
    
if __name__ == "__main__":
    run_tests()
