import threading
import sys
import time

class Spinner:
    def __init__(self, message="Loading"):
        self.spinning = False
        self.thread = None
        self.message = message
        self.chars = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
        
    def spin(self):
        i = 0
        while self.spinning:
            sys.stdout.write(f'\r{self.message} {self.chars[i % len(self.chars)]} ')
            sys.stdout.flush()
            i += 1
            time.sleep(0.08)  # Smooth animation speed
    
    def start(self):
        self.spinning = True
        self.thread = threading.Thread(target=self.spin, daemon=True)
        self.thread.start()
    
    def stop(self, final_message="Done!"):
        self.spinning = False
        if self.thread:
            self.thread.join()
        sys.stdout.write(f'\r{final_message}\n')
        sys.stdout.flush()

__all__ = ['Spinner']
