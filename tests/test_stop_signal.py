import threading
import queue
import time
import sys
import os
sys.path.append(os.getcwd())
from web.app import app, session, terminate_thread

# Mock session for standalone testing if needed, or use app's session
def test_system_exit_handling():
    # Setup session
    session.output_queue = queue.Queue()
    session.input_queue = queue.Queue()
    session.is_running = True
    
    def target():
        try:
            while True:
                time.sleep(0.1)
        except SystemExit:
            session.output_queue.put({'type': 'stopped', 'data': 'Stopped'})
        finally:
            if session.is_running:
                 session.output_queue.put({'type': 'finished'})

    t = threading.Thread(target=target)
    t.start()
    session.current_thread = t
    
    time.sleep(0.5)
    
    # Trigger stop
    terminate_thread(t)
    # Also simulate backend logic of clearing is_running logic *after* killing?
    # In app.py: stop_execution sets is_running=False, THEN kills thread.
    session.is_running = False 
    
    t.join(timeout=2)
    assert not t.is_alive()
    
    # Check queue
    messages = []
    while not session.output_queue.empty():
        messages.append(session.output_queue.get())
        
    print(messages)
    
    # Should contain 'stopped'
    has_stopped = any(m['type'] == 'stopped' for m in messages)
    assert has_stopped
    
    # Should NOT contain 'finished' because is_running was set to False
    has_finished = any(m['type'] == 'finished' for m in messages)
    assert not has_finished

if __name__ == "__main__":
    test_system_exit_handling()
    print("Test Passed")
