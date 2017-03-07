#!/usr/local/bin/python3

class Address:
  def __init__(self, postcode):
    self.postcode=postcode


class UKAddress(Address):
  def postcode_area(self):
    return self.postcode.split(' ')[0]


class PostcodeRatebook:
  def __init__(self, postcode_map):
    self.postcode_map=postcode_map

  def price(self, origin, destination):
    return self.postcode_map[origin.postcode_area()][destination.postcode_area()]
