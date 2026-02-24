import requests
import time
import subprocess
import sys
import os
import json
import threading

# Helper to read SSE stream
def read_sse(url, event_list):
    try:
        with requests.get(url, stream=True) as response:
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith("data: "):
                        data_str = decoded[6:]
                        try:
                            data = json.loads(data_str)
                            event_list.append(data)
                            if data.get('type') in ['finished', 'stopped']:
                                break
                        except:
                            pass
    except Exception as e:
        print(f"Stream error: {e}")

def main():
    # Start the server
    print("Starting web server...")
    server_process = subprocess.Popen(
        [sys.executable, 'src/web/app.py'],
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to start
    time.sleep(5)
    
    BASE_URL = "http://127.0.0.1:5000"
    
    try:
        print("\n--- Testing /start_execution (Simple Print) ---")
        code = """
        Algorithme TestPrint;
        Debut
            Ecrire("Hello World");
        Fin.
        """
        
        # Start Execution
        resp = requests.post(f"{BASE_URL}/start_execution", json={"code": code})
        if resp.status_code != 200 or not resp.json().get('success'):
            print(f"FAIL: Start execution failed. {resp.text}")
            return
        
        print("PASS: Execution started.")
        
        # Connect to Stream
        events = []
        stream_thread = threading.Thread(target=read_sse, args=(f"{BASE_URL}/stream", events))
        stream_thread.start()
        stream_thread.join(timeout=10)
        
        # Verify events
        stdout_events = [e['data'] for e in events if e['type'] == 'stdout']
        finished_event = next((e for e in events if e['type'] == 'finished'), None)
        
        print(f"Events received: {len(events)}")
        print(f"Stdout: {stdout_events}")
        
        if any("Hello World" in s for s in stdout_events):
            print("PASS: Output 'Hello World' received.")
        else:
            print("FAIL: 'Hello World' not found in output.")
            
        if finished_event:
            print("PASS: Finished event received.")
        else:
            print("FAIL: Finished event missing.")

        # --- Test Stop Execution ---
        print("\n--- Testing /start_execution (Infinite Loop & Stop) ---")
        code_loop = """
        Algorithme TestLoop;
        Var i : Entier;
        Debut
            i := 0;
            Tant Que i < 100 Faire
                Ecrire("Loop");
                // Sleep not available directly, but busy wait or just many prints
            Fin Tant Que;
        Fin.
        """
        # Actually without sleep it might finish too fast. 
        # Let's relies on the fact that we can stop it.
        # Use Read to block?
        
        code_block = """
        Algorithme TestBlock;
        Var x : Entier;
        Debut
            Ecrire("Waiting...");
            Lire(x);
        Fin.
        """
        
        resp = requests.post(f"{BASE_URL}/start_execution", json={"code": code_block})
        if resp.status_code == 200:
            events_stop = []
            stream_thread = threading.Thread(target=read_sse, args=(f"{BASE_URL}/stream", events_stop))
            stream_thread.start()
            
            time.sleep(2) # Wait for it to allow connection 
            
            # Request Stop
            print("Sending Stop request...")
            resp_stop = requests.post(f"{BASE_URL}/stop_execution")
            if resp_stop.status_code == 200 and resp_stop.json().get('success'):
                print("PASS: Stop request accepted.")
            else:
                print(f"FAIL: Stop request failed. {resp_stop.text}")
            
            stream_thread.join(timeout=5)
            
            stopped_event = next((e for e in events_stop if e['type'] == 'stopped'), None)
            if stopped_event:
                print("PASS: Stopped event received.")
            else:
                print(f"FAIL: Stopped event missing. Events: {events_stop}")
                
    except Exception as e:
        print(f"ERROR: {e}")
        
    finally:
        print("\nStopping web server...")
        server_process.terminate()
        try:
            server_process.communicate(timeout=2)
        except:
            server_process.kill()

if __name__ == "__main__":
    main()
