import sys
import os
import unittest

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from compiler.parser import compile_algo

class TestStringMutation(unittest.TestCase):
    def test_string_assignment(self):
        code = """
        Algorithme TestStr;
        Var s[10] : Chaine;
        Debut
            s <- "hello";
            s[0] <- 'H';
            Ecrire(s);
        Fin.
        """
        python_code, errors = compile_algo(code)
        self.assertFalse(errors, f"Compilation errors: {errors}")
        
        # Capture stdout
        from io import StringIO
        import contextlib
        f = StringIO()
        
        exec_globals = {
            "print": lambda *args: f.write(" ".join(map(str, args)) + "\n"),
            "_algo_assign_fixed_string": lambda t, s: t.__setitem__(slice(None), list(s.ljust(len(t), '\0')[:len(t)])),
            "_algo_set_char": lambda t, i, v: t.__setitem__(i, v) if i < len(t) else (_ for _ in ()).throw(IndexError())
        }
        
        try:
            with contextlib.redirect_stdout(f):
                exec(python_code, exec_globals)
        except Exception as e:
            self.fail(f"Execution failed: {e}")
            
        output = f.getvalue().strip()
        self.assertEqual(output, "Hello")

    def test_string_out_of_bounds(self):
        code = """
        Algorithme TestBound;
        Var s[2] : Chaine;
        Debut
            s <- "hi";
            s[5] <- 'x';
        Fin.
        """
        python_code, errors = compile_algo(code)
        self.assertFalse(errors)
        
        try:
            exec_globals = {
                "print": lambda *args: None,
                "_algo_assign_fixed_string": lambda t, s: t.__setitem__(slice(None), list(s.ljust(len(t), '\0')[:len(t)])),
                "_algo_set_char": lambda t, i, v: t.__setitem__(i, v) if 0 <= i < len(t) else None
            }
            exec(python_code, exec_globals)
        except Exception as e:
            self.fail(f"Should silently bounds-check, but raised: {type(e)}")

if __name__ == '__main__':
    unittest.main()
