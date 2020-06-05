from flask import Flask

app = Flask(__name__)
from lens_app import views
