#!/usr/local/bin/python3
from urllib.parse import urlencode
#from urllib.request import urlopen
import urllib.request
import json
import re

def address_str(address):
  return ', '.join(filter(lambda x : x is not None,
                   [address.get('number', None), address.get('street', None),
                    address.get('town', None), address.get('postcode', None),
                    address.get('country', None)]))

def postcode_area_us(address):
  return address['postcode'][:3]

def postcode_area_uk(address):
  return address['postcode'].split(' ')[0]

postcode_area_by_country={'UK': postcode_area_uk,
                          'US': postcode_area_us}

def postcode_area(address):
  return postcode_area_by_country[address['country']](address)

def is_usable_uk_address(address):
  return address['postcode'] is not None and \
    address['number'] is not None and \
    re.fullmatch(r'[A-Z]{2}[0-9]{1,2} [0-9][A-Z]{2}', address['postcode']) is not None

def is_usable_us_address(address):
  pass

address_validators={'UK': is_usable_uk_address,
                    'US': is_usable_us_address}

def is_usable_address(address):
  try:
    return address_validators[address['country']](address)
  except KeyError:
    return False

class MemberwiseEquality:
  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.__dict__ == other.__dict__
    return NotImplemented

  def __ne__(self, other):
    if isinstance(other, self.__class__):
      return self.__dict__ != other.__dict__
    return NotImplemented


class PostcodeRateBook:
  def __init__(self, postcode_map):
    self.postcode_map=postcode_map

  def price(self, origin, destination):
    return self.postcode_map[postcode_area(origin)][postcode_area(destination)]

class DistanceSource:
  def distance(self, origin, destination):
    pass


class FlatRateDistanceRateBook:
  def __init__(self, distance_source, rate_pence_per_mile):
    self.rate=rate_pence_per_mile
    self.distance_source=distance_source

  def price(self, origin, destination):
    return self.rate * self.distance_source.distance(origin, destination)


class GoogleDistanceURL:
  def __init__(self, key):
    self.key=key

  def url(self, origin, destination):
    return 'https://maps.googleapis.com/maps/api/distancematrix/json?' +\
            urlencode({'units': 'imperial', 'origins': address_str(origin),
                       'destinations': address_str(destination), 'key': self.key}) 


class Distance(MemberwiseEquality):
  def __init__(self, dist_text, dist_value, time_text, time_value):
    self.dist_text=dist_text
    self.dist_value=dist_value
    self.time_text=time_text
    self.time_value=time_value


class GoogleDistance:
  def __init__(self, key):
    self.url=GoogleDistanceURL(key)

  def distance(self, origin, destination):
    with urllib.request.urlopen(self.url.url(origin, destination)) as response:
      json_response=json.loads(response.read());
      distance=json_response['rows'][0]['elements'][0]['distance']
      duration=json_response['rows'][0]['elements'][0]['duration']
      return Distance(distance['text'], distance['value'],
                      duration['text'], duration['value'])

class Pricer:
  def __init__(self, ratebook):
    self.ratebook=ratebook

  def quote(self, journey):
    origin=journey['origin']
    destination=journey['destination']
    try:
      return {'origin': origin,
              'destination': destination,
              'price':self.ratebook.price(origin, destination)}
    except KeyError as e:
      key=e.args[0]
      if key==postcode_area(origin):
        error_address='Origin'
      elif key==postcode_area(destination):
        error_address='Destination'
      else:
        error_address='Unknown'
      return {'origin':origin,
              'destination':destination,
              'error':"{} postcode '{}' not found".format(error_address, key)}


class BookingStore:
  def __init__(self):
    self.bookings={}
    self.last_id=0

  def add(self, booking):
    self.last_id+=1
    self.bookings[self.last_id]=booking
    return self.last_id


