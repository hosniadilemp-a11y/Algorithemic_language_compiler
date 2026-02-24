import requests
import time

# Wait a moment for server to be ready
time.sleep(1)

BASE_URL = "http://127.0.0.1:5000"

print("Testing Examples Endpoint...")
print("-" * 50)

try:
    # Test /examples endpoint
    response = requests.get(f"{BASE_URL}/examples", timeout=5)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        examples = response.json()
        print(f"\nFound {len(examples)} examples:")
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
                print("\n✅ Examples endpoint is working correctly!")
            else:
                print(f"❌ Failed to load example: {response2.text}")
    else:
        print(f"❌ Failed to get examples list: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to server. Is it running on port 5000?")
except Exception as e:
    print(f"❌ Error: {e}")
