import json
from geopy.geocoders import Nominatim
import geocoder


def add_venue(address):
    geocoded = geocoder.google(address)
    geojson = geocoded.geojson
    with open('static/venue.json', 'r') as outfile:
        content = json.loads(outfile.read())
        content['features'].append(geojson)

    with open('static/venue.json', 'w') as outfile:
        json.dump(content, outfile)

if __name__ == "__main__":

    venues = ["305 Harrison Street, Seattle, WA 98109",
              "925 East Pike Street, Seattle, WA 98122",
              "911 Pine Street, Seattle, WA 98101",
              "2200 2nd Avenue, Seattle, WA 98121",
              "216 Union Street, Seattle, WA 98101",
              "1426 1st Avenue, Seattle, WA 98101",
              '1050 North 34th Street, Seattle, WA 98103',
              '5213 Ballard Avenue Northwest, Seattle, WA 98107',
              '1411 21st Avenue, Seattle, WA 98122',
              '412 North 36th Street, Seattle, WA 98103'
              ]
  
    total_result = {'type': 'FeatureCollection', 'features': []}

    for venue in venues:
        geocoded = geocoder.google(venue)
        geojson = geocoded.geojson
        total_result['features'].append(geojson)

    with open('static/venue.json', 'w') as outfile:
        json.dump(total_result, outfile)
