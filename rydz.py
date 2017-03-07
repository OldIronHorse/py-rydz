#!/usr/local/bin/python3

class Address:
  def __init__(self, number=None, street=None, town=None, postcode=None, country=None):
    self.number=number
    self.street=street
    self.town=town
    self.postcode=postcode
    self.country=country

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.__dict__ == other.__dict__
    return NotImplemented

  def __ne__(self, other):
    if isinstance(other, self.__class__):
      return self.__dict__ != other.__dict__
    return NotImplemented


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
