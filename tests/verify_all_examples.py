import os
import sys
import glob

# Add parent directory to path
# Add parent directory to path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(root_dir, 'src'))

from compiler.parser import compile_algo

def verify_examples():
    examples_dir = os.path.join(os.path.dirname(__file__), '..', 'examples')
    algo_files = glob.glob(os.path.join(examples_dir, '**', '*.algo'), recursive=True)
    
    print(f"Found {len(algo_files)} examples in {examples_dir}")

    print("-" * 60)
    
    success_count = 0
    failed_count = 0

    import subprocess
    
    for file_path in algo_files:
        filename = os.path.basename(file_path)
        # print(f"Testing {filename}...", end=' ')
        
        try:
            # Run compilation in subprocess to ensure clean state
            cli_script = os.path.join(os.path.dirname(__file__), 'compile_cli.py')
            result = subprocess.run(
                [sys.executable, cli_script, file_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"[PASS] {filename}")
                success_count += 1
            else:
                print(f"[FAIL] {filename}")
                print(f"  Stdout: {result.stdout}")
                print(f"  Stderr: {result.stderr}")
                failed_count += 1
                
        except Exception as e:
            print(f"[FAIL] {filename} (Exception): {e}")
            failed_count += 1
            
    print("-" * 60)
    print(f"Summary: {success_count} Passed, {failed_count} Failed")

if __name__ == "__main__":
    verify_examples()
