#!/usr/local/bin/python3

class Address:
  def __init__(self, postcode):
    self.postcode=postcode


class PostcodeRatebook:
  def __init__(self, postcode_map):
    self.postcode_map=postcode_map

  def price(self, origin, destination):
    return self.postcode_map[origin.postcode.split(' ')[0]][destination.postcode.split(' ')[0]]
