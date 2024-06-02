from libraries import * 
from constants import *

# Inserts a decimal on position k
def insert_decimal(number, k):
    if number is None:
        return None
    else:
        num_str = str(number).replace('.', '')
        num_str = num_str[:k] + '.' + num_str[k:]
        return float(num_str)
    

# Filters only points which are on polygons
def filter_points_within_polygon(points, polygon, lat_column='latitude', lon_column='longitude'):
    # Create a Shapely Point geometry column from latitude and longitude
    points['geometry'] = gpd.points_from_xy(points[lon_column], points[lat_column])
    
    # Convert the points DataFrame to a GeoDataFrame
    gdf_points = gpd.GeoDataFrame(points, geometry='geometry')
    
    # Filter points within the polygon
    filtered_points = gdf_points[gdf_points.geometry.within(polygon)]
    
    return filtered_points


# Obtains all streets in urban polygons using Open street map
def get_streets_within_polygon(polygon):
    bbox = polygon.bounds
    # Fetch streets within the bounding box
    streets = ox.graph_from_bbox(north=bbox[3], south=bbox[1], east=bbox[2], west=bbox[0], network_type='all')
    
    # Convert the graph to a GeoDataFrame
    streets_gdf = ox.graph_to_gdfs(streets, nodes=False, edges=True)
    
    # Filter streets in the bounding box to only those within the polygon
    streets_within_polygon = streets_gdf[streets_gdf.intersects(polygon)]
    
    return streets_within_polygon


# Samples points from the streets
def sample_points_on_streets(edges, num_points=4):
    sampled_points = []
    for _, row in edges.iterrows():
        line = row.geometry
        if isinstance(line, LineString):
            length = line.length
            distances = np.linspace(0, length, num_points)
            points = [line.interpolate(distance) for distance in distances]
            sampled_points.extend(points)
    return sampled_points


# Removes points which are too close
def remove_close_points(gdf, min_distance):
    # Convert the GeoDataFrame to a numpy array of coordinates
    coords = np.array([[point.x, point.y] for point in gdf.geometry])
    
    # Build a KDTree for fast spatial indexing
    tree = KDTree(coords)
    
    # Find pairs of points within the specified minimum distance
    pairs = tree.query_pairs(min_distance)
    
    # Create a set to track points to keep
    to_keep = set(range(len(gdf)))
    
    for i, j in pairs:
        # Keep the first point and remove the second point in each pair
        if j in to_keep:
            to_keep.remove(j)
    
    # Filter the GeoDataFrame to keep only the required points
    filtered_gdf = gdf.iloc[list(to_keep)]
    
    return filtered_gdf


# Extracts latitude and longitude from geometry value
def get_coordinates_from_geometry(geometry):
    match = re.match(r'POINT \(([^ ]+) ([^ ]+)\)', geometry)
    if match:
        longitude, latitude = match.groups()
        return float(latitude), float(longitude)


# Calculates walking distance between two sets of coordinates
def calculate_distance(origin, destination):
    result = gmaps.distance_matrix(origins = [origin], destinations = [destination], mode = "walking")
        
    # Check if the response contains the distance information
    if 'rows' in result and len(result['rows']) > 0:
        elements = result['rows'][0]['elements']
        if len(elements) > 0 and 'distance' in elements[0]:
            # Parse the result and extract the walking distance 
            return elements[0]['distance']['value'] # Distance in meters


# Replaces all 1's with calculated distances
def replace_1_with_distances(flag_matrix):
    for i in range(flag_matrix.shape[0]):
        for j in range(flag_matrix.shape[1]):
            if flag_matrix.iat[i, j] == 1:
                flag_matrix.iat[i, j] = calculate_distance(flag_matrix.index[i], flag_matrix.columns[j])

    return flag_matrix


# Calculates cost matrix for given sets of cards and aeds
def get_cost_matrix(cards, aeds, city, num_closest_aeds):
    distance_matrix = cdist(cards[city], aeds[city], metric = 'euclidean')  # Transposed
    flag_matrix = np.zeros_like(distance_matrix)

    for row in range(distance_matrix.shape[0]):
        row_indices = np.argsort(distance_matrix[row, :])[:num_closest_aeds]
        flag_matrix[row, row_indices] = 1

    # Column names
    cards_str = cards[city].apply(lambda x: f"{x['latitude']}, {x['longitude']}", axis = 1)
    flag_matrix = pd.DataFrame(flag_matrix, index = cards_str, columns = aeds[city].apply(tuple, axis = 1))
    flag_matrix.replace(0, INF_LENGTH, inplace=True)

    confirmation = input(f"This will initialize {len(flag_matrix) * num_closest_aeds} API requests. Are you sure? (yes/no): ")
    if confirmation == "yes":            
        # Replace all marked cells with real calculated distances
        return(replace_1_with_distances(flag_matrix))
    else:
        print("OK. Will not procced.\n")
        return(np.zeros_like(flag_matrix))

# Converts any format of coordinates into a tuple
def make_coordinates_tuple(s):
    s = str(s)
    s = s.split('(')[1].split(')')[0].split(', ')
    s = map(float, s)
    return tuple(s)