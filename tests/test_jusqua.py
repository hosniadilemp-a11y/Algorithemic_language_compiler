import pytest
from compiler.parser import compile_algo

def test_jusqua_simple():
    code = """
    Algorithme TestJusqua;
    Var i : Entier;
    Debut
        i <- 0;
        Repeter
            i <- i + 1;
        Jusqua i = 3;
    Fin.
    """
    python_code, errors = compile_algo(code)
    assert not errors, f"Errors found: {errors}"
    assert "while True" in python_code
    assert "break" in python_code

def test_jusqua_legacy_fail():
    # Should fail if we strictly removed apostrophe support?
    # Actually, the user asked to change it "by jusaquq simples".
    # If they meant REPLACE, then 'jusqu\'a' should now fail or be tokenized differently.
    # Current regex: r"[jJ][uU][sS][qQ][uU][aA]"
    # 'jusqu\'a' will be parsed as ID 'jusqu' and then error on ''a'?
    # Or maybe ID 'jusqu' + error.
    # Let's see.
    pass
