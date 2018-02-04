import xml.etree.cElementTree as ET
import pprint
import urllib2
from bs4 import BeautifulSoup
import re
from collections import defaultdict
import requests
import csv
OSM_PATH = "detroit_michigan.osm"



street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Circle", "Way", "Row", "Crescent", "Line", "Sideroad", 
            "South", "North", "West", "East", "Highway"]

canada_list = ["Geobase_Import_2009", "NRCan-CanVec-7.0", "NRCan-CanVec-10.0"]



def count_tags_users(filename):
	'''this function counts the number of possible tags inside osm '''
	'''also serves to find number of users'''
    kTags = {}
    users = set()
    for event, elem in ET.iterparse(filename):
        if kTags.has_key(elem.tag):
            kTags[elem.tag] +=1
        else:
            kTags[elem.tag] = 1
        attribk = elem.attrib
        if attribk.has_key('uid'):
        	users.add(attribk['uid'])
    return (kTags,users)

def get_zip():
    '''this function reads the csv file from "zip.csv and outputs list of all zip'''
	zipC = []
	with open("zip.csv", "r") as f:
		reader = csv.DictReader(f)
		for line in reader:
			zipint = int(line['\xef\xbb\xbfzipcode'])
			zipC.append(zipint)
	return zipC		

zipvalues = get_zip()

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def audit_zip(zipset, zipcode):
    '''add zip into zipset if zip is not in default zip list'''
	try:
		int(zipcode)
		if int(zipcode) not in zipvalues:
			zipset.add(zipcode)
	except:
		zipset.add(zipcode)



def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def is_zip(elem):
	return (elem.attrib['k'] == "tiger:zip_left")

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """return element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def audit(osmfile):
	'''audit the data file to identify misalignment'''
	'''default is to return a tuple of street_types, zipset, and canada'''
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    canCount=0
    zipset = set()
    for elem in get_element(osm_file, tags =('node', 'way')):
        for tag in elem.iter("tag"):
        	if is_street_name(tag):
        		audit_street_type(street_types, tag.attrib['v'])
        	if is_zip(tag):
        		audit_zip(zipset,tag.attrib['v'])
        	if tag.attrib['v'] in canada_list:
        		canCount+=1

    osm_file.close()
    return [street_types, zipset, canCount]




if __name__ == "__main__":
	None