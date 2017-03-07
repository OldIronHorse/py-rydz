#!/usr/local/bin/python3
from unittest import TestCase,main
from rydz import PostcodeRatebook, UKAddress

class TestAddress(TestCase):
  def test_postcode_area(self):
    a=UKAddress(postcode='RM14 1PX')
    self.assertEqual('RM14', a.postcode_area())

class TestPostcodePricing(TestCase):
  def setUp(self):
    self.ratebook = PostcodeRatebook({'TW11':{'NW1':22.5, 'RM14':65.25},
                                     'NW1': {'RM14':52.5, 'TW11':23.25},
                                     'RM14':{'NW1':62.5, 'TW11':63.25}})

  def test_valid_address(self):
    self.assertEqual(52.5, self.ratebook.price(UKAddress(postcode='NW1 1AB'),
                                               UKAddress(postcode='RM14 2CD')))
    self.assertEqual(63.25, self.ratebook.price(UKAddress(postcode='RM14 1AB'),
                                                UKAddress(postcode='TW11 2CD')))

  def test_unknown_origin_postcode(self):
    with self.assertRaises(KeyError):
      self.assertEqual(63.25, self.ratebook.price(UKAddress(postcode='RM12 1AB'),
                                                  UKAddress(postcode='TW11 2CD')))

  def test_unknown_destination_postcode(self):
    with self.assertRaises(KeyError):
      self.assertEqual(63.25, self.ratebook.price(UKAddress(postcode='RM14 1AB'),
                                                  UKAddress(postcode='TW10 2CD')))



if __name__=='__main__':
  main()
