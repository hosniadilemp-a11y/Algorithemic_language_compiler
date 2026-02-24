import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000/compile"

def run_test(name, code, input_data="", expected_output=None, expected_in_output=None):
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

        if expected_output is not None and output != expected_output:
            print(f"FAILED (Output Mismatch)")
            print(f"Expected: {expected_output!r}")
            print(f"Got:      {output!r}")
            return False
            
        if expected_in_output is not None and expected_in_output not in output:
             print(f"FAILED (Output Missing Content)")
             print(f"Expected to contain: {expected_in_output!r}")
             print(f"Got: {output!r}")
             return False

        print("PASSED")
        return True
    except Exception as e:
        print(f"FAILED (Exception: {e})")
        return False

def main():
    all_passed = True
    
    # Test 1: Hello World
    code1 = """
    Algorithme Hello;
    Debut
        Ecrire("Bonjour le monde");
    Fin.
    """
    if not run_test("Hello World", code1, expected_output="Bonjour le monde"):
        all_passed = False

    # Test 2: Arithmetic
    code2 = """
    Algorithme Maths;
    Var x : Entier;
    Debut
        x := 10 + 20;
        Ecrire(x);
    Fin.
    """
    if not run_test("Arithmetic", code2, expected_output="30"):
        all_passed = False

    # Test 3: Input (Lire)
    code3 = """
    Algorithme InputTest;
    Var n : Entier;
    Debut
        Ecrire("Entrez un nombre:");
        Lire(n);
        Ecrire("Vous avez entré: ", n);
    Fin.
    """
    # Note: Mock input prints prompt, so output includes prompt.
    # Python print adds space between arguments. "Vous avez entré: " + " " + "42"
    if not run_test("Input", code3, input_data="42", expected_in_output="Vous avez entré:  42"):
        all_passed = False
    
    # Test 4: Loop (Pour)
    code4 = """
    Algorithme Boucle;
    Var i, s : Entier;
    Debut
        s := 0;
        Pour i := 1 a 5 Faire
            s := s + i;
        Finpour;
        Ecrire(s);
    Fin.
    """
    if not run_test("Loop Pour", code4, expected_output="15"): # 1+2+3+4+5 = 15
        all_passed = False

    # Test 5: Conditional (Si/Sinon)
    code5 = """
    Algorithme Condition;
    Var x : Entier;
    Debut
        x := 10;
        Si x > 5 Alors
            Ecrire("Grand");
        Sinon
            Ecrire("Petit");
        Fsi;
    Fin.
    """
    if not run_test("Condition Si", code5, expected_output="Grand"):
        all_passed = False

    if all_passed:
        print("\nAll tests passed successfully!")
        sys.exit(0)
    else:
        print("\nSome tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
