#!/usr/bin/env python
from rydz import Pricer, PostcodeRateBook, add_booking
import logging
import json
from flask import Flask, request, Response, jsonify
from flask_pymongo import PyMongo
from flask.json import JSONEncoder
from bson import ObjectId

class MongoJSONEncoder(JSONEncoder):
  def default(self, o):
    if isinstance(o, ObjectId):
      return str(o)
    else:
      return JSONEncoder(self, o)


app = Flask(__name__)
app.json_encoder=MongoJSONEncoder

app.config['MONGO_DBNAME'] = 'rides'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/restdb'

mongo = PyMongo(app)

postcode_pricer=Pricer(PostcodeRateBook({'TW11':{'NW1':22.5, 'RM14':65.25},
                                         'NW1': {'RM14':52.5, 'TW11':23.25},
                                         'RM14':{'NW1':62.5, 'TW11':63.25}}))

def price_booking(pricer, booking_json):
  booking_json['quoted_price']=pricer.quote(booking_json)['price']
  return booking_json

@app.route("/quote") #GET by default
def quote():
  content = request.get_json()
  logging.debug('/quote: %s', content)
  response=postcode_pricer.quote(content)
  logging.debug('/quote: %s', response)
  return jsonify(response)

@app.route("/bookings", methods=['GET', 'POST'])
def bookings():
  content = request.get_json()
  app.logger.debug('/bookings: %s', content)
  if request.method=='POST':
    response=add_booking(mongo.db.bookings, price_booking(postcode_pricer, request.get_json()))
  elif request.method=='GET':
    #list bookings
    bs=[]
    for b in mongo.db.bookings.find():
      bs.append(b)
    response={'status':'OK', 'bookings':bs}
  else:
    pass
  app.logger.debug('/bookings: %s', response)
  return jsonify(response)

@app.route("/bookings/<booking_id>", methods=['GET', 'PUT', 'DELETE'])
def bookings_by_id(booking_id):
  content = request.get_json()
  app.logger.debug('/bookings/%s: %s', booking_id, content)
  bookings=mongo.db.bookings
  try:
    if request.method=='GET':
      #fetch booking details
      booking=bookings.find_one({"_id":ObjectId(booking_id)})
      response={'status':'OK',
                'booking':booking}
    elif request.method=='PUT':
      #update booking details
      #TODO update in place
      response=add_booking(mongo.db.bookings, request.get_json())
    elif request.method=='DELETE':
      #cancel booking
      response={'status': 'OK',
                'booking': booking_store.pop(booking_id)}
    else:
      pass
  except KeyError:
    response={'status':'ERROR',
             'reason':'no booking for id',
             'booking_id':booking_id}
  app.logger.debug('/bookings/%s: %s', booking_id, response)
  return jsonify(response)

if __name__ == "__main__":
  #TODO set sensible logging format
  handler=logging.StreamHandler()
  handler.setLevel(logging.DEBUG)
  app.logger.addHandler(handler)
  app.logger.setLevel(logging.DEBUG)
  app.run()
