#!/usr/local/bin/python3
from unittest import TestCase,main
from rydz import PostcodeRatebook, Address

class TestPostcodePricing(TestCase):
  def setUp(self):
    self.ratebook = PostcodeRatebook({'TW11':{'NW1':22.5, 'RM14':65.25},
                                     'NW1': {'RM14':52.5, 'TW11':23.25},
                                     'RM14':{'NW1':62.5, 'TW11':63.25}})

  def test_valid_address(self):
    self.assertEqual(52.5, self.ratebook.price(Address(postcode='NW1 1AB'),
                                               Address(postcode='RM14 2CD')))


if __name__=='__main__':
  main()
