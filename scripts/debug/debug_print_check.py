import sys
import contextlib
import threading
import queue
import time
from web.debugger import TraceRunner

output_queue = queue.Queue()

class StreamToQueue:
    def write(self, text):
        if text:
            output_queue.put(f"stdout: {repr(text)}")
    def flush(self):
        pass

def worker():
    stream = StreamToQueue()
    code = """
print("Hello World")
x = 10
print("X is", x)
"""
    tracer = TraceRunner()
    
    print("Worker: Starting redirect")
    with contextlib.redirect_stdout(stream):
        print("Worker: Inside redirect (before exec)")
        tracer.run(code, {}, stdout_capture=stream)
        print("Worker: Inside redirect (after exec)")
    print("Worker: Finished")

t = threading.Thread(target=worker)
t.start()
t.join()

print("--- QUEUE CONTENTS ---")
while not output_queue.empty():
    print(output_queue.get())
