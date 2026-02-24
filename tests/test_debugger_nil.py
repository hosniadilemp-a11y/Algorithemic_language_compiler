import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from web.debugger import TraceRunner

code = """
promo = None
b = True
f = False
l = [1, None, 3]
"""

class MockFrame:
    def __init__(self, f_locals, f_globals, co_name='<module>'):
        self.f_locals = f_locals
        self.f_globals = f_globals
        self.f_code = type('Code', (), {'co_name': co_name, 'co_filename': '<string>'})
        self.f_lineno = 1

def test_nil():
    runner = TraceRunner()
    # We need to simulate the environment enough for TraceRunner.trace_lines
    # TraceRunner.run does exec() which is better
    
    # Mock _algo_vars_info to ensure variables are picked up
    exec_globals = {
        '_algo_vars_info': {
            'promo': {'addr': 1000, 'type': 'POINTEUR_ENTIER'},
            'b': {'addr': 1004, 'type': 'BOOLEEN'},
            'f': {'addr': 1005, 'type': 'BOOLEEN'},
            'l': {'addr': 1006, 'type': 'TABLEAU_ENTIER_3'},
            '_algo_heap': {'2000': {'id': 103, 'nom': 'Zizou', 'note': 14.5, 'suiv': None}}
        },
        '_algo_heap': {'2000': {'id': 103, 'nom': 'Zizou', 'note': 14.5, 'suiv': None}},
        '_algo_heap_types': {2000: 'ETUDIANT'}
    }
    
    steps = runner.run(code, exec_globals)
    last_step = steps[-1]
    vars = last_step['variables']
    
    print(f"promo: {vars['promo']['value']}")
    print(f"heap_2000: {vars['heap_2000']['value']}")
    
    assert vars['promo']['value'] == 'NIL'
    assert 'NIL' in vars['heap_2000']['value']
    assert 'None' not in vars['heap_2000']['value']
    print("SUCCESS: Record fields also use NIL!")

if __name__ == "__main__":
    test_nil()
