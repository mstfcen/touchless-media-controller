import time
from pynput.keyboard import Controller, Key

class MediaInterface:
    """Handles keyboard simulation for media control."""
    
    def __init__(self):
        self.keyboard = Controller()
        self.last_action_time = {}

    def execute_command(self, action_key, action_name, cooldown=0.1, log_message=None):
        """
        Presses a key with a cooldown timer to prevent spamming.
        """
        now = time.time()
        last_time = self.last_action_time.get(action_name, 0)
        
        if now - last_time > cooldown:
            self.keyboard.press(action_key)
            self.keyboard.release(action_key)
            self.last_action_time[action_name] = now
            
            if log_message:
                print(log_message)