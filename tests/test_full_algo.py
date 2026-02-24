import requests
import json
import codecs

BASE_URL = "http://127.0.0.1:5000/compile"
ALGO_FILE = "full_test.algo"

def run_full_test():
    print(f"Reading {ALGO_FILE}...")
    try:
        with codecs.open(ALGO_FILE, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Prepare inputs: Name=Alice, Int=50, Float=10.5
    # Expect: "Petit nombre" (50 <= 100), loops, calc result 10.5*2.5+10 = 26.25+10 = 36.25
    input_data = "Alice\n50\n10.5"
    
    print("Sending code to compiler...")
    try:
        payload = {"code": code, "input_data": input_data}
        response = requests.post(BASE_URL, json=payload)
        data = response.json()
        
        if not data.get('success'):
            print("FAILED (Compilation Error)")
            print(f"Error: {data.get('error')}")
            return

        output = data.get('output', '').strip()
        errors = data.get('errors', '').strip()

        if errors:
            print("WARNING: Runtime Errors Detected:")
            print(errors)
        
        print("\n--- EXECUTION OUTPUT ---")
        print(output)
        print("------------------------")
        
        # Validation checks
        checks = [
            "Bonjour Alice",
            "Resultat (reel * 2.5 + 10) = 36.25",
            "C'est un PETIT nombre",
            "Iteration n° 3",
            "Compte a rebours : 1"
        ]
        
        all_passed = True
        for check in checks:
            if check not in output:
                print(f"[MISSING] '{check}'")
                all_passed = False
            else:
                print(f"[OK] Found '{check}'")
        
        if all_passed:
            print("\nSUCCESS: All comprehensive checks passed.")
        else:
            print("\nFAILURE: Some checks missing.")

    except Exception as e:
        print(f"FAILED (Exception: {e})")

if __name__ == "__main__":
    run_full_test()
