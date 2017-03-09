#!/usr/local/bin/python3
from unittest import TestCase,main
from unittest.mock import MagicMock, mock_open, patch
import urllib.request
from rydz import PostcodeRateBook, Address, UKAddress, USAddress,\
  DistanceSource, FlatRateDistanceRateBook, GoogleDistanceURL, Distance,\
  GoogleDistance, Pricer

class TestAddress(TestCase):
  def test_fully_populated(self):
    a=Address(number=56, street='King Edward Road', town='Teddington',
              postcode='TW11 2BC', country='UK')
    self.assertEqual(56, a.number)
    self.assertEqual('King Edward Road', a.street)
    self.assertEqual('Teddington', a.town)
    self.assertEqual('TW11 2BC', a.postcode)
    self.assertEqual('UK', a.country)

  def test_postcode_area_UK(self):
    a=UKAddress(postcode='RM14 1PX')
    self.assertEqual('RM14', a.postcode_area())

  def test_postcode_area_US(self):
    a=USAddress(postcode='90210')
    self.assertEqual('902', a.postcode_area())

  def test_str_full(self):
    self.assertEqual('56, King Edward Road, Teddington, TW11 9BC, UK',
                     str(Address(number='56', street='King Edward Road',
                                 town='Teddington', postcode='TW11 9BC',
                                 country='UK')))

  def test_str_partial(self):
    self.assertEqual('56, King Edward Road, UK',
                     str(Address(number='56', street='King Edward Road',
                                 country='UK')))


class TestPostcodePricing(TestCase):
  def setUp(self):
    self.ratebook = PostcodeRateBook({'TW11':{'NW1':22.5, 'RM14':65.25},
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


class TestDistancePricing(TestCase):
  def test_flat_rate(self):
    distance_source=MagicMock(DistanceSource)
    distance_source.distance=MagicMock(return_value=100)
    ratebook=FlatRateDistanceRateBook(distance_source, 0.5)
    self.assertEqual(50, ratebook.price(Address(postcode='NW1 1AB'),
                                        Address(postcode='RM14 2CD')))
    distance_source.distance.assert_called_with(Address(postcode='NW1 1AB'),
                                              Address(postcode='RM14 2CD')) 

class TestDistance(TestCase):
  def test_equal_true(self):
    self.assertEqual(Distance("1", 2, "3", 4), Distance("1", 2, "3", 4))

  def test_equal_false(self):
    self.assertNotEqual(Distance("1", 5, "3", 4), Distance("1", 2, "3", 4))


class TestGoogleDistanceURL(TestCase):
  def test_city_to_city(self):
    gdu=GoogleDistanceURL('my_key')
    self.assertEqual('https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=London%2C+UK&destinations=Edinburgh%2C+UK&key=my_key',
                     gdu.url(Address(town='London', country='UK'),
                             Address(town='Edinburgh', country='UK')))


class TestGoogleDistance(TestCase):
  @patch('urllib.request.urlopen')
  def test_city_to_city(self, mock_urlopen):
    cm=MagicMock()
    cm.getcode.return_value=200
    cm.read.return_value='''
{
  "destination_addresses" : [ "Edinburgh, UK" ],
  "origin_addresses" : [ "London, UK" ],
  "rows" : [
    {
      "elements" : [
        {
          "distance" : {
           "text" : "414 mi",
           "value" : 666440
          },
          "duration" : {
            "text" : "7 hours 13 mins",
            "value" : 25979
          },
          "status" : "OK"
        }
      ]
    }
  ],
  "status" : "OK"
} '''
    cm.__enter__.return_value=cm
    mock_urlopen.return_value=cm
    self.assertEqual(Distance(dist_text='414 mi', dist_value=666440,
                              time_text='7 hours 13 mins', time_value=25979),
                     GoogleDistance('my_key').distance(Address(town='London',
                                                               country='UK'),
                                                       Address(town='Edinburgh',
                                                               country='UK')))
    mock_urlopen.assert_called_with('https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=London%2C+UK&destinations=Edinburgh%2C+UK&key=my_key')


class TestJsonQuote(TestCase):
  def setUp(self):
    self.pricer=Pricer(PostcodeRateBook({'TW11':{'NW1':22.5, 'RM14':65.25},
                                         'NW1': {'RM14':52.5, 'TW11':23.25},
                                         'RM14':{'NW1':62.5, 'TW11':63.25}}))

  def test_postcode_to_postcode_valid(self):
    self.assertEqual({"origin":{"postcode":"NW1 1AB"},
                      "destination":{"postcode":"RM14 2CD"},
                      "price":52.5},
                      self.pricer.json_quote({"origin":{"postcode":"NW1 1AB"},
                                              "destination":{"postcode":"RM14 2CD"}}))
    self.assertEqual({"origin":{"postcode":"RM14 1AB"},
                      "destination":{"postcode":"TW11 2CD"},
                      "price":63.25},
                      self.pricer.json_quote({"origin":{"postcode":"RM14 1AB"},
                                              "destination":{"postcode":"TW11 2CD"}}))

  def test_postcode_to_postcode_not_found(self):
    self.assertEqual({"origin":{"postcode":"NW9 1AB"},
                      "destination":{"postcode":"RM14 2CD"},
                      "error":"Origin postcode 'NW9' not found"},
                      self.pricer.json_quote({"origin":{"postcode":"NW9 1AB"},
                                              "destination":{"postcode":"RM14 2CD"}}))
    self.assertEqual({"origin":{"postcode":"RM14 1AB"},
                      "destination":{"postcode":"TW1 2CD"},
                      "error":"Destination postcode 'TW1' not found"},
                      self.pricer.json_quote({"origin":{"postcode":"RM14 1AB"},
                                              "destination":{"postcode":"TW1 2CD"}}))


if __name__=='__main__':
  main()
