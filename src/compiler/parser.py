import ply.yacc as yacc
from compiler.lexer import tokens

# Global registry for record (Enregistrement) type definitions
# { 'TypeName': { 'field_name': 'FieldType', ... } }  (ordered dict preserves field order)
record_types = {}

# Indentation management
indent_level = 0
base_function_indent = ""

def get_indent():
    # Inside a function, we might need a base indent plus the current level
    return base_function_indent + "    " * indent_level

def increase_indent():
    global indent_level
    indent_level += 1

def decrease_indent():
    global indent_level
    indent_level -= 1

# Symbol Table with scoping
# symbol_table = { 'global': {}, 'func_name': {} }
symbol_table = {'global': {}}
scope_stack = ['global']
function_return_types = {}
globals_modified_in_subprogram = {}

def push_scope(name):
    scope_stack.append(name)
    if name not in symbol_table:
        symbol_table[name] = {}

def pop_scope():
    if len(scope_stack) > 1:
        scope_stack.pop()

def get_current_scope():
    return symbol_table[scope_stack[-1]]

def add_variable(name, type_name):
    get_current_scope()[name] = type_name

def is_local_scope():
    return len(scope_stack) > 1

def find_variable(name):
    """Search for variable in scope stack (local then global)."""
    for scope in reversed(scope_stack):
        if name in symbol_table.get(scope, {}):
            var_type = symbol_table[scope][name]
            alloc_name = f"{scope}.{name}" if scope != 'global' else name
            return var_type, alloc_name
    return 'UNKNOWN', name

current_subprogram_type = None # 'function' or 'procedure'

def get_default_value(type_name):
    t = type_name.lower()
    if t == 'entier': return '0'
    if t == 'reel': return '0.0'
    if t == 'chaine': return '""'
    if t == 'booleen': return 'False'
    if t == 'caractere': return "''"
    if 'pointeur' in t or t.startswith('pointeur_'): return 'None'  # NIL pointer
    # User-defined record type — emit empty dict initialiser
    if type_name in record_types:
        return _build_record_init(type_name)
    return '{}'

def _build_record_init(type_name):
    """Build the Python dict literal that represents a fresh record of the given type."""
    fields = record_types.get(type_name, {})
    items = []
    for fname, ftype in fields.items():
        default = get_default_value(ftype)
        items.append(f"'{fname}': {default}")
    return '{' + ', '.join(items) + '}'

def check_type_compatibility(var_type, expr_type):
    if var_type == 'UNKNOWN' or expr_type == 'UNKNOWN':
        return True # Be lenient with unknown types
    
    # Normalize to lowercase for comparison
    v_type = var_type.lower()
    e_type = expr_type.lower()
    
    # Allow NIL (POINTEUR) to be assigned to any pointer type
    if v_type.startswith('pointeur_') and e_type == 'pointeur':
        return True
    
    # Exact match (case-insensitive)
    if v_type == e_type:
        return True
    
    # Handle _TYPE suffix variations
    v_base = v_type.replace('_type', '')
    e_base = e_type.replace('_type', '')
    if v_base == e_base:
        return True
    
    # Allow numeric promotions (Entier -> Reel)
    if v_base in ['reel'] and e_base in ['entier']:
        return True
    
    # Allow types with internal structure if base matches
    if v_type.startswith('tableau_') and e_type.startswith('tableau_'):
         return v_type == e_type
    
    if v_type.startswith('matrice_') and e_type.startswith('matrice_'):
         return v_type == e_type
    
    # Allow array to pointer decay (e.g., ptr := t where t is an array)
    if v_type.startswith('pointeur_') and e_type.startswith('tableau_'):
        v_base = v_type.replace('pointeur_', '').replace('_type', '')
        e_base = e_type.replace('tableau_', '').replace('_type', '')
        if v_base == e_base:
            return True

    # Allow Chaine to decay to pointer (it's an array of characters)
    if v_type.startswith('pointeur_') and e_type == 'chaine':
        v_base = v_type.replace('pointeur_', '').replace('_type', '')
        if v_base in ['chaine', 'caractere']:
            return True
            
    return False

# Precedence rules
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('left', 'EQUALS', 'NEQUALS', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'DIV', 'MOD'),
    ('right', 'UMINUS'),
    ('left', 'DOT', 'ARROW', 'LBRACKET', 'CARET')
)

# Grammar Rules

# Pointer Class Definition to be embedded
pointer_class_code = r'''
class Pointer:
    def __init__(self, var_name=None, namespace=None, index=0, base_var=None, alloc_name=None):
        self.var_name = var_name
        self.namespace = namespace if namespace is not None else {}
        self.index = index
        self.base_var = base_var
        self.alloc_name = alloc_name if alloc_name is not None else var_name

    def _get_target_container(self):
        # base_var takes priority — used for record-backed pointers from _algo_allouer_record
        if self.base_var is not None:
            return self.base_var
        # Only after checking base_var do we apply the NIL check on var_name
        if self.var_name is None:
            raise ValueError("Cannot dereference NIL pointer")
        if self.var_name in self.namespace:
            return self.namespace[self.var_name]
        elif self.var_name in globals():
            return globals()[self.var_name]
        else:
            raise NameError(f"Variable '{self.var_name}' not found")

    def _get(self):
        target = self._get_target_container()
        if isinstance(target, list):
            if not (0 <= self.index < len(target)):
                raise IndexError(f"Segmentation fault: Access out of bounds at index {self.index}")
            return target[self.index]
        if self.index != 0:
             raise IndexError("Segmentation fault: Pointer arithmetic on scalar variable out of bounds")
        return target

    def _get_string(self):
        target = self._get_target_container()
        if isinstance(target, list):
            if not (0 <= self.index < len(target)): return ""
            return _algo_to_string(target[self.index:])
        return str(target)

    
    def _set(self, value):
        target = self._get_target_container()
        if isinstance(target, list):
            if not (0 <= self.index < len(target)):
                raise IndexError(f"Segmentation fault: Write out of bounds at index {self.index}")
            target[self.index] = value
        else:
            if self.index != 0:
                 raise IndexError("Segmentation fault: Pointer arithmetic on scalar variable out of bounds")
            if self.var_name in self.namespace:
                self.namespace[self.var_name] = value
            else:
                globals()[self.var_name] = value
    
    def _assign(self, other):
        # Mutates this pointer to point to what 'other' points to (used for Var parameters)
        if isinstance(other, Pointer):
            self.var_name = other.var_name
            self.namespace = other.namespace
            self.index = other.index
            self.base_var = other.base_var
            self.alloc_name = getattr(other, 'alloc_name', other.var_name)
            if hasattr(other, '_heap_addr'):
                self._heap_addr = getattr(other, '_heap_addr')
            elif hasattr(self, '_heap_addr'):
                delattr(self, '_heap_addr')
        elif other is None:
            self.var_name = None
            self.namespace = {}
            self.index = 0
            self.base_var = None
            self.alloc_name = None
            if hasattr(self, '_heap_addr'):
                delattr(self, '_heap_addr')
        else:
             raise TypeError("Cannot assign non-pointer to pointer via _assign")

    def _clone(self):
        new_ptr = Pointer(self.var_name, self.namespace, self.index, self.base_var, getattr(self, 'alloc_name', self.var_name))
        if hasattr(self, '_heap_addr'):
            new_ptr._heap_addr = self._heap_addr
        return new_ptr

    def __add__(self, offset):
        return Pointer(self.var_name, self.namespace, self.index + int(offset), self.base_var, getattr(self, 'alloc_name', self.var_name))

    def __sub__(self, offset):
        return Pointer(self.var_name, self.namespace, self.index - int(offset), self.base_var, getattr(self, 'alloc_name', self.var_name))

    def __eq__(self, other):
        if other is None:
            # If it has a heap address or base_var, it's not NIL
            if hasattr(self, '_heap_addr') or self.base_var is not None:
                return False
            return self.var_name is None
        if isinstance(other, Pointer):
            # Check for heap address equality if both have it
            if hasattr(self, '_heap_addr') and hasattr(other, '_heap_addr'):
                return self._heap_addr + self.index == other._heap_addr + other.index
            return (self.var_name == other.var_name and 
                    self.index == other.index and 
                    id(self.base_var) == id(other.base_var))
        return False
    
    def __str__(self):
        if hasattr(self, '_heap_addr'):
            return f"@{self._heap_addr + self.index}"
        if self.var_name is None:
            return "NIL"
        try:
            lookup_name = self.alloc_name if hasattr(self, 'alloc_name') and self.alloc_name else self.var_name
            if lookup_name in _algo_vars_info:
                info = _algo_vars_info[lookup_name]
                base = info['addr']
                stride = info.get('element_size', 4)
                addr = base + (self.index * stride)
                return f"@{addr}"
            else:
                return f"@{lookup_name}+{self.index}"

        except:
            return "UNKNOWN"

    def __repr__(self):
        return str(self)

    def __getitem__(self, i):
        return (self + i)._get()

    def __setitem__(self, i, value):
        (self + i)._set(value)
'''

def p_program(p):
    '''program : type_block program_subprogram_list ALGORITHME ID SEMICOLON declarations DEBUT statements FIN DOT
               | type_block ALGORITHME ID SEMICOLON declarations DEBUT statements FIN DOT
               | program_subprogram_list ALGORITHME ID SEMICOLON declarations DEBUT statements FIN DOT
               | ALGORITHME ID SEMICOLON declarations DEBUT statements FIN DOT'''
    if len(p) == 11:
        # type_block + subprograms + algo
        algo_name = p[4]
        sub_progs = p[2]
        declarations_code = p[6]
        statements_code = p[8]
    elif len(p) == 10:
        if p[1] and not isinstance(p[1], str):
            # type_block + algo (no subprograms)
            algo_name = p[3]
            sub_progs = ""
            declarations_code = p[5]
            statements_code = p[7]
        else:
            # subprograms + algo (no type_block) -- original
            algo_name = p[3]
            sub_progs = p[1]
            declarations_code = p[5]
            statements_code = p[7]
    else:
        algo_name = p[2]
        sub_progs = ""
        declarations_code = p[4]
        statements_code = p[6]

    # Inject memory map
    import json
    vars_info_json = json.dumps(mem_alloc.vars_info)
    
    # Build the Python code - functions defined in dependency order
    code = f"# Algo: {algo_name}\n"
    code += "import sys\nimport builtins\n"
    code += "\n# Helper functions (dependency order)\n"

    # 1. _algo_read - no deps
    code += "def _algo_read():\n"
    code += "    try:\n"
    code += "        return input()\n"
    code += "    except EOFError:\n"
    code += "        return ''\n\n"

    # 1b. _algo_ecrire - Ecrire without auto-newline; interprets \\n and \\t
    code += "def _algo_ecrire(*args):\n"
    code += "    import sys\n"
    code += "    parts = []\n"
    code += "    for a in args:\n"
    code += "        s = _algo_to_string(a)\n"
    code += "        # Display #0 as the visible null sentinel\n"
    code += "        s = s.replace('#0', chr(0))\n"
    code += "        s = s.replace('\\\\n', '\\n').replace('\\\\t', '\\t')\n"
    code += "        parts.append(s)\n"
    code += "    sys.stdout.write(' '.join(parts))\n"
    code += "    sys.stdout.flush()\n\n"

    # 2. _algo_to_string - no deps; MUST come before assign/concat/longueur
    code += "def _algo_to_string(val):\n"
    code += "    if val is None: return 'NIL'\n"
    code += "    if isinstance(val, bool): return 'Vrai' if val else 'Faux'\n"
    code += "    if isinstance(val, list):\n"
    code += "        res = ''\n"
    code += "        for char in val:\n"
    code += "            if char is None or char == '\\0' or char == '#0': break\n"
    code += "            res += str(char)\n"
    code += "        return res\n"
    code += "    return str(val)\n\n"

    # 3. _algo_assign_fixed_string - depends on _algo_to_string
    code += "def _algo_deref_to_list(target):\n"
    code += "    # Dereference a Pointer to get its backing list\n"
    code += "    if hasattr(target, 'base_var') and target.base_var is not None:\n"
    code += "        return target.base_var\n"
    code += "    if hasattr(target, 'get_target_container'):\n"
    code += "        try: return target.get_target_container()\n"
    code += "        except: pass\n"
    code += "    return target\n\n"

    code += "def _algo_assign_fixed_string(target_list, source_val):\n"
    code += "    target_list = _algo_deref_to_list(target_list)\n"
    code += "    if not isinstance(target_list, list):\n"
    code += "        raise TypeError('Variable Chaine non initialisee. Declarez avec s[N]: Chaine.')\n"
    code += "    limit = len(target_list)\n"
    code += "    s_val = ''\n"
    code += "    if hasattr(source_val, '_get_target_container'):\n"
    code += "        targ = source_val._get_target_container()\n"
    code += "        while hasattr(targ, '_get_target_container'): targ = targ._get_target_container()\n"
    code += "        if isinstance(targ, list):\n"
    code += "            s_val = _algo_to_string(targ[source_val.index:])\n"
    code += "        else:\n"
    code += "            s_val = _algo_to_string(source_val._get_string() if hasattr(source_val, '_get_string') else source_val._get())\n"
    code += "    else:\n"
    code += "        s_val = _algo_to_string(source_val)\n"
    code += "    if limit > 0:\n"
    code += "        s_val = s_val[:limit-1]\n"
    code += "        for i in range(len(s_val)):\n"
    code += "            target_list[i] = s_val[i]\n"
    code += "        target_list[len(s_val)] = '#0'\n"
    code += "        for i in range(len(s_val)+1, limit):\n"
    code += "            target_list[i] = None\n"
    code += "    return target_list\n\n"

    # 4. _algo_longueur - depends on _algo_to_string
    code += "def _algo_longueur(val):\n"
    code += "    return len(_algo_to_string(val))\n\n"

    # 4b. _algo_set_char - set a character at 0-based index in a fixed string
    code += "def _algo_set_char(target_list, index, char_val):\n"
    code += "    target_list = _algo_deref_to_list(target_list)\n"
    code += "    if not isinstance(target_list, list):\n"
    code += "        raise TypeError(f\'Cannot set char: not a list (got {type(target_list).__name__})\')\n"
    code += "    idx = int(index)  # 0-based index\n"
    code += "    if 0 <= idx < len(target_list):\n"
    code += "        if char_val == '#0' or char_val is None:\n"
    code += "            target_list[idx] = '#0'\n"
    code += "        else:\n"
    code += "            target_list[idx] = str(char_val)[0]\n"
    code += "    return target_list\n\n"

    # 4c. _algo_get_char - get a character at 0-based index from a fixed string
    code += "def _algo_get_char(target_list, index):\n"
    code += "    target_list = _algo_deref_to_list(target_list)\n"
    code += "    if isinstance(target_list, list):\n"
    code += "        idx = int(index)  # 0-based index\n"
    code += "        if 0 <= idx < len(target_list):\n"
    code += "            c = target_list[idx]\n"
    code += "            return c if c is not None and c != '#0' else '#0'\n"
    code += "        return ''\n"
    code += "    s = str(target_list)\n"
    code += "    idx = int(index)\n"
    code += "    return s[idx] if 0 <= idx < len(s) else ''\n\n"

    # 5. _algo_concat - depends on _algo_to_string; stops at #0
    code += "def _algo_concat(val1, val2):\n"
    code += "    s1 = _algo_to_string(val1)\n"
    code += "    s2 = _algo_to_string(val2)\n"
    code += "    # Stop at #0 null terminator in plain strings\n"
    code += "    s1 = s1.split('#0')[0] if '#0' in s1 else s1\n"
    code += "    s2 = s2.split('#0')[0] if '#0' in s2 else s2\n"
    code += "    return s1 + s2\n\n"

    # 5b. _algo_make_string - create a fresh char-list from a string (for ^^Caractere slot)
    code += "def _algo_make_string(s, max_size=256):\n"
    code += "    s = str(s) if not isinstance(s, str) else s\n"
    code += "    s = s[:max_size - 1]  # leave room for #0\n"
    code += "    arr = [None] * max_size\n"
    code += "    for i, c in enumerate(s):\n"
    code += "        arr[i] = c\n"
    code += "    arr[len(s)] = '#0'\n"
    code += "    return arr\n\n"

    # 6. _algo_read_typed - depends on _algo_assign_fixed_string, _algo_read
    code += "def _algo_read_typed(current_val, input_val=None, target_type_name='CHAINE'):\n"
    code += "    if input_val is None: input_val = _algo_read()\n"
    code += "    t = target_type_name.upper()\n"
    code += "    if 'CHAINE' in t:\n"
    code += "        if isinstance(current_val, list):\n"
    code += "            _algo_assign_fixed_string(current_val, input_val)\n"
    code += "            return current_val\n"
    code += "        return str(input_val)\n"
    code += "    if 'BOOLEEN' in t or isinstance(current_val, bool):\n"
    code += "        s = str(input_val).lower()\n"
    code += "        if s in ['vrai', 'true', '1']: return True\n"
    code += "        if s in ['faux', 'false', '0']: return False\n"
    code += "        raise ValueError(f\"Type mismatch: '{input_val}' n'est pas un Booleen valide.\")\n"
    code += "    elif 'ENTIER' in t or isinstance(current_val, int):\n"
    code += "        try: return int(input_val)\n"
    code += "        except:\n"
    code += "            raise ValueError(f\"Type mismatch: '{input_val}' n'est pas un Entier valide.\")\n"
    code += "    elif 'REEL' in t or isinstance(current_val, float):\n"
    code += "        try: return float(input_val)\n"
    code += "        except:\n"
    code += "            raise ValueError(f\"Type mismatch: '{input_val}' n'est pas un Reel valide.\")\n"

    code += "    return input_val\n\n"

    # 7. memory allocation helpers
    code += "_algo_heap = {}\n"
    code += "_algo_heap_next_addr = 50000\n\n"
    code += "def _algo_allouer(size_in_bytes):\n"
    code += "    global _algo_heap_next_addr\n"
    code += "    addr = _algo_heap_next_addr\n"
    code += "    _algo_heap_next_addr += size_in_bytes\n"
    code += "    allocated_list = [None] * max(1, size_in_bytes)\n"
    code += "    _algo_heap[addr] = allocated_list\n"
    code += "    ptr = Pointer(var_name=f'_heap_{addr}', namespace=_algo_heap, index=0, base_var=allocated_list)\n"
    code += "    ptr._heap_addr = addr\n"
    code += "    return ptr\n\n"
    
    code += "def _algo_liberer(ptr):\n"
    code += "    if ptr and hasattr(ptr, '_heap_addr'):\n"
    code += "        addr = ptr._heap_addr\n"
    code += "        if addr in _algo_heap:\n"
    code += "            del _algo_heap[addr]\n"
    code += "            ptr.base_var = None\n"
    code += "            ptr.var_name = None\n\n"
    
    def _field_byte_size(type_str, rec_types, _seen=None):
        """Return the byte size of a single field given its type string."""
        if _seen is None:
            _seen = set()
        t = type_str.upper()
        if t in ('ENTIER', 'ENTIER_TYPE'): return 4
        if t in ('REEL', 'REEL_TYPE'): return 8
        if t in ('BOOLEEN', 'BOOLEEN_TYPE'): return 1
        if t in ('CARACTERE', 'CARACTERE_TYPE'): return 1
        # Pointer types (POINTEUR_X or ^ prefix) — architectural pointer width
        if t.startswith('POINTEUR_') or t.startswith('^'): return 8
        # Chaine[N] or TABLEAU_Chaine_N  → N bytes
        if t.startswith('TABLEAU_CHAINE_'):
            try: return int(t.split('_')[-1])
            except ValueError: return 1
        if 'CHAINE' in t: return 1  # bare Chaine (shouldn't normally reach here)
        # Array field: TABLEAU_<ElemType>_<N>
        if t.startswith('TABLEAU_'):
            parts = t.split('_')
            try:
                n = int(parts[-1])
                elem_type = '_'.join(parts[1:-1])
                return n * _field_byte_size(elem_type, rec_types, _seen)
            except (ValueError, IndexError):
                return 4
        # User-defined nested record type — recursive, guard against cycles
        if type_str in rec_types and type_str not in _seen:
            _seen = _seen | {type_str}
            return sum(_field_byte_size(ft, rec_types, _seen)
                       for ft in rec_types[type_str].values())
        return 4  # fallback

    # Compute true byte sizes for each record type
    record_sizes = {}
    for name, fields in record_types.items():
        record_sizes[name] = sum(_field_byte_size(ft, record_types) for ft in fields.values())

    code += f"_algo_record_sizes = {record_sizes!r}\n\n"
    code += "def _algo_taille(type_name):\n"
    code += "    t = type_name.lower()\n"
    code += "    if 'pointeur' in t or t.startswith('^'): return 8\n"
    code += "    if 'entier' in t: return 4\n"
    code += "    if 'reel' in t: return 8\n"
    code += "    if 'booleen' in t: return 1\n"
    code += "    if 'caractere' in t: return 1\n"
    code += "    if 'chaine' in t: return 1\n"
    code += "    # User-defined record type — uses precomputed sizes\n"
    code += "    if type_name in _algo_record_sizes: return _algo_record_sizes[type_name]\n"
    code += "    return 4\n\n"

    # 8. record-aware allocator: wraps an initialised dict in a Pointer
    # Uses index=0 and base_var=record_dict so Pointer._get() returns the dict directly
    code += "def _algo_allouer_record(record_dict):\n"
    code += "    global _algo_heap_next_addr\n"
    code += "    addr = _algo_heap_next_addr\n"
    code += "    _algo_heap_next_addr += 1\n"
    code += "    _algo_heap[addr] = record_dict\n"
    code += "    ptr = Pointer(var_name=None, namespace=None, index=0, base_var=record_dict)\n"
    code += "    ptr._heap_addr = addr\n"
    code += "    return ptr\n\n"


    code += f"global _algo_vars_info\n_algo_vars_info = {vars_info_json}\n\n"
    code += pointer_class_code + "\n"
    code += f"{declarations_code}\n\n{sub_progs}\n\n{statements_code}\n"

    p[0] = code
    
    # Reset all state for next build if needed
    global symbol_table, scope_stack, parser_errors, indent_level
    # But usually reset_parser() is called outside.

def p_program_subprogram_list_single(p):
    '''program_subprogram_list : sub_program'''
    p[0] = p[1]

def p_program_subprogram_list_multiple(p):
    '''program_subprogram_list : program_subprogram_list sub_program'''
    p[0] = f"{p[1]}\n{p[2]}"

def p_declarations_empty(p):
    '''declarations : '''
    p[0] = ""
    # Also ensure allocator is fresh if we start a new declarations block?
    # No, declarations is recursive.

def p_declarations_vars(p):
    '''declarations : declarations VAR var_definitions
                    | declarations CONST const_definitions
                    | declarations TYPE ID EQUALS ENREGISTREMENT DEBUT field_list FIN SEMICOLON
                    | declarations TYPE ID EQUALS ENREGISTREMENT field_list FIN SEMICOLON
                    | declarations sub_program'''
    if len(p) == 4:
        p[0] = f"{p[1]}\n{p[3]}"  # VAR / CONST
    elif len(p) in (10, 9):
        # Inline Type declaration (individual keyword form)
        type_name = p[3]
        field_list = p[7] if len(p) == 10 else p[6]
        _register_type(type_name, field_list)
        p[0] = p[1]  # no runtime code added
    else:
        p[0] = f"{p[1]}\n{p[2]}"  # sub_program

# -----------------------------------------------------------------------
# Type block (Enregistrement declarations)  - appears BEFORE Algorithme
# Each record type declaration uses its OWN 'Type' keyword:
#   Type Foo = Enregistrement Debut ... Fin;
#   Type Bar = Enregistrement Debut ... Fin;
# -----------------------------------------------------------------------

def _register_type(type_name, field_list):
    """Register a record type definition and return None (no runtime code needed)."""
    record_types[type_name] = field_list

def p_type_block_single(p):
    '''type_block : TYPE ID EQUALS ENREGISTREMENT DEBUT field_list FIN SEMICOLON
                  | TYPE ID EQUALS ENREGISTREMENT field_list FIN SEMICOLON'''
    type_name = p[2]
    field_list = p[6] if len(p) == 9 else p[5]
    _register_type(type_name, field_list)
    p[0] = None  # no runtime code

def p_type_block_multiple(p):
    '''type_block : type_block TYPE ID EQUALS ENREGISTREMENT DEBUT field_list FIN SEMICOLON
                  | type_block TYPE ID EQUALS ENREGISTREMENT field_list FIN SEMICOLON'''
    type_name = p[3]
    field_list = p[7] if len(p) == 10 else p[6]
    _register_type(type_name, field_list)
    p[0] = None

def p_field_list_single(p):
    '''field_list : field_definition'''
    p[0] = p[1]

def p_field_list_multiple(p):
    '''field_list : field_list field_definition'''
    merged = dict(p[1])
    merged.update(p[2])
    p[0] = merged

def p_field_definition(p):
    '''field_definition : ID COLON type SEMICOLON
                        | ID LBRACKET NUMBER RBRACKET COLON type SEMICOLON'''
    if len(p) == 5:
        p[0] = {p[1]: p[3]}
    else:
        # Array field: store as TABLEAU_<type>_<size>
        p[0] = {p[1]: f"TABLEAU_{p[6]}_{p[3]}"}

def p_field_definition_multi(p):
    '''field_definition : ID COMMA field_definition'''
    name = p[1]
    fdict = p[3]
    first_type = next(iter(fdict.values()))
    if first_type.startswith('TABLEAU_'):
        base_type = first_type.split('_')[1]
    else:
        base_type = first_type
    p[0] = {**fdict, name: base_type}

def p_field_definition_array_multi(p):
    '''field_definition : ID LBRACKET NUMBER RBRACKET COMMA field_definition'''
    name = p[1]
    size = p[3]
    fdict = p[6]
    first_type = next(iter(fdict.values()))
    if first_type.startswith('TABLEAU_'):
        base_type = first_type.split('_')[1]
    else:
        base_type = first_type
    p[0] = {**fdict, name: f"TABLEAU_{base_type}_{size}"}

# Memory Allocation Helper
class MemoryAllocator:
    def __init__(self, start_address=1000):
        self.next_address = start_address
        self.vars_info = {} # name -> {'addr': int, 'size': int, 'type': str}

    def allocate(self, name, type_name, count=1):
        size = self.get_type_size(type_name) * count
        addr = self.next_address
        self.next_address += size
        self.vars_info[name] = {'addr': addr, 'size': size, 'element_size': self.get_type_size(type_name), 'type': type_name}
        return addr

    def get_type_size(self, type_name):
        t = type_name.upper()
        # 1. Check if it's a known record type
        if type_name in record_types:
            fields = record_types[type_name]
            return sum(self.get_type_size(ft) for ft in fields.values())
        
        # 2. Handle pointer types
        if t.startswith('POINTEUR') or t.startswith('^'):
            return 8 # Architectural pointer size
            
        # 3. Handle base types
        if t in ('ENTIER', 'ENTIER_TYPE'): return 4
        if t in ('REEL', 'REEL_TYPE'): return 8
        if t in ('BOOLEEN', 'BOOLEEN_TYPE'): return 1
        if t in ('CARACTERE', 'CARACTERE_TYPE'): return 1
        
        # 4. Handle Chaine and Arrays
        if t.startswith('TABLEAU_CHAINE_'):
            try: return int(t.split('_')[-1])
            except: return 1
        if 'CHAINE' in t: return 1
        
        if t.startswith('TABLEAU_'):
            parts = t.split('_')
            try:
                # Format: TABLEAU_ELEMENTTYPE_SIZE
                n = int(parts[-1])
                elem_type = '_'.join(parts[1:-1])
                return n * self.get_type_size(elem_type)
            except:
                return 4
                
        return 4 # Default

mem_alloc = MemoryAllocator()

def p_var_definitions(p):
    '''var_definitions : var_definitions var_definition
                       | var_definition'''
    if len(p) == 3:
        p[0] = f"{p[1]}{p[2]}"
    else:
        p[0] = p[1]

def p_var_definition(p):
    '''var_definition : var_list SEMICOLON'''
    # p[1] is (code, type)
    if isinstance(p[1], tuple):
        p[0] = f"{p[1][0]}\n"
    else:
        p[0] = f"{p[1]}\n"

def p_const_definitions(p):
    '''const_definitions : const_definitions const_definition
                         | const_definition'''
    if len(p) == 3:
        p[0] = f"{p[1]}{p[2]}"
    else:
        p[0] = p[1]

def p_const_definition(p):
    '''const_definition : const_list SEMICOLON'''
    p[0] = f"{p[1]}\n"


def p_var_list_multiple(p):
    '''var_list : ID COMMA var_list'''
    var_name = p[1]
    prev_code, type_name = p[3]
    if type_name.upper() in ('CHAINE', 'CHAINE_TYPE') and '[' not in var_name:
        parser_errors.append({"line": p.lineno(1), "column": 0,
            "message": f"Variables de type Chaine doivent avoir une taille fixe (ex: {var_name}[10]: Chaine)",
            "type": "Semantic Error", "error_code": "E2.4"})
    
    add_variable(var_name, type_name)
    alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
    mem_alloc.allocate(alloc_name, type_name)
    
    if type_name.upper().startswith('POINTEUR_') or type_name.upper() == 'POINTEUR':
        ns = "locals()" if is_local_scope() else "globals()"
        init_val = f"Pointer(\"{var_name}\", {ns})"
    else:
        init_val = get_default_value(type_name)
        
    code = f"{get_indent()}{var_name} = {init_val}\n{prev_code}"
    p[0] = (code, type_name)

def p_var_list_array_multiple(p):
    '''var_list : ID LBRACKET NUMBER RBRACKET COMMA var_list'''
    var_name = p[1]
    size = int(p[3])
    prev_code, type_name = p[6]
    
    # This handles both Chaine[N] and Type[N]
    if type_name.upper() in ('CHAINE', 'CHAINE_TYPE'):
        add_variable(var_name, 'CHAINE')
        alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
        mem_alloc.allocate(alloc_name, 'CHAINE', count=size)
        code = f"{get_indent()}{var_name} = ['\\0'] * {size}\n{prev_code}"
        p[0] = (code, type_name)
    else:
        arr_type = f"TABLEAU_{type_name}_{size}"
        add_variable(var_name, arr_type)
        alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
        mem_alloc.allocate(alloc_name, type_name, count=size)
        code = f"{get_indent()}{var_name} = [None] * {size}\n{prev_code}"
        p[0] = (code, type_name)


def p_var_list_tableau(p):
    '''var_list : ID COLON TABLEAU DE type'''
    var_name = p[1]
    arr_type = f"TABLEAU_{p[5]}"
    add_variable(var_name, arr_type)
    
    alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
    mem_alloc.allocate(alloc_name, p[5], count=1) # Treat as pointer to array?
    
    p[0] = (f"{get_indent()}{var_name} = []", p[5])

def p_var_list_matrix_multiple(p):
    '''var_list : ID LBRACKET NUMBER RBRACKET LBRACKET NUMBER RBRACKET COMMA var_list'''
    var_name = p[1]
    rows = int(p[3])
    cols = int(p[6])
    prev_code, type_name = p[9]
    
    mat_type = f"MATRICE_{type_name}"
    add_variable(var_name, mat_type)
    
    # Allocate memory for matrix (rows * cols)
    size = rows * cols
    alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
    mem_alloc.allocate(alloc_name, type_name, count=size)
    
    # Initialize with None
    code = f"{get_indent()}{var_name} = [[None] * {cols} for _ in range({rows})]\n{prev_code}"
    
    p[0] = (code, type_name)

def p_var_list_matrix(p):
    '''var_list : ID LBRACKET NUMBER RBRACKET LBRACKET NUMBER RBRACKET COLON type'''
    var_name = p[1]
    var_type = p[9]
    mat_type = f"MATRICE_{var_type}"
    add_variable(var_name, mat_type)
    
    # Allocate memory for matrix (rows * cols)
    size = int(p[3]) * int(p[6])
    alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
    mem_alloc.allocate(alloc_name, var_type, count=size)
    
    # Initialize with None
    code = f"{get_indent()}{var_name} = [[None] * {p[6]} for _ in range({p[3]})]"
    
    p[0] = (code, var_type)

def p_var_list_record(p):
    '''var_list : ID COLON type'''
    # Catches record types as well as plain scalars
    # (Scalar case handled in p_var_list_scalar; this is the fallback for user-defined types)
    var_name = p[1]
    var_type = p[3]

    if var_type in record_types:
        add_variable(var_name, var_type)
        alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
        mem_alloc.allocate(alloc_name, var_type)
        init_expr = _build_record_init(var_type)
        code = f"{get_indent()}{var_name} = {init_expr} # {var_type}"
        p[0] = (code, var_type)
    else:
        # Delegate same logic as p_var_list_scalar
        if var_type.upper() in ('CHAINE', 'CHAINE_TYPE'):
            error_msg = f"Variables de type Chaine doivent avoir une taille fixe (ex: {var_name}[10]: Chaine)"
            parser_errors.append({"line": p.lineno(1), "column": 0, "message": error_msg,
                                   "type": "Semantic Error", "error_code": "E2.4"})
        add_variable(var_name, var_type)
        alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
        mem_alloc.allocate(alloc_name, var_type)
        if var_type.upper().startswith('POINTEUR_') or var_type.upper() == 'POINTEUR':
            ns = "locals()" if is_local_scope() else "globals()"
            code = f"{get_indent()}{var_name} = Pointer(\"{var_name}\", {ns}) # {var_type}"
        else:
            code = f"{get_indent()}{var_name} = None # {var_type}"
        p[0] = (code, var_type)

def p_var_list_record_array(p):
    '''var_list : ID LBRACKET NUMBER RBRACKET COLON type'''
    var_name = p[1]
    var_type = p[6]
    size = int(p[3])

    if var_type in record_types:
        add_variable(var_name, f"TABLEAU_{var_type}")
        alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
        mem_alloc.allocate(alloc_name, var_type, count=size)
        init_expr = _build_record_init(var_type)
        code = f"{get_indent()}{var_name} = [{init_expr} for _ in range({size})] # Tableau de {var_type}"
        p[0] = (code, var_type)
    elif var_type.upper() in ('CHAINE', 'CHAINE_TYPE'):
        add_variable(var_name, 'CHAINE')
        alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
        mem_alloc.allocate(alloc_name, var_type, count=size)
        code = f"{get_indent()}{var_name} = [None] * {size}"
        p[0] = (code, var_type)
    else:
        final_type = f"TABLEAU_{var_type}"
        add_variable(var_name, final_type)
        alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
        mem_alloc.allocate(alloc_name, var_type, count=size)
        code = f"{get_indent()}{var_name} = [None] * {size}"
        p[0] = (code, var_type)

def p_const_list(p):
    '''const_list : ID EQUALS value'''
    p[0] = f"{p[1]} = {p[3]}"

def p_sub_program(p):
    '''sub_program : function_definition
                   | procedure_definition'''
    p[0] = p[1]

def p_function_head(p):
    '''function_head : FONCTION ID LPAREN'''
    name = p[2]
    push_scope(name)
    globals_modified_in_subprogram[name] = set()
    global current_subprogram_type
    current_subprogram_type = 'function'
    p[0] = name

def p_procedure_head(p):
    '''procedure_head : PROCEDURE ID LPAREN'''
    name = p[2]
    push_scope(name)
    globals_modified_in_subprogram[name] = set()
    global current_subprogram_type
    current_subprogram_type = 'procedure'
    p[0] = name

def p_function_definition(p):
    '''function_definition : function_head parameter_list RPAREN COLON type SEMICOLON sub_program_body
                           | function_head parameter_list RPAREN COLON type sub_program_body'''
    name = p[1]
    ret_type = p[5]
    function_return_types[name] = ret_type
    params_code, param_list = p[2]
    body_code = p[7] if len(p) == 8 else p[6]
    pop_scope()
    global current_subprogram_type
    current_subprogram_type = None
    global current_subprogram_var_params
    
    clone_stmts = ""
    for param_name, param_type in param_list:
        if ('POINTEUR' in param_type or param_type == 'POINTEUR') and param_name not in current_subprogram_var_params:
            clone_stmts += f"    {param_name} = {param_name}._clone() if hasattr({param_name}, '_clone') else {param_name}\n"
            
    current_subprogram_var_params = set()
    
    global_vars = globals_modified_in_subprogram.get(name, set())
    global_stmt = f"    global {', '.join(global_vars)}\n" if global_vars else ""
    
    p[0] = f"def {name}({params_code}):\n{global_stmt}{clone_stmts}{body_code}\n"

def p_procedure_definition(p):
    '''procedure_definition : procedure_head parameter_list RPAREN SEMICOLON sub_program_body
                            | procedure_head parameter_list RPAREN sub_program_body'''
    name = p[1]
    params_code, param_list = p[2]
    body_code = p[5] if len(p) == 6 else p[4]
    pop_scope()
    global current_subprogram_type
    current_subprogram_type = None
    global current_subprogram_var_params
    
    clone_stmts = ""
    for param_name, param_type in param_list:
        if ('POINTEUR' in param_type or param_type == 'POINTEUR') and param_name not in current_subprogram_var_params:
            clone_stmts += f"    {param_name} = {param_name}._clone() if hasattr({param_name}, '_clone') else {param_name}\n"
            
    current_subprogram_var_params = set()
    
    global_vars = globals_modified_in_subprogram.get(name, set())
    global_stmt = f"    global {', '.join(global_vars)}\n" if global_vars else ""
    
    p[0] = f"def {name}({params_code}):\n{global_stmt}{clone_stmts}{body_code}\n"

def p_parameter_list_empty(p):
    '''parameter_list : '''
    p[0] = ("", [])

def p_parameter_list_single(p):
    '''parameter_list : parameter_declaration'''
    p[0] = (p[1][0], [p[1][1]])

def p_parameter_list_multiple(p):
    '''parameter_list : parameter_declaration COMMA parameter_list'''
    p[0] = (f"{p[1][0]}, {p[3][0]}", [p[1][1]] + p[3][1])

def p_parameter_declaration_simple(p):
    '''parameter_declaration : ID COLON type
                             | VAR ID COLON type'''
    if len(p) == 4:
        name = p[1]
        type_name = p[3]
    else:
        # p[1] is 'VAR'
        name = p[2]
        type_name = p[4]
        global current_subprogram_var_params
        # Ensure the set exists before adding
        if 'current_subprogram_var_params' not in globals() or current_subprogram_var_params is None:
             current_subprogram_var_params = set()
        current_subprogram_var_params.add(name)
        
    add_variable(name, type_name)
    alloc_name = f"{scope_stack[-1]}.{name}"
    mem_alloc.allocate(alloc_name, type_name)
    p[0] = (name, (name, type_name))

def p_parameter_declaration_array(p):
    '''parameter_declaration : ID LBRACKET NUMBER RBRACKET COLON type
                             | VAR ID LBRACKET NUMBER RBRACKET COLON type'''
    if len(p) == 7:
        name = p[1]
        size = p[3]
        type_name = p[6]
    else:
        # VAR branch
        name = p[2]
        size = p[4]
        type_name = p[7]
        global current_subprogram_var_params
        if 'current_subprogram_var_params' not in globals() or current_subprogram_var_params is None:
             current_subprogram_var_params = set()
        current_subprogram_var_params.add(name)
        
    arr_type = f"TABLEAU_{type_name}_{size}"
    add_variable(name, arr_type)
    alloc_name = f"{scope_stack[-1]}.{name}"
    if isinstance(size, int):
        mem_alloc.allocate(alloc_name, type_name, count=size)
        mem_alloc.vars_info[alloc_name]['type'] = f"TABLEAU_{size}"
    else:
        mem_alloc.allocate(alloc_name, type_name)
    p[0] = (name, (name, type_name))

def p_parameter_declaration_matrix(p):
    '''parameter_declaration : ID LBRACKET NUMBER RBRACKET LBRACKET NUMBER RBRACKET COLON type
                             | VAR ID LBRACKET NUMBER RBRACKET LBRACKET NUMBER RBRACKET COLON type'''
    if len(p) == 10:
        name = p[1]
        rows = p[3]
        cols = p[6]
        type_name = p[9]
    else:
        # VAR branch
        name = p[2]
        rows = p[4]
        cols = p[7]
        type_name = p[10]

    add_variable(name, type_name)
    alloc_name = f"{scope_stack[-1]}.{name}"
    if isinstance(rows, int) and isinstance(cols, int):
        total_size = rows * cols
        mem_alloc.allocate(alloc_name, type_name, count=total_size)
        mem_alloc.vars_info[alloc_name]['type'] = f"MATRICE_{rows}x{cols}"
    else:
        mem_alloc.allocate(alloc_name, type_name)
    p[0] = (name, (name, type_name))

def p_sub_program_body_start(p):
    '''sub_program_body_start : '''
    increase_indent()
    global current_subprogram_var_params
    if 'current_subprogram_var_params' not in globals():
         current_subprogram_var_params = set()

def p_sub_program_body_vars(p):
    '''sub_program_body : VAR sub_program_body_start var_definitions DEBUT statements FIN SEMICOLON'''
    vars_code = p[3]
    stats_code = p[5]
    decrease_indent()
    p[0] = f"{vars_code}\n{stats_code}"

def p_sub_program_body_no_vars(p):
    '''sub_program_body : sub_program_body_start DEBUT statements FIN SEMICOLON'''
    stats_code = p[3]
    decrease_indent()
    p[0] = f"{stats_code}"

def p_statement_return(p):
    '''statement : RETOURNER expression SEMICOLON'''
    global current_subprogram_type
    if current_subprogram_type != 'function':
        error_msg = f"Erreur semantique: RETOURNER n'est autorise que dans une FONCTION."
        parser_errors.append({
            "line": p.lineno(1),
            "column": 0,
            "message": error_msg,
            "type": "Semantic Error",
            "error_code": "E5.1"
        })
    expr_code, expr_type = p[2]
    p[0] = f"{get_indent()}return {expr_code}"

def p_expression_call(p):
    '''expression : ID LPAREN argument_list RPAREN'''
    name = p[1]
    args_code, _ = p[3]
    ret_type = function_return_types.get(name, 'UNKNOWN')
    p[0] = (f"{name}({args_code})", ret_type)

def p_argument_list_empty(p):
    '''argument_list : '''
    p[0] = ("", [])

def p_argument_list_single(p):
    '''argument_list : expression'''
    p[0] = (p[1][0], [p[1][1]])

def p_argument_list_multiple(p):
    '''argument_list : expression COMMA argument_list'''
    p[0] = (f"{p[1][0]}, {p[3][0]}", [p[1][1]] + p[3][1])

def p_type(p):
    '''type : ENTIER_TYPE
            | REEL_TYPE
            | CHAINE_TYPE
            | BOOLEEN_TYPE
            | CARACTERE_TYPE
            | CARET type
            | ID'''
    if len(p) == 2:
        val = p[1]
        # If it's an ID that matches a registered record type, use it directly
        if val in record_types:
            p[0] = val
        else:
            p[0] = val  # Unknown user type; may trigger semantic error elsewhere
    else:
        base_type = p[2]
        p[0] = f'POINTEUR_{base_type}'

# -----------------------------------------------------------------------
# Field access expressions  (record.field  and  ptr->field)
# -----------------------------------------------------------------------

def p_expression_field_access(p):
    '''expression : expression DOT ID'''
    rec_code, rec_type = p[1]
    field_name = p[3]
    # Determine the type of this field from the record_types registry
    field_type = 'UNKNOWN'
    if rec_type in record_types:
        field_type = record_types[rec_type].get(field_name, 'UNKNOWN')
    p[0] = (f"{rec_code}['{field_name}']", field_type)

def p_expression_arrow_access(p):
    '''expression : expression ARROW ID'''
    ptr_code, ptr_type = p[1]
    field_name = p[3]
    # Determine the record type that this pointer points to
    rec_type = ptr_type.replace('POINTEUR_', '', 1) if ptr_type.startswith('POINTEUR_') else 'UNKNOWN'
    field_type = 'UNKNOWN'
    if rec_type in record_types:
        field_type = record_types[rec_type].get(field_name, 'UNKNOWN')
    # ->field is shorthand for (ptr^).field, i.e. ptr._get()[field]
    p[0] = (f"({ptr_code})._get()['{field_name}']", field_type)

# -----------------------------------------------------------------------
# Field assignment statements  (rec.field := val  and  ptr->field := val)
# -----------------------------------------------------------------------

def p_statement_assign_field(p):
    '''statement : expression DOT ID ASSIGN expression SEMICOLON'''
    rec_code, rec_type = p[1]
    field_name = p[3]
    val_code, val_type = p[5]
    p[0] = f"{get_indent()}{rec_code}['{field_name}'] = ({val_code})._clone() if hasattr({val_code}, '_clone') else {val_code}"

def p_statement_assign_arrow_field(p):
    '''statement : expression ARROW ID ASSIGN expression SEMICOLON'''
    ptr_code, ptr_type = p[1]
    field_name = p[3]
    val_code, val_type = p[5]
    # ptr->field := val  is  ptr._get()['field'] = val
    p[0] = f"{get_indent()}({ptr_code})._get()['{field_name}'] = ({val_code})._clone() if hasattr({val_code}, '_clone') else {val_code}"

def p_statements(p):
    '''statements : statements statement
                  | statement'''
    if len(p) == 3:
        p[0] = f"{p[1]}\n{p[2]}"
    else:
        p[0] = f"{p[1]}"

def p_statement_expression(p):
    '''statement : expression SEMICOLON'''
    expr_code, expr_type = p[1]
    p[0] = f"{get_indent()}{expr_code}"

def check_allocation_semantic(p, var_name, expr_code, is_array_access=False):
    if '_algo_allouer(' in expr_code and '_algo_taille(' in expr_code:
        import re
        m = re.search(r"_algo_taille\('([^']+)'\)", expr_code)
        if m:
            alloc_type = m.group(1).upper()
            var_type, _ = find_variable(var_name)
            if var_type == 'UNKNOWN': return
            var_type = var_type.upper()
            
            var_ptr_count = var_type.count('^') + var_type.count('POINTEUR_')
            var_base = var_type.replace('^', '').replace('POINTEUR_', '').replace('_TYPE', '').upper()
            alloc_ptr_count = alloc_type.count('^') + alloc_type.count('POINTEUR_')
            alloc_base = alloc_type.replace('^', '').replace('POINTEUR_', '').replace('_TYPE', '').upper()
            
            expected_diff = 2 if is_array_access else 1
            if var_base != alloc_base or var_ptr_count != alloc_ptr_count + expected_diff:
                error_msg = f"Erreur semantique: Impossible d'allouer espace '{alloc_type}' pour '{var_name}' (Type declare: {var_type})"
                parser_errors.append({
                    "line": p.lineno(1),
                    "column": 0,
                    "message": error_msg,
                    "type": "Semantic Error",
                    "error_code": "E3.2"
                })

def p_statement_assign(p):
    '''statement : ID ASSIGN expression SEMICOLON'''
    var_name = p[1]
    expr_code, expr_type = p[3]
    var_type, _ = find_variable(var_name)
    
    if is_local_scope() and var_name not in symbol_table[scope_stack[-1]]:
        globals_modified_in_subprogram[scope_stack[-1]].add(var_name)

    if var_type != 'UNKNOWN' and expr_type != 'UNKNOWN':
        if not check_type_compatibility(var_type, expr_type):
            error_msg = f"Type mismatch: Cannot assign {expr_type} to {var_name} ({var_type})"
            from compiler.lexer import find_column
            parser_errors.append({
                "line": p.lineno(1),
                "column": 0,
                "message": error_msg,
                "type": "Semantic Error"
            })
            
    check_allocation_semantic(p, var_name, expr_code, is_array_access=False)
            
    p[0] = f"{get_indent()}{var_name} = {expr_code}"
    
    # Special handling for fixed strings to preserve list reference and enforce size
    if var_type == 'CHAINE':
         # If the RHS is a pointer to a string (ptr^), we want the raw pointer object 
         # passed into `_algo_assign_fixed_string` so it can slice it from the index onwards.
         # So we intercept the `._get()` call if it was an assignment from a dereferenced pointer.
         if '._get_string()' in expr_code:
             # Match: ((ptr_chaine)._get_string() if hasattr(...) else (ptr_chaine)._get())
             # To bypass this entire wrapper and just pass the pointer for direct slicing in `_algo_assign...`
             raw_expr = expr_code.split(')._get_string()')[0]
             if raw_expr.startswith('(('): raw_expr = raw_expr[2:]
             elif raw_expr.startswith('('): raw_expr = raw_expr[1:]
             p[0] = f"{get_indent()}{var_name} = _algo_assign_fixed_string({var_name}, {raw_expr})"
         elif expr_code.endswith(')._get()'):
             raw_expr = expr_code[:-len(')._get()')]
             if raw_expr.startswith('('): raw_expr = raw_expr[1:]
             p[0] = f"{get_indent()}{var_name} = _algo_assign_fixed_string({var_name}, {raw_expr})"
         else:
             p[0] = f"{get_indent()}{var_name} = _algo_assign_fixed_string({var_name}, {expr_code})"
    elif 'POINTEUR' in var_type:
         ns = "locals()" if is_local_scope() else "globals()"
         
         if expr_type.startswith('TABLEAU_') or expr_type == 'CHAINE':
             # Array decay: assign array to pointer directly
             p[0] = f"{get_indent()}{var_name}._assign(Pointer(\"{expr_code}\", {ns}, index=0, base_var={expr_code}))"
         else:
             # Regular assignment: evaluate expression and mutate the existing pointer object via _assign
             p[0] = f"{get_indent()}_tmp_{var_name} = {expr_code}\n{get_indent()}{var_name}._assign(Pointer(\"{var_name}_ptr_src\", {ns}, index=0, base_var=_tmp_{var_name}) if isinstance(_tmp_{var_name}, list) and not hasattr(_tmp_{var_name}, '_get_target_container') else _tmp_{var_name})"



def p_statement_assign_pointer_deref(p):
    '''statement : ID CARET ASSIGN expression SEMICOLON'''
    ptr_name = p[1]
    expr_code, expr_type = p[4]
    ptr_type, _ = find_variable(ptr_name)
    
    # Assign to the dereferenced pointer (ptr^ := value)
    p[0] = f"{get_indent()}{ptr_name}._set({expr_code})"

# Redundant rules removed (consolidated into p_statement_assign_field)

def p_statement_liberer(p):
    '''statement : LIBERER LPAREN expression RPAREN SEMICOLON'''
    p[0] = f"{get_indent()}_algo_liberer({p[3][0]})"

def p_statement_io_write(p):
    '''statement : ECRIRE LPAREN expression_list RPAREN SEMICOLON'''
    # Print without automatic newline; interpret \\n and \\t in the output string
    p[0] = f"{get_indent()}_algo_ecrire({p[3]})"

def p_id_list(p):
    '''id_list : id_or_array_access
               | id_or_array_access COMMA id_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_id_or_array_access(p):
    '''id_or_array_access : ID
                          | ID CARET
                          | ID LBRACKET expression RBRACKET
                          | ID LBRACKET expression RBRACKET LBRACKET expression RBRACKET'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3 and str(p[2]) == '^':
        p[0] = f"{p[1]}^"
    elif len(p) == 5:
        p[0] = f"{p[1]}[{p[3][0]}]"
    else:
        p[0] = f"{p[1]}[{p[3][0]}][{p[6][0]}]"

def p_statement_io_read(p):
    '''statement : LIRE LPAREN id_list RPAREN SEMICOLON'''
    indent = get_indent()
    vars = p[3]
    code_blocks = []
    
    for var_name_access in vars:
        is_deref = isinstance(var_name_access, str) and var_name_access.endswith('^')
        if is_deref:
            base_name = var_name_access[:-1]
        else:
            base_name = var_name_access.split('[')[0]
            
        if is_local_scope() and base_name not in symbol_table[scope_stack[-1]]:
            globals_modified_in_subprogram[scope_stack[-1]].add(base_name)
            
        # Resolve type for _algo_read_typed
        type_str = "'UNKNOWN'"
        
        full_type, _ = find_variable(base_name)
        if full_type != 'UNKNOWN':
            if is_deref:
                if full_type.startswith('POINTEUR_'):
                    type_str = f"'{full_type.replace('POINTEUR_', '')}'"
                elif full_type == 'POINTEUR':
                    type_str = "'UNKNOWN'"
            elif '[' in var_name_access:
                if full_type.startswith('TABLEAU_'):
                    type_str = f"'{full_type.replace('TABLEAU_', '')}'"
                elif full_type.startswith('MATRICE_'):
                     type_str = f"'{full_type.replace('MATRICE_', '')}'"
                else:
                    type_str = f"'{full_type}'"
            else:
                type_str = f"'{full_type}'"
        
        if is_deref:
            block = f"{indent}{base_name}._set(_algo_read_typed({base_name}._get(), _algo_read(), {type_str}))"
        else:
            block = f"{indent}{var_name_access} = _algo_read_typed({var_name_access}, _algo_read(), {type_str})"
        code_blocks.append(block)
        
    p[0] = "\n".join(code_blocks)

def p_indent_inc(p):
    '''indent_inc :'''
    increase_indent()

def p_indent_dec(p):
    '''indent_dec :'''
    decrease_indent()

def p_statement_if_complete(p):
    '''statement : SI condition ALORS indent_inc statements indent_dec FSI
                 | SI condition ALORS indent_inc statements indent_dec FIN SI
                 | SI condition ALORS indent_inc statements indent_dec FSI SEMICOLON
                 | SI condition ALORS indent_inc statements indent_dec FIN SI SEMICOLON'''
    # stats is always at index 5
    p[0] = f"{get_indent()}if {p[2]}:\n{p[5]}"

def p_statement_if_else(p):
    '''statement : SI condition ALORS indent_inc statements indent_dec SINON indent_inc statements indent_dec FSI
                 | SI condition ALORS indent_inc statements indent_dec SINON indent_inc statements indent_dec FIN SI
                 | SI condition ALORS indent_inc statements indent_dec SINON indent_inc statements indent_dec FSI SEMICOLON
                 | SI condition ALORS indent_inc statements indent_dec SINON indent_inc statements indent_dec FIN SI SEMICOLON'''
    p[0] = f"{get_indent()}if {p[2]}:\n{p[5]}\n{get_indent()}else:\n{p[9]}"

def p_statement_while(p):
    '''statement : TANT_QUE QUE condition FAIRE indent_inc statements indent_dec FIN TANT_QUE QUE
                 | TANT_QUE QUE condition FAIRE indent_inc statements indent_dec FIN TANT_QUE
                 | TANT_QUE QUE condition FAIRE indent_inc statements indent_dec FIN_TANT_QUE
                 | TANT_QUE condition FAIRE indent_inc statements indent_dec FIN_TANT_QUE
                 | TANT_QUE QUE condition FAIRE indent_inc statements indent_dec FIN TANT_QUE QUE SEMICOLON
                 | TANT_QUE QUE condition FAIRE indent_inc statements indent_dec FIN TANT_QUE SEMICOLON
                 | TANT_QUE QUE condition FAIRE indent_inc statements indent_dec FIN_TANT_QUE SEMICOLON
                 | TANT_QUE condition FAIRE indent_inc statements indent_dec FIN_TANT_QUE SEMICOLON'''
    # Rule 1: TANT_QUE (1) QUE (2) condition (3) FAIRE (4) indent_inc (5) statements (6) ...
    # Rule 4: TANT_QUE (1) condition (2) FAIRE (3) indent_inc (4) statements (5) ...
    
    if str(p[2]).lower() == 'que':
        cond = p[3]
        stats = p[6]
    else:
        cond = p[2]
        stats = p[5]
        
    p[0] = f"{get_indent()}while {cond}:\n{stats}"

def p_statement_for(p):
    '''statement : POUR ID ASSIGN expression ID expression FAIRE indent_inc statements indent_dec FIN POUR
                 | POUR ID ASSIGN expression ID expression FAIRE indent_inc statements indent_dec FIN_POUR
                 | POUR ID ASSIGN expression ID expression FAIRE indent_inc statements indent_dec FIN POUR SEMICOLON
                 | POUR ID ASSIGN expression ID expression FAIRE indent_inc statements indent_dec FIN_POUR SEMICOLON'''
    if p[5].lower() != 'a':
        from compiler.lexer import find_column
        parser_errors.append({
            "line": p.lineno(5),
            "column": 0,
            "message": f"Expected 'a' in Pour loop, got '{p[5]}'",
            "type": "Syntax Error",
            "error_code": "E2.3"
        })
    start_expr = p[4][0]
    end_expr = p[6][0]
    p[0] = f"{get_indent()}for {p[2]} in range({start_expr}, {end_expr} + 1):\n{p[9]}"

def p_condition(p):
    '''condition : expression'''
    p[0] = p[1][0]

def p_statement_repeat(p):
    '''statement : REPETER indent_inc statements indent_dec JUSQUA condition
                 | REPETER indent_inc statements indent_dec JUSQUA condition SEMICOLON'''
    p[0] = f"{get_indent()}while True:\n{p[3]}\n{get_indent()}    if {p[6]}:\n{get_indent()}        break"

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression MOD expression
                  | expression DIV expression
                  | expression EQUALS expression
                  | expression NEQUALS expression
                  | expression LT expression
                  | expression LE expression
                  | expression GT expression
                  | expression GE expression
                  | expression AND expression
                  | expression OR expression
                  | LPAREN expression RPAREN'''
    
    if len(p) == 4 and p[1] == '(':
         # Parentheses group
         p[0] = (f"({p[2][0]})", p[2][1])
         return

    op = p[2]
    code1, type1 = p[1]
    code2, type2 = p[3]
    
    res_type = 'UNKNOWN'
    
    # Check for pointer arithmetic: ptr + int or ptr - int
    # Also handle array + int (decay array to pointer)
    is_ptr_op = 'POINTEUR' in str(type1) or 'POINTEUR' in str(type2)
    is_array_op = 'TABLEAU' in str(type1) or 'TABLEAU' in str(type2)
    
    if (is_ptr_op or is_array_op) and op in ['+', '-']:
        # If array, convert to pointer for arithmetic
        if 'TABLEAU' in str(type1):
            # code1 is var_name. We need to make it a Pointer
            # But wait, code1 might be "t[i]" which is an element (ENTIER).
            # The type1 check should prevent this unless type1 really IS 'TABLEAU_...'
            # In p_expression_id, we return (var_name, var_type).
            # So if type1 is TABLEAU_ENTIER, code1 is just "t".
            var_name = code1
            code1 = f"Pointer(\"{var_name}\", locals(), index=0, base_var={var_name})"
            type1 = 'POINTEUR'
            
        if 'TABLEAU' in str(type2):
             var_name = code2
             code2 = f"Pointer(\"{var_name}\", locals(), index=0, base_var={var_name})"
             type2 = 'POINTEUR'
            
        p[0] = (f"{code1} {op} {code2}", type1 if 'POINTEUR' in str(type1) else type2)
        return

    if op in ['+', '-', '*', '/', 'mod', 'div']:
        if type1 in ['ENTIER', 'REEL'] and type2 in ['ENTIER', 'REEL']:
            if type1 == 'REEL' or type2 == 'REEL' or op == '/':
                 res_type = 'REEL'
            else:
                 res_type = 'ENTIER'
        # NOTE: String concatenation via + is NOT allowed.
        # Use Concat(s1, s2) function instead.
    elif op in ['=', '<>', '<', '<=', '>', '>=', 'et', 'ou', 'non']:
        res_type = 'BOOLEEN'

    op_lower = op.lower()
    if op_lower == '=': op = '=='
    if op_lower == '<>': op = '!='
    if op_lower == 'et': op = 'and'
    if op_lower == 'ou': op = 'or'
    if op_lower == 'mod': op = '%'
    if op_lower == 'div': op = '//'
    
    p[0] = (f"{code1} {op} {code2}", res_type)

def p_expression_unary(p):
    '''expression : NOT expression'''
    p[0] = (f"not ({p[2][0]})", 'BOOLEEN')

def p_expression_unary_minus(p):
    '''expression : MINUS expression %prec UMINUS'''
    p[0] = (f"-({p[2][0]})", p[2][1])

def p_expression_number(p):
    '''expression : NUMBER'''
    val = p[1]
    if isinstance(val, float):
        p[0] = (str(val), 'REEL')
    else:
        p[0] = (str(val), 'ENTIER')

def p_expression_id(p):
    '''expression : ID'''
    var_name = p[1]
    var_type, _ = find_variable(var_name)
    p[0] = (var_name, var_type)

def p_expression_string(p):
    '''expression : STRING_LITERAL'''
    p[0] = (repr(p[1]), 'CHAINE')

def p_expression_char(p):
    '''expression : CHAR_LITERAL'''
    p[0] = (repr(p[1]), 'CARACTERE_TYPE')

def p_expression_bool(p):
    '''expression : VRAI
                  | FAUX'''
    code = 'True' if p[1].lower() == 'vrai' else 'False'
    p[0] = (code, 'BOOLEEN_TYPE')

def p_expression_nil(p):
    '''expression : NIL'''
    p[0] = ('None', 'POINTEUR')

def p_expression_address(p):
    '''expression : AMPERSAND ID'''
    var_name = p[2]
    var_type, _ = find_variable(var_name)
    ns = "locals()" if is_local_scope() else "globals()"
    alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
    p[0] = (f"Pointer(\"{var_name}\", {ns}, alloc_name=\"{alloc_name}\")", f"POINTEUR_{var_type}")

def p_expression_address_array(p):
    '''expression : AMPERSAND ID LBRACKET expression RBRACKET'''
    var_name = p[2]
    idx_code = p[4][0]
    var_type, _ = find_variable(var_name)
    elem_type = 'UNKNOWN'
    if var_type.startswith('TABLEAU_'):
        elem_type = var_type.replace('TABLEAU_', '')
    elif var_type == 'CHAINE':
        elem_type = 'CARACTERE_TYPE'
    ns = "locals()" if is_local_scope() else "globals()"
    alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
    p[0] = (f"Pointer(\"{var_name}\", {ns}, index={idx_code}, base_var={var_name}, alloc_name=\"{alloc_name}\")", f"POINTEUR_{elem_type}")

def p_expression_address_matrix(p):
    '''expression : AMPERSAND ID LBRACKET expression RBRACKET LBRACKET expression RBRACKET'''
    var_name = p[2]
    idx1 = p[4][0]
    idx2 = p[7][0]
    var_type, _ = find_variable(var_name)
    elem_type = 'UNKNOWN'
    if var_type.startswith('MATRICE_'):
        elem_type = var_type.replace('MATRICE_', '')
    ns = "locals()" if is_local_scope() else "globals()"
    alloc_name = f"{scope_stack[-1]}.{var_name}" if is_local_scope() else var_name
    # To point to mat[i][j], the base_var is the specific row, index is j
    p[0] = (f"Pointer(\"{var_name}_row_\" + str({idx1}), {ns}, index={idx2}, base_var={var_name}[{idx1}], alloc_name=\"{alloc_name}\")", f"POINTEUR_{elem_type}")

def p_expression_dereference(p):
    '''expression : expression CARET'''
    expr_code, expr_type = p[1]
    
    # Get the value from the pointer (postfix notation: ptr^)
    if expr_type.upper().startswith('POINTEUR') or expr_type == 'UNKNOWN':
        base_type = expr_type.replace('POINTEUR_', '', 1).replace('^', '', 1) if expr_type.upper().startswith('POINTEUR') else 'UNKNOWN'
        
        # If pointing to a string/character array, dereferencing should return the string 
        # (until null terminator) instead of just the first char.
        if base_type.upper() in ('CHAINE', 'CHAINE_TYPE', 'CARACTERE', 'CARACTERE_TYPE', 'POINTEUR_CHAINE'):
             p[0] = (f'(({expr_code})._get_string() if hasattr({expr_code}, "_get_string") else ({expr_code})._get())', base_type.upper())
        else:
             p[0] = (f'({expr_code})._get()', base_type)
    else:
        p[0] = (f'({expr_code})._get()', 'UNKNOWN')


def p_expression_len(p):
    '''expression : LONGUEUR LPAREN expression RPAREN'''
    p[0] = (f"_algo_longueur({p[3][0]})", 'ENTIER')

def p_expression_allouer(p):
    '''expression : ALLOUER LPAREN expression RPAREN'''
    size_code, _ = p[3]
    # Detect allouer(taille(RecordTypeName)) at parse time and return a dict-backed Pointer
    import re
    m = re.match(r"_algo_taille\('([^']+)'\)", size_code.strip())
    if m:
        type_name = m.group(1)
        if type_name in record_types:
            # Build the initialised dict inline so the Pointer wraps a real record dict
            init_expr = _build_record_init(type_name)
            p[0] = (f"_algo_allouer_record({init_expr})", f"POINTEUR_{type_name}")
            return
    p[0] = (f"_algo_allouer({size_code})", 'POINTEUR')

def p_expression_taille(p):
    '''expression : TAILLE LPAREN type RPAREN'''
    p[0] = (f"_algo_taille('{p[3]}')", 'ENTIER')

def p_expression_concat(p):
    '''expression : CONCAT LPAREN expression COMMA expression RPAREN'''
    p[0] = (f"_algo_concat({p[3][0]}, {p[5][0]})", 'CHAINE')

def p_expression_list(p):
    '''expression_list : expression
                       | expression COMMA expression_list'''
    if len(p) == 2:
        p[0] = p[1][0]
    else:
        p[0] = f"{p[1][0]}, {p[3]}"

def p_value(p):
    '''value : NUMBER
             | STRING_LITERAL
             | VRAI
             | FAUX'''
    if p[1].lower() == 'vrai':
        p[0] = 'True'
    elif p[1].lower() == 'faux':
        p[0] = 'False'
    else:
        p[0] = str(p[1])

def p_expression_array_access(p):
    '''expression : ID LBRACKET expression RBRACKET'''
    var_name = p[1]
    idx_code = p[3][0]
    var_type, _ = find_variable(var_name)
    elem_type = 'UNKNOWN'
    if var_type.startswith('TABLEAU_'):
        elem_type = var_type.replace('TABLEAU_', '')
        p[0] = (f"{var_name}[{idx_code}]", elem_type)
    elif var_type.upper().startswith('MATRICE_CHAINE'):
        elem_type = 'CHAINE'
        p[0] = (f"{var_name}[{idx_code}]", elem_type)
    elif var_type == 'CHAINE':
        elem_type = 'CARACTERE_TYPE'
        p[0] = (f"_algo_get_char({var_name}, {idx_code})", elem_type)
    else:
        p[0] = (f"{var_name}[{idx_code}]", elem_type)

def p_expression_matrix_access(p):
    '''expression : ID LBRACKET expression RBRACKET LBRACKET expression RBRACKET'''
    var_name = p[1]
    idx1 = p[3][0]
    idx2 = p[6][0]
    mat_type, _ = find_variable(var_name)
    elem_type = 'UNKNOWN'
    if mat_type.upper().startswith('MATRICE_CHAINE'):
        elem_type = 'CARACTERE_TYPE'
        p[0] = (f"_algo_get_char({var_name}[{idx1}], {idx2})", elem_type)
    elif mat_type.startswith('MATRICE_'):
        elem_type = mat_type.replace('MATRICE_', '')
        p[0] = (f"{var_name}[{idx1}][{idx2}]", elem_type)
    else:
        p[0] = (f"{var_name}[{idx1}][{idx2}]", elem_type)

def p_statement_assign_array(p):
    '''statement : ID LBRACKET expression RBRACKET ASSIGN expression SEMICOLON'''
    var_name = p[1]
    idx_code = p[3][0]
    val_code = p[6][0]
    val_type = p[6][1]

    var_type, _ = find_variable(var_name)
    
    check_allocation_semantic(p, var_name, val_code, is_array_access=True)

    if var_type.upper() in ['CHAINE', 'CHAINE_TYPE']:
        # Single string var: character assignment
        if val_type == 'CHAINE':
            parser_errors.append({
                "line": p.lineno(1),
                "column": 0,
                "message": f"Type error: '{var_name}[{idx_code}]' attend un Caractere (guillemets simples 'X'), pas une Chaine. Utilisez: {var_name}[{idx_code}] <- 'X'",
                "type": "Semantic Error",
                "error_code": "E3.3"
            })
        p[0] = f"{get_indent()}{var_name} = _algo_set_char({var_name}, {idx_code}, {val_code})"
    elif var_type.upper().startswith('MATRICE_CHAINE'):
        # mots[i] := "word"  — assign a whole row of the word-matrix
        p[0] = f"{get_indent()}_algo_assign_fixed_string({var_name}[{idx_code}], {val_code})"
    elif 'POINTEUR_POINTEUR_CARACTERE' in var_type.upper() or 'POINTEUR_POINTEUR_CARACTERE_TYPE' in var_type.upper():
        # mots[i] := "word"  — for ^^Caractere: store a fresh char-array in the pointer slot
        # If it's a string literal, create a char-array from it
        # If it's an allocated pointer (_algo_allouer), store it directly
        if val_type in ('CHAINE', 'CHAINE_TYPE'):
            # Fill the already-allocated char-array with the string value
            p[0] = f"{get_indent()}_algo_assign_fixed_string({var_name}[{idx_code}], {val_code})"
        else:
            # allouer(...) or pointer — store as-is
            p[0] = f"{get_indent()}{var_name}[{idx_code}] = ({val_code})._clone() if hasattr({val_code}, '_clone') else {val_code}"
    else:
        p[0] = f"{get_indent()}{var_name}[{idx_code}] = ({val_code})._clone() if hasattr({val_code}, '_clone') else {val_code}"

def p_statement_assign_matrix(p):
    '''statement : ID LBRACKET expression RBRACKET LBRACKET expression RBRACKET ASSIGN expression SEMICOLON'''
    var_name = p[1]
    idx1, idx2, val = p[3][0], p[6][0], p[9][0]
    val_type = p[9][1]
    mat_type, _ = find_variable(var_name)
    mat_type = mat_type.upper()
    if mat_type.startswith('MATRICE_CHAINE'):
        # mots[i][j] := 'c'  — set one character inside a word-row
        if val_type in ('CHAINE', 'CHAINE_TYPE'):
            parser_errors.append({
                "line": p.lineno(1),
                "column": 0,
                "message": f"Erreur: '{var_name}[{p[3][0]}][{p[6][0]}]' attend un Caractere, pas une Chaine.",
                "type": "Semantic Error",
                "error_code": "E3.3"
            })
            p[0] = f"{get_indent()}pass  # blocked: string assigned to char slot"
        else:
            p[0] = f"{get_indent()}_algo_set_char({var_name}[{idx1}], {idx2}, {val})"

    elif 'POINTEUR_POINTEUR_CARACTERE' in mat_type:
        # ^^Caractere: mots[i][j] := 'c' is valid (set char in allocated word)
        # BUT mots[i][j] := "string" is an error
        if val_type in ('CHAINE', 'CHAINE_TYPE'):
            parser_errors.append({
                "line": p.lineno(1),
                "column": 0,
                "message": f"Erreur: '{var_name}[{idx1}][{idx2}]' attend un Caractere, pas une Chaine. Utilisez: {var_name}[{idx1}] <- \"mot\" pour assigner un mot entier.",
                "type": "Semantic Error",
                "error_code": "E3.3"
            })
            p[0] = f"{get_indent()}pass  # blocked: string assigned to char slot"
        else:
            # set a character in the dynamically allocated word
            p[0] = f"{get_indent()}_algo_set_char({var_name}[{idx1}], {idx2}, {val})"
    else:
        p[0] = f"{get_indent()}{var_name}[{idx1}][{idx2}] = ({val})._clone() if hasattr({val}, '_clone') else {val}"

# Error tracking
parser_errors = []

def p_error(p):
    if p:
        error_msg = f"Syntax error at '{p.value}'"
        from compiler.lexer import find_column
        col = find_column(p.lexer.lexdata, p)
        parser_errors.append({
            "line": p.lineno,
            "column": col,
            "message": error_msg,
            "type": "Syntax Error",
            "error_code": "E2.1"
        })
    else:
        parser_errors.append({
            "line": 0,
            "column": 0,
            "message": "Syntax error at EOF",
            "type": "Syntax Error",
            "error_code": "E2.2"
        })

def p_var_definition_error(p):
    '''var_definition : var_list error'''
    error_msg = f"Missing semicolon or invalid syntax after variable definition"
    from compiler.lexer import find_column
    col = find_column(p.lexer.lexdata, p.slice[2])
    parser_errors.append({
        "line": p.lineno(2),
        "column": col,
        "message": error_msg,
        "type": "Syntax Error",
        "error_code": "E2.4"
    })
    # Try to return valid code part so parsing continues
    # p[1] is (code, type)
    if isinstance(p[1], tuple):
         p[0] = f"{p[1][0]}\n"
    else:
         p[0] = ""

def p_statement_error(p):
    '''statement : error SEMICOLON'''
    error_msg = f"Syntax error in statement"
    from compiler.lexer import find_column
    col = find_column(p.lexer.lexdata, p.slice[1])
    parser_errors.append({
        "line": p.lineno(1),
        "column": col,
        "message": error_msg,
        "type": "Syntax Error",
        "error_code": "E2.4"
    })
    p[0] = ""


# Build the parser
parser = yacc.yacc(debug=True)

def compile_algo(code):
    global indent_level, symbol_table, scope_stack, parser_errors, current_subprogram_type, function_return_types
    indent_level = 0
    symbol_table = {'global': {}}
    scope_stack = ['global']
    function_return_types = {}
    current_subprogram_type = None
    parser_errors = []
    record_types.clear()   # Reset record type registry for each new compilation
    
    # Reset memory allocator for new compilation
    mem_alloc.__init__()
    
    from compiler.lexer import lexer, clear_lexer_errors, get_lexer_errors
    clear_lexer_errors()
    lexer.lineno = 1
    
    try:
        result = parser.parse(code, lexer=lexer)
    except Exception as e:
        import traceback
        with open("traceback_debug.txt", "w") as f:
            f.write(traceback.format_exc())
        return None, [{"line": 0, "column": 0, "message": str(e), "type": "Critical Error"}]
    
    all_errors = get_lexer_errors() + parser_errors
    return result, all_errors
