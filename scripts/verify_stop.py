import threading
import time
import ctypes
import queue

def terminate_thread(thread):
    if not thread or not thread.is_alive():
        print("Thread not alive")
        return

    print(f"Terminating thread {thread.ident}")
    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exc)
    if res == 0:
        print("Thread ID not found")
    elif res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), None)
        print("Failed to set async exc")
    else:
        print("Async exc set successfully")

def target():
    try:
        print("Thread started")
        while True:
            time.sleep(0.1)
    except SystemExit:
        print("Thread caught SystemExit")
    except Exception as e:
        print(f"Thread caught {type(e)}")
    finally:
        print("Thread exiting")

t = threading.Thread(target=target)
t.start()
time.sleep(1)
print("Stopping thread...")
terminate_thread(t)
t.join(timeout=2)
if t.is_alive():
    print("Thread FAILED to stop")
else:
    print("Thread stopped successfully")
