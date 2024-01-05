import paho.mqtt.publish as publish
import subprocess

import shelve
from .r315 import rx
from . import (SETTINGS_FILE,
               led_a,
               led_b,
               led_c,
               led_d,
               LOGGER)

class Listener:
    _learn_mode = False
    _rx = None
    _associations = {}
    LEDs = (led_a, led_b, led_c, led_d)
    _reset_held = False
    
    def __init__(self, gpio = 20):
        with shelve.open(SETTINGS_FILE) as remote_file:
            self._known_remotes=remote_file.get('remotes',[])
            try:
                self._associations = remote_file.get('associations', {})
            except (AttributeError, ModuleNotFoundError):
                self._associations = {}
            
        self._rx = rx(gpio=gpio, callback=self._rx_callback)

    def _rx_callback(self, remote_id, button_num, code, bits, gap, t0, t1):
        """This will be run when a button is pressed on a known remote."""
        LOGGER.info(f"Received button press from {remote_id}, Button: {button_num}")
        if self._learn_mode:
            if remote_id not in self._known_remotes:
                self._known_remotes.append(remote_id)
                with shelve.open(SETTINGS_FILE) as remote_file:
                    remote_file['remotes']=self._known_remotes
                LOGGER.warning(f"Added remote with id {remote_id}")
            return
    
        if remote_id not in self._known_remotes:
            LOGGER.warning(f"Ignoring message from remote {remote_id} as it is not in our known remotes database")
            return #Ignore input from unknown remotes
    
        LOGGER.debug(f"Remote ID: {remote_id} Button: {button_num} Bits: {bits} gap: {gap} t0:{t0} t1:{t1}")
        
        self.LEDs[button_num-1].blink(on_time = .5, off_time = 0, n = 1)
        
        if button_num in self._associations:
            self._associations[button_num](button_num)
            
        try:
            publish.single("CarLink/remote", f"ON_{button_num}", hostname="conductor.brewstersoft.net",
                           auth={'username': 'hamqtt','password': 'Sh@nima821',})
        except:
            LOGGER.exception("Unable to post message in response to button press")
        
    
    def set_learn_mode(self):
        self._learn_mode=not self._learn_mode
        if self._learn_mode:
            LOGGER.warning("Entered Learn Mode")
        else:
            LOGGER.warning("Left Learn Mode")
            
    def set_association(self, button, func):
        self._associations[button] = func
        with shelve.open(SETTINGS_FILE) as remote_file:
            remote_file['associations'] = self._associations
            
    def reset_released(self):
        # Make sure we jsut pressed the button, not held it down
        if self._reset_held:
            self.shutdown()
            return
        
        LOGGER.warning("Restarting due to button press")
        subprocess.call('sudo reboot', shell=True)

    def shutdown(self):
        LOGGER.warning("Shutting down due to reset hold")
        subprocess.call('sudo shutdown -h now', shell=True)
        
    def reset_held(self):
        self._reset_held = True
        
        