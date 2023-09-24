from flask import Flask, render_template, request
import json
app=Flask(__name__)

def hex_to_rgb(hexa):
    return [int(hexa[i:i+2], 16)  for i in (0, 2, 4)]

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

@app.route("/config")
def get_config():
    with open('config.json', 'r') as json_f:
        config = json.load(json_f)
    return json.dumps(config)

@app.route("/edit_config", methods = ['POST', 'GET'])
def edit_config():
    with open('config.json', 'r') as json_f:
        config = json.load(json_f)
    if request.method == "GET":
        return render_template('edit_config.jinja', config=config, sorted=sorted, rgb_to_hex=rgb_to_hex)
    if request.method == 'POST':
        config["forecast_interval_minutes"] = int(request.form["interval-select"])
        config["latitude"]=float(request.form["latitude-select"])
        config["longitude"]=float(request.form["longitude-select"])
        list_dbz = config["colors"].keys()
        for dbz in list_dbz:
            config["colors"][dbz]["rgb"]=hex_to_rgb(request.form[dbz+'_color'].lstrip('#'))
            config["colors"][dbz]["name"]=request.form[dbz+'_name']#.rstrip(" rain color")
        with open('config.json', 'w') as json_f:
            json.dump(config, json_f,indent=2)
        return "Sucess "+ json.dumps(config)


        
    