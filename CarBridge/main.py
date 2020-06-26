import shelve
import flask
from . import app, SETTINGS_FILE

@app.route('/')
def index():
    template_args={}
    with shelve.open(SETTINGS_FILE) as settings:
        targets = settings.get('targets', {})
        
    for button,url in targets.items():
        if url is None:
            url=''
        template_args[button]=url
        
    print(template_args)

    return flask.render_template("targets.html",**template_args)


@app.route('/setTargets', methods=["POST"])
def setTargets():
    targets = {}
    for target in flask.request.form:
        targets[target] = flask.request.form.get(target)
        
    with shelve.open(SETTINGS_FILE) as settings:
        settings['targets'] = targets
    print(targets)

    return flask.redirect(flask.url_for("index"))
