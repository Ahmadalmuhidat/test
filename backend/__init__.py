from flask import Flask
import json

app = Flask(__name__)

from backend import routes
