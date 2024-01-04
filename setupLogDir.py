import os
LOG_DIR = '/var/log/rf2mqtt'
os.makedirs(LOG_DIR, exist_ok=True)
os.chmod(LOG_DIR, 777)