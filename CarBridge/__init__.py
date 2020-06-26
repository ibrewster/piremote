import os
SETTINGS_FILE = 'known_remotes'

from .watcher import Listener

import flask
from gpiozero import LED,Button


# Set up some I/O
# Button status LEDs
led_a=LED(4,initial_value=True)
led_b=LED(18,initial_value=True)
led_c=LED(22,initial_value=True)
led_d=LED(24,initial_value=True)
status_green=LED(16)
status_red=LED(13)

learn_button=Button(12)

rx_listner = Listener()
learn_button.when_pressed=rx_listner.set_learn_mode

from .actions import run_url
rx_listner.set_association(1,run_url)

app = flask.Flask(__name__)

#Drop priviliges
if os.getuid() ==0:
    UID=33
    GID=33
    
    os.setgroups([])
    os.setgid(GID)
    os.setuid(UID)

from . import main
