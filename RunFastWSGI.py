import atexit
import logging

import paho.mqtt.publish as publish

#import fastwsgi
import bjoern
from CarBridge import app

# fastwsgi.run(
    # wsgi_app = app,
    # host = '0.0.0.0',
    # port = 5000
# )

@atexit.register
def at_exit():
    logger = logging.getLogger()
    try:
        publish.single("CarLink/availability", "offline", hostname="conductor.brewstersoft.net",
                       auth={'username': 'hamqtt','password': 'Sh@nima821',}, retain=True)
    except:
        logger.exception("Unable to post offline message")
        
    logger.info("Execution complete. Shutting down")


bjoern.run(
    wsgi_app = app,
    host = '0.0.0.0',
    port = 5000,
    reuse_port=True
)