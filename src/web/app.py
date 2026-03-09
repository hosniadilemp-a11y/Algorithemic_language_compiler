import sys
import os
import secrets
import logging
# Add parent directory to path to allow importing 'compiler'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print(">>> [DEBUG] APP STARTING UP...", flush=True)

from flask import Flask, render_template, request, jsonify, Response
from flask_login import current_user, login_required
import io
import contextlib
from compiler.parser import parser, compile_algo
print(">>> [DEBUG] PARSER IMPORTED", flush=True)

from web.debugger import TraceRunner
from web.models import db, Chapter, Question, Choice, Problem, TestCase, User, QuizAttempt, ChallengeSubmission, UserBadge
from web.extensions import login_manager, oauth, mail
from web.sandbox.runner import execute_code
print(">>> [DEBUG] MODELS AND EXTENSIONS IMPORTED", flush=True)
from sqlalchemy import func, distinct
import json
import secrets

# Handle Windows console encoding issues for scientific/accented characters
if sys.platform == 'win32':
    try:
        import io
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

import logging
# Aggressively silence all logging to prevent OSError [Errno 22] on Windows console
logging.disable(logging.CRITICAL)
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('werkzeug').disabled = True

app = Flask(__name__)


@app.before_request
def update_last_seen():
    if current_user.is_authenticated:
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        if current_user.last_seen is None:
            current_user.last_seen = now
            try:
                db.session.commit()
            except:
                db.session.rollback()
        else:
            # We need to make sure last_seen is offset-aware before comparing
            last_seen_utc = current_user.last_seen
            if last_seen_utc.tzinfo is None:
                last_seen_utc = last_seen_utc.replace(tzinfo=datetime.timezone.utc)
            if (now - last_seen_utc).total_seconds() > 60:
                current_user.last_seen = now
                try:
                    db.session.commit()
                except:
                    db.session.rollback()


# Basic Config
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Attempt to detect which driver to use
    use_psycopg3 = False
    try:
        import psycopg
        use_psycopg3 = True
    except ImportError:
        pass
    
    if database_url.startswith('postgres://'):
        driver = 'postgresql+psycopg://' if use_psycopg3 else 'postgresql://'
        database_url = database_url.replace('postgres://', driver, 1)
    elif database_url.startswith('postgresql://'):
        if use_psycopg3:
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    # Hide password in logs
    safe_log_url = database_url.split('@')[-1] if '@' in database_url else "HIDDEN"
    print(f">>> CONFIGURED DATABASE_URL: {safe_log_url} (Psycopg3: {use_psycopg3})", flush=True)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or f"sqlite:///{os.path.join(BASE_DIR, 'algocompiler.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

safe_uri = app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else "sqlite"
print(f">>> [DEBUG] SQLALCHEMY_DATABASE_URI: {safe_uri}", flush=True)

try:
    print(">>> [DEBUG] INITIALIZING DB...", flush=True)
    db.init_app(app)
    with app.app_context():
        print(">>> [DEBUG] ENSURING TABLES EXIST (db.create_all)...", flush=True)
        db.create_all()
        print(">>> [DEBUG] DB TABLES CHECKED/CREATED OK", flush=True)
        
        # Auto-seed if empty
        if Question.query.count() == 0 and not os.environ.get('SKIP_SEED'):
            print(">>> [DEBUG] DB EMPTY. SEEDING FROM JSON...", flush=True)
            try:
                from web.seed_from_json import seed_from_json
                seed_from_json()
                print(">>> [DEBUG] SEEDING COMPLETED", flush=True)
            except Exception as seed_err:
                print(f">>> [DEBUG] SEEDING FAILED (NON-FATAL): {seed_err}", flush=True)
except Exception as e:
    print(f">>> [CRITICAL] DB SETUP FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.stdout.flush()

# Mail Config (Resend defaults for easier testing)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.resend.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 465))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', 'on', '1']
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'resend')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'onboarding@resend.dev')

# OAuth Config Placeholder
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID', 'placeholder')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET', 'placeholder')
app.config['GITHUB_CLIENT_ID'] = os.environ.get('GITHUB_CLIENT_ID', 'placeholder')
app.config['GITHUB_CLIENT_SECRET'] = os.environ.get('GITHUB_CLIENT_SECRET', 'placeholder')

# Initialize extensions
login_manager.init_app(app)
oauth.init_app(app)
mail.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Register Auth Blueprint
from web.auth import auth_bp
app.register_blueprint(auth_bp)

# Register Admin Blueprint (Teacher Dashboard at /admin)
from web.admin import admin_bp
app.register_blueprint(admin_bp)

# Correct path to examples and fixtures
EXAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'examples'))
FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tests', 'fixtures'))

@app.route('/')
def index():
    return render_template('index.html')

from flask import send_from_directory
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/course')
def course():
    return render_template('course.html')

@app.route('/progress')
@login_required
def progress_page():
    return render_template('progress.html')

@app.route('/problems')
def problems_page():
    return render_template('problems.html')

@app.route('/challenge/<int:problem_id>')
def challenge_page(problem_id):
    # Just render the template. JS will fetch the problem details via API
    return render_template('challenge.html', problem_id=problem_id)

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

@app.route('/api/validate_algo', methods=['POST'])
def validate_algo():
    """Validate a course snippet against the current compiler without executing it."""
    try:
        data = request.get_json(silent=True) or {}
        code = data.get('code', '')
        if isinstance(code, dict):
            code = json.dumps(code)
        code = str(code)

        if not code.strip():
            return jsonify({'ok': False, 'errors': [{'message': 'Code vide'}]}), 200

        result = compile_algo(code)

        # Modern parser returns (python_code, errors)
        if isinstance(result, tuple):
            python_code, errors = result
            if errors:
                return jsonify({'ok': False, 'errors': errors}), 200
                
            return jsonify({'ok': bool(python_code), 'errors': []}), 200

        # Backward compatibility
        return jsonify({'ok': bool(result), 'errors': [] if result else [{'message': 'Compilation failed'}]}), 200
    except Exception as e:
        return jsonify({'ok': False, 'errors': [{'message': str(e)}]}), 200

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

        if current_user.is_authenticated:
            # Check interpretation
            all_correct = (score == total)
            none_correct = (score == 0)

            # Capture level before save
            old_xp, _, old_level, _ = compute_xp_and_level(current_user.id)

            attempt = QuizAttempt(
                user_id=current_user.id,
                chapter_id=chapter.id,
                score=score,
                total_questions=total,
                all_correct=all_correct,
                none_correct=none_correct,
                details=json.dumps(details)
            )
            db.session.add(attempt)
            db.session.commit()

            # Percentile calculation
            # Calculate how many unique users have a score lower than this one
            all_scores = db.session.query(
                func.max(QuizAttempt.score)
            ).filter(
                QuizAttempt.chapter_id == chapter.id
            ).group_by(QuizAttempt.user_id).all()
            
            all_scores_list = [s[0] for s in all_scores if s[0] is not None]
            total_participants = len(all_scores_list)
            
            percentile = 0
            if total_participants > 1:
                # Count scores strictly lower
                lower_scores = sum(1 for s in all_scores_list if s < score)
                percentile = (lower_scores / (total_participants - 1)) * 100
            elif total_participants == 1:
                percentile = 100

            # Capture level after save
            new_xp, _, new_level, new_xp_to_next = compute_xp_and_level(current_user.id)
            level_up = new_level['num'] > old_level['num']

            return jsonify({
                'success': True,
                'saved': True,
                'percentile': round(percentile, 1),
                'xp_earned': new_xp - old_xp,
                'xp_total': new_xp,
                'level': new_level,
                'level_up': level_up,
                'xp_to_next': new_xp_to_next
            })

        return jsonify({'success': True, 'saved': False})
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

        print(f"\n--- DEBUG: GENERATED PYTHON CODE (LIVE EXECUTION) ---\n{python_code}\n-----------------------------------------------------\n")

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
                    def __init__(self):
                        import io
                        self.buffer = io.StringIO()
                    def write(self, text):
                        if text:
                            self.buffer.write(text)
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

                    def isatty(self):
                        return False

                    def getvalue(self):
                        return self.buffer.getvalue()

                    def fileno(self):
                        import io
                        raise io.UnsupportedOperation("fileno")
                
                stream = StreamToQueue()
                
                # Global redirection for this thread to capture all prints and logs
                with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):

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
                        s1 = _algo_to_string(val1) if isinstance(val1, list) else str(val1)
                        s2 = _algo_to_string(val2) if isinstance(val2, list) else str(val2)
                        return s1 + s2
                        
                    def _algo_assign_fixed_string(target_list, source_val):
                        # Update target_list in-place to match source_val (string or list)
                        if not isinstance(target_list, list): return target_list
                        limit = len(target_list)
                        s_val = ''
                        if hasattr(source_val, '_get_target_container'):
                            targ = source_val._get_target_container()
                            while hasattr(targ, '_get_target_container'): 
                                targ = targ._get_target_container()
                            if isinstance(targ, list):
                                s_val = _algo_to_string(targ[source_val.index:])
                            else:
                                s_val = str(source_val._get_string() if hasattr(source_val, '_get_string') else source_val._get())
                        elif isinstance(source_val, list):
                             s_val = _algo_to_string(source_val)
                        else:
                             s_val = str(source_val)
                        
                        if limit > 0:
                            s_val = s_val[:limit-1]
                            for i in range(len(s_val)):
                                target_list[i] = s_val[i]
                            target_list[len(s_val)] = '\0'
                            for i in range(len(s_val)+1, limit):
                                target_list[i] = None
                        return target_list

                    # Mock input for LIRE if needed
                    def _algo_read_typed(current_val, raw_val, target_type_name='CHAINE'):
                        type_to_check = target_type_name.upper()
                        if 'CHAINE' in type_to_check:
                            if isinstance(current_val, list):
                                 _algo_assign_fixed_string(current_val, raw_val)
                                 return current_val
                            return str(raw_val)
                        if 'BOOLEEN' in type_to_check or isinstance(current_val, bool):
                            val_str = str(raw_val).lower()
                            if val_str in ['vrai', 'true', '1']: return True
                            if val_str in ['faux', 'false', '0']: return False
                            raise ValueError(f"Type mismatch: '{raw_val}' n'est pas un Booléen valide.")
                        if 'ENTIER' in type_to_check or isinstance(current_val, int):
                            try: return int(raw_val)
                            except: raise ValueError(f"Type mismatch: '{raw_val}' n'est pas un Entier valide.")
                        if 'REEL' in type_to_check or isinstance(current_val, float):
                            try: return float(raw_val)
                            except: raise ValueError(f"Type mismatch: '{raw_val}' n'est pas un Reel valide.")
                        if isinstance(current_val, list): return raw_val 
                        return str(raw_val)

                    def _algo_set_char(target_list, index, char_val):
                        if not isinstance(target_list, list): return target_list
                        idx = int(index)
                        if 0 <= idx < len(target_list):
                            c = str(char_val)[0] if char_val else "\0"
                            target_list[idx] = c
                        return target_list

                    def _algo_get_char(target_list, index):
                        if isinstance(target_list, list):
                            idx = int(index)
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
                            'input': mock_input, 
                        '__builtins__': safe_builtins
                    }

                    tracer = TraceRunner()
                    
                    def on_log_step(step):
                         if not ctx.is_running:
                             raise SystemExit("Execution stopped by user")
                         try:
                             while ctx.is_running:
                                 try:
                                     ctx.output_queue.put({'type': 'trace', 'data': step}, timeout=0.1)
                                     break
                                 except queue.Full:
                                     if not ctx.is_running: break
                                     continue
                         except:
                             pass
                    
                    # Run execution
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


@app.route('/api/problems', methods=['GET'])
def get_problems():
    topics = request.args.getlist('topic')
    difficulties = request.args.getlist('difficulty')
    
    query = Problem.query
    if topics:
        query = query.filter(Problem.topic.in_(topics))
    if difficulties:
        query = query.filter(Problem.difficulty.in_(difficulties))
    
    problems = query.all()
    
    # Get solved problems for the current user if authenticated
    solved_ids = set()
    if current_user.is_authenticated:
        solved_submissions = ChallengeSubmission.query.filter_by(user_id=current_user.id, passed=True).all()
        solved_ids = {s.problem_id for s in solved_submissions}

    # Count distinct users who attempted each problem
    attempt_counts = (
        db.session.query(
            ChallengeSubmission.problem_id,
            func.count(distinct(ChallengeSubmission.user_id))
        )
        .group_by(ChallengeSubmission.problem_id)
        .all()
    )
    attempt_map = {prob_id: count for prob_id, count in attempt_counts}

    # Count distinct users who solved each problem
    solver_counts = (
        db.session.query(
            ChallengeSubmission.problem_id,
            func.count(distinct(ChallengeSubmission.user_id))
        )
        .filter(ChallengeSubmission.passed == True)
        .group_by(ChallengeSubmission.problem_id)
        .all()
    )
    solver_map = {prob_id: count for prob_id, count in solver_counts}
    
    return jsonify({
        'success': True,
        'problems': [
            {
                'id': p.id,
                'title': p.title,
                'topic': p.topic,
                'difficulty': p.difficulty,
                'solved': p.id in solved_ids if current_user.is_authenticated else None,
                'attempted_users': attempt_map.get(p.id, 0),
                'solvers': solver_map.get(p.id, 0),
                'success_rate': round((solver_map.get(p.id, 0) / attempt_map.get(p.id, 1)) * 100, 1) if attempt_map.get(p.id, 0) else 0,
                'description': p.description[:150] + '...' if p.description and len(p.description) > 150 else p.description
            }
            for p in problems
        ]
    })

@app.route('/api/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    problem = db.session.get(Problem, problem_id)
    if not problem:
        return jsonify({'success': False, 'error': 'Problem not found'}), 404
    # Return only public test cases to frontend
    public_cases = [tc for tc in problem.test_cases if tc.is_public]
    
    return jsonify({
        'success': True,
        'problem': {
            'id': problem.id,
            'title': problem.title,
            'description': problem.description,
            'topic': problem.topic,
            'difficulty': problem.difficulty,
            'template_code': problem.template_code,
            'test_cases': [{
                'id': tc.id,
                'input': tc.input_data,
                'expected_output': tc.expected_output
            } for tc in public_cases]
        }
    })

@app.route('/submission_results')
def submission_results():
    return render_template('submission_results.html')

from web.sandbox.runner import execute_code
# Assuming compiler is available in the same scope as before for `run` endpoint
import ast

@app.route('/api/submissions/custom', methods=['POST'])
def submit_custom_code():
    data = request.get_json()
    code = data.get('code')
    custom_input = data.get('input', '')
    
    # 1. Compile Algo code to Python
    result = compile_algo(code)
    
    # Handle tuple return (code, errors)
    if isinstance(result, tuple):
        python_code, errors = result
        if errors:
            return jsonify({'success': False, 'error': 'Compilation failed', 'details': errors})
    else:
        python_code = result
        
    if not python_code:
        return jsonify({'success': False, 'error': 'Compilation failed (Syntax Error)'})
        
        
    tc_data = [{
        'id': 'custom',
        'input': custom_input,
        'expected_output': ''
    }]
    
    
    results = execute_code(python_code, tc_data)
    
    return jsonify({
        'success': True,
        'all_passed': results[0]['passed'],
        'results': results
    })

@app.route('/api/submissions', methods=['POST'])
def submit_code():
    data = request.get_json()
    problem_id = data.get('problem_id')
    code = data.get('code')
    execute_all = data.get('execute_all', False)
    time_taken_seconds = data.get('time_taken_seconds', 0)
    
    problem = db.session.get(Problem, problem_id)
    if not problem:
        return jsonify({'success': False, 'error': 'Problem not found'}), 404
    
    # 1. Compile Algo code to Python
    result = compile_algo(code)
    
    # Handle tuple return (code, errors)
    if isinstance(result, tuple):
        python_code, errors = result
        if errors:
            # Return structured errors exactly as expected by frontend mapping
            return jsonify({'success': False, 'error': 'Compilation failed', 'details': errors})
    else:
        python_code = result
        
    if not python_code:
        return jsonify({'success': False, 'error': 'Compilation failed (Syntax Error)'})
    
    
    # 2. Select test cases
    if execute_all:
        test_cases = problem.test_cases
    else:
        test_cases = [tc for tc in problem.test_cases if tc.is_public]
        
    # 3. Format test case data for sandbox
    tc_data = [{
        'id': tc.id,
        'input': tc.input_data,
        'expected_output': tc.expected_output
    } for tc in test_cases]
    
    # 4. Execute in sandbox
    raw_results = execute_code(python_code, tc_data)
    
    # Merge original tc_data with execution results
    results = []
    for i, raw_res in enumerate(raw_results):
        tc_info = tc_data[i]
        results.append({
            'test_case_id': tc_info['id'],
            'input': tc_info['input'],
            'expected_output': tc_info['expected_output'],
            'actual_output': raw_res['actual_output'],
            'passed': raw_res['passed'],
            'error': raw_res['error']
        })
    
    # Calculate all_passed
    all_passed = all(r['passed'] for r in results) if results else False
    
    # Save submission if user is logged in and it's a full submission
    level_up_info = None
    if current_user.is_authenticated and execute_all:
        score_percent = sum(1 for r in results if r['passed']) / len(results) * 100 if results else 0

        # Capture level before save
        old_xp, _, old_level, _ = compute_xp_and_level(current_user.id)

        submission = ChallengeSubmission(
            user_id=current_user.id,
            problem_id=problem.id,
            score=score_percent,
            code=code,
            passed=all_passed,
            time_taken_seconds=time_taken_seconds
        )
        db.session.add(submission)
        db.session.commit()

        # Capture level after save
        new_xp, _, new_level, new_xp_to_next = compute_xp_and_level(current_user.id)
        if new_level['num'] > old_level['num']:
            level_up_info = {
                'level_up': True,
                'new_level': new_level,
                'xp_earned': new_xp - old_xp,
                'xp_total': new_xp,
                'xp_to_next': new_xp_to_next
            }

    return jsonify({
        'success': True,
        'all_passed': all_passed,
        'results': results,
        **(level_up_info or {})
    })


# ─────────────────────────────────────────────────────────────────────────────
# XP POINTS & LEVEL SYSTEM
# ─────────────────────────────────────────────────────────────────────────────
LEVEL_DEFS = [
    # (min_xp, level_num, name_fr, color, glow, icon, special_requirement_key)
    (0,    1, "Novice",      "#6c757d", "rgba(108,117,125,0.5)", "⌨️", None),
    (50,   2, "Initié",      "#0dcaf0", "rgba(13,202,240,0.5)",  "💻", None),
    (200,  3, "Apprenti",    "#fd7e14", "rgba(253,126,20,0.5)",  "🛠️", None),
    (500,  4, "Confirmé",    "#0d6efd", "rgba(13,110,253,0.5)",  "⚙️", None),
    (1200, 5, "Expert",      "#ffc107", "rgba(255,193,7,0.5)",   "🚀", None),
    (3000, 6, "Maître",      "#a855f7", "rgba(168,85,247,0.5)",  "♾️", "master_criteria"),
]

def compute_xp_and_level(user_id):
    """Return (xp_total, xp_breakdown, level_dict, xp_to_next) for a user."""
    from web.models import QuizAttempt, ChallengeSubmission, UserBadge, Chapter

    quiz_attempts = QuizAttempt.query.filter_by(user_id=user_id).all()
    submissions   = ChallengeSubmission.query.filter_by(user_id=user_id, passed=True).all()
    badges        = UserBadge.query.filter_by(user_id=user_id).all()

    chapters = {c.id: c.identifier for c in Chapter.query.all()}

    breakdown = []
    xp = 0

    # Quiz XP — per chapter, count the BEST attempt (if score >= 80%) → +10 XP
    chapter_best = {}
    for qa in quiz_attempts:
        pct = qa.score / qa.total_questions if qa.total_questions else 0
        if pct >= 0.8:
            prev = chapter_best.get(qa.chapter_id, 0)
            chapter_best[qa.chapter_id] = max(prev, qa.score)
    for cid, best_score in chapter_best.items():
        ident = chapters.get(cid, f"Chap {cid}")
        breakdown.append({"label": f"Quiz — {ident.capitalize()}", "xp": 10, "icon": "📚"})
        xp += 10

    # Challenge XP — per unique passed problem → scaled by difficulty
    passed_pids = set()
    for sub in submissions:
        if sub.problem_id not in passed_pids:
            passed_pids.add(sub.problem_id)
    
    if passed_pids:
        passed_problems = Problem.query.filter(Problem.id.in_(passed_pids)).all()
        for p in passed_problems:
            if p.difficulty == 'Easy':
                val = 10
                icon = "🌱"
            elif p.difficulty == 'Medium':
                val = 20
                icon = "⚡"
            elif p.difficulty == 'Hard':
                val = 50
                icon = "🔥"
            else:
                val = 25
                icon = "⚔️"
            breakdown.append({"label": f"Défi #{p.id} ({p.difficulty})", "xp": val, "icon": icon})
            xp += val

    # Badge XP — per badge → +50 XP
    from web.models import UserBadge as UB
    badge_map = {
        "streak_3": "Séquence 3 Jours", "streak_7": "Séquence 7 Jours",
        "course_1": "Premier Pas", "course_3": "Étudiant Assidu",
        "course_7": "Érudit", "course_10_master": "Algo Master",
        "chall_1": "Développeur", "chall_5": "Codeur",
        "chall_10_beg": "Débutant Challenges", "chall_20_int": "Intermédiaire Challenges",
        "chall_50_adv": "Avancé Challenges", "chall_100_mast": "Maître des Défis",
        "hacker_bronze": "Hacker Bronze", "hacker_gold": "Hacker Or",
        "hacker_platinum": "Hacker Platine", "hacker_diamond": "Hacker Diamant",
        "hacker_master": "Maître Hacker", "hacker_grandmaster": "Grand Maître Hacker",
    }
    for ub in badges:
        label = badge_map.get(ub.badge_id, ub.badge_id)
        breakdown.append({"label": f"Badge : {label}", "xp": 50, "icon": "🏅"})
        xp += 50

    # Determine level
    # Check master criteria for level 6
    total_challenges = len(passed_pids)
    all_quiz_pct = 0
    if quiz_attempts:
        # average of best % per chapter
        chapter_pct = {}
        for qa in quiz_attempts:
            p = qa.score / qa.total_questions * 100 if qa.total_questions else 0
            chapter_pct[qa.chapter_id] = max(chapter_pct.get(qa.chapter_id, 0), p)
        all_quiz_pct = sum(chapter_pct.values()) / len(chapter_pct) if chapter_pct else 0

    master_ok = (xp >= 3000 and all_quiz_pct >= 95 and total_challenges >= 50)
    
    current_level = LEVEL_DEFS[0]
    for lvl in LEVEL_DEFS:
        min_xp, lnum, name, color, glow, icon, special = lvl
        if special == "master_criteria":
            if master_ok:
                current_level = lvl
        elif xp >= min_xp:
            current_level = lvl

    # XP to next level
    next_xp = None
    for lvl in LEVEL_DEFS:
        if lvl[0] > xp:
            next_xp = lvl[0]
            break
    # If we're level 6 (max) and criteria met, no next level
    if current_level[1] == 6:
        xp_to_next = 0
        next_level_name = None
    elif next_xp is not None:
        xp_to_next = next_xp - xp
        next_level_name = [l[2] for l in LEVEL_DEFS if l[0] == next_xp][0]
    else:
        xp_to_next = 0
        next_level_name = None

    level_dict = {
        "num": current_level[1],
        "name": current_level[2],
        "color": current_level[3],
        "glow": current_level[4],
        "icon": current_level[5],
        "min_xp": current_level[0],
        "next_xp": next_xp,
        "next_level_name": next_level_name,
    }
    return xp, breakdown, level_dict, xp_to_next

@app.route('/api/user/progress', methods=['GET'])
def get_user_progress():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    # Aggregate data
    quiz_attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.timestamp.desc()).all()
    submissions = ChallengeSubmission.query.filter_by(user_id=current_user.id).order_by(ChallengeSubmission.timestamp.desc()).all()
    
    chapter_stats = {}
    for qa in quiz_attempts:
        chap_id = qa.chapter_id
        is_completed = (qa.score / qa.total_questions) >= 0.8 if qa.total_questions > 0 else False
        score_perc = (qa.score / qa.total_questions * 100) if qa.total_questions > 0 else 0
        
        if chap_id not in chapter_stats:
            chapter_stats[chap_id] = {
                'all_correct': is_completed, 
                'taken': True, 
                'score': qa.score, 
                'total': qa.total_questions,
                'attempts_count': 1,
                'total_perc': score_perc
            }
        else:
            chapter_stats[chap_id]['attempts_count'] += 1
            chapter_stats[chap_id]['total_perc'] += score_perc
            if is_completed:
                chapter_stats[chap_id]['all_correct'] = True
            if qa.score > chapter_stats[chap_id]['score']:
                chapter_stats[chap_id]['score'] = qa.score
                chapter_stats[chap_id]['total'] = qa.total_questions

    # Finalize average calculation
    for chap_id in chapter_stats:
        stats = chapter_stats[chap_id]
        stats['avg_score'] = round(stats['total_perc'] / stats['attempts_count'], 1)
            
    # Map chapter IDs to their identifiers to send back to frontend
    chapters = Chapter.query.all()
    chapter_map = {c.id: c.identifier for c in chapters}
    
    frontend_chapter_stats = {}
    for cid, stats in chapter_stats.items():
        if cid in chapter_map:
            frontend_chapter_stats[chapter_map[cid]] = stats

    challenge_stats = {}
    for sub in submissions:
        pid = sub.problem_id
        if pid not in challenge_stats:
            challenge_stats[pid] = {'passed': False, 'best_score': 0}
        if sub.passed:
            challenge_stats[pid]['passed'] = True
        if sub.score > challenge_stats[pid]['best_score']:
             challenge_stats[pid]['best_score'] = sub.score

    total_quizzes = len(quiz_attempts)
    perfect_quizzes = sum(1 for q in quiz_attempts if q.all_correct)
    unique_perfect_chapters = sum(1 for cid in frontend_chapter_stats if frontend_chapter_stats[cid].get('all_correct'))
    
    total_challenges_attempted = len(set(sub.problem_id for sub in submissions))
    passed_challenges = sum(1 for pid in challenge_stats if challenge_stats[pid]['passed'])
    
    # --- NEW ADVANCED STATISTICS (Phase 6) ---
    # 1. Challenge Distributions
    challenge_topic_dist = {}
    challenge_diff_dist = {'Easy': 0, 'Medium': 0, 'Hard': 0}
    
    # We only count UNIQUE passed problems for distribution
    passed_pids = [pid for pid, s in challenge_stats.items() if s['passed']]
    if passed_pids:
        passed_problems = Problem.query.filter(Problem.id.in_(passed_pids)).all()
        for p in passed_problems:
            challenge_topic_dist[p.topic] = challenge_topic_dist.get(p.topic, 0) + 1
            challenge_diff_dist[p.difficulty] = challenge_diff_dist.get(p.difficulty, 0) + 1

    # 2. Temporal Quiz Data (Daily Averages)
    daily_stats = {}
    for qa in quiz_attempts:
        day = qa.timestamp.date().isoformat()
        if day not in daily_stats:
            daily_stats[day] = {'total_score': 0, 'count': 0}
        daily_stats[day]['total_score'] += (qa.score / qa.total_questions) * 100
        daily_stats[day]['count'] += 1
    
    daily_avg_quiz_score = [
        {'day': d, 'avg': round(s['total_score'] / s['count'], 1)} 
        for d, s in sorted(daily_stats.items())
    ]

    # 3. Per-Chapter Score Evolution
    # Format: { 'chap_identifier': [ {timestamp, score_perc} ] }
    quiz_evolution_per_chapter = {}
    # Process in chronological order for the chart
    for qa in sorted(quiz_attempts, key=lambda x: x.timestamp):
        ident = chapter_map.get(qa.chapter_id)
        if not ident: continue
        if ident not in quiz_evolution_per_chapter:
            quiz_evolution_per_chapter[ident] = []
        quiz_evolution_per_chapter[ident].append({
            'ts': qa.timestamp.isoformat(),
            'score': round((qa.score / qa.total_questions) * 100, 1)
        })

    # --- END ADVANCED STATISTICS ---

    # --- NEW BADGES LOGIC based on Badges.txt ---
    # Streaks calculation (simplified for now to days active based on timestamps)
    # Course completion stats
    courses_completed = sum(1 for cid in frontend_chapter_stats if frontend_chapter_stats[cid].get('all_correct'))
    
    # Challenge Stats
    challenges_completed = passed_challenges
    
    # Mastery / Hacker Stats
    # Assuming "hard" challenges are those marked difficulty='Hard'
    hard_problems_passed = ChallengeSubmission.query.join(Problem).filter(
        ChallengeSubmission.user_id == current_user.id,
        ChallengeSubmission.passed == True,
        Problem.difficulty == 'Hard'
    ).with_entities(Problem.id).distinct().count()

    total_course_score = sum(stats['score']/stats['total'] for stats in chapter_stats.values()) if chapter_stats else 0
    num_courses_taken = len(chapter_stats) if chapter_stats else 1
    avg_course_score = (total_course_score / num_courses_taken) * 100
    
    # Calculate badges to award
    badges_to_award = []
    
    # 1. Streaks (Require complex date parsing - simplified placeholder for demo or basic activity)
    # We will award 3 day streak if they have submissions/quizzes on 3 distinct days
    import datetime
    distinct_active_days = set([d.timestamp.date() for d in submissions] + [d.timestamp.date() for d in quiz_attempts])
    active_days = len(distinct_active_days)
    
    if active_days >= 3: badges_to_award.append("streak_3")
    if active_days >= 7: badges_to_award.append("streak_7")
    if active_days >= 14: badges_to_award.append("streak_14")
    if active_days >= 30: badges_to_award.append("streak_30")
    if active_days >= 60: badges_to_award.append("streak_60")
    if active_days >= 90: badges_to_award.append("streak_90")
    if active_days >= 180: badges_to_award.append("streak_180")
    if active_days >= 365: badges_to_award.append("streak_365")
    
    # 2. Courses
    if courses_completed >= 1: badges_to_award.append("course_1")
    if courses_completed >= 3: badges_to_award.append("course_3")
    if courses_completed >= 7: badges_to_award.append("course_7")
    if courses_completed >= 10: badges_to_award.append("course_10_master")
    
    # 3. Challenges 
    if challenges_completed >= 1: badges_to_award.append("chall_1")
    if challenges_completed >= 5: badges_to_award.append("chall_5")
    if challenges_completed >= 10: badges_to_award.append("chall_10_beg")
    if challenges_completed >= 20: badges_to_award.append("chall_20_int")
    if challenges_completed >= 50: badges_to_award.append("chall_50_adv")
    if challenges_completed >= 100: badges_to_award.append("chall_100_mast")
        
    # 4. Mastery Hacker
    all_courses_finished = courses_completed >= 10
    if all_courses_finished and avg_course_score > 70 and challenges_completed >= 10 and hard_problems_passed >= 2:
        badges_to_award.append("hacker_bronze")
    if all_courses_finished and avg_course_score > 80 and challenges_completed >= 15 and hard_problems_passed >= 3:
        badges_to_award.append("hacker_gold")
    if all_courses_finished and avg_course_score > 90 and challenges_completed >= 20 and hard_problems_passed >= 4:
        badges_to_award.append("hacker_platinum")
    if all_courses_finished and avg_course_score > 92 and challenges_completed >= 30 and hard_problems_passed >= 6:
        badges_to_award.append("hacker_diamond")
    if all_courses_finished and avg_course_score > 95 and challenges_completed >= 40 and hard_problems_passed >= 8:
        badges_to_award.append("hacker_master")
    if all_courses_finished and avg_course_score > 99 and challenges_completed >= 50 and hard_problems_passed >= 10:
        badges_to_award.append("hacker_grandmaster")
        
    # 5. Maitre Badges (Assuming specific topic problem counts)
    def chapter_prob_passed(topic):
        return ChallengeSubmission.query.join(Problem).filter(
            ChallengeSubmission.user_id == current_user.id,
            ChallengeSubmission.passed == True,
            Problem.topic == topic
        ).with_entities(Problem.id).distinct().count()
        
    if chapter_prob_passed("Arrays") >= 20: badges_to_award.append("maitre_tableaux")
    if chapter_prob_passed("Strings") >= 20: badges_to_award.append("maitre_chaines")
    if chapter_prob_passed("Enregistrements") >= 20: badges_to_award.append("maitre_enregistrements")
    if chapter_prob_passed("Listes_Chainees") >= 20: badges_to_award.append("maitre_listes")
    if chapter_prob_passed("Files") >= 20: badges_to_award.append("maitre_files")
    if chapter_prob_passed("Piles") >= 20: badges_to_award.append("maitre_piles")

    # Query existing badges to see what's new
    existing_badges = {ub.badge_id: ub for ub in UserBadge.query.filter_by(user_id=current_user.id).all()}
    
    new_badges_awarded = []
    for bid in badges_to_award:
        if bid not in existing_badges:
            ub = UserBadge(user_id=current_user.id, badge_id=bid, seen=False)
            db.session.add(ub)
            new_badges_awarded.append(bid)
            existing_badges[bid] = ub
            
    if new_badges_awarded:
        db.session.commit()

    # Define metadata for frontend delivery
    badge_defs = {
        "streak_3": {"name": "Séquence 3 Jours", "desc": "Actif pendant 3 jours distincts", "icon": "fas fa-fire", "category": "streak"},
        "streak_7": {"name": "Séquence 7 Jours", "desc": "Actif pendant 7 jours distincts", "icon": "fas fa-fire-alt", "category": "streak"},
        "streak_14": {"name": "Séquence 14 Jours", "desc": "Actif pendant 14 jours distincts", "icon": "fas fa-burn", "category": "streak"},
        "streak_30": {"name": "Séquence Mensuelle", "desc": "Actif pendant 30 jours", "icon": "fas fa-calendar-check", "category": "streak"},
        
        "course_1": {"name": "Premier Pas", "desc": "1 cours terminé", "icon": "fas fa-book-open", "category": "course"},
        "course_3": {"name": "Étudiant Assidu", "desc": "3 cours terminés", "icon": "fas fa-book-reader", "category": "course"},
        "course_7": {"name": "Érudit", "desc": "7 cours terminés", "icon": "fas fa-graduation-cap", "category": "course"},
        "course_10_master": {"name": "Algo Master", "desc": "10 cours terminés", "icon": "fas fa-university", "category": "course"},
        
        "chall_1": {"name": "Développeur", "desc": "1 défi terminé", "icon": "fas fa-keyboard", "category": "challenges"},
        "chall_5": {"name": "Codeur", "desc": "5 défis terminés", "icon": "fas fa-laptop-code", "category": "challenges"},
        "chall_10_beg": {"name": "Débutant", "desc": "10 défis terminés", "icon": "fas fa-medal", "category": "challenges"},
        "chall_20_int": {"name": "Intermédiaire", "desc": "20 défis terminés", "icon": "fas fa-award", "category": "challenges"},
        "chall_50_adv": {"name": "Avancé", "desc": "50 défis terminés", "icon": "fas fa-trophy", "category": "challenges"},
        "chall_100_mast": {"name": "Maître des Défis", "desc": "100 défis terminés", "icon": "fas fa-crown", "category": "challenges"},
        
        "hacker_bronze": {"name": "Hacker Bronze", "desc": "Tous cours, avg > 70%, 10 défis dont 2 difficiles", "icon": "fas fa-user-ninja", "category": "mastery"},
        "hacker_gold": {"name": "Hacker Or", "desc": "Tous cours, avg > 80%, 15 défis dont 3 difficiles", "icon": "fas fa-user-ninja", "category": "mastery"},
        "hacker_platinum": {"name": "Hacker Platine", "desc": "Tous cours, avg > 90%, 20 défis dont 4 difficiles", "icon": "fas fa-user-ninja", "category": "mastery"},
        "hacker_diamond": {"name": "Hacker Diamant", "desc": "Tous cours, avg > 92%, 30 défis dont 6 difficiles", "icon": "fas fa-user-astronaut", "category": "mastery"},
        "hacker_master": {"name": "Maître Hacker", "desc": "Tous cours, avg > 95%, 40 défis dont 8 difficiles", "icon": "fas fa-user-secret", "category": "mastery"},
        "hacker_grandmaster": {"name": "Grand Maître Hacker", "desc": "Tous cours, avg > 99%, 50 défis dont 10 difficiles", "icon": "fas fa-user-secret", "category": "mastery"},
        
        "maitre_tableaux": {"name": "Maitre des Tableaux", "desc": "20 problèmes sur Arrays", "icon": "fas fa-table", "category": "maitre"},
        "maitre_chaines": {"name": "Maitre des Chaines", "desc": "20 problèmes sur Strings", "icon": "fas fa-font", "category": "maitre"},
        "maitre_enregistrements": {"name": "Maitre des Enregistrements", "desc": "20 problèmes d'Enregistrements", "icon": "fas fa-address-card", "category": "maitre"},
        "maitre_listes": {"name": "Maitre des Listes Chainees", "desc": "20 problèmes sur LinkedList", "icon": "fas fa-link", "category": "maitre"},
        "maitre_files": {"name": "Maitre des Files", "desc": "20 problèmes sur Files", "icon": "fas fa-layer-group", "category": "maitre"},
        "maitre_piles": {"name": "Maitre des Piles", "desc": "20 problèmes sur Piles", "icon": "fas fa-bars", "category": "maitre"},
    }
    
    # Send up all definitions, marking which ones the user earned vs locked
    badges_response = []
    for bid, meta in badge_defs.items():
        badges_response.append({
            "id": bid,
            "name": meta["name"],
            "description": meta["desc"],
            "icon": meta["icon"],
            "category": meta["category"],
            "earned": bid in existing_badges,
            "seen": existing_badges[bid].seen if bid in existing_badges else True
        })

    # Topic counts for "Maitre" badges
    topics = ["Arrays", "Strings", "Enregistrements", "Listes_Chainees", "Files", "Piles"]
    topic_counts = {t: chapter_prob_passed(t) for t in topics}

    # Activity Heatmap Data (last 365 days)
    activity_map = {}
    today = datetime.date.today()
    one_year_ago = today - datetime.timedelta(days=365)
    
    for d in distinct_active_days:
        if d >= one_year_ago:
            activity_map[d.isoformat()] = sum(1 for sub in submissions if sub.timestamp.date() == d) + \
                                         sum(1 for qa in quiz_attempts if qa.timestamp.date() == d)

    # XP and Level computation
    xp_total, xp_breakdown, level_dict, xp_to_next = compute_xp_and_level(current_user.id)

    return jsonify({
        'success': True,
        'progress': {
            'chapter_stats': frontend_chapter_stats,
            'challenge_stats': challenge_stats,
            'total_quizzes_taken': total_quizzes,
            'total_challenges_attempted': total_challenges_attempted,
            'challenges_completed': passed_challenges,
            'active_days': active_days,
            'courses_completed': courses_completed,
            'hard_challenges_completed': hard_problems_passed,
            'avg_course_score': avg_course_score,
            'topic_counts': topic_counts,
            'badges': badges_response,
            'activity_map': activity_map,
            'xp_total': xp_total,
            'xp_breakdown': xp_breakdown,
            'level': level_dict,
            'xp_to_next': xp_to_next,
            'advanced_stats': {
                'challenge_topic_dist': challenge_topic_dist,
                'challenge_diff_dist': challenge_diff_dist,
                'daily_avg_quiz_score': daily_avg_quiz_score,
                'quiz_evolution_per_chapter': quiz_evolution_per_chapter
            }
        }
    })

@app.route('/leaderboard')
@app.route('/leaderboards')
def leaderboard_page():
    return render_template('leaderboard.html')

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    users = User.query.all()
    leaderboard = []
    
    for user in users:
        # Calculate Power Score using the same formula as compute_xp_and_level
        xp_total, _, level_dict, _ = compute_xp_and_level(user.id)
        
        # Breakdown counters for display in the table
        q_count = QuizAttempt.query.filter_by(user_id=user.id).filter(QuizAttempt.score / QuizAttempt.total_questions >= 0.8).count()
        c_count = ChallengeSubmission.query.filter_by(user_id=user.id, passed=True).count()
        b_count = UserBadge.query.filter_by(user_id=user.id).count()
        
        leaderboard.append({
            'name': user.name,
            'score': xp_total,
            'level': {
                'num': level_dict['num'],
                'name': level_dict['name'],
                'icon': level_dict['icon'],
                'color': level_dict['color'],
                'glow': level_dict['glow']
            },
            'quizzes': q_count,
            'challenges': c_count,
            'badges': b_count
        })
    
    # Sort by score descending
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    
    return jsonify({
        'success': True,
        'leaderboard': leaderboard
    })

@app.route('/badges')
@login_required
def badges_page():
    return render_template('badges.html')

@app.route('/api/user/badges/seen', methods=['POST'])
@login_required
def mark_badges_seen():
    try:
        data = request.json or {}
        badge_ids = data.get('badge_ids', [])
        
        if badge_ids:
            # Mark specific badges
            UserBadge.query.filter(
                UserBadge.user_id == current_user.id,
                UserBadge.badge_id.in_(badge_ids)
            ).update({"seen": True}, synchronize_session=False)
        else:
            # Mark all as seen
            UserBadge.query.filter_by(
                user_id=current_user.id, 
                seen=False
            ).update({"seen": True}, synchronize_session=False)
            
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    name = data.get('name')
    dob_str = data.get('date_of_birth')
    study_year = data.get('study_year')
    
    if not name:
        return jsonify({'success': False, 'error': 'Le pseudo est requis'}), 400
        
    current_user.name = name
    current_user.study_year = study_year
    
    if dob_str:
        try:
            from datetime import datetime
            current_user.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            pass # Ignore invalid date format
            
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Profil mis à jour avec succès'
    })

@app.route('/api/challenge/<int:problem_id>/live')
def live_contest(problem_id):
    from web.models import ChallengeSubmission
    import datetime
    
    # Simplified real-time tracking: only consider submissions from the last 24 hours
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
    submissions = ChallengeSubmission.query.filter(
        ChallengeSubmission.problem_id == problem_id,
        ChallengeSubmission.timestamp >= cutoff
    ).all()
    
    user_map = {}
    for s in submissions:
        uid = s.user_id
        if uid not in user_map:
            user_map[uid] = {
                'user': s.user,
                'attempts': 0,
                'best_score': 0,
                'passed': False,
                'best_time': 999999
            }
        
        entry = user_map[uid]
        entry['attempts'] += 1
        
        if s.score > entry['best_score']:
            entry['best_score'] = s.score
            entry['best_time'] = s.time_taken_seconds
            entry['passed'] = s.passed
        elif s.score == entry['best_score'] and s.time_taken_seconds < entry['best_time']:
            entry['best_time'] = s.time_taken_seconds

    results = []
    for uid, data in user_map.items():
        status = 'Échoué'
        if data['passed']:
            status = 'Réussi'
        elif data['best_score'] > 0:
            status = 'Partiel'
            
        results.append({
            'user_id': uid,
            'name': data['user'].name if data['user'] else f"User {uid}",
            'score': round(data['best_score'], 1),
            'time_taken': data['best_time'] if data['best_time'] != 999999 else 0,
            'attempts': data['attempts'],
            'status': status,
            'passed': data['passed']
        })
        
    results.sort(key=lambda x: (-x['score'], x['time_taken']))
    
    return jsonify({'success': True, 'leaderboard': results})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=True)
