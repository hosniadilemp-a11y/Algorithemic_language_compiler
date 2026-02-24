import sys
import os
import unittest
from io import StringIO
import contextlib

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from compiler.parser import compile_algo

class TestInputValidation(unittest.TestCase):
    def test_invalid_integer_input(self):
        code = """
        Algorithme TestInt;
        Var age : Entier;
        Debut
            Lire(age);
        Fin.
        """
        python_code, errors = compile_algo(code)
        self.assertFalse(errors)
        
        # Prepare execution environment
        # Mock input to return "adel" then "10"
        inputs = ["adel", "10"]
        def mock_input(prompt=''):
            if inputs:
                return inputs.pop(0)
            raise EOFError
            
        exec_globals = {
            "input": mock_input,
            "print": lambda *args: None
        }
        
        # Capture stderr? No, the code raises ValueError.
        # We want to ensure it raises ValueError
        
        try:
            exec(python_code, exec_globals)
        except ValueError as e:
            print(f"\nCaught expected error: {e}")
            self.assertIn("Type mismatch", str(e))
            self.assertIn("adel", str(e))
            self.assertIn("Entier", str(e))
            return

        self.fail("Did not raise ValueError for invalid integer input")

    def test_invalid_boolean_input(self):
        code = """
        Algorithme TestBool;
        Var b : Booleen;
        Debut
            Lire(b);
        Fin.
        """
        python_code, errors = compile_algo(code)
        
        inputs = ["NotABool"]
        def mock_input(prompt=''):
            return inputs.pop(0)
            
        exec_globals = {"input": mock_input, "print": lambda *args: None}
        
        try:
            exec(python_code, exec_globals)
        except ValueError as e:
            print(f"\nCaught expected error: {e}")
            self.assertIn("Type mismatch", str(e))
            self.assertIn("Booleen", str(e))
            return

        self.fail("Did not raise ValueError for invalid boolean input")

if __name__ == '__main__':
    unittest.main()
