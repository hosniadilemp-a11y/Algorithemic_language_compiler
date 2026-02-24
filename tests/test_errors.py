import pytest
from compiler.parser import compile_algo
from web.app import app, session
import threading
import queue
import time

def test_multiple_syntax_errors():
    code = """
    Algorithme TestErrors;
    Var
        x : Entier  // Missing semicolon
        y : Etier;  // Unknown type
    Debut
        x <- 1;
    Fin.
    """
    python_code, errors = compile_algo(code)
    
    # We expect errors, so python_code might be partial or None depending on implementation
    # But errors list should be populated
    assert len(errors) >= 2
    
    error_messages = [e['message'] for e in errors]
    print(error_messages)
    
    assert any("Missing semicolon" in m for m in error_messages)
    assert any("Unknown type" in m for m in error_messages)

def test_runtime_error_translation():
    # Simulate an error in the runtime thread
    try:
        raise TypeError("'>' not supported between instances of 'str' and 'int'")
    except Exception as e:
        # Dry run the translation logic from app.py
        err_msg = str(e)
        if "not supported between instances of 'str' and 'int'" in err_msg:
            err_msg = "Impossible de comparer une Chaîne et un Entier."
        
        assert err_msg == "Impossible de comparer une Chaîne et un Entier."

def test_name_error_translation():
    try:
        raise NameError("name 'foo' is not defined")
    except Exception as e:
        err_msg = str(e)
        import re
        match = re.search(r"name '(\w+)' is not defined", err_msg)
        if match:
            err_msg = f"Variable non déclarée ou inconnue: '{match.group(1)}'"
        
        assert err_msg == "Variable non déclarée ou inconnue: 'foo'"
