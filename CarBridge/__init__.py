"""Initalize the application. We do some weird things with import order here to
allow us to better show progress as we load."""
import os
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings')

from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'filename': '/var/log/rf2mqtt/error.log',
            'maxBytes': 1048576,
            'backupCount': 5,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi', 'file']
    }
})

print("Importing GPIOZero")
from gpiozero import LED,Button

# Set up some I/O
# Button status LEDs
print("Setting up LEDS")
led_a=LED(4,initial_value=True)
led_b=LED(18,initial_value=False)
led_c=LED(22,initial_value=False)
led_d=LED(24,initial_value=False)
status_green=LED(12)
status_red=LED(13)

print("Importing Listener")
from .watcher import Listener
led_b.on()

print("Importing Flask")
import flask

learn_button=Button(16)
reset_button = Button(5, hold_time=3)

led_c.on()
print("Creating Listener")
rx_listner = Listener()
learn_button.when_pressed=rx_listner.set_learn_mode
reset_button.when_pressed = rx_listner.restart
reset_button.when_held = rx_listner.shutdown
led_d.on()

from .utils import run_url, startup_complete
rx_listner.set_association(1,run_url)
rx_listner.set_association(2,run_url)
rx_listner.set_association(3,run_url)
rx_listner.set_association(4,run_url)

print("Starting Flask")

app = flask.Flask(__name__)

print("Running")

#Drop priviliges
if os.getuid() ==0:
    UID=33
    GID=33
    
    os.setgroups([])
    os.setgid(GID)
    os.setuid(UID)

from . import main

startup_complete()
