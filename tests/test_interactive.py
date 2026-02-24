import requests
import time
import subprocess
import sys
import os
import threading
import json

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
    
    # 1. Start Interaction
    print("\n--- Testing Interactive Execution ---")
    code = """
    Algorithme Interactif;
    Var nom : Chaine;
    Debut
        Ecrire("Entrez nom:");
        Lire(nom);
        Ecrire("Bonjour ", nom);
    Fin.
    """
    
    print("Starting execution...")
    resp = requests.post(f"{BASE_URL}/start_execution", json={"code": code})
    if resp.status_code == 200:
        print("Execution started.")
    else:
        print(f"FAIL: Start failed {resp.status_code}")
        exit(1)

    # 2. Listen to Stream
    def listen_stream():
        print("Listening to stream...")
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
                            print("[INPUT REQUESTED] Sending 'Alice'...")
                            # Send Input
                            requests.post(f"{BASE_URL}/send_input", json={"input": "Alice"})
                        elif type == 'finished':
                            print("[FINISHED]")
                            break
                        elif type == 'error':
                             print(f"[ERROR] {content}")

    # Run listener in thread (or just blocking since we anticipate finish)
    # But since requests.get blocks, we do it here.
    listen_stream()
    
    print("Interactive Test Complete.")

except Exception as e:
    print(f"ERROR: {e}")

finally:
    print("\nStopping web server...")
    server_process.terminate()
    try:
        out, err = server_process.communicate(timeout=2)
    except:
        server_process.kill()
