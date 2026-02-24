import sys
sys.path.append("src")
from compiler.parser import compile_algo

code = """
Algorithme ChaineTaillePointer;
Var
    phrase[50] : Chaine;
    ptr_chaine : ^Chaine; // Ou ^Caractere en simulation
    lens : Entier;
    temp_chaine[50] : Chaine;

Debut
    phrase := "Pointeurs!";
    ptr_chaine := phrase;
    
    Ecrire("--- Probleme: Analyser une variable via Pointeur ---", "\\n");
    Ecrire("Chaine originale: ", phrase, "\\n");
    
    // Utiliser le pointeur pour interagir
    Ecrire("La chaine (via pointeur) est : ", ptr_chaine^, "\\n");
    
    // Accès au premier caractere, simulé via tableau/chaine pointe
    // En syntaxe algorithmique simulée, ptr_chaine^[i] est valide
    temp_chaine := ptr_chaine^;
    lens := Longueur(temp_chaine);
    Ecrire("Premier caractere (via ptr_chaine^[0]) : ", temp_chaine[0], "\\n");
    Ecrire("Dernier caractere : ", temp_chaine[lens - 1], "\\n");
Fin.
"""

result, errors = compile_algo(code)
if errors:
    print(errors)
    sys.exit(1)

exec_globals = {}
exec(result, exec_globals)

try:
    print("TEMP_CHAINE IN PYTHON:", exec_globals['temp_chaine'])
except Exception as e:
    print(e)

