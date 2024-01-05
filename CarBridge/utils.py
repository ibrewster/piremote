import shelve
import urllib

import requests
import paho.mqtt.publish as publish


from . import (SETTINGS_FILE,
               status_red,
               status_green,
               led_a,
               led_b,
               led_c,
               led_d,
               LOGGER)

def run_url(button):
    with shelve.open(SETTINGS_FILE) as settings:
        targets = settings.get('targets', {})
        
    url = targets.get('button_' + str(button))
    if url is None:
        LOGGER.error(f"No url specified for button {button}")
        status_red.blink(on_time=2/7, off_time=2/7, n=2)
        return
    
    try:
        result=requests.get(url, verify = False)
    except (requests.exceptions.ConnectionError, requests.exceptions.MissingSchema):
        LOGGER.error(f"Connection error for url {url}")
        status_red.blink(on_time=1/14, off_time=1/4, n=6)
    else:        
        if result.status_code==200:
            LOGGER.info(f"Succesfully called url {url}")
            status_green.blink(on_time=1/7, off_time=1/7, n=4)
        else:
            LOGGER.error(f'Error calling url {url}')
            status_red.blink(on_time=1/7, off_time=1/7, n=4)        
    
    LOGGER.info(f"Completed url call for button {button}")
    
def startup_complete():
    LOGGER.info("Running startup final")
    LOGGER.info("Checking for network...")
    while True:
        try:
            urllib.request.urlopen('https://watchman.brewstersoft.net', timeout=1)
            break
        except:
            LOGGER.info("Unable to establish connection to watchman. Waiting for network.")
            
    try:
        status_green.blink(on_time=.3,off_time=.3,n=3, background = False)
    except Exception as e:
        LOGGER.info(f"Unable to blink green light. {e}")
    finally:
        LOGGER.debug("This should always print.")
    LOGGER.info("Blink Complete. Turning off LEDS")

    led_a.off()
    led_b.off()
    led_c.off()
    led_d.off()
    
    LOGGER.info("Sending MQTT online")
    publish.single("CarLink/availability", "online", hostname="watchman.brewstersoft.net")
    
    LOGGER.info("Ran startup complete")
    