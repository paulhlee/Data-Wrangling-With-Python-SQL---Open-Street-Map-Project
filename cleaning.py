import xml.etree.cElementTree as ET
import pprint
import urllib2
from bs4 import BeautifulSoup
import re
from collections import defaultdict
import requests
import csv
import cerberus
import schema
import codecs
import pprint
OSM_PATH = "detroit_michigan.osm"

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Circle", "Way", "Row", "Crescent", "Line", "Sideroad", 
            "South", "North", "West", "East", "Highway"]
def find_allstreets():
	#this function queries against a source to list all possible streets in
	#city of detroit
	streetlist = []
	url = 'https://geographic.org/streetview/usa/mi/detroit.html'
	response = urllib2.urlopen(url)
	webContent = response.read()
	mypage = webContent.decode("utf8")
	soup = BeautifulSoup(mypage, 'html.parser')
	streetNames = soup.find_all("li")
	for street in streetNames:
		streetlist.append(street.text)
	return streetlist

def find_allzips():
	zipre = re.compile(r'^[0-9]{5}')
	urlzip = 'https://data.mongabay.com/igapo/zip_codes/metropolitan-areas/metro-zip/Detroit%20(MI)1.html'
	headers = {'User-Agent':'Mozilla/5.0'}
	page = requests.get(urlzip)
	soup = BeautifulSoup(page.text, "html.parser")
	zipset = set()
	zipcodes = soup.find_all("td")
	for tags in zipcodes:
		m= zipre.search(tags.text)
		if m!= None:
			ziptext = m.group()
			zipset.add(ziptext)
	return list(zipset)


'''methods used to update street name'''
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")
list_of_streets = find_allstreets()
mapping = {"Ave": "Avenue",
            'St.': "Street",
            'Rd.': "Road",
            'Ct': "Court",
            'DR': "Drive",
            'Dr': "Drive",
            'Hwy': "Highway",
            'Blvd': "Boulevard"}
def update_street_name(tagl, mapping, list_of_streets):
	tagk = tagl.attrib
	if is_street_name(tagl):
		streetval = tagl.attrib['v']
		if len(streetval.split())==1:
			for street in list_of_streets:
				if street.startswith(streetval):
					return street
		m = street_type_re.search(streetval)
		if m:
			street_type = m.group()
			if street_type in mapping:
				street = mapping[street_type]
				return tagl.attrib['v'].replace(street_type,street)
			if "," in streetval:
				streetl = streetval.split(",")
				streetn= streetl[0]
				out = filter(lambda x: not x.isdigit(), streetn)
				return out.strip()
	else:
		return

# '''''''''''''''"in this case for zip codes, if a tag has : in zip code, the ":"'''''''
# '''''''''''''''it is usally a highway or a trail, and the : is used to decribe the''''
# '''''''''''''''range of area the trail encompassess''''''''''''''''''''''''''''''''''''
def update_zip(tagl):
	if ":" in tagl.attrib['v']:
		zipcode = tagl.attrib['v'].split(":")
		return zipcode[0]


def which_country(element):
	# canada1 = elem.find('.//tag[@v="NRCan-CanVec-7.0"]') 
	# canada = elem.find('.//tag[@v="NRCan-CanVec-10.0"]')
	canada = element.find('.//tag[@k="source"]')
	canada1 = element.find('.//tag[@k="is_in"]')
	if canada!=None:
		if "canvec" in canada.attrib['v'].lower() or "geobase" in canada.attrib['v'].lower():
			return "Canada"
	elif canada1!=None:
		if "canada" in canada1.attrib['v'].lower():
			return "Canada"
	else:
		return "USA"


'''''''''''import function'''''''''''

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type','country']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type','country']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

def tag_treatment(tlist, nid,country):
  tags = []
  if len(tlist) ==0:
    return tags
  else:
    for tagl in tlist:
      tagd = {}
      tagA = tagl.attrib
      tagd['country'] = country
      tagd['id'] = nid
      tempK = tagA['k']
      tagd['value'] = tagA['v']
      if tempK == "addr:street":
      	correction = update_street_name(tagl,mapping,list_of_streets)
      	if correction != None:
      		tagd['value'] = correction
      elif tempK =='tiger:zip_left':
      	zipCorrect = update_zip(tagl)
      	if zipCorrect!= None:
      		tagd['value'] = zipCorrect
      if PROBLEMCHARS.match(tempK):
        return
      elif LOWER_COLON.match(tempK):
        ksplit = tempK.split(":")
        if len(ksplit)<=2:
          tagd['key'] = ksplit[1]
          tagd['type'] = ksplit[0]
        elif len(ksplit)>2:
          tagd['key'] = ":".join(ksplit[1:])
          tagd['type'] = ksplit[0]
      else:
        tagd['key'] = tagA['k']
        tagd['type'] = 'regular'

      tags.append(tagd)
  return tags


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    # YOUR CODE HERE
    if element.tag == 'node':
        tagab = element.attrib
        country = which_country(element)
        for key in NODE_FIELDS:
          node_attribs[key] = tagab[key]

        tlist = element.findall('tag')
        tags = tag_treatment(tlist, node_attribs['id'],country)

        return {'node': node_attribs, 'node_tags': tags}

    elif element.tag == 'way':
      waytag = element.attrib
      country = which_country(element)
      for key in WAY_FIELDS:
        way_attribs[key] = waytag[key]
      waynodes = element.findall("nd")
      position = 0
      for nd in waynodes:
        ninfo = nd.attrib
        ndict = {}
        ndict['id'] = waytag['id']
        ndict['node_id'] = ninfo['ref']
        ndict['position'] = position
        position+=1
        way_nodes.append(ndict)
      waytags = element.findall("tag")
      tags = tag_treatment(waytags, way_attribs['id'],country)

      return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================fdic= #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)

