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
    
    # Test Code: Fixed String and Array
    code = """
    Algorithme TestSyntaxe;
    Var s[5] : Chaine;
    Var t : Tableau de Entier;
    Debut
        Ecrire("--- Test Chaine ---");
        s[0] <- "H";
        s[1] <- "i";
        Ecrire(s);
        
        Ecrire("--- Test Tableau ---");
        // Python lists are dynamic, so this should work if we use append methodology?
        // But our syntax t[i] <- val requires pre-allocation or append?
        // If 't' is [], t[0] <- 1 will fail in Python (IndexError).
        // User asked for "Tableau de Entier". 
        // If it's dynamic, we might need Append/Ajouter? 
        // Or maybe they expect fixed size like t = [0]*N via some other logic?
        // But the declaration "Var t: Tableau de Entier" implies dynamic or unknown size.
        // Let's testing if it compiles first.
    Fin.
    """
    
    print("Starting execution...")
    resp = requests.post(f"{BASE_URL}/start_execution", json={"code": code})
    if resp.status_code != 200:
        print(f"Failed to start: {resp.text}")
        exit(1)

    # Listen
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
                    elif type == 'finished':
                        print("[FINISHED]")
                        break
                        
except Exception as e:
    print(f"Error: {e}")
finally:
    server_process.terminate()
