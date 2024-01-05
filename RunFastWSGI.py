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

bjoern.run(
    wsgi_app = app,
    host = '0.0.0.0',
    port = 5000,
    reuse_port=True
)

try:
    publish.single("CarLink/availability", "offline", hostname="watchman.brewstersoft.net")
except:
    logger = logging.getLogger()
    logger.exception("Unable to post offline message")
