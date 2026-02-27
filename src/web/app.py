import sys
import os
# Add parent directory to path to allow importing 'compiler'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, jsonify, Response
import io
import contextlib
from compiler.parser import parser, compile_algo

from web.debugger import TraceRunner
from web.models import db, Chapter, Question, Choice, UserProgress

app = Flask(__name__)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///algocompiler.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Ensure database tables exist and seed data if empty
with app.app_context():
    db.create_all()
    # Auto-seed if empty
    from web.models import Question
    if Question.query.count() == 0:
        print("Production DB is empty. Seeding quiz data...")
        try:
            from web.seed_quiz import seed_chapter_1
            seed_chapter_1()
        except Exception as e:
            print(f"Failed to auto-seed: {e}")


# Correct path to examples and fixtures
EXAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'examples'))
FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tests', 'fixtures'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/course')
def course():
    return render_template('course.html')

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

@app.route('/examples')
def list_examples():
    try:
        categories = {
            "Basics": [],
            "Arrays": [],
            "Strings": [],
            "Functions": [],
            "Pointers": [],
            "Dynamic_Allocation": [],
            "Enregistrements": [],
            "Listes_Chainees": [],
            "Piles": [],
            "Files": []
        }

        # Helper to categorize based on filename
        def categorize(filepath, is_fixture=False):
            if is_fixture:
                return "Fixtures"
            
            dirname = os.path.dirname(filepath).replace('\\', '/')
            if dirname:
                cat = dirname.replace('Allocation', ' Allocation').replace('_', ' ').replace('  ', ' ')
                # normalize common case
                if "dynamic" in cat.lower() and "alloc" in cat.lower():
                    cat = "Dynamic Allocation"
                if "enregistr" in cat.lower():
                    return "Enregistrements"
                if "pile" in cat.lower() or "stack" in cat.lower():
                    return "Piles"
                if "file" in cat.lower() or "queue" in cat.lower():
                    return "Files"
                if "liste" in cat.lower() or "chain" in cat.lower():
                    return "Listes_Chainees"
                return cat

            name = filepath.lower()
            if "dynamic" in name or "alloc" in name:
                return "Dynamic Allocation"
            if name.startswith("str_") or "string" in name or "chaine" in name:
                return "Strings"
            if "ptr" in name or "pointer" in name:
                return "Pointers"
            if "liste" in name or "chain" in name or "linked" in name:
                return "Listes_Chainees"
            if "pile" in name or "stack" in name:
                return "Piles"
            if "file" in name or "queue" in name:
                return "Files"
            if "record" in name or "enregistr" in name:
                return "Enregistrements"
            if "func" in name or "fonction" in name or "proc" in name:
                return "Functions"
            if "array" in name or "tableau" in name:
                return "Arrays"
            if name.startswith("test_"):
                return "Tests"
            return "Basics"

        # Main examples
        if os.path.exists(EXAMPLES_DIR):
            for root, dirs, files in os.walk(EXAMPLES_DIR):
                for f in files:
                    if f.endswith('.algo'):
                        # Get relative path for grouping
                        rel_path = os.path.relpath(os.path.join(root, f), EXAMPLES_DIR)
                        cat = categorize(rel_path)
                        # Ensure forward slashes for URLs
                        filepath_url = rel_path.replace('\\\\', '/')
                        if cat not in ["Tests", "Fixtures"]:
                            if cat not in categories:
                                categories[cat] = []
                            categories[cat].append({'name': f, 'path': filepath_url})
        
        # Sort each category: 00_Tutoriel first, then alphabetically
        for cat in categories:
            categories[cat].sort(key=lambda x: (
                0 if x['name'].startswith('00_Tutoriel') else 1,
                x['name'].lower()
            ))

        # Remove empty categories
        filtered_categories = {k: v for k, v in categories.items() if v and k not in ["Tests", "Fixtures"]}
        return jsonify(filtered_categories)
    except Exception as e:
        print(f"DEBUG: Exception in list_examples: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({})

@app.route('/example/<path:filename>')
def get_example(filename):
    try:
        # Security check
        if '..' in filename:
             return jsonify({'error': "Invalid filename"}), 400
             
        # Determine path
        if filename.startswith('fixtures/'):
            real_filename = filename.split('/', 1)[1]
            filepath = os.path.join(FIXTURES_DIR, real_filename)
        else:
            filepath = os.path.join(EXAMPLES_DIR, filename)

        if not os.path.exists(filepath):
            return jsonify({'error': "File not found"}), 404
            
        with open(filepath, 'r', encoding='utf-8') as f:
            code_content = f.read()
            
        # Check for associated .input file
        input_content = ""
        # Handle input file path logic based on directory
        base_path = os.path.splitext(filepath)[0]
        input_filepath = base_path + ".input"
        
        if os.path.exists(input_filepath):
             with open(input_filepath, 'r', encoding='utf-8') as f:
                 input_content = f.read()

        return jsonify({
            'code': code_content,
            'input': input_content
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- QUIZ API ENDPOINTS ---

import random

@app.route('/api/quiz/<chapter_identifier>')
def get_quiz(chapter_identifier):
    try:
        chapter = Chapter.query.filter_by(identifier=chapter_identifier).first()
        if not chapter:
            return jsonify({'error': 'Chapter not found in database'}), 404

        # Requirements: 6 Easy, 8 Medium, 6 Hard (Total 20)
        # If not enough, get as many as possible
        easy_q = Question.query.filter_by(chapter_id=chapter.id, difficulty='Easy').all()
        medium_q = Question.query.filter_by(chapter_id=chapter.id, difficulty='Medium').all()
        hard_q = Question.query.filter_by(chapter_id=chapter.id, difficulty='Hard').all()

        selected_questions = (
            random.sample(easy_q, min(6, len(easy_q))) +
            random.sample(medium_q, min(8, len(medium_q))) +
            random.sample(hard_q, min(6, len(hard_q)))
        )
        random.shuffle(selected_questions)

        quiz_data = []
        for q in selected_questions:
            choices = Choice.query.filter_by(question_id=q.id).all()
            
            # Get the correct choice and up to 3 random incorrect choices
            correct_choice = next((c for c in choices if c.is_correct), None)
            incorrect_choices = [c for c in choices if not c.is_correct]
            selected_incorrect = random.sample(incorrect_choices, min(3, len(incorrect_choices)))
            
            final_choices = [correct_choice] + selected_incorrect if correct_choice else selected_incorrect
            random.shuffle(final_choices)

            quiz_data.append({
                'id': q.id,
                'type': q.type,
                'difficulty': q.difficulty,
                'concept': q.concept,
                'text': q.text,
                'explanation': q.explanation,
                'choices': [{'id': c.id, 'text': c.text, 'is_correct': c.is_correct} for c in final_choices]
            })

        return jsonify({'questions': quiz_data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/save_progress', methods=['POST'])
def save_quiz_progress():
    try:
        data = request.json
        chapter_identifier = data.get('chapter_identifier')
        score = data.get('score')
        total = data.get('total')
        details = data.get('details', '{}') 

        chapter = Chapter.query.filter_by(identifier=chapter_identifier).first()
        if not chapter:
            return jsonify({'error': 'Chapter not found'}), 404

        progress = UserProgress(
            chapter_id=chapter.id,
            score=score,
            total_questions=total,
            details=json.dumps(details)
        )
        db.session.add(progress)
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

import threading

import queue
import time
import json

# Global Session State
class GlobalSession:
    def __init__(self):
        self.input_queue = queue.Queue(maxsize=1000) # Limit size to prevent memory issues
        self.output_queue = queue.Queue(maxsize=10000) # Limit output buffer
        self.is_running = False
        self.current_thread = None

    def reset(self):
        self.input_queue = queue.Queue(maxsize=1000)
        self.output_queue = queue.Queue(maxsize=10000)
        self.is_running = False
        self.current_thread = None
        self.current_ctx = None

session = GlobalSession()

import ctypes

def terminate_thread(thread):
    """Terminates a python thread from another thread.
    :param thread: a threading.Thread instance
    """
    if not thread or not thread.is_alive():
        return

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(thread.ident), exc)
    if res == 0:
        # Thread might be dead already
        pass
    elif res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(thread.ident), None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

@app.route('/stop_execution', methods=['POST'])
def stop_execution_route():
    global session
    if session.is_running:
        session.is_running = False
        if hasattr(session, 'current_ctx') and session.current_ctx:
            session.current_ctx.is_running = False
        
        # Force kill the thread
        if session.current_thread:
             try:
                 terminate_thread(session.current_thread)
             except Exception as e:
                 print(f"Error terminating thread: {e}")

        # Unblock any waiting input
        try:
             # Drain input queue to ensure put doesn't block if full
             while not session.input_queue.empty():
                 try: session.input_queue.get_nowait()
                 except: break
             session.input_queue.put(None) 
        except:
             pass
        
        # Clear queues
        try:
            with session.input_queue.mutex:
                session.input_queue.queue.clear()
            with session.output_queue.mutex:
                session.output_queue.queue.clear()
        except Exception:
            # In case mutex is locked or other issues
            pass
            
        # session.output_queue.put({'type': 'finished', 'data': 'Execution stopped by user.'})
        # We rely on the thread catching SystemExit and sending 'stopped'
        
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Not running'})

@app.route('/doc/errors')
def doc_errors():
    return render_template('errors.html')

@app.route('/start_execution', methods=['POST'])
def start_execution():
    global session
    data = request.json
    code = data.get('code', '')
    if isinstance(code, dict):
        # Fallback if frontend accidentally sends an object or object payload was double-nested
        import json
        code = json.dumps(code)
    code = str(code)

    if session.is_running:
        return jsonify({'success': False, 'error': 'Already running'})

    try:
        print(f"DEBUG: app session ID: {id(session)}")
        # Transpile to Python
        # Use compile_algo to ensure indent_level is reset
        result = compile_algo(code)
        
        # Handle tuple return (code, errors)
        if isinstance(result, tuple):
            python_code, errors = result
            if errors:
                # Return structured errors
                return jsonify({'success': False, 'error': 'Compilation failed', 'details': errors})
        else:
             python_code = result # Fallback for backward compatibility if parser didn't update (shouldn't happen)

        if not python_code:
            return jsonify({'success': False, 'error': 'Compilation failed (Syntax Error)'})

        # Save to file (optional, for debug)
        with open('output.py', 'w', encoding='utf-8') as f:
            f.write(python_code)

        # Reset Session
        session.reset()
        session.is_running = True
        
        class RunContext:
            def __init__(self, in_q, out_q):
                self.is_running = True
                self.input_queue = in_q
                self.output_queue = out_q
                
        ctx = RunContext(session.input_queue, session.output_queue)
        session.current_ctx = ctx
        
        # Check for pre-loaded input file
        input_file_content = data.get('inputFileContent', '')
        if input_file_content:
             # Split by lines and put into input queue
             lines = input_file_content.split('\n')
             for line in lines:
                 session.input_queue.put(line.strip())

        # Thread Target
        def run_script():
            try:
                # Mock Input
                def mock_input(prompt=''):
                    if prompt:
                        ctx.output_queue.put({'type': 'stdout', 'data': prompt})
                    
                    # Check if we have pre-loaded input in queue
                    if not ctx.input_queue.empty():
                         return ctx.input_queue.get()

                    # Request Input from Frontend
                    # print("DEBUG: Sending input_request to frontend")
                    ctx.output_queue.put({'type': 'input_request'})
                    
                    # Block wait for input
                    # print("DEBUG: Waiting for input from session.input_queue")
                    user_input = ctx.input_queue.get()
                    if user_input is None: # Signal to stop
                        raise EOFError("Execution Terminated")
                    return user_input

                # Mock Print? 
                # We need to capture stdout.
                # TraceRunner captures it, but we also want real-time streaming.
                # Let's create a stream-like object that puts to queue.
                class StreamToQueue:
                    def write(self, text):
                        if text:
                            try:
                                # Use timeout to allow checking if session is still running
                                # This prevents deadlock if queue is full and stop is requested
                                while ctx.is_running:
                                    try:
                                        ctx.output_queue.put({'type': 'stdout', 'data': text}, timeout=0.5)
                                        break
                                    except queue.Full:
                                        if not ctx.is_running: break
                                        continue
                            except Exception:
                                pass
                    def flush(self):
                        pass
                
                stream = StreamToQueue()

                # Prepare builtins
                # Custom print to ensure capture
                def custom_print(*args, **kwargs):
                    sep = kwargs.get('sep', ' ')
                    end = kwargs.get('end', '\n')
                    file = kwargs.get('file', None)
                    if file is None:
                        text = sep.join(map(str, args)) + end
                        stream.write(text)
                    else:
                        try:
                            file.write(sep.join(map(str, args)) + end)
                        except:
                            pass

                # Helper to convert Algo types (like char lists) to string for display
                def _algo_to_string(val):
                    if isinstance(val, bool): return "Vrai" if val else "Faux"
                    if isinstance(val, list):
                        res = ""
                        for char in val:
                            if char is None or char == "\0": break
                            res += str(char)
                        return res
                    return str(val)

                
                def _algo_longueur(val):
                    """Calculate length of a string (stops at null terminator for fixed strings)"""
                    if isinstance(val, list):
                        return len(_algo_to_string(val))
                    return len(str(val))
                
                def _algo_concat(val1, val2):
                    """Concatenate two strings, handling fixed-size string arrays"""
                    # Convert both values to strings
                    str1 = ""
                    # Concatenate two values (string or fixed-string list)
                    s1 = _algo_to_string(val1) if isinstance(val1, list) else str(val1)
                    s2 = _algo_to_string(val2) if isinstance(val2, list) else str(val2)
                    return s1 + s2
                    
                def _algo_assign_fixed_string(target_list, source_val):
                    # Update target_list in-place to match source_val (string or list)
                    # Enforce size limit and terminator
                    if not isinstance(target_list, list): return target_list # Should be list
                    limit = len(target_list)
                    
                    # Convert source to string first
                    s_val = ''
                    # Check if source_val is a Pointer pointing to an array (array decay read)
                    if hasattr(source_val, '_get_target_container'):
                        targ = source_val._get_target_container()
                        # Sub-pointers decay wrapper (chaine Pointers points to base_var=Pointer(...)
                        while hasattr(targ, '_get_target_container'): 
                            targ = targ._get_target_container()
                        
                        if isinstance(targ, list):
                            # It's a pointer to an array, extract from index onwards
                            s_val = _algo_to_string(targ[source_val.index:])
                        else:
                            # Evaluate scalar value
                            s_val = str(source_val._get_string() if hasattr(source_val, '_get_string') else source_val._get())
                    elif isinstance(source_val, list):
                         s_val = _algo_to_string(source_val)
                    else:
                         s_val = str(source_val)
                    
                    # Truncate to limit - 1 to ensure room for terminator if limit > 0
                    if limit > 0:
                        s_val = s_val[:limit-1]
                        
                        # Fill list
                        for i in range(len(s_val)):
                            target_list[i] = s_val[i]
                        target_list[len(s_val)] = '\0' # Terminator
                        # Pad rest with None
                        for i in range(len(s_val)+1, limit):
                            target_list[i] = None
                    return target_list


                # Mock input for LIRE if needed
                if False:
                    pass 
                
                # Parser generates: x = _algo_read_typed(x, _algo_read())
                # app.py defines: def _algo_read_typed(current_val, raw_input): ...
                
                def _algo_read_typed(current_val, raw_val, target_type_name='CHAINE'):
                    # Strict Type Enforcement based on current_val OR target_type_name
                    
                    # Determine effective type check
                    type_to_check = target_type_name.upper()
                    
                    # Handle Fixed Strings
                    if 'CHAINE' in type_to_check:
                        # If it's a list (fixed Chaine), update in place
                        if isinstance(current_val, list):
                             _algo_assign_fixed_string(current_val, raw_val)
                             return current_val
                        # If scalar (dynamic? forbidden? or None init), return string
                        return str(raw_val)

                    # Handle Boolean
                    if 'BOOLEEN' in type_to_check or isinstance(current_val, bool):
                        val_str = str(raw_val).lower()
                        if val_str in ['vrai', 'true', '1']: return True
                        if val_str in ['faux', 'false', '0']: return False
                        raise ValueError(f"Type mismatch: '{raw_val}' n'est pas un Booléen valide.")

                    # Handle Integer
                    if 'ENTIER' in type_to_check or isinstance(current_val, int):
                        try: 
                            val = int(raw_val)
                            return val
                        except: 
                            raise ValueError(f"Type mismatch: '{raw_val}' n'est pas un Entier valide.")

                    # Handle Float
                    if 'REEL' in type_to_check or isinstance(current_val, float):
                        try:
                            val = float(raw_val)
                            return val
                        except: 
                            raise ValueError(f"Type mismatch: '{raw_val}' n'est pas un Reel valide.")


                    # Handle Lists (Arrays or Fixed Strings) - Complex case if None
                    if isinstance(current_val, list):
                        return raw_val 
                    
                    # Default: String
                    return str(raw_val)

                def _algo_set_char(target_list, index, char_val):
                    """Set character at 0-based index in a fixed string"""
                    if not isinstance(target_list, list):
                        raise TypeError(f"Variable Chaine non initialisee. Declarez avec s[N]: Chaine (recu: {type(target_list).__name__})")
                    idx = int(index)  # 0-based
                    if 0 <= idx < len(target_list):
                        c = str(char_val)[0] if char_val else "\0"
                        target_list[idx] = c
                    return target_list

                def _algo_get_char(target_list, index):
                    """Get character at 0-based index from a fixed string"""
                    if isinstance(target_list, list):
                        idx = int(index)  # 0-based
                        if 0 <= idx < len(target_list):
                            c = target_list[idx]
                            return c if c is not None and c != "\0" else ""
                        return ""
                    s = str(target_list)
                    idx = int(index)
                    return s[idx] if 0 <= idx < len(s) else ""

                # Prepare builtins
                safe_builtins = {}
                if isinstance(__builtins__, dict):
                    safe_builtins = __builtins__.copy()
                else:
                    safe_builtins = __builtins__.__dict__.copy()

                exec_globals = {
                    '_algo_to_string': _algo_to_string,
                    '_algo_longueur': _algo_longueur,
                    '_algo_concat': _algo_concat,
                    '_algo_assign_fixed_string': _algo_assign_fixed_string,
                    '_algo_set_char': _algo_set_char,
                    '_algo_get_char': _algo_get_char,
                    '_algo_read_typed': _algo_read_typed,
                    'print': custom_print,
                    'input': mock_input, 
                    '__builtins__': safe_builtins
                }

                with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                    # Use TraceRunner?
                    # TraceRunner is tricky in typical streaming because it collects steps.
                    # If we want real-time inspector, TraceRunner needs to push steps to queue?
                    # For now, let's focus on Console Interactivity.
                    # We can use TraceRunner but modify it or wrap it.
                    # The user wants "panel to see the variable... change during execution".
                    # So YES, we need TraceRunner to push events.
                    
                    # Let's subclass or modify TraceRunner behavior via callback?
                    # Or just use TraceRunner logic here.
                    
                    
                    tracer = TraceRunner()
                    
                    # Callback to push step to queue
                    def on_log_step(step):
                         if not ctx.is_running:
                             raise SystemExit("Execution stopped by user")
                         try:
                             # Try putting with timeout to allow checking run state
                             while ctx.is_running:
                                 try:
                                     ctx.output_queue.put({'type': 'trace', 'data': step}, timeout=0.1)
                                     break
                                 except queue.Full:
                                     if not ctx.is_running: break
                                     continue
                         except:
                             pass
                    
                    # Run
                    tracer.run(python_code, exec_globals, stdout_capture=stream, on_step=on_log_step)

            except SystemExit:
                 ctx.output_queue.put({'type': 'stopped', 'data': 'Exécution interrompue.'})
            except Exception as e:
                # Translate Python errors to friendly Algo errors
                err_msg = str(e)
                error_type = type(e).__name__
                
                if "not supported between instances of 'str' and 'int'" in err_msg:
                    err_msg = "Impossible de comparer une Chaîne et un Entier."
                elif "not supported between instances of 'int' and 'str'" in err_msg:
                    err_msg = "Impossible de comparer un Entier et une Chaîne."
                elif "unsupported operand type(s)" in err_msg:
                    err_msg = f"Opération impossible entre ces types: {err_msg}"
                elif "name" in err_msg and "is not defined" in err_msg:
                    # Extract variable name
                    import re
                    match = re.search(r"name '(\w+)' is not defined", err_msg)
                    if match:
                        err_msg = f"Variable non déclarée ou inconnue: '{match.group(1)}'"
                    else:
                        err_msg = "Variable non déclarée."
                elif "division by zero" in err_msg:
                    err_msg = "[E4.5] Division par zéro impossible."
                elif "list index out of range" in err_msg:
                    err_msg = "[E4.4] Accès au tableau expiré ou hors limites."
                elif isinstance(e, TimeoutError):
                    err_msg = "[E4.1] Boucle infinie détectée (Temps/Instructions dépassés)."
                elif isinstance(e, RecursionError):
                    err_msg = "[E4.2] Erreur de récursion infinie (Trop d'appels de sous-programmes)."
                elif isinstance(e, MemoryError):
                    err_msg = "[E4.3] Dépassement de capacité mémoire (Trop d'allocations)."
                    
                session.output_queue.put({'type': 'error', 'data': f"Erreur d'exécution ({error_type}): {err_msg}"})
            finally:
                # If we stopped manually, we might have already sent 'stopped'
                # But to be safe, let's mark finished if we were running
                if session.is_running:
                     session.output_queue.put({'type': 'finished'})
                     session.is_running = False

        # Start Thread
        t = threading.Thread(target=run_script)
        t.daemon = True # Kill thread if main process ends
        t.start()
        session.current_thread = t

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            try:
                # Get message from queue, wait up to 1s
                msg = session.output_queue.get(timeout=1.0)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg['type'] == 'finished':
                    break
            except queue.Empty:
                if not session.is_running and session.output_queue.empty():
                    break
                # Send heartbeat
                yield ": keepalive\n\n"
    
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/send_input', methods=['POST'])
def send_input():
    global session
    if not session.is_running:
         return jsonify({'success': False, 'error': 'Not running'})
         
    data = request.json
    user_input = data.get('input')
    # print(f"DEBUG: Received input from frontend: '{user_input}'")
    session.input_queue.put(user_input)
    return jsonify({'success': True})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)
