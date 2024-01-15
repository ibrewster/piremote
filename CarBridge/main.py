import shelve
import flask
from . import app, SETTINGS_FILE

@app.route('/')
def index():
    
    with shelve.open(SETTINGS_FILE) as settings:
        targets = settings.get('targets', {})
        mqtt_broker = settings.get('mqtt_broker', '')
        mqtt_user = settings.get('mqtt_user', '')
        mqtt_password = settings.get('mqtt_password', '')
        mqtt_channel = settings.get('mqtt_channel', '')
        
    template_args={
        'mqtt_broker': mqtt_broker,
        'mqtt_user': mqtt_user,
        'mqtt_password': mqtt_password,
        'mqtt_channel': mqtt_channel,
    }
    
    for button,url in targets.items():
        if url is None:
            url=''
        template_args[button]=url
        
    return flask.render_template("targets.html",**template_args)


@app.route('/setTargets', methods=["POST"])
def setTargets():
    targets = {}
    for target in flask.request.form:
        targets[target] = flask.request.form.get(target)
        
    with shelve.open(SETTINGS_FILE) as settings:
        settings['targets'] = targets

    return flask.redirect(flask.url_for("index"))

@app.route('/setMQTT', methods=["POST"])
def setMQTT():
    with shelve.open(SETTINGS_FILE) as settings:
        for setting in flask.request.form:
            settings[setting] = flask.request.form[setting]
            
    return flask.redirect(flask.url_for("index"))
        
    
