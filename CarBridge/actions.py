import shelve
import requests

from . import SETTINGS_FILE, status_red, status_green

def run_url(button):
    with shelve.open(SETTINGS_FILE) as settings:
        targets = settings.get('targets', {})
        
    url = targets.get('button_' + str(button))
    if url is None:
        print(f"No url specified for button {button}")
        status_red.blink(on_time=2/7, off_time=2/7, n=2)
        return
    
    try:
        result=requests.get(url)
    except (requests.exceptions.ConnectionError, requests.exceptions.MissingSchema):
        print(f"Connection error for url {url}")
        status_red.blink(on_time=1/14, off_time=1/4, n=6)
    else:        
        if result.status_code==200:
            print(f"Succesfully called url {url}")
            status_green.blink(on_time=1/7, off_time=1/7, n=4)
        else:
            print(f'Error calling url {url}')
            status_red.blink(on_time=1/7, off_time=1/7, n=4)        
    
    print("This is the action for button 1")