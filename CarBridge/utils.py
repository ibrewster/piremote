import shelve
import socket
import time

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


class LEDGroup:
    def __init__(self, *members):
        self._members = members
        
    def on(self):
        for item in self._members:
            item.on()
    
    def off(self):
        for item in self._members:
            item.off()
            
    def blink(self, on_time=1, off_time=1, n=None, background=True):
        for item in self._members:
            item.blink(on_time, off_time, n, True) # Must be background
            
        if n is not None and background is False:
            sleep_time = (on_time + off_time) * n
            time.sleep(sleep_time) # block for the blinking time


def run_url(button):
    with shelve.open(SETTINGS_FILE) as settings:
        targets = settings.get('targets', {})
        
    url = targets.get('button_' + str(button))
    if url is None or url == '':
        LOGGER.warning(f"No url specified for button {button}")
        return
    
    try:
        result=requests.get(url, verify = False)
    except (requests.exceptions.ConnectionError, requests.exceptions.MissingSchema):
        LOGGER.exception(f"Connection error for url {url}")
        status_red.blink(on_time=1/14, off_time=1/4, n=6)
    else:        
        if result.status_code==200:
            LOGGER.info(f"Succesfully called url {url}")
            status_green.blink(on_time=1/7, off_time=1/7, n=4)
        else:
            LOGGER.error(f'Error calling url {url} (status code {result.status_code}), text: {result.text}')
            status_red.blink(on_time=1/7, off_time=1/7, n=4)        
    
    LOGGER.info(f"Completed url call for button {button}")
    
def post_mqtt(button):
    with shelve.open(SETTINGS_FILE) as settings:
        mqtt_broker = settings.get('mqtt_broker')
        mqtt_user = settings.get('mqtt_user')
        mqtt_password = settings.get('mqtt_password')
        mqtt_channel = settings.get('mqtt_channel', 'CarLink/remote/{button}')
        
    if mqtt_broker is None:
        LOGGER.warning("No MQTT Broker specified, not posting message")
        return
    
    auth = None
    if mqtt_user is not None and mqtt_password is not None:
        auth = {'username': mqtt_user, 'password': mqtt_password}
    
    try:
        publish.single(mqtt_channel.format(button=button), "ON", hostname=mqtt_broker,
                       auth=auth)
    except:
        status_red.blink(on_time=1/7, off_time=1/7, n=4)
        LOGGER.exception("Unable to post message in response to button press")
    else:
        LOGGER.info("Message posted to MQTT in response to button press")
        status_green.blink(on_time=1/7, off_time=1/7, n=4)
        
    
def startup_complete():
    LOGGER.info("Running final startup")
    LOGGER.info("Checking for network...")
    while True:
        try:
            publish.single("CarLink/availability", "online", hostname="conductor.brewstersoft.net",
                           auth={'username': 'hamqtt','password': 'Sh@nima821',}, retain=True)
            break
        except (socket.gaierror, socket.timeout):
            LOGGER.info("unable to post available message to MQTT. Waiting for MQTT/Network")
                
    
    led_d.on()
    status_green.blink(on_time=.3,off_time=.3,n=3, background = False)

    LOGGER.info("Blink Complete. Turning off LEDS")

    led_a.off()
    led_b.off()
    led_c.off()
    led_d.off()
    
    LOGGER.info("Startup complete")
    