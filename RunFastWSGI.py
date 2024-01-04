import paho.mqtt.publish as publish

import bjoern
from CarBridge import app

bjoern.run(
    wsgi_app = app,
    host = '0.0.0.0',
    port = 5000,
    reuse_port = True)

publish.single("CarLink/availability", "offline", hostname="watchman.brewstersoft.net")
