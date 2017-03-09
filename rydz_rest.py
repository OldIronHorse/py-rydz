#!/usr/local/bin/python3
from rydz import Pricer, PostcodeRateBook
import logging
import json
from flask import Flask, request
app = Flask(__name__)

postcode_pricer=Pricer(PostcodeRateBook({'TW11':{'NW1':22.5, 'RM14':65.25},
                                         'NW1': {'RM14':52.5, 'TW11':23.25},
                                         'RM14':{'NW1':62.5, 'TW11':63.25}}))

@app.route("/")
def index():
  return "Index Page"

@app.route("/hello")
def hello():
  return "Hello World!"

@app.route("/quote") #GET by default
def quote():
  content = request.get_json()
  logging.info('/quote: %s', content)
  response=postcode_pricer.json_quote(content)
  logging.info('/quote: %s', response)
  return json.dumps(response)

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  app.run()
