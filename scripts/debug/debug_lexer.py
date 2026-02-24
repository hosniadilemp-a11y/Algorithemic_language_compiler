from compiler.lexer import lexer

code = """Var 
    x : Entier;
    a : Reel;
"""

lexer.input(code)
for tok in lexer:
    print(tok)
