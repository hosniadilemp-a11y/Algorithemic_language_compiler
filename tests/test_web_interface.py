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
    BASE_URL = "http://127.0.0.1:5000/compile"
    
    # Test Data: Simple Algorithm
    code = """
    Algorithme TestWeb;
    Var x : Entier;
    Debut
        x := 10;
        Ecrire("Web Test: ", x * 2);
    Fin.
    """
    
    print("Sending request to /compile...")
    response = requests.post(BASE_URL, json={"code": code, "input_data": ""})
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("SUCCESS: Compilation and Execution via Web Interface passed.")
            print("Output:", data.get('output').strip())
            
            if "Web Test: 20" in data.get('output'):
                print("Verification: PASSED")
            else:
                print("Verification: FAILED (Incorrect Output)")
        else:
            print("FAILURE: Web Interface returned error.")
            print("Error:", data.get('error'))
    else:
        print(f"FAILURE: HTTP Error {response.status_code}")

except Exception as e:
    print(f"ERROR: {e}")

finally:
    print("Stopping web server...")
    server_process.terminate()
    try:
        out, err = server_process.communicate(timeout=2)
        if out: print("Server Stdout:", out.decode())
        if err: print("Server Stderr:", err.decode())
    except:
        server_process.kill()
