#!/usr/local/bin/python3

from flask import Flask, request
app = Flask(__name__)

@app.route("/")
def index():
  return "Index Page"

@app.route("/hello")
def hello():
  return "Hello World!"

@app.route("/quote") #GET by default
def quote():
  content = request.get_json()
  print(content)
  return "not enough info :-("

if __name__ == "__main__":
  app.run()
