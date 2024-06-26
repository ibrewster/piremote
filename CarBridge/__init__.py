"""Initalize the application. We do some weird things with import order here to
allow us to better show progress as we load."""
import os
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings')

import logging
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

LOGGER = logging.getLogger()

LOGGER.info("Importing GPIOZero")
from gpiozero import LED,Button

# Set up some I/O
# Button status LEDs
LOGGER.info("Setting up LEDS")
led_a=LED(4,initial_value=True)
led_a.blink()

led_b=LED(18,initial_value=False)
led_c=LED(22,initial_value=False)
led_d=LED(24,initial_value=False)

status_green=LED(12)
status_red=LED(13)

from .utils import LEDGroup
button_leds = LEDGroup(led_a, led_b, led_c, led_d)

# Setup the exit function
import atexit
import paho.mqtt.publish as publish

@atexit.register
def at_exit():
    try:
        publish.single("CarLink/availability", "offline", hostname="conductor.brewstersoft.net",
                       auth={'username': 'hamqtt','password': 'Sh@nima821',}, retain=True)
    except:
        LOGGER.exception("Unable to post offline message")
        
    LOGGER.info("Execution complete. Shutting down")
    status_red.blink(on_time=.3,off_time=.3,n=3, background = False)
    

LOGGER.info("Importing Listener")
from .watcher import Listener

led_a.on()
led_b.blink()

LOGGER.info("Importing Flask")
import flask

learn_button=Button(16)
reset_button = Button(5, hold_time=3)

led_b.on()
led_c.blink()

LOGGER.info("Creating Listener")
rx_listner = Listener()

learn_button.when_pressed=rx_listner.set_learn_mode

reset_button.when_released = rx_listner.reset_released
reset_button.when_held = rx_listner.reset_held

led_c.on()
led_d.blink()

from .utils import run_url, startup_complete
rx_listner.set_association(1,run_url)
rx_listner.set_association(2,run_url)
rx_listner.set_association(3,run_url)
rx_listner.set_association(4,run_url)

LOGGER.info("Starting Flask")

app = flask.Flask(__name__)

LOGGER.info("Flask app initialized")

#Drop priviliges
if os.getuid() ==0:
    UID=33
    GID=33
    
    os.setgroups([])
    os.setgid(GID)
    os.setuid(UID)

from . import main

startup_complete()
