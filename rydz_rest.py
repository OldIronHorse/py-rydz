#!/usr/local/bin/python3
from rydz import Pricer, PostcodeRateBook, BookingStore, is_usable_address
import logging
import json
from datetime import datetime
from flask import Flask, request, Response
app = Flask(__name__)

postcode_pricer=Pricer(PostcodeRateBook({'TW11':{'NW1':22.5, 'RM14':65.25},
                                         'NW1': {'RM14':52.5, 'TW11':23.25},
                                         'RM14':{'NW1':62.5, 'TW11':63.25}}))

booking_store=BookingStore()

@app.route("/quote") #GET by default
def quote():
  content = request.get_json()
  logging.debug('/quote: %s', content)
  response=postcode_pricer.quote(content)
  logging.debug('/quote: %s', response)
  return Response(json.dumps(response), mimetype='application/json')

@app.route("/bookings", methods=['GET', 'POST'])
def bookings():
  content = request.get_json()
  app.logger.debug('/bookings: %s', content)
  if request.method=='POST':
    try:
      #create a booking
      booking_json=request.get_json()
      if not is_usable_address(booking_json['origin']):
        response={'status':'ERROR','reason':'invalid origin address'}
      elif not is_usable_address(booking_json['destination']):
        response={'status':'ERROR','reason':'invalid destination address'}
      else:
        booking_json['quoted_price']=postcode_pricer.quote(booking_json)['price']
        datetime.strptime(booking_json['pickup_time'], '%Y-%m-%d %H:%M')
        booking_id=booking_store.add(booking_json)
        response={"status":'OK',
                  "booking_id": booking_id,
                  "booking": booking_store.bookings[booking_id]}
    except ValueError as ve:
      response={"status": "ERROR",
                "reason": str(ve)}
    except KeyError as ke:
      response={"status": "ERROR",
                "reason": "{} missing".format(ke)}
  elif request.method=='GET':
    #list bookings
    response={'status':'OK', 'bookings':booking_store.bookings}
  else:
    pass
  app.logger.debug('/bookings: %s', response)
  return Response(json.dumps(response), mimetype='application/json')

@app.route("/bookings/<booking_id>", methods=['GET', 'PUT', 'DELETE'])
def bookings_by_id(booking_id):
  content = request.get_json()
  app.logger.debug('/bookings/%s: %s', booking_id, content)
  try:
    if request.method=='GET':
      #fetch booking details
      response={'status':'OK',
                'booking':booking_store.bookings[booking_id],
                'booking_id':booking_id}
    elif request.method=='PUT':
      #update booking details
      pass
    elif request.method=='DELETE':
      #cancel booking
      response={'status': 'OK',
                'booking': booking_store.pop(booking_id)}
      pass
    else:
      pass
  except KeyError:
    response={'status':'ERROR',
             'reason':'no booking for id',
             'booking_id':booking_id}
  app.logger.debug('/bookings/%s: %s', booking_id, response)
  return Response(json.dumps(response), mimetype='application/json')

if __name__ == "__main__":
  #TODO set sensible logging format
  handler=logging.StreamHandler()
  handler.setLevel(logging.DEBUG)
  app.logger.addHandler(handler)
  app.logger.setLevel(logging.DEBUG)
  app.run()
