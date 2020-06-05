from lens_app import app
from flask import render_template
from flask import request

@app.route('/')

@app.route('/index')
def index():
    return render_template("index.html",)

@app.route('/output')
def output():
  usage = request.args.get('inputGroupSelect01')
  number = 'Coming soon...'
  return render_template("output.html", my_output=number)