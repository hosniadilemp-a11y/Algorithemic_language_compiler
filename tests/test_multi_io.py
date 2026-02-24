import requests
import json
import threading
import time
import subprocess
import sys
import os

# Start server
server_process = subprocess.Popen(
    [sys.executable, 'web/app.py'],
    cwd=os.getcwd(),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
time.sleep(5)

try:
    BASE_URL = "http://127.0.0.1:5000"
    
    # Test Code with Multiple Inputs on One Line
    code = """
    Algorithme TestInputMulti;
    Var a, b : Entier;
    Debut
        Ecrire("Entrez deux nombres");
        Lire(a, b);
        Ecrire("Somme:", a + b);
    Fin.
    """
    
    print("Starting execution...")
    resp = requests.post(f"{BASE_URL}/start_execution", json={"code": code})
    if resp.status_code != 200:
        print("Failed to start")
        exit(1)

    # Listen and interact
    with requests.get(f"{BASE_URL}/stream", stream=True) as r:
        for line in r.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    data = json.loads(decoded[6:])
                    type = data.get('type')
                    content = data.get('data')
                    
                    if type == 'stdout':
                        print(f"[STDOUT] {content}")
                    elif type == 'input_request':
                        print("[INPUT REQUESTED] Sending '10 20'...")
                        # Send BOTH values in one line
                        requests.post(f"{BASE_URL}/send_input", json={"input": "10 20"})
                        
                    elif type == 'finished':
                        print("[FINISHED]")
                        break
                        
except Exception as e:
    print(f"Error: {e}")
finally:
    server_process.terminate()
