# Algo: Gestion_Bibliotheque_Municipale
import sys
import builtins

# Helper functions (dependency order)
_algo_input_buffer = []
def _algo_read():
    global _algo_input_buffer
    while True:
        if _algo_input_buffer:
            return _algo_input_buffer.pop(0)
        try:
            line = input()
        except EOFError:
            return ''
        if line is None:
            return ''
        parts = str(line).strip().split()
        if parts:
            _algo_input_buffer.extend(parts)

def _algo_ecrire(*args):
    parts = []
    for a in args:
        s = _algo_to_string(a)
        # Display #0 as the visible null sentinel
        s = s.replace('#0', chr(0))
        s = s.replace('\\n', '\n').replace('\\t', '\t')
        parts.append(s)
    print(' '.join(parts), end='')

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
        s = str(input_val).lower()
        if s in ['vrai', 'true', '1']: return True
        if s in ['faux', 'false', '0']: return False
        raise ValueError(f"Type mismatch: '{input_val}' n'est pas un Booleen valide.")
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

def _algo_allouer(size_in_bytes, element_size=1):
    global _algo_heap_next_addr
    addr = _algo_heap_next_addr
    _algo_heap_next_addr += size_in_bytes
    num_elements = size_in_bytes // element_size if element_size > 0 else size_in_bytes
    allocated_list = [None] * max(1, num_elements)
    _algo_heap[addr] = allocated_list
    _algo_vars_info[f'_heap_{addr}'] = {'addr': addr, 'size': size_in_bytes, 'element_size': element_size}
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

_algo_record_sizes = {'Auteur': 88, 'Livre': 97, 'Adherent': 50, 'Pret': 15}

def _algo_taille(type_name):
    t = type_name.lower()
    if 'pointeur' in t or t.startswith('^'): return 1
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
_algo_vars_info = {"Init_Auteur.a": {"addr": 1000, "size": 88, "element_size": 88, "type": "Auteur"}, "Init_Auteur.id": {"addr": 1088, "size": 4, "element_size": 4, "type": "Entier"}, "Init_Auteur.nom": {"addr": 1092, "size": 1, "element_size": 1, "type": "Chaine"}, "Init_Auteur.nat": {"addr": 1093, "size": 1, "element_size": 1, "type": "Chaine"}, "Init_Livre.l": {"addr": 1094, "size": 97, "element_size": 97, "type": "Livre"}, "Init_Livre.code": {"addr": 1191, "size": 1, "element_size": 1, "type": "Chaine"}, "Init_Livre.tit": {"addr": 1192, "size": 1, "element_size": 1, "type": "Chaine"}, "Init_Livre.auth": {"addr": 1193, "size": 4, "element_size": 4, "type": "Entier"}, "Init_Livre.y": {"addr": 1197, "size": 4, "element_size": 4, "type": "Entier"}, "Init_Livre.p": {"addr": 1201, "size": 8, "element_size": 8, "type": "Reel"}, "Booleen_Peut_Emprunter.a": {"addr": 1209, "size": 50, "element_size": 50, "type": "Adherent"}, "Entier_Chercher_Auteur.catalogue": {"addr": 1259, "size": 440, "element_size": 88, "type": "TABLEAU_5"}, "Entier_Chercher_Auteur.n": {"addr": 1699, "size": 4, "element_size": 4, "type": "Entier"}, "Entier_Chercher_Auteur.id": {"addr": 1703, "size": 4, "element_size": 4, "type": "Entier"}, "Entier_Chercher_Auteur.i": {"addr": 1707, "size": 4, "element_size": 4, "type": "Entier"}, "Enregistrer_Pret.p": {"addr": 1711, "size": 15, "element_size": 15, "type": "Pret"}, "Enregistrer_Pret.l": {"addr": 1726, "size": 97, "element_size": 97, "type": "Livre"}, "Enregistrer_Pret.a": {"addr": 1823, "size": 50, "element_size": 50, "type": "Adherent"}, "Enregistrer_Pret.d": {"addr": 1873, "size": 1, "element_size": 1, "type": "Chaine"}, "Traiter_Retour.p": {"addr": 1874, "size": 15, "element_size": 15, "type": "Pret"}, "Traiter_Retour.l": {"addr": 1889, "size": 97, "element_size": 97, "type": "Livre"}, "Traiter_Retour.a": {"addr": 1986, "size": 50, "element_size": 50, "type": "Adherent"}, "Afficher_Details_Livre.l": {"addr": 2036, "size": 97, "element_size": 97, "type": "Livre"}, "Afficher_Details_Livre.cat_auth": {"addr": 2133, "size": 440, "element_size": 88, "type": "TABLEAU_5"}, "Afficher_Details_Livre.n_auth": {"addr": 2573, "size": 4, "element_size": 4, "type": "Entier"}, "Afficher_Details_Livre.idx": {"addr": 2577, "size": 4, "element_size": 4, "type": "Entier"}, "Afficher_Bilan_Adherent.a": {"addr": 2581, "size": 50, "element_size": 50, "type": "Adherent"}, "Reel_Calculer_Valeur_Stock.stock": {"addr": 2631, "size": 970, "element_size": 97, "type": "TABLEAU_10"}, "Reel_Calculer_Valeur_Stock.n": {"addr": 3601, "size": 4, "element_size": 4, "type": "Entier"}, "Reel_Calculer_Valeur_Stock.i": {"addr": 3605, "size": 4, "element_size": 4, "type": "Entier"}, "Reel_Calculer_Valeur_Stock.total": {"addr": 3609, "size": 8, "element_size": 8, "type": "Reel"}, "Rechercher_Par_Auteur.auth_nom": {"addr": 3617, "size": 1, "element_size": 1, "type": "Chaine"}, "Rechercher_Par_Auteur.stock": {"addr": 3618, "size": 970, "element_size": 97, "type": "TABLEAU_10"}, "Rechercher_Par_Auteur.n": {"addr": 4588, "size": 4, "element_size": 4, "type": "Entier"}, "Rechercher_Par_Auteur.cat_auth": {"addr": 4592, "size": 440, "element_size": 88, "type": "TABLEAU_5"}, "Rechercher_Par_Auteur.na": {"addr": 5032, "size": 4, "element_size": 4, "type": "Entier"}, "Rechercher_Par_Auteur.idx_a": {"addr": 5036, "size": 4, "element_size": 4, "type": "Entier"}, "Rechercher_Par_Auteur.id_a": {"addr": 5040, "size": 4, "element_size": 4, "type": "Entier"}, "Rechercher_Par_Auteur.i": {"addr": 5044, "size": 4, "element_size": 4, "type": "Entier"}, "les_auteurs": {"addr": 5048, "size": 440, "element_size": 88, "type": "Auteur"}, "le_stock": {"addr": 5488, "size": 970, "element_size": 97, "type": "Livre"}, "les_membres": {"addr": 6458, "size": 250, "element_size": 50, "type": "Adherent"}, "les_prets": {"addr": 6708, "size": 150, "element_size": 15, "type": "Pret"}, "valeur_totale": {"addr": 6858, "size": 8, "element_size": 8, "type": "Reel"}, "i": {"addr": 6866, "size": 4, "element_size": 4, "type": "Entier"}}


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
                stride = info.get('element_size', 1)
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


les_auteurs = [{'identifiant': 0, 'nom_complet': ['\0'] * 50, 'nationalite': ['\0'] * 30, 'nombre_oeuvres': 0} for _ in range(5)] # Tableau de Auteur
le_stock = [{'isbn': ['\0'] * 20, 'titre': ['\0'] * 60, 'id_auteur': 0, 'annee_pub': 0, 'est_dispo': False, 'prix_u': 0.0} for _ in range(10)] # Tableau de Livre
les_membres = [{'num_carte': 0, 'nom': ['\0'] * 40, 'date_adh': "", 'livres_en_main': 0, 'suspendu': False} for _ in range(5)] # Tableau de Adherent
les_prets = [{'id_pret': 0, 'isbn_livre': "", 'id_adherent': 0, 'date_depart': "", 'rendu': False, 'delai_jours': 0} for _ in range(10)] # Tableau de Pret
valeur_totale = 0.0 # Reel
i = 0 # Entier


def Init_Auteur(a, id, nom, nat):
    _tmp_val = id
    a['identifiant'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    _tmp_val = nom
    a['nom_complet'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    _tmp_val = nat
    a['nationalite'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    _tmp_val = 0
    a['nombre_oeuvres'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val

def Init_Livre(l, code, tit, auth, y, p):
    _tmp_val = code
    l['isbn'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    _tmp_val = tit
    l['titre'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    _tmp_val = auth
    l['id_auteur'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    _tmp_val = y
    l['annee_pub'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    _tmp_val = p
    l['prix_u'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
    _tmp_val = True
    l['est_dispo'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val

def Booleen_Peut_Emprunter(a):
    if a['suspendu']:
        return (False)
    if a['livres_en_main'] >= 3:
        return (False)
    return (True)

def Entier_Chercher_Auteur(catalogue, n, id):
    i = 0 # Entier

    for i in range(0, n - 1 + 1):
        if catalogue[i]['identifiant'] == id:
            return (i)
    return (-(1))

def Enregistrer_Pret(p, l, a, d):
    if l['est_dispo'] and Booleen_Peut_Emprunter(a):
        _tmp_val = 5000 + a['num_carte']
        p['id_pret'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
        _tmp_val = l['isbn']
        p['isbn_livre'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
        _tmp_val = a['num_carte']
        p['id_adherent'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
        _tmp_val = d
        p['date_depart'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
        _tmp_val = False
        p['rendu'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
        _tmp_val = 15
        p['delai_jours'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
        _tmp_val = False
        l['est_dispo'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
        _tmp_val = a['livres_en_main'] + 1
        a['livres_en_main'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
        _algo_ecrire('[SUCCES] Pret enregistre pour ')
        _algo_ecrire(a['nom'])
        _algo_ecrire('\n')
    else:
        _algo_ecrire("[ERREUR] Impossible d'emprunter ")
        _algo_ecrire(l['titre'])
        _algo_ecrire('\n')

def Traiter_Retour(p, l, a):
    if p['rendu'] == False:
        _tmp_val = True
        p['rendu'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
        _tmp_val = True
        l['est_dispo'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
        _tmp_val = a['livres_en_main'] - 1
        a['livres_en_main'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
        _algo_ecrire('[RETOUR] Livre ')
        _algo_ecrire(l['titre'])
        _algo_ecrire(' rendu par ')
        _algo_ecrire(a['nom'])
        _algo_ecrire('\n')

def Afficher_Details_Livre(l, cat_auth, n_auth):
    idx = 0 # Entier

    idx = Entier_Chercher_Auteur(cat_auth, n_auth, l['id_auteur'])
    _algo_ecrire('* TITRE : ')
    _algo_ecrire(l['titre'])
    _algo_ecrire(' (ISBN: ')
    _algo_ecrire(l['isbn'])
    _algo_ecrire(')\n')
    if idx != -(1):
        _algo_ecrire('  AUTEUR: ')
        _algo_ecrire(cat_auth[idx]['nom_complet'])
        _algo_ecrire(' [')
        _algo_ecrire(cat_auth[idx]['nationalite'])
        _algo_ecrire(']\n')
    _algo_ecrire('  ETAT  : ')
    if l['est_dispo']:
        _algo_ecrire('DISPONIBLE\n')
    else:
        _algo_ecrire('EMPRUNTE\n')

def Afficher_Bilan_Adherent(a):
    _algo_ecrire('Adherent : ')
    _algo_ecrire(a['nom'])
    _algo_ecrire(' (Carte n°')
    _algo_ecrire(a['num_carte'])
    _algo_ecrire(')\n')
    _algo_ecrire('   Livres actifs : ')
    _algo_ecrire(a['livres_en_main'])
    _algo_ecrire('\n')
    if a['suspendu']:
        _algo_ecrire('   *** STATUT : SUSPENDU ***\n')

def Reel_Calculer_Valeur_Stock(stock, n):
    i = 0 # Entier
    total = 0.0 # Reel

    total = 0.0
    for i in range(0, n - 1 + 1):
        total = total + stock[i]['prix_u']
    return (total)

def Rechercher_Par_Auteur(auth_nom, stock, n, cat_auth, na):
    i = 0
    id_a = 0
    idx_a = 0 # Entier

    _algo_ecrire("\nResultats pour l'auteur : ")
    _algo_ecrire(auth_nom)
    _algo_ecrire('\n')
    for i in range(0, na - 1 + 1):
        if cat_auth[i]['nom_complet'] == auth_nom:
            id_a = cat_auth[i]['identifiant']
            for j in range(0, n - 1 + 1):
                if stock[j]['id_auteur'] == id_a:
                    _algo_ecrire('  - ')
                    _algo_ecrire(stock[j]['titre'])
                    _algo_ecrire('\n')


Init_Auteur(les_auteurs[0], 1, 'Victor Hugo', 'Francais')
Init_Auteur(les_auteurs[1], 2, 'Albert Camus', 'Francais')
Init_Auteur(les_auteurs[2], 3, 'Kateb Yacine', 'Algerien')
Init_Livre(le_stock[0], '978-2070409', 'Les Miserables', 1, 1862, 25.5)
Init_Livre(le_stock[1], '978-2070360', "L'Etranger", 2, 1942, 12.0)
Init_Livre(le_stock[2], '978-2020228', 'Nedjma', 3, 1956, 18.0)
Init_Livre(le_stock[3], '978-2070410', 'Notre-Dame de Paris', 1, 1831, 22.0)
_tmp_val = 1001
les_membres[0]['num_carte'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
_tmp_val = 'Samy'
les_membres[0]['nom'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
_tmp_val = 0
les_membres[0]['livres_en_main'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
_tmp_val = False
les_membres[0]['suspendu'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
_tmp_val = 1002
les_membres[1]['num_carte'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
_tmp_val = 'Amine'
les_membres[1]['nom'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
_tmp_val = 2
les_membres[1]['livres_en_main'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
_tmp_val = True
les_membres[1]['suspendu'] = _tmp_val._clone() if hasattr(_tmp_val, '_clone') else _tmp_val
_algo_ecrire('=== LOGICIEL DE GESTION DE BIBLIOTHEQUE ===\n')
_algo_ecrire('\nInventaire actuel :\n')
Afficher_Details_Livre(le_stock[0], les_auteurs, 3)
Afficher_Details_Livre(le_stock[1], les_auteurs, 3)
Afficher_Details_Livre(le_stock[2], les_auteurs, 3)
_algo_ecrire('\n--- Simulation de transaction ---\n')
Enregistrer_Pret(les_prets[0], le_stock[0], les_membres[0], '23/02/2026')
Enregistrer_Pret(les_prets[1], le_stock[2], les_membres[1], '23/02/2026')
Rechercher_Par_Auteur('Victor Hugo', le_stock, 4, les_auteurs, 3)
_algo_ecrire('\nBilan Adherent Samy :\n')
Afficher_Bilan_Adherent(les_membres[0])
valeur_totale = Reel_Calculer_Valeur_Stock(le_stock, 4)
_algo_ecrire('\nValeur patrimoniale de la bibliotheque : ')
_algo_ecrire(valeur_totale)
_algo_ecrire(' Euros\n')
_algo_ecrire('\nExécution terminée.\n')
