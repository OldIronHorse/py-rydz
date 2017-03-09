#!/usr/local/bin/python3
from urllib.parse import urlencode
#from urllib.request import urlopen
import urllib.request
import json

class MemberwiseEquality:
  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.__dict__ == other.__dict__
    return NotImplemented

  def __ne__(self, other):
    if isinstance(other, self.__class__):
      return self.__dict__ != other.__dict__
    return NotImplemented


class Address(MemberwiseEquality):
  def __init__(self, number=None, street=None, town=None, postcode=None, country=None):
    self.number=number
    self.street=street
    self.town=town
    self.postcode=postcode
    self.country=country

  def __str__(self):
    return ', '.join(filter(lambda x : x is not None,
                     [self.number, self.street, self.town, self.postcode, self.country]))


class UKAddress(Address):
  def postcode_area(self):
    return self.postcode.split(' ')[0]


class USAddress(Address):
  def postcode_area(self):
    return self.postcode[:3]


class PostcodeRateBook:
  def __init__(self, postcode_map):
    self.postcode_map=postcode_map

  def price(self, origin, destination):
    return self.postcode_map[origin.postcode_area()][destination.postcode_area()]

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
            urlencode({'units': 'imperial', 'origins': origin,
                       'destinations': destination, 'key': self.key}) 


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
    with urllib.request.urlopen(self.url.url(str(origin), str(destination))) as response:
      json_response=json.loads(response.read());
      distance=json_response['rows'][0]['elements'][0]['distance']
      duration=json_response['rows'][0]['elements'][0]['duration']
      return Distance(distance['text'], distance['value'],
                      duration['text'], duration['value'])

class Pricer:
  def __init__(self, ratebook):
    self.ratebook=ratebook

  def json_quote(self, json):
    origin=UKAddress(postcode=json['origin']['postcode'])
    destination=UKAddress(postcode=json['destination']['postcode'])
    try:
      return {'origin':json['origin'],
              'destination':json['destination'],
              'price':self.ratebook.price(origin, destination)}
    except KeyError as e:
      key=e.args[0]
      if key==origin.postcode_area():
        error_address='Origin'
      elif key==destination.postcode_area():
        error_address='Destination'
      else:
        error_address='Unknown'
      return {'origin':json['origin'],
              'destination':json['destination'],
              'error':"{} postcode '{}' not found".format(error_address, key)}
