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
  return 'postcode' in address and \
    'number' in address and \
    'street' in address and \
    re.fullmatch(r'[A-Z]{2}[0-9]{1,2} [0-9][A-Z]{2}', address['postcode']) is not None

us_states={'AL': ('Alabama', 'Ala.'),
           'AK': ('Alaska', 'Alaska'),
           'AS': ('American Samoa', ''),
           'AZ': ('Arizona', 'Ariz.'),
           'AR': ('Arkansas', 'Ark.'),
           'CA': ('California', 'Calif.'),
           'CO': ('Colorado', 'Colo.'),
           'CT': ('Connecticut', 'Conn.'),
           'DE': ('Delaware', 'Del.'),
           'DC': ('Dist. of Columbia', 'D.C.'),
           'FL': ('Florida', 'Fla.'),
           'GA': ('Georgia', 'Ga.'),
           'GU': ('Guam', 'Guam'),
           'HI': ('Hawaii', 'Hawaii'),
           'ID': ('Idaho', 'Idaho'),
           'IL': ('Illinois', 'Ill.'),
           'IN': ('Indiana', 'Ind.'),
           'IA': ('Iowa', 'Iowa'),
           'KS': ('Kansas', 'Kans.'),
           'KY': ('Kentucky', 'Ky.'),
           'LA': ('Louisiana', 'La.'),
           'ME': ('Maine', 'Maine'),
           'MD': ('Maryland', 'Md.'),
           'MH': ('Marshall Islands'),
           'MA': ('Massachusetts', 'Mass.'),
           'MI': ('Michigan', 'Mich.'),
           'FM': ('Micronesia'),
           'MN': ('Minnesota', 'Minn.'),
           'MS': ('Mississippi', 'Miss.'),
           'MO': ('Missouri', 'Mo.'),
           'MT': ('Montana', 'Mont.'),
           'NE': ('Nebraska', 'Nebr.'),
           'NV': ('Nevada', 'Nev.'),
           'NH': ('New Hampshire', 'N.H.'),
           'NJ': ('New Jersey', 'N.J.'),
           'NM': ('New Mexico', 'N.M.'),
           'NY': ('New York', 'N.Y.'),
           'NC': ('North Carolina', 'N.C.'),
           'ND': ('North Dakota', 'N.D.'),
           'MP': ('Northern Marianas'),
           'OH': ('Ohio', 'Ohio'),
           'OK': ('Oklahoma', 'Okla.'),
           'OR': ('Oregon', 'Ore.'),
           'PW': ('Palau'),
           'PA': ('Pennsylvania', 'Pa.'),
           'PR': ('Puerto Rico', 'P.R.'),
           'RI': ('Rhode Island', 'R.I.'),
           'SC': ('South Carolina', 'S.C.'),
           'SD': ('South Dakota', 'S.D.'),
           'TN': ('Tennessee', 'Tenn.'),
           'TX': ('Texas', 'Tex.'),
           'UT': ('Utah', 'Utah'),
           'VT': ('Vermont', 'Vt.'),
           'VA': ('Virginia', 'Va.'),
           'VI': ('Virgin Islands', 'V.I.'),
           'WA': ('Washington', 'Wash.'),
           'WV': ('West Virginia', 'W.Va.'),
           'WI': ('Wisconsin', 'Wis.'),
           'WY': ('Wyoming', 'Wyo.')}

def is_usable_us_address(address):
  return ('state' not in address or address['state'] in us_states) and \
    'number' in address and \
    'street' in address and \
    re.fullmatch(r'[0-9]{5}', address['postcode']) is not None

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
              'status': 'OK',
              'price':self.ratebook.price(origin, destination)}
    except KeyError as e:
      key=e.args[0]
      if key=='postcode':
        reason='postcode required for pricing'
      elif key==postcode_area(origin):
        reason="origin postcode not found"
      elif key==postcode_area(destination):
        reason="destination postcode not found"
      else:
        reason='Unknown'
      return {'origin':origin,
              'destination':destination,
              'status':'ERROR',
              'reason':reason}


class BookingStore:
  def __init__(self):
    self.bookings={}
    self.last_id=0

  def add(self, booking):
    self.last_id+=1
    self.bookings[str(self.last_id)]=booking
    return str(self.last_id)

  def pop(self, booking_id):
    return self.bookings.pop(booking_id)

