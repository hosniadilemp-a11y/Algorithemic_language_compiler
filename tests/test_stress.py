import pytest
from compiler.parser import compile_algo

def test_long_arithmetic_expression():
    # Create a very long addition expression: 1 + 1 + 1 ...
    n = 1000
    expr = " + ".join(["1"] * n)
    code = f"""
    Algorithme StressTest;
    Var res : Entier;
    Debut
        res <- {expr};
        Ecrire(res);
    Fin.
    """
    python_code, errors = compile_algo(code)
    assert not errors, f"Errors found: {errors}"
    assert python_code is not None

def test_deep_nested_parentheses():
    # (((...1...)))
    n = 200
    expr = "(" * n + "1" + ")" * n
    code = f"""
    Algorithme StressTestParen;
    Var res : Entier;
    Debut
        res <- {expr};
    Fin.
    """
    python_code, errors = compile_algo(code)
    assert not errors, f"Errors found: {errors}"
    assert python_code is not None

def test_long_logical_expression():
    # Vrai OU Vrai OU ...
    n = 500
    expr = " OU ".join(["Vrai"] * n)
    code = f"""
    Algorithme StressLogic;
    Var b : Booleen;
    Debut
        b <- {expr};
    Fin.
    """
    python_code, errors = compile_algo(code)
    assert not errors, f"Errors found: {errors}"
    assert python_code is not None

def test_complex_mixed_expression():
    # Mixed arithmetic and logic with comparisons
    # (1 + 2 * 3 > 5) ET (10 MOD 3 = 1) OU (NON Vrai)
    # create a long chain of these
    part = "(1 + 2 * 3 > 5) ET (10 MOD 3 = 1)"
    n = 100
    expr = " OU ".join([part] * n)
    
    code = f"""
    Algorithme StressMixed;
    Var res : Booleen;
    Debut
        res <- {expr};
        Ecrire(res);
    Fin.
    """
    python_code, errors = compile_algo(code)
    assert not errors, f"Errors found: {errors}"
    assert python_code is not None

def test_long_comparison_chain():
    # 1 < 2 ET 2 < 3 ET 3 < 4 ...
    n = 200
    parts = []
    for i in range(n):
        parts.append(f"{i} < {i+1}")
    expr = " ET ".join(parts)
    
    code = f"""
    Algorithme StressCompare;
    Var res : Booleen;
    Debut
        res <- {expr};
        Ecrire(res);
    Fin.
    """
    python_code, errors = compile_algo(code)
    assert not errors, f"Errors found: {errors}"
    assert python_code is not None
