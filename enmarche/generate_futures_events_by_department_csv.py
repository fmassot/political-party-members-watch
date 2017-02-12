from __future__ import print_function

import csv
import dateutil.parser
import json
import os
import requests
import shapefile
import subprocess
import sys

from shapely.geometry import Polygon, Point
from pprint import pprint as pp


COMMITTEES_CSV = '../data/macron-committee.csv'
DEPARTMENTS_SHAPEFILE = '../../departements-20170102-shp/departements-20170102' # See https://www.data.gouv.fr/fr/datasets/contours-des-departements-francais-issus-d-openstreetmap/

SLUG_BASE = 'https://en-marche.fr/espaceperso/evenement/'

MODE = ''

def load_committees():
    '''Loads committees info from CSV file'''
    with open(COMMITTEES_CSV, 'r') as csv_f:
        csv_reader = csv.DictReader(csv_f)
        return list(csv_reader)
    
def is_in_poly(poly, lng, lat):
    '''Tells if a longitude/latitude is within a GPS-based polygon'''
    try:
        lat = float(lat)
        lng = float(lng)
    except:
        return False
        
    point = Point(lng, lat)
    return poly.contains(point)
    
def filter_dept_committees(shape):
    '''Returns all committees of one department based on GPS data'''
    dept_poly = Polygon(shape.points)
    
    committees = load_committees()
    return filter(lambda c: is_in_poly(dept_poly, c['lng'], c['lat']), committees)
    
    pp(dept_committees)
    
    
def get_committee(id_):
    '''Fetchs detailed information about a committee from en-marche website.
       If in dev-mode, cache JSON data to avoid waiting and hammering the site.
    '''
    if MODE == 'DEV':
        if not os.path.exists('_cache'):
            os.mkdir('_cache')
        cache_file = os.path.join('_cache', id_ + '.json')
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)

    def _dl():
        print('Fetching committee', id_)
        try_count = 0
        while try_count < 5:
            try:
                #committee_json = requests.get("https://en-marche.fr/api/committee/" + str(id_), verify=False).json() # Not working for me (blocks on SSL neg.)?! Switch to wget command.
                return json.loads(subprocess.check_output(['wget', 'https://en-marche.fr/api/committee/' + str(id_), '-O', '-']))
            except Exception as e:
                try_count += 1
                print('ERROR:', e)

        raise Exception("Cannot download committe with id " + str(id_))
        
    committee_json = _dl()
    
    if MODE == 'DEV':
        with open(cache_file, 'w') as f:
            json.dump(committee_json, f)
    
    return committee_json
    
def get_committee_future_events(committee, start_date, stop_date):
    '''Returns a generator yielding all events of a committee between start_date and stop_date'''
    committee_json = get_committee(committee['id'])
    
    events = committee_json['events']
    for event in events:
        event_date = dateutil.parser.parse(event['date'].split('T')[0]).date()
        event_date_end = dateutil.parser.parse(event['dateEnd'].split('T')[0]).date()
        if (start_date <= event_date <= stop_date) or (start_date <= event_date_end <= stop_date):
            yield event
            
def get_committees_future_events(committees, start_date, stop_date):
    '''Returns a list of all events happening between start_date and stop_date for all given committees'''
    events = []
    for committee in committees:
        events += list(get_committee_future_events(committee, start_date, stop_date))
        
    return events
    
def write_csv_events(events, filename):
    '''Writes an event list to a CSV file'''
    fields = 'date_format heure_format ville titre lien'.split(' ')
    with open(filename, 'wb') as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        for event in events:
            if event['city'] is None:
                event['city'] = event['zipcode']
            writer.writerow({
                'date_format': dateutil.parser.parse(event['date']).strftime('%d/%m/%Y'),
                'heure_format': dateutil.parser.parse(event['timeStart']).strftime('%H:%M'),
                'ville': event['city'].encode('utf-8'),
                'titre': event['name'].encode('utf-8'),
                'lien': SLUG_BASE + event['slug']
            })

def main(dept_code, start_date_str, stop_date_str):
    start_date = dateutil.parser.parse(start_date_str).date()
    stop_date = dateutil.parser.parse(stop_date_str).date()

    shpf = shapefile.Reader(DEPARTMENTS_SHAPEFILE)
    dept_idx = {rec[0]: i for i, rec in enumerate(shpf.records())}
    
    if dept_code not in dept_idx:
        print('ERROR: Could not recognize department code:', dept_code)
        return
        
    dept_data = shpf.shapeRecord(dept_idx[dept_code])
    dept_record = dept_data.record
    dept_shape = dept_data.shape
    
    print('Processing for department', dept_record[0], '-', dept_record[1])
    
    dept_committees = filter_dept_committees(dept_shape)
    
    print('Found', len(dept_committees), 'committees in department', dept_record[0], 'with', sum(map(lambda c: int(c['membersCount']), dept_committees)), 'members')
    
    dept_events = get_committees_future_events(dept_committees, start_date, stop_date)
    print(len(dept_events), 'events found between', start_date_str, 'and', stop_date_str)
    
    csv_filename = 'events_' + str(dept_code) + '_' + start_date_str + '_' + stop_date_str + '.csv'
    write_csv_events(dept_events, csv_filename)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('USAGE:', sys.argv[0], 'DEPT_CODE_INSEE START_DATE STOP_DATE')
        print('START|STOP_DATE: YYYY-MM-DD')
        sys.exit(-1)
        
    main(*sys.argv[1:4])
