from compiler.parser import compile_algo

code = """
Algorithme TestTypeCheck;
Var
    x : Entier;
    s : Chaine;
Debut
    x <- 10;
    s <- "Bonjour";
    
    x <- "Erreur"; // Should trigger semantic error
    s <- 123;      // Should trigger semantic error
    
    x <- x + 5;    // OK
    s <- s + "!";  // OK
Fin.
"""

print("Compiling Semantic Test...")
result, errors = compile_algo(code)

if errors:
    print("ERRORS FOUND:")
    for e in errors:
        print(f"[{e['type']}] Line {e['line']}: {e['message']}")
else:
    print("NO ERRORS (Unexpected!)")
    print(result)
