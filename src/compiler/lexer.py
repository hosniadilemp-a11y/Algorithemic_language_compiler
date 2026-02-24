import ply.lex as lex

# List of token names
tokens = (
    'ALGORITHME', 'VAR', 'CONST', 'DEBUT', 'FIN',
    'SI', 'ALORS', 'SINON', 'FSI',
    'POUR', 'FIN_POUR', 'TANT_QUE', 'FIN_TANT_QUE', 'FAIRE', 'REPETER', 'JUSQUA',
    'ECRIRE', 'LIRE', 'RETOURNER', 'FONCTION', 'PROCEDURE',
    'ALLOUER', 'LIBERER', 'TAILLE',
    'TABLEAU', 'DE',
    'ENTIER_TYPE', 'REEL_TYPE', 'CHAINE_TYPE', 'BOOLEEN_TYPE', 'CARACTERE_TYPE',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD', 'DIV',
    'ASSIGN', 'EQUALS', 'NEQUALS', 'LT', 'LE', 'GT', 'GE',
    'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET', 'COMMA', 'SEMICOLON', 'COLON', 'DOT',
    'ID', 'NUMBER', 'STRING_LITERAL', 'CHAR_LITERAL',
    'AND', 'OR', 'NOT', 'QUE',
    'LONGUEUR', 'CONCAT',
    'VRAI', 'FAUX',
    'CARET', 'AMPERSAND', 'NIL',  # Pointer support
    'TYPE', 'ENREGISTREMENT', 'ARROW'  # Record support
)

# Regular expression rules for simple tokens
t_PLUS    = r'\+'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_COMMA   = r','
t_SEMICOLON = r';'
t_COLON   = r':'
t_DOT     = r'\.'
t_CARET   = r'\^'  # Pointer type and dereference
t_AMPERSAND = r'&'  # Address-of operator
t_EQUALS  = r'='
t_NEQUALS = r'<>'
t_LT      = r'<'
t_LE      = r'<='
t_GE      = r'>='
t_GT      = r'>'
t_ARROW   = r'->'
# t_JUSQUA handled as function

def t_MINUS(t):
    r'-(?!>)'          # minus only when NOT followed by >
    return t

# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t\r'

# Reserved words map
reserved = {
    'algorithme': 'ALGORITHME',
    'var': 'VAR',
    'const': 'CONST',
    'debut': 'DEBUT',
    'fin': 'FIN',
    'si': 'SI',
    'alors': 'ALORS',
    'sinon': 'SINON',
    'fsi': 'FSI',
    'finsi': 'FSI',      # Mapped to FSI
    'pour': 'POUR',
    'finpour': 'FIN_POUR',
    'tant': 'TANT_QUE',
    'tantque': 'TANT_QUE',  # TantQue as one word
    'fintantque': 'FIN_TANT_QUE',  # FinTantQue as one word
    'que': 'QUE',
    'faire': 'FAIRE',
    # 'a' removed from reserved words - now allowed as variable name
    'repeter': 'REPETER',
    'jusqua': 'JUSQUA',
    'tableau': 'TABLEAU',
    'de': 'DE',
    'ecrire': 'ECRIRE',
    'lire': 'LIRE',
    'retourner': 'RETOURNER',
    'fonction': 'FONCTION',
    'procedure': 'PROCEDURE',
    'var': 'VAR',
    'allouer': 'ALLOUER',
    'liberer': 'LIBERER',
    'taille': 'TAILLE',
    'entier': 'ENTIER_TYPE',
    'reel': 'REEL_TYPE',
    'chaine': 'CHAINE_TYPE',
    'booleen': 'BOOLEEN_TYPE',
    'caractere': 'CARACTERE_TYPE',
    'mod': 'MOD',
    'div': 'DIV',
    'et': 'AND',
    'ou': 'OR',
    'non': 'NOT',
    'longueur': 'LONGUEUR',
    'long': 'LONGUEUR', # Alias
    'concat': 'CONCAT',
    'vrai': 'VRAI',
    'faux': 'FAUX',
    'nil': 'NIL',  # Null pointer
    'type': 'TYPE',  # Record type declaration
    'enregistrement': 'ENREGISTREMENT',  # Record keyword
}

def t_ASSIGN(t):
    r':=|<-'
    return t

def t_CHAR_LITERAL(t):
    r"'[^']*'|\#0"
    if t.value == '#0':
        t.value = '#0'   # keep as sentinel string for null char
    else:
        t.value = t.value[1:-1]   # strip quotes
    return t

def t_STRING_LITERAL(t):
    r'"[^"]*"'
    raw = t.value[1:-1]   # strip quotes
    # process escape sequences
    raw = raw.replace('\\n', '\n').replace('\\t', '\t')
    t.value = raw
    return t

def t_NUMBER(t):
    r'\d+(\.\d+)?'
    if '.' in t.value:
        t.value = float(t.value)
    else:
        t.value = int(t.value)
    return t

def t_JUSQUA(t):
    r"[jJ][uU][sS][qQ][uU][aA]"
    return t

def t_ID(t):
    r'[a-zA-Z_]([a-zA-Z_0-9]|(-(?!>)))*'
    t.type = reserved.get(t.value.lower(), 'ID')    # Check for reserved words
    # print(f"DEBUG LEXER: {t.value} -> {t.type}") # Commented out to reduce noise, enable if needed
    
    # Handle 'TANT QUE' - this is tricky in lexer.
    # Usually 'TANT' and 'QUE' are separate. Parser will handle 'TANT QUE'.
    # But for 'FIN SI', 'FIN POUR', etc., we might want to handle them.
    # For now, let's keep them as separate tokens ID or keyword.
    
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_comment(t):
    r'(//[^\n]*)|(\#(?!\d)[^\n]*)'
    pass

# Error handling
errors = []

def find_column(input, token):
    line_start = input.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

def t_error(t):
    error_msg = f"Illegal character '{t.value[0]}'"
    errors.append({
        "line": t.lexer.lineno,
        "column": find_column(t.lexer.lexdata, t),
        "message": error_msg,
        "type": "Lexical Error",
        "error_code": "E1.1"
    })
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

def get_lexer_errors():
    return errors

def clear_lexer_errors():
    global errors
    errors = []

# Helper function to test
def test_lexer(data):
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)

if __name__ == '__main__':
    data = '''
    Algorithme Test;
    Var x : Entier;
    Debut
        x := 10;
        Si x > 5 Alors
            Ecrire("Grand");
        Fin
    Fin.
    '''
    test_lexer(data)
