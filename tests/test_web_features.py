import requests
import time
import subprocess
import sys
import os

# Start the server
print("Starting web server...")
server_process = subprocess.Popen(
    [sys.executable, 'web/app.py'],
    cwd=os.getcwd(),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait for server to start
time.sleep(5)

try:
    BASE_URL = "http://127.0.0.1:5000"
    
    # 1. Test /examples
    print("\n--- Testing /examples ---")
    resp = requests.get(f"{BASE_URL}/examples")
    if resp.status_code == 200:
        files = resp.json()
        print(f"Examples found: {len(files)}")
        if "full_test.algo" in files:
            print("PASS: full_test.algo found.")
        else:
            print("FAIL: full_test.algo not found.")
    else:
        print(f"FAIL: HTTP {resp.status_code}")

    # 2. Test /example/content
    print("\n--- Testing /example/full_test.algo ---")
    resp = requests.get(f"{BASE_URL}/example/full_test.algo")
    if resp.status_code == 200:
        content = resp.text
        if "Algorithme TestComplet" in content:
            print("PASS: Content loaded correctly.")
        else:
            print("FAIL: Content mismatch.")
    else:
        print(f"FAIL: HTTP {resp.status_code}")

    # 3. Test Trace in /compile
    print("\n--- Testing Trace in /compile ---")
    code = """
    Algorithme TraceTest;
    Var i : Entier;
    Debut
        i := 1;
        Ecrire(i);
        i := 2;
        Ecrire(i);
    Fin.
    """
    resp = requests.post(f"{BASE_URL}/compile", json={"code": code})
    if resp.status_code == 200:
        data = resp.json()
        trace = data.get('trace')
        if trace and isinstance(trace, list) and len(trace) > 0:
            print(f"PASS: Trace returned with {len(trace)} steps.")
            # Check variable changes
            vars_found = [step['variables'].get('i') for step in trace if 'variables' in step]
            print(f"Variable sequence: {vars_found}")
            if '1' in str(vars_found) and '2' in str(vars_found):
                print("PASS: Variable evolution captured.")
        else:
            print("FAIL: No trace returned.")
    else:
        print(f"FAIL: HTTP {resp.status_code}")

except Exception as e:
    print(f"ERROR: {e}")

finally:
    print("\nStopping web server...")
    server_process.terminate()
    try:
        out, err = server_process.communicate(timeout=2)
    except:
        server_process.kill()
