import bjoern
from CarBridge import app

bjoern.run(
    wsgi_app = app,
    host = '0.0.0.0',
    port = 5000,
    reuse_port = True
)