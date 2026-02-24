import sys
import copy

class TraceRunner:
    def __init__(self):
        self.steps = []
        self.stdout_capture = None
        self.step_count = 0
        self.max_steps = 1000000  # Protect against infinite loops
    
    def trace_calls(self, frame, event, arg):
        if event != 'call':
            return
        return self.trace_lines

    def trace_lines(self, frame, event, arg):
        self.step_count += 1
        if self.step_count > self.max_steps:
            raise TimeoutError("Boucle infinie détectée")
            
        if event not in ['line', 'return']:
            return
        
        # Skip internal helper functions (like _algo_read)
        if frame.f_code.co_name.startswith('_'):
             return None

        # Filter out system/library frames
        co = frame.f_code
        filename = co.co_filename
        if filename != '<string>':
            return
        
        # Capture locals
        try:
            def format_algo_value(val):
                if val is None: return 'NIL'
                if isinstance(val, bool): return 'Vrai' if val else 'Faux'
                if isinstance(val, list):
                    items = [format_algo_value(i) for i in val]
                    return "[" + ", ".join(items) + "]"
                if isinstance(val, dict):
                    items = [f"'{k}': {format_algo_value(v)}" for k, v in val.items()]
                    return "{" + ", ".join(items) + "}"
                return str(val)

            local_vars = {}
            
            # Try to import Pointer class and address helper dynamically
            Pointer = None
            get_simulated_address = None
            try:
                import sys
                import os
                # Add parent directory to path
                parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                from compiler.parser import Pointer
            except ImportError:
                pass  # Pointer class not available
            
            # Get simulated address function from the executing code's globals
            if 'frame' in dir() and hasattr(frame, 'f_globals'):
                get_simulated_address = frame.f_globals.get('_get_simulated_address')

            # Retrieve memory map from globals
            mem_map = frame.f_globals.get('_algo_vars_info', {})
            
            func_name = frame.f_code.co_name
            is_global = (func_name == '<module>')
            
            vars_to_process = []
            if is_global:
                for k, v in frame.f_locals.items():
                    vars_to_process.append((k, v, k, k))
            else:
                for k, v in frame.f_globals.items():
                    if k in mem_map and '.' not in k:
                        vars_to_process.append((k, v, k, k))
                for k, v in frame.f_locals.items():
                    vars_to_process.append((k, v, f"{func_name}.{k}", f"_{func_name}.{k}"))

            for original_k, v, map_key, display_key in vars_to_process:
                if original_k.startswith('_'): continue # Hide internal vars like _raw_input, __builtins__
                if original_k in ['builtins', '__builtins__', 'sys', 'Pointer']: continue
                if callable(v): continue
                
                var_address = '-'
                python_type = type(v).__name__
                algo_type = python_type
                
                # Map to Algo types
                if python_type == 'int': algo_type = 'Entier'
                elif python_type == 'float': algo_type = 'Reel'
                elif python_type == 'bool': algo_type = 'Booleen'
                elif python_type == 'str': algo_type = 'Chaine'
                elif python_type == 'list': algo_type = 'Tableau'
                
                # Resolve address and static type from map if available
                if map_key in mem_map:
                    var_address = f"@{mem_map[map_key]['addr']}"
                    # Prefer declared type if available (e.g. for Arrays)
                    if 'type' in mem_map[map_key]:
                         declared_type = mem_map[map_key]['type']
                         # Clean up internal names
                         if declared_type.endswith('_TYPE'):
                             declared_type = declared_type[:-5]
                         if declared_type.startswith('TABLEAU_'):
                             declared_type = f"Tableau ({declared_type[8:]})"
                         if declared_type.startswith('MATRICE_'):
                             declared_type = f"Matrice ({declared_type[8:]})"
                         if declared_type == 'CHAINE':
                             declared_type = 'Chaine'
                         algo_type = declared_type.title()

                # Special handling for Pointer objects
                if Pointer and isinstance(v, Pointer):
                     algo_type = 'Pointeur'
                     # Make sure target address gets properly mapped when referencing array
                     target_address = str(v)
                     val_str = target_address
                     var_size = 1
                     if map_key in mem_map and 'size' in mem_map[map_key]:
                         var_size = mem_map[map_key]['size']
                         
                     local_vars[display_key] = {
                         'value': val_str,
                         'address': var_address,
                         'type': algo_type,
                         'size': var_size
                     }
                     # If it points to a base array directly (array decay), we can append extra info or just leave it
                     continue
                
                var_size = '-'
                try:
                    # Use simulated taille for sizes
                    if algo_type == 'Entier': var_size = 4
                    elif algo_type == 'Reel': var_size = 8
                    elif algo_type == 'Booleen': var_size = 1
                    elif algo_type == 'Caractere': var_size = 1
                    elif isinstance(v, list) and 'Chaine' in algo_type:
                        var_size = len(v) * 1  # 1 byte per character slot
                    elif isinstance(v, list) and 'Tableau' in algo_type:
                        var_size = len(v) * 4  # default 4 bytes per element
                    elif isinstance(v, str):
                        if '#0' in v:
                            var_size = v.index('#0')  # length up to null terminator
                        else:
                            var_size = len(v)
                            
                    if map_key in mem_map and 'size' in mem_map[map_key]:
                        var_size = mem_map[map_key]['size']
                    
                    local_vars[display_key] = {
                        'value': format_algo_value(v),
                        'address': var_address,
                        'type': algo_type,
                        'size': var_size
                    }
                except:
                    local_vars[display_key] = {
                        'value': format_algo_value(v),
                        'address': var_address,
                        'type': 'unknown',
                        'size': '-'
                    }
            
            # Extract and format dynamically allocated memory chunks from _algo_heap
            algo_heap = frame.f_globals.get('_algo_heap', {})
            
            # Infer types for heap chunks by tracing pointers in globals and locals
            ptr_types = {}
            # 1. Start from named variables
            all_vars = {**frame.f_globals, **frame.f_locals}
            for k, v in all_vars.items():
                if hasattr(v, '_heap_addr') and v._heap_addr:
                    if k in mem_map:
                        ptype = mem_map[k].get('type', '')
                        if ptype.upper().startswith('POINTEUR_'):
                            ptr_types[int(v._heap_addr)] = ptype[9:] # remove POINTEUR_

            # 2. Trace pointers inside known heap blocks to type sub-allocations (like matrices)
            for _ in range(2): # 2 passes to handle nested pointers up to double pointers
                for heap_addr_str, heap_list in algo_heap.items():
                    h_addr = int(heap_addr_str)
                    if h_addr in ptr_types:
                        base = ptr_types[h_addr]
                        if base.upper().startswith('POINTEUR_'):
                            subtype = base[9:]
                            # elements should be pointers, register their targets
                            for item in heap_list:
                                if hasattr(item, '_heap_addr') and item._heap_addr:
                                    ptr_types[int(item._heap_addr)] = subtype

            # Persist inferred types across steps so orphaned memory retains its type
            algo_heap_types = frame.f_globals.get('_algo_heap_types', {})
            for addr, ptype in ptr_types.items():
                algo_heap_types[addr] = ptype
            if '_algo_heap_types' not in frame.f_globals:
                frame.f_globals['_algo_heap_types'] = algo_heap_types
            
            ptr_types = algo_heap_types

            for heap_addr, heap_list in algo_heap.items():
                heap_addr_int = int(heap_addr)
                
                dyn_type = "Dynamique"
                elem_size = 1 # default bytes for unknown
                
                if heap_addr_int in ptr_types:
                    base_type = ptr_types[heap_addr_int]
                    if base_type.upper().startswith('POINTEUR_'):
                        dyn_type = "^" + base_type.replace('POINTEUR_', '')
                        elem_size = 1
                    elif 'ENTIER' in base_type.upper():
                        dyn_type = "Entier"
                        elem_size = 4
                    elif 'REEL' in base_type.upper():
                        dyn_type = "Reel"
                        elem_size = 8
                    elif 'BOOLEEN' in base_type.upper():
                        dyn_type = "Booleen"
                        elem_size = 1
                    elif 'CARACTERE' in base_type.upper():
                        dyn_type = "Caractere"
                        elem_size = 1

                # -----------------------------------------------
                # Record-backed heap entry (dict from allouer_record)
                # -----------------------------------------------
                if isinstance(heap_list, dict):
                    num_fields = len(heap_list)
                    # Determine type name from inferred ptr_types
                    rec_type_name = "Enregistrement"
                    if heap_addr_int in ptr_types:
                        bt = ptr_types[heap_addr_int]
                        if bt.startswith('POINTEUR_'):
                            rec_type_name = bt.replace('POINTEUR_', '')
                    
                    # Get actual byte size from precomputed table if available
                    algo_record_sizes = frame.f_globals.get('_algo_record_sizes', {})
                    actual_byte_size = algo_record_sizes.get(rec_type_name, num_fields * 4)
                    
                    fields_to_format = list(heap_list.items())[:4]
                    field_summary = ", ".join(
                        f"{k}={format_algo_value(v)}" for k, v in fields_to_format
                    )
                    if num_fields > 4:
                        field_summary += ", ..."
                    
                    local_vars[f"heap_{heap_addr}"] = {
                        'name': f"Enregistrement alloue",
                        'value': f"{{{field_summary}}}",
                        'address': f"@{heap_addr}",
                        'type': rec_type_name,
                        'size': actual_byte_size
                    }
                    continue
                
                # Truncate Python list back to logical element count (size // elem_size)
                logical_count = len(heap_list) // elem_size if elem_size > 0 else len(heap_list)
                display_list = heap_list[:logical_count]
                
                # Treat Array of Characters as a visible array
                if dyn_type == "Caractere":
                    display_type = "Tableau (Caractere)"
                    display_val = format_algo_value(display_list)
                elif logical_count == 1:
                    display_type = f"Valeur ({dyn_type})"
                    display_val = format_algo_value(display_list[0]) if display_list else "NIL"
                else:
                    display_type = f"Tableau ({dyn_type})"
                    display_val = format_algo_value(display_list)
                
                local_vars[f"heap_{heap_addr}"] = {
                    'name': f"Allocated space",
                    'value': display_val,
                    'address': f"@{heap_addr}",
                    'type': display_type,
                    'size': len(heap_list) # Show exact simulated byte size
                }


            # Capture Output so far
            output_so_far = ""
            if self.stdout_capture and hasattr(self.stdout_capture, 'getvalue'):
                 output_so_far = self.stdout_capture.getvalue()
            
            step = {
                'line': frame.f_lineno,
                'variables': local_vars,
                'output': output_so_far,
                'event': event
            }
            self.steps.append(step)
            if self.on_step:
                self.on_step(step)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            pass
            
        return self.trace_lines

    def run(self, code, exec_globals, stdout_capture=None, on_step=None):
        self.steps = []
        self.step_count = 0
        self.stdout_capture = stdout_capture
        self.on_step = on_step
        # Compile code with filename <string> to match filter
        compiled = compile(code, '<string>', 'exec')
        
        sys.settrace(self.trace_calls)
        try:
            exec(compiled, exec_globals)
        finally:
            sys.settrace(None)
        
        return self.steps
