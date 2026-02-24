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
    
    # Test Code: Full Test Algo
    code = """
    Algorithme TestComplet;
    Var entierVal, compteur : Entier;
    Var reelVal, resultatCalcul : Reel;
    Var nomUtilisateur : Chaine;
    Var estGrand : Booleen;

    Debut
        Ecrire("--- DEBUT DU TEST COMPLET ---");
        Ecrire("Veuillez entrer : votre nom, un nombre entier, et un nombre reel :");
        Lire(nomUtilisateur, entierVal, reelVal);

        Ecrire("Bonjour", nomUtilisateur, "!");
        Ecrire("Vous avez saisi :", entierVal, "et", reelVal);
        
        resultatCalcul := reelVal * 2.5 + 10.0;
        Ecrire("Resultat =", resultatCalcul);
    Fin.
    """
    
    print("Starting execution...")
    resp = requests.post(f"{BASE_URL}/start_execution", json={"code": code})
    if resp.status_code != 200:
        print("Failed to start")
        exit(1)

    # Listen and interact
    input_sent = False
    trace_received = False
    
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
                    elif type == 'trace':
                        trace_received = True
                        vars = content.get('variables', {})
                        if vars:
                             print(f"[TRACE] Vars: {vars}")
                             
                    elif type == 'input_request':
                        if not input_sent:
                            print("[INPUT REQUESTED] Sending 'Adel 10 20.5'...")
                            requests.post(f"{BASE_URL}/send_input", json={"input": "Adel 10 20.5"})
                            input_sent = True
                        
                    elif type == 'finished':
                        print("[FINISHED]")
                        break
                        
    if not trace_received:
        print("FAILURE: No trace events received!")
        exit(1)
        
except Exception as e:
    print(f"Error: {e}")
finally:
    server_process.terminate()
    stdout, stderr = server_process.communicate()
    if stderr:
        print("--- SERVER STDERR ---")
        print(stderr.decode())
