#!/usr/bin/env python
from unittest import TestCase,main
from unittest.mock import MagicMock, mock_open, patch
import urllib.request
from datetime import datetime
from pytz import timezone
from rydz import PostcodeRateBook, \
  DistanceSource, FlatRateDistanceRateBook, GoogleDistanceURL, Distance,\
  GoogleDistance, Pricer, add_booking, validate_booking, \
  InvalidAddressException, \
  address_str, postcode_area, validate_address

class TestAddress(TestCase):
  def test_postcode_area_UK(self):
    a={'postcode': 'RM14 1PX', 'country': 'UK'}
    self.assertEqual('RM14', postcode_area(a))

  def test_postcode_area_US(self):
    a={'postcode': '90210', 'country': 'US'}
    self.assertEqual('902', postcode_area(a))

  def test_str_full(self):
    self.assertEqual('56, King Edward Road, Teddington, TW11 9BC, UK',
                     address_str({'number': '56', 'street': 'King Edward Road',
                                  'town': 'Teddington', 'postcode': 'TW11 9BC',
                                  'country': 'UK'}))

  def test_str_partial(self):
    self.assertEqual('56, King Edward Road, TW11 9BC',
                     address_str({'number': '56', 'street': 'King Edward Road',
                                  'postcode': 'TW11 9BC'}))



class TestPostcodePricing(TestCase):
  def setUp(self):
    self.ratebook = PostcodeRateBook({'TW11':{'NW1':22.5, 'RM14':65.25},
                                     'NW1': {'RM14':52.5, 'TW11':23.25},
                                     'RM14':{'NW1':62.5, 'TW11':63.25}})

  def test_valid_address(self):
    self.assertEqual(52.5, self.ratebook.price({'postcode': 'NW1 1AB', 'country': 'UK'},
                                               {'postcode': 'RM14 2CD', 'country': 'UK'}))
    self.assertEqual(63.25, self.ratebook.price({'postcode': 'RM14 1AB', 'country': 'UK'},
                                                {'postcode': 'TW11 2CD', 'country': 'UK'}))

  def test_unknown_origin_postcode(self):
    with self.assertRaises(KeyError):
      self.assertEqual(63.25, self.ratebook.price({'postcode': 'RM12 1AB', 'country': 'UK'},
                                                  {'postcode': 'TW11 2CD', 'country': 'UK'}))

  def test_unknown_destination_postcode(self):
    with self.assertRaises(KeyError):
      self.assertEqual(63.25, self.ratebook.price({'postcode': 'RM14 1AB', 'country': 'UK'},
                                                  {'postcode': 'TW10 2CD', 'country': 'UK'}))


class TestDistancePricing(TestCase):
  def test_flat_rate(self):
    distance_source=MagicMock(DistanceSource)
    distance_source.distance=MagicMock(return_value=100)
    ratebook=FlatRateDistanceRateBook(distance_source, 0.5)
    self.assertEqual(50, ratebook.price({'postcode': 'NW1 1AB', 'country': 'UK'},
                                        {'postcode': 'RM14 2CD', 'country': 'UK'}))
    distance_source.distance.assert_called_with({'postcode': 'NW1 1AB', 'country': 'UK'},
                                                {'postcode': 'RM14 2CD', 'country': 'UK'}) 

class TestDistance(TestCase):
  def test_equal_true(self):
    self.assertEqual(Distance("1", 2, "3", 4), Distance("1", 2, "3", 4))

  def test_equal_false(self):
    self.assertNotEqual(Distance("1", 5, "3", 4), Distance("1", 2, "3", 4))


class TestGoogleDistanceURL(TestCase):
  def test_city_to_city(self):
    gdu=GoogleDistanceURL('my_key')
    self.assertEqual('https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=London%2C+UK&destinations=Edinburgh%2C+UK&key=my_key',
                     gdu.url({'town': 'London', 'country': 'UK'},
                             {'town': 'Edinburgh', 'country': 'UK'}))


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
                     GoogleDistance('my_key').distance({'town': 'London',
                                                        'country': 'UK'},
                                                       {'town': 'Edinburgh',
                                                        'country': 'UK'}))
    mock_urlopen.assert_called_with('https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=London%2C+UK&destinations=Edinburgh%2C+UK&key=my_key')


class TestJsonQuote(TestCase):
  def setUp(self):
    self.pricer=Pricer(PostcodeRateBook({'TW11':{'NW1':22.5, 'RM14':65.25},
                                         'NW1': {'RM14':52.5, 'TW11':23.25},
                                         'RM14':{'NW1':62.5, 'TW11':63.25}}))

  def test_postcode_to_postcode_valid(self):
    self.assertEqual({"origin":{"postcode":"NW1 1AB", 'country': 'UK'},
                      "destination":{"postcode":"RM14 2CD", 'country': 'UK'},
                      "status":"OK",
                      "price":52.5},
                      self.pricer.quote({"origin":{"postcode":"NW1 1AB",
                                                   'country': 'UK'},
                                         "destination":{"postcode":"RM14 2CD",
                                                        'country': 'UK'}}))
    self.assertEqual({"origin":{"postcode":"RM14 1AB", 'country': 'UK'},
                      "destination":{"postcode":"TW11 2CD", 'country': 'UK'},
                      "status":"OK",
                      "price":63.25},
                      self.pricer.quote({"origin":{"postcode":"RM14 1AB",
                                                   'country': 'UK'},
                                         "destination":{"postcode":"TW11 2CD",
                                                        'country': 'UK'}}))

  def test_postcode_to_postcode_not_found(self):
    self.assertEqual({"origin":{"postcode":"NW9 1AB", 'country': 'UK'},
                      "destination":{"postcode":"RM14 2CD", 'country': 'UK'},
                      "status":"ERROR",
                      "reason":"origin postcode not found"},
                      self.pricer.quote({"origin":{"postcode":"NW9 1AB",
                                                   'country': 'UK'},
                                         "destination":{"postcode":"RM14 2CD",
                                                        'country': 'UK'}}))
    self.assertEqual({"origin":{"postcode":"RM14 1AB", 'country': 'UK'},
                      "destination":{"postcode":"TW1 2CD", 'country': 'UK'},
                      "status":"ERROR",
                      "reason":"destination postcode not found"},
                      self.pricer.quote({"origin":{"postcode":"RM14 1AB",
                                                   'country': 'UK'},
                                         "destination":{"postcode":"TW1 2CD",
                                                        'country': 'UK'}}))

class MockMongoCollection:
  def __init__(self):
    self.last_id=0
    self.rows=[]

  def insert(self, doc):
    self.last_id+=1
    doc_=doc.copy()
    doc_['_id']=self.last_id
    self.rows.append(doc_)
    return self.last_id

  def find_one(self, key_map):
    result_rows=self.rows
    for k in key_map:
      filter(lambda r: r[k]==key_map[k], result_rows)
    return list(result_rows)[0]

class TestAddBooking(TestCase):
  def setUp(self):
    self.bs=MockMongoCollection()

  def test_json_add(self):
    self.maxDiff=None
    self.assertEqual({'status':'OK',
                      'booking':{'_id':1,
                        'origin':{
                            'number':55,
                            'street':'King Edward Road',
                            'town':'Teddington',
                            'postcode':'TW11 1AB',
                            'country':'UK'
                         },
                         'destination':{
                            'number':14,
                            'street':'Forth Road',
                            'town':'Upminster',
                            'postcode':'RM14 2QY',
                            'country':'UK'
                         },
                          'pickup_time':'2017-09-15 15:30',
                          'passengers':['a.passenger@acompany.com'],
                          'booker':'a.booker@acompany.com',
                          'quoted_price':65.25
                      }},
                     add_booking(self.bs,{'origin':{
                          'number':55,
                          'street':'King Edward Road',
                          'town':'Teddington',
                          'postcode':'TW11 1AB',
                          'country':'UK'
                        },
                        'destination':{
                          'number':14,
                          'street':'Forth Road',
                          'town':'Upminster',
                          'postcode':'RM14 2QY',
                          'country':'UK'
                        },
                        'pickup_time':'2017-09-15 15:30',
                        'passengers':['a.passenger@acompany.com'],
                        'booker':'a.booker@acompany.com',
                        'quoted_price':65.25
                      }))
    self.assertEqual([{'_id':1,
                       'origin': {'number': 55,
                                  'street': 'King Edward Road',
                                  'town': 'Teddington',
                                  'postcode': 'TW11 1AB',
                                  'country': 'UK'},
                        'destination': {'number': 14,
                                        'street': 'Forth Road',
                                        'town': 'Upminster',
                                        'postcode': 'RM14 2QY',
                                        'country': 'UK'},
                        'pickup_time': '2017-09-15 15:30',
                        'passengers': ['a.passenger@acompany.com'],
                        'booker': 'a.booker@acompany.com',
                        'quoted_price': 65.25}],
                      self.bs.rows)


class TestUsableAddress(TestCase):
  def test_empty(self):
    with self.assertRaises(InvalidAddressException) as context:
      self.assertFalse(validate_address({}))

  def test_unsupported_country(self):
    with self.assertRaises(InvalidAddressException) as context:
      self.assertFalse(validate_address({'number':14,
                                          'street':'Forth Road',
                                          'town':'Upminster',
                                          'postcode':'RM14 2QY',
                                          'country':'FR'}))
    self.assertEqual("Unsupported country: 'FR'", str(context.exception))

  def test_missing_number(self):
    with self.assertRaises(InvalidAddressException) as context:
      self.assertFalse(validate_address({'street':'Forth Road',
                                          'town':'Upminster',
                                          'postcode':'RM14 2QY',
                                          'country':'UK'}))
    self.assertEqual("'number'", str(context.exception))

  def test_missing_street(self):
    with self.assertRaises(InvalidAddressException) as context:
      self.assertFalse(validate_address({'number':14,
                                         'town':'Upminster',
                                         'postcode':'RM14 2QY',
                                         'country':'UK'}))
    self.assertEqual("'street'", str(context.exception))

  def test_missing_town(self):
    with self.assertRaises(InvalidAddressException) as context:
      self.assertTrue(validate_address({'number':14,
                                         'street':'Forth Road',
                                         'postcode':'RM14 2QY',
                                         'country':'UK'}))
    self.assertEqual("'town'", str(context.exception))

  def test_missing_country(self):
    with self.assertRaises(InvalidAddressException) as context:
      self.assertFalse(validate_address({'number':14,
                                          'street':'Forth Road',
                                          'town':'Upminster',
                                          'postcode':'RM14 2QY'}))
    self.assertEqual("'country'", str(context.exception))

  def test_malformed_postcode_uk(self):  
    with self.assertRaises(InvalidAddressException) as context:
      self.assertFalse(validate_address({'number':14,
                                          'street':'Forth Road',
                                          'town':'Upminster',
                                          'postcode':'90210',
                                          'country':'UK'}))
    self.assertEqual("'postcode'", str(context.exception))

  def test_valid_us(self):
    validate_address({'number':1202,
                       'street':'42nd Street',
                       'city':'New York',
                       'state':'NY',
                       'postcode':'01234',
                       'country':'US'})

  def test_minimal_us(self):
    validate_address({'number': 52,
                       'street': 'Hutton Drive',
                       'postcode': '90210',
                       'country': 'US'})

  def test_missing_number_us(self):
    with self.assertRaises(InvalidAddressException) as context:
      self.assertFalse(validate_address({'street': 'Hutton Drive',
                                          'postcode': '90210',
                                          'country': 'US'}))
    self.assertEqual("'number'", str(context.exception))

  def test_missing_street_us(self):
    with self.assertRaises(InvalidAddressException) as context:
      self.assertFalse(validate_address({'number': 52,
                                          'postcode': '90210',
                                          'country': 'US'}))
    self.assertEqual("'street'", str(context.exception))

  def test_missing_postcode_us(self):
    with self.assertRaises(InvalidAddressException) as context:
      self.assertFalse(validate_address({'number': 52,
                                          'street': 'Hutton Drive',
                                          'country': 'US'}))
    self.assertEqual("'postcode'", str(context.exception))

  def test_malformed_postcode_too_short_us(self):
    with self.assertRaises(InvalidAddressException) as context:
      validate_address({'number':1202,
                         'street':'42nd Street',
                         'city':'New York',
                         'state':'NY',
                         'postcode':'0123',
                         'country':'US'})
    self.assertEqual("'postcode'", str(context.exception))

  def test_malformed_postcode_too_long_us(self):
    with self.assertRaises(InvalidAddressException) as context:
      validate_address({'number':1202,
                         'street':'42nd Street',
                         'city':'New York',
                         'state':'NY',
                         'postcode':'012345',
                         'country':'US'})
    self.assertEqual("'postcode'", str(context.exception))

  def test_malformed_postcode_nonnumeric_us(self):
    with self.assertRaises(InvalidAddressException) as context:
      validate_address({'number':1202,
                         'street':'42nd Street',
                         'city':'New York',
                         'state':'NY',
                         'postcode':'01w35',
                         'country':'US'})
    self.assertEqual("'postcode'", str(context.exception))


class TestValidateBooking(TestCase):
  def test_valid_booking_uk(self):
    validate_booking({'origin':{
                        'number':55,
                        'street':'King Edward Road',
                        'town':'Teddington',
                        'postcode':'TW11 1AB',
                        'country':'UK'},
                      'destination':{
                        'number':14,
                        'street':'Forth Road',
                        'town':'Upminster',
                        'postcode':'RM14 2QY',
                        'country':'UK'},
                      'pickup_time':'2017-09-15 15:30',
                      'passengers':['a.passenger@acompany.com'],
                      'booker':'a.booker@acompany.com',
                      'quoted_price':65.25})


if __name__=='__main__':
  main()
