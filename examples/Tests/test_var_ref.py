# Algo: TestVarRef
import sys
import builtins

# Helper functions (dependency order)
def _algo_read():
    try:
        return input()
    except EOFError:
        return ''

def _algo_ecrire(*args):
    import sys
    parts = []
    for a in args:
        s = _algo_to_string(a)
        # Display #0 as the visible null sentinel
        s = s.replace('#0', chr(0))
        s = s.replace('\\n', '\n').replace('\\t', '\t')
        parts.append(s)
    sys.stdout.write(' '.join(parts))
    sys.stdout.flush()

def _algo_to_string(val):
    if val is None: return 'NIL'
    if isinstance(val, bool): return 'Vrai' if val else 'Faux'
    if isinstance(val, list):
        res = ''
        for char in val:
            if char is None or char == '\0' or char == '#0': break
            res += str(char)
        return res
    return str(val)

def _algo_deref_to_list(target):
    # Dereference a Pointer to get its backing list
    if hasattr(target, 'base_var') and target.base_var is not None:
        return target.base_var
    if hasattr(target, 'get_target_container'):
        try: return target.get_target_container()
        except: pass
    return target

def _algo_assign_fixed_string(target_list, source_val):
    target_list = _algo_deref_to_list(target_list)
    if not isinstance(target_list, list):
        raise TypeError('Variable Chaine non initialisee. Declarez avec s[N]: Chaine.')
    limit = len(target_list)
    s_val = ''
    if hasattr(source_val, '_get_target_container'):
        targ = source_val._get_target_container()
        while hasattr(targ, '_get_target_container'): targ = targ._get_target_container()
        if isinstance(targ, list):
            s_val = _algo_to_string(targ[source_val.index:])
        else:
            s_val = _algo_to_string(source_val._get_string() if hasattr(source_val, '_get_string') else source_val._get())
    else:
        s_val = _algo_to_string(source_val)
    if limit > 0:
        s_val = s_val[:limit-1]
        for i in range(len(s_val)):
            target_list[i] = s_val[i]
        target_list[len(s_val)] = '#0'
        for i in range(len(s_val)+1, limit):
            target_list[i] = None
    return target_list

def _algo_longueur(val):
    return len(_algo_to_string(val))

def _algo_set_char(target_list, index, char_val):
    target_list = _algo_deref_to_list(target_list)
    if not isinstance(target_list, list):
        raise TypeError(f'Cannot set char: not a list (got {type(target_list).__name__})')
    idx = int(index)  # 0-based index
    if 0 <= idx < len(target_list):
        if char_val == '#0' or char_val is None:
            target_list[idx] = '#0'
        else:
            target_list[idx] = str(char_val)[0]
    return target_list

def _algo_get_char(target_list, index):
    target_list = _algo_deref_to_list(target_list)
    if isinstance(target_list, list):
        idx = int(index)  # 0-based index
        if 0 <= idx < len(target_list):
            c = target_list[idx]
            return c if c is not None and c != '#0' else '#0'
        return ''
    s = str(target_list)
    idx = int(index)
    return s[idx] if 0 <= idx < len(s) else ''

def _algo_concat(val1, val2):
    s1 = _algo_to_string(val1)
    s2 = _algo_to_string(val2)
    # Stop at #0 null terminator in plain strings
    s1 = s1.split('#0')[0] if '#0' in s1 else s1
    s2 = s2.split('#0')[0] if '#0' in s2 else s2
    return s1 + s2

def _algo_make_string(s, max_size=256):
    s = str(s) if not isinstance(s, str) else s
    s = s[:max_size - 1]  # leave room for #0
    arr = [None] * max_size
    for i, c in enumerate(s):
        arr[i] = c
    arr[len(s)] = '#0'
    return arr

def _algo_read_typed(current_val, input_val=None, target_type_name='CHAINE'):
    if input_val is None: input_val = _algo_read()
    t = target_type_name.upper()
    if 'CHAINE' in t:
        if isinstance(current_val, list):
            _algo_assign_fixed_string(current_val, input_val)
            return current_val
        return str(input_val)
    if 'BOOLEEN' in t or isinstance(current_val, bool):
        return str(input_val).lower() in ['vrai', 'true', '1']
    elif 'ENTIER' in t or isinstance(current_val, int):
        try: return int(input_val)
        except:
            raise ValueError(f"Type mismatch: '{input_val}' n'est pas un Entier valide.")
    elif 'REEL' in t or isinstance(current_val, float):
        try: return float(input_val)
        except:
            raise ValueError(f"Type mismatch: '{input_val}' n'est pas un Reel valide.")
    return input_val

_algo_heap = {}
_algo_heap_next_addr = 50000

def _algo_allouer(size_in_bytes):
    global _algo_heap_next_addr
    addr = _algo_heap_next_addr
    _algo_heap_next_addr += size_in_bytes
    allocated_list = [None] * max(1, size_in_bytes)
    _algo_heap[addr] = allocated_list
    ptr = Pointer(var_name=f'_heap_{addr}', namespace=_algo_heap, index=0, base_var=allocated_list)
    ptr._heap_addr = addr
    return ptr

def _algo_liberer(ptr):
    if ptr and hasattr(ptr, '_heap_addr'):
        addr = ptr._heap_addr
        if addr in _algo_heap:
            del _algo_heap[addr]
            ptr.base_var = None
            ptr.var_name = None

_algo_record_sizes = {'Monome': 16}

def _algo_taille(type_name):
    t = type_name.lower()
    if 'pointeur' in t or t.startswith('^'): return 8
    if 'entier' in t: return 4
    if 'reel' in t: return 8
    if 'booleen' in t: return 1
    if 'caractere' in t: return 1
    if 'chaine' in t: return 1
    # User-defined record type — uses precomputed sizes
    if type_name in _algo_record_sizes: return _algo_record_sizes[type_name]
    return 4

def _algo_allouer_record(record_dict):
    global _algo_heap_next_addr
    addr = _algo_heap_next_addr
    _algo_heap_next_addr += 1
    _algo_heap[addr] = record_dict
    ptr = Pointer(var_name=None, namespace=None, index=0, base_var=record_dict)
    ptr._heap_addr = addr
    return ptr

global _algo_vars_info
_algo_vars_info = {"Init.P": {"addr": 1000, "size": 8, "element_size": 8, "type": "POINTEUR_POINTEUR_Monome"}, "Init.m": {"addr": 1008, "size": 8, "element_size": 8, "type": "POINTEUR_Monome"}, "Test.R": {"addr": 1016, "size": 8, "element_size": 8, "type": "POINTEUR_Monome"}, "Root": {"addr": 1024, "size": 8, "element_size": 8, "type": "POINTEUR_Monome"}}


class Pointer:
    def __init__(self, var_name=None, namespace=None, index=0, base_var=None):
        self.var_name = var_name
        self.namespace = namespace if namespace is not None else {}
        self.index = index
        self.base_var = base_var

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
    
    def __add__(self, offset):
        return Pointer(self.var_name, self.namespace, self.index + int(offset), self.base_var)

    def __sub__(self, offset):
        return Pointer(self.var_name, self.namespace, self.index - int(offset), self.base_var)

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
            if self.var_name in _algo_vars_info:
                info = _algo_vars_info[self.var_name]
                base = info['addr']
                stride = info.get('element_size', 4)
                addr = base + (self.index * stride)
                return f"@{addr}"
            else:
                return f"@{self.var_name}+{self.index}"

        except:
            return "UNKNOWN"

    def __repr__(self):
        return str(self)

    def __getitem__(self, i):
        return (self + i)._get()

    def __setitem__(self, i, value):
        (self + i)._set(value)


def Init(P):
    m = None # POINTEUR_Monome

    _tmp_m = _algo_allouer_record({'coeff': 0.0, 'suiv': None})
    m = Pointer("m_ptr_src", locals(), index=0, base_var=_tmp_m) if isinstance(_tmp_m, list) and not hasattr(_tmp_m, '_get_target_container') else _tmp_m
    (m)._get()['coeff'] = 5.0
    (m)._get()['suiv'] = None
    P._set(m)

def Test():
    R = None # POINTEUR_Monome

    _tmp_R = None
    R = Pointer("R_ptr_src", locals(), index=0, base_var=_tmp_R) if isinstance(_tmp_R, list) and not hasattr(_tmp_R, '_get_target_container') else _tmp_R
    Init(Pointer("R", locals()))
    _algo_ecrire('Inside Fonction, R^.coeff: ', (R)._get()['coeff'])
    return (R)

Root = None # POINTEUR_Monome




_tmp_Root = Test()
Root = Pointer("Root_ptr_src", globals(), index=0, base_var=_tmp_Root) if isinstance(_tmp_Root, list) and not hasattr(_tmp_Root, '_get_target_container') else _tmp_Root
if Root != None:
    _algo_ecrire('Root^.coeff: ', (Root)._get()['coeff'])
