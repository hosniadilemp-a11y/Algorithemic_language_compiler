import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000/compile"

def run_test(name, code, input_data="", expected_match=None):
    print(f"Running Test: {name}...", end=" ")
    try:
        payload = {"code": code, "input_data": input_data}
        response = requests.post(BASE_URL, json=payload)
        data = response.json()
        
        if not data.get('success'):
            print("FAILED (Compilation Error)")
            print(f"Error: {data.get('error')}")
            return False

        output = data.get('output', '').strip()
        errors = data.get('errors', '').strip()

        if errors:
            print("FAILED (Runtime Error)")
            print(f"Stderr: {errors}")
            return False

        if expected_match and expected_match not in output:
            print(f"FAILED (Content Missing)")
            print(f"Expected to contain: {expected_match!r}")
            print(f"Got: {output!r}")
            return False

        print("PASSED")
        return True
    except Exception as e:
        print(f"FAILED (Exception: {e})")
        return False

def main():
    # Test: All 4 types
    code = """
    Algorithme TestTousTypes;
    Var i : Entier;
    Var r : Reel;
    Var s : Chaine;
    Var b : Booleen;
    Debut
        Ecrire("Entrez un entier:");
        Lire(i);
        Ecrire("Entrez un reel:");
        Lire(r);
        Ecrire("Entrez une chaine:");
        Lire(s);
        Ecrire("Entrez un booleen:");
        Lire(b);
        
        Ecrire("Resultats:");
        Ecrire(i, r, s, b);
        
        // Arithmetic Check (implicitly checks if i is int)
        Ecrire("i+1=", i + 1);
    Fin.
    """
    
    inputs = "42\n3.14\nBonjour\nVrai"
    
    # We expect i+1 to work, so 'i+1= 43' should be in output.
    # If i is string "42", i+1 throws TypeError in Python (captured in errors)
    
    run_test("All Types Declaration & IO", code, input_data=inputs, expected_match="i+1= 43")

if __name__ == "__main__":
    main()
