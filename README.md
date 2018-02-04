
# Open Street Map - Explore Detroit Metroit

### Map Area

* open street map:https://www.openstreetmap.org/  <br>
* map source: https://mapzen.com/data/metro-extracts/metro/detroit_michigan/

Detroit is the city I am heading to after my graduation. Before getting there, I am using the project to better familiarize myself with this city


## Problems Encountered in the Map

### Street names
**Abbreviations**
There are several datapoints with the street names abbreviated. The abbreivations are convereted to their complete words using the "mapping" dictionary and inside the "import.py" module

```python
mapping = {"Ave": "Avenue",
            'St.': "Street",
            'Rd.': "Road",
            'Ct': "Court",
            'DR': "Drive",
            'Dr': "Drive",
            'Hwy': "Highway",
            'Blvd': "Boulevard"}
```
**Incomplete names**
From the audit, I have noticed many streets have incomlete names, such that the user only includes the name of the street, but not the street type. The type of street is not found in other children tag.
<br>
```python
incomplete_street = ['Yemans', 'Baseline', 'Orland', 'Wyoming', 'Cedarview', 'Lenox', 'Sheldon', 'Lothrop', 'Edenwood', 'Dickerson', 'Pembroke', 'Saginaw', 'Roslyn', 'Livernois', 'Poplar', 'Greenfield', 'Olympia', 'Kinloch', 'Washington', 'Sugarbush', 'Boardwalk', 'Shrewsbury', 'Woodward', 'Broadway', 'Chippewa', 'Central', 'Second', 'Tecumseh', 'Biddle', 'Prairie', 'Drexel', 'Sylvester', 'Silvermaple', 'Fenton', 'Overland', 'Glencastle', 'Stratford', 'Gardendale', 'Quincy', 'Davis', 'Leathorne', 'Starkweather', 'Evaline', 'Novi', 'Glengary', 'Renfrew', 'Picadilly', 'Edwin', 'Gratiot', 'Stoepel', 'Equestrian', 'Davison', 'Belmont', 'Dequindre', 'Monica', 'Caroline', 'Middlebelt', 'Lichfield', 'Cass', 'Capitol', 'Garfield', 'Straford', 'Canterbury']
```
To clean the data, I gathered the complete list of streets in detroit from:<br>
> https://geographic.org/streetview/usa/mi/detroit.html>
<br>

Using a urlib2, I queried and downloaded the list of street names in Detroit into a python list. This query is later used in "import.py" to match the incomplete streets with the complete name

```python
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
```


**Multiple or Incorrect Zipcodes**

There are nodes or ways with multiple zipcodes. Understandibly for ways, the zipcodes may span certain geographic areas, such as "48017:48073". However,for this exercise, I am using only the start zip codes.
<br>
Secondly, using uslib2, I queried and downloaded into a csv file the list of all zipcodes in the detroit metropolitan area. The csv file is used to cross-check against the data from OSM.

```python
problem_zip = set(['99999', '48003;48444', '48025:48219', '48223; 48239; 48223', '48207:48214', '48374:48393', '48371; 48362', '48095:48306', '48062:48063', '48328;48386', '48085:48098', '48180; 48192', '48158;48176', '48067:48073', '48417:48433', '43612; 48182', '48126:48128', '48221;48235', '48211:48234', '48009:48304', '48219;48152', '48301;48322', '48348:48362', '48301;48322:48322', '78184', '48104; 48109', '48350:48442', '48334:48336', '48386;48382;48383', '48213:48224', '48025:48073', '48350;48348:48350', '48204:48210', '48105:48187', '48182; 43612', '48168;48167', '48131;48161', '48223:48228', '48073:48084', '48030:48071', '48180; 48192; 48192', '48202:48208', '48235;48219:48235', '48327:48328', '48327:48329', '48211;48213', '48306:48309', '48137:49285', '48223:48227', '48217; 48218', '48183; 48192', '48219:48221:48235', '48183; 48195', '48192; 48174', '48021:48091', '48017:48073', '48217;48217;48124', '48348:48350', '48133; 48182; 48133', '48038:48313', '48209; 48210', '48192; 48195', '48178:48178;48105;48178', '48239; 48228', '48109;48105', '48185:48187', '48137;49285', '48207:48211', '48098:48304', '48328:48341', '48320:48342'])

```



**US or Canada**
Inside this dataset, there are **94,465** ways and nodes entry on Canada. Why Canada?<br>
Windsor, Ontario is right across the river from detroit, and when downloading the data from OSM, that got included as well.
<br>
They are identified by the following tags:
<body style="background-color:powderblue;">
```xml
<tag k="source" v="NRCan-CanVec-10.0" />
<tag k="source" v="NRCan-CanVec-7.0" />
<tag k="source" v="Geobase_Import_2009" />
```
</body>
When importing to sqlite in "import.py", I am electing to add a new field to ways and nodes as to whether the entry is in Canda or US


# Overview of the Data


**File Sizes**
```
detroit_michigan.osm...........970.4 MB
mydb.sqlite...................574.0 MB
```


**Number of Unique Users**
```sqlite
QUERY = "SELECT COUNT(DISTINCT(nw.user)) 
FROM (SELECT user FROM nodes UNION ALL
SELECT user From ways) as nw;"
```
RESULT: 2149


**Number of nodes and ways** 
<br>
```sqlite
QUERY = "SELECT COUNT(DISTINCT(id)) FROM nodes; "
```
*Number of Nodes*:<br>
RESULT: 4467404
<br>
<br>
```sqlite
QUERY = "SELECT COUNT(DISTINCT(id)) FROM ways;"
```
*Number of ways*:<br>
RESULT: 519607
<br>


### Exploring deeper into the dataset

To delve deeper, I want to query the top 20 most used key in nodetags and waytags

**Top 10 tags**

*From nodes_tags*
<br>
```sqlite
QUERY = "SELECT key, COUNT(*) as count FROM nodetags GROUP BY key ORDER BY count desc LIMIT 15;"
```
RESULT:
```
your output:
   (u'', 337133)
   (u'source', 55061)
   (u'street', 50323)
   (u'housenumber', 50260)
   (u'city', 48412)
   (u'highway', 27229)
   (u'power', 14208)
   (u'name', 12589)
   (u'amenity', 8282)
   (u'created_by', 4571)
   (u'ele', 4148)
   (u'feature_id', 3788)
   (u'created', 3312)
   (u'man_made', 3295)
   (u'county_id', 3209)
```

*From ways_tags*
<br>
```sqlite
QUERY = "SELECT key, COUNT(*) as count FROM waytags GROUP BY key ORDER BY count desc LIMIT 15;"
```
RESULT:
```
your output:
   (u'highway', 296254)
   (u'name', 174936)
   (u'county', 132602)
   (u'cfcc', 132509)
   (u'name_base', 121481)
   (u'building', 115534)
   (u'reviewed', 112021)
   (u'name_type', 111454)
   (u'zip_left', 96098)
   (u'zip_right', 92245)
   (u'source', 89034)
   (u'lanes', 77076)
   (u'footway', 46231)
   (u'oneway', 46185)
   (u'maxspeed', 40241)
```

### Exploring Nodes

**Top 15 amenities**
The amenity key looks interesting, next I want to find what are the top 15 amenities.

```sqlite
QUERY = "SELECT value, COUNT(*) as count FROM nodetags where key = 'amenity' group by value order by count desc LIMIT 15;"
```
RESULT:
```
your output:
   (u'school', 1786)
   (u'place_of_worship', 1198)
   (u'restaurant', 839)
   (u'fast_food', 464)
   (u'parking', 455)
   (u'bench', 447)
   (u'fuel', 392)
   (u'toilets', 225)
   (u'cafe', 209)
   (u'grave_yard', 172)
   (u'bank', 147)
   (u'fire_station', 146)
   (u'bicycle_parking', 134)
   (u'pharmacy', 115)
   (u'doctors', 107)
```
The fact that there are more schools than the number of restaruarnts, fast food, and cafes combied is a bit suspicous. <br>
The graveyard output is bit spooky
The preliminary analysis suggests there are many missing nodes in this dataset

**Cities with most restaurants**
```sqlite
QUERY = "SELECT B.value as zip, COUNT(*) as num from nodetags as A, nodetags as B WHERE A.idnode = B.idnode AND (A.value = 'restaurant' OR A.value = 'cafe' OR A.value ='fast_food') and B.key = 'city' GROUP BY B.value ORDER BY num desc LIMIT 5;"
```

RESULT:
```
your output:
   (u'Ann Arbor', 76)
   (u'Ferndale', 43)
   (u'Detroit', 24)
   (u'Troy', 15)
   (u'Dearborn', 7)
```

Ann Arbor is the city with the most restaurants!<br>
What is a bit alarming is when joining self-joining restaruants type with their "city", only 274 entries have a city listed!


**most popular cuisine type**
```sqlite
QUERY = "SELECT nodetags.value, count(*) as count from nodetags group by nodetags.value having nodetags.key = 'cuisine' order by count desc"
```
Result:
```
your output:
   (u'pizza', 123)
   (u'burger', 115)
   (u'sandwich', 108)
   (u'coffee_shop', 66)
   (u'american', 59)
   (u'mexican', 54)
   (u'chinese', 45)
   (u'italian', 24)
   (u'thai', 19)
   (u'chicken', 14)
```
GREAT city for burgers and pizzas! Also Thai food
    

**most popular burger joint**
```sqlite
QUERY = "SELECT name, COUNT(*) as count FROM (SELECT B.value as name, A.value as cuisineName from nodetags as A, nodetags as B WHERE A.idnode = B.idnode AND (A.key = 'cuisine') and B.key = 'name') Group BY name Having cuisineName = 'burger' ORDER BY COUNT DESC;"
```
```
Result:
your output:
   (u"McDonald's", 50) 
   (u'Burger King', 20)
   (u"Wendy's", 12)
   (u"Culver's", 3)
   (u'Five Guys', 3)
   (u'White Castle', 3)
   (u'A&W', 2)
   (u'Sonic', 2)
   (u'Burger 21', 1)
   (u'Checkers Drive-In', 1)
   (u"Dagwood's Deli", 1)
   (u'Five Guys #MI-0494', 1)
   (u'Fuddruckers', 1)
   (u'Great Plains Burger Co.', 1)
   (u'Halo Burger', 1)
```
Never tried Culver's, but definitely worth a visit !

## A fragmented map
The biggest improvement I see going forward is much of the map remains incomplete. Judging from the results from the queried, there are many points of interest not entered into the dataset. <br>
As something I may look into - is adding more tags about current nodes to create a more comprehensive database. Some challenges associated with this task may be getting a reliable data source, identifying all the nodes required such tags, and standardizing the tag format for future users looking to contribute. One issue with the current dataset is many nodes are missing information on "zip-code", "city", "cuisine" value if they are restuarants. A good starting point is to revisit these nodes and assign the correct information to them. Unless there is a data base where I can easily match one value to another to fill in the missing information, the task will be manual, and quite arduous. 
