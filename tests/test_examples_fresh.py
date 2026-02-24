import requests
import subprocess
import sys
import os
import time

print("Starting fresh server instance...")
print("-" * 50)

# Start the server
server_process = subprocess.Popen(
    [sys.executable, 'src/web/app.py'],
    cwd=os.getcwd(),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait for server to start
print("Waiting for server to start...")
time.sleep(5)

BASE_URL = "http://127.0.0.1:5000"

try:
    print("\nTesting Examples Endpoint...")
    print("-" * 50)
    
    # Test /examples endpoint
    response = requests.get(f"{BASE_URL}/examples", timeout=5)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        examples = response.json()
        print(f"\n✅ Found {len(examples)} examples:")
        for example in examples:
            print(f"  - {example}")
        
        # Test loading a specific example
        if examples:
            test_file = examples[0]
            print(f"\nTesting loading: {test_file}")
            response2 = requests.get(f"{BASE_URL}/example/{test_file}", timeout=5)
            print(f"Status Code: {response2.status_code}")
            
            if response2.status_code == 200:
                data = response2.json()
                print(f"Code length: {len(data.get('code', ''))} characters")
                print(f"First 100 chars: {data.get('code', '')[:100]}")
                print("\n✅ Examples are loading correctly!")
            else:
                print(f"❌ Failed to load example: {response2.text}")
        else:
            print("❌ No examples found!")
    else:
        print(f"❌ Failed to get examples list: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to server.")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    print("\nStopping test server...")
    server_process.terminate()
    try:
        server_process.communicate(timeout=2)
    except:
        server_process.kill()
    print("Done!")
