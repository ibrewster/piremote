from r315 import rx
import shelve
import pigpio
from signal import pause
from gpiozero import PWMLED,LED,Button

import logging
LOGGER = logging.getLogger()
   
if __name__ == "__main__":
   RX=20
   
   with shelve.open("known_remotes") as remote_file:
      _known_remotes=remote_file.get('remotes',[])

   learn_mode=False
   
   def rx_callback(remote_id,button_num, code, bits, gap, t0, t1):
      """This will be run when a button is pressed on a known remote."""
      if learn_mode:
         if remote_id not in _known_remotes:
            _known_remotes.append(remote_id)
            with shelve.open("known_remotes") as remote_file:
               remote_file['remotes']=_known_remotes
            LOGGER.warning(f"Added remote with id {remote_id}")
         return
      
      if remote_id not in _known_remotes:
         return #Ignore input from unknown remotes
      
      LOGGER.debug(f"Remote ID: {remote_id} Button: {button_num} Bits: {bits} gap: {gap} t0:{t0} t1:{t1}")
      
   def set_learn_mode():
      global learn_mode
      learn_mode=not learn_mode
      if learn_mode:
         LOGGER.warning("Entered Learn Mode")
      else:
         LOGGER.warning("Left Learn Mode")

   rx=rx(gpio=RX, callback=rx_callback)
   
   learn_button=Button(12)
   learn_button.when_pressed=set_learn_mode

   LOGGER.info(f"Waiting for input on GPIO {RX}")
   pause()   