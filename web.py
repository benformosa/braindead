#!/usr/bin/python3

import flask
import mon
import yaml

app = flask.Flask(__name__)
configfile = 'config.yml'

with open(configfile, 'r') as stream:
    try:
        config = yaml.load(stream)
    except yaml.YAMLError as e:
        print(e)

@app.route('/')
def services():
    with open(config['services'], 'r') as stream:
        try:
            services = yaml.load(stream) 
        except yaml.YAMLError as e:
            print(e)

    checked_services = mon.check_services(services)
    
    return flask.render_template('services.html.j2', services=checked_services)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=80)
