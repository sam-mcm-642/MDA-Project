from libraries import *

data_path = "/Users/Jovan/Desktop/MDA-Project/Data"
belgium_polygons_path = "/BelgiumUrbanPolygons/BE_STATBEL_SH_SU_UA_CITY_2019_v60.gpkg"

original_path = "/0_DataOriginal"
clean_path = "/1_DataClean"
possible_locations_path = "/2_PossibleLocations"
optimal_indicators_path = "/3_OptimalIndicators"
app_path = "/4_DataApp"

GOOGLE_API_KEY = "AIzaSyAxfHDWbGY-RNCky0QA0Kgr24xtDHhSa6c"
gmaps = googlemaps.Client(key = GOOGLE_API_KEY)

cardiac_codes = ["P003", "P011", "P039"]
cities = ["Antwerpen", "Brugge", "Brussels", "Charleroi", "Gent", "Leuven", "Liege", "Oostende"]

BELGIUM_NORTH = 52
BELGIUM_SOUTH = 49
BELGIUM_WEST = 2.5
BELGIUM_EAST = 6.4

SEED = 42
TEST_SIZE = 0.25
SAMPLE_SIZE = 0.015
MIN_DISTANCE = 0.0012

INF_LENGTH = 1000
CLOSEST_AEDS = 10
COVERAGE_RADIUS = 150