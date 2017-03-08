#!/usr/local/bin/python3
from unittest import TestCase,main
from unittest.mock import MagicMock
from rydz import PostcodeRateBook, Address, UKAddress, USAddress,\
  DistanceSource, FlatRateDistanceRateBook, GoogleDistanceURL

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


class TestGoogleDistanceURL(TestCase):
  def test_city_to_city(self):
    gdu=GoogleDistanceURL('my_key')
    self.assertEqual('https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=London%2C+UK&destinations=Edinburgh%2C+UK&key=my_key',
                     gdu.url(Address(town='London', country='UK'),
                             Address(town='Edinburgh', country='UK')))

#    gu=MagicMock(GoogleDistanceUrl)
#    gu.url=MagicMock(return 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=London,%20UK&destinations=Edniburgh,%20&key=###key###')
#    ou=MagicMock(urllib.request)
#    ou.urlopen(return 
#    self.assertEqual(Distance(dist_text='414 mi', dist_value=666433,
#                              time_text='7 hrs 11 mins', time_value=25874),
#                     GoogleDistance('##key##').distance(Address(town='London', country='UK'))
#                                                        Address(town='Edinburgh', country='UK'))
#    gu.assert_called_with(Address(town='London', country='UK'),
#                          Address(town='Edinburgh', country='UK'))



if __name__=='__main__':
  main()
