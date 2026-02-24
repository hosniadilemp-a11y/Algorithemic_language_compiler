import subprocess
import sys
import glob

files = glob.glob('examples/*.algo')
for f in files:
    result = subprocess.run([sys.executable, "tests/compile_cli.py", f], capture_output=True, text=True)
    status = "OK" if result.returncode == 0 else "FAIL"
    print(f"{f}: {status}")
    if result.returncode != 0:
        print(f"  Output: {result.stdout}")
        print(f"  Error: {result.stderr}")
